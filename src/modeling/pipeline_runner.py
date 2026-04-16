"""Shared modeling pipeline runner with memoization for mart builders."""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
import pandas as pd

from src.modeling.data import load_modeling_data
from src.modeling.evaluator import (
    evaluate_final_model,
    find_best_model,
    split_dev_test,
)
from src.modeling.features import build_feature_sets
from src.modeling.threshold import (
    build_probability_bins,
    build_threshold_cost_curve,
    select_threshold,
)
from src.modeling.trainer import MODEL_REGISTRY, _is_installed, run_walk_forward_cv


@lru_cache(maxsize=1)
def _run_pipeline_cached(connection_string: str | None) -> tuple:
    """Run the full modeling pipeline once and cache results.

    Returns tuple of:
        (X, y, timestamps, feature_sets,
         cv_results, oof_df,
         X_dev, y_dev, X_test, y_test,
         best_info, threshold, threshold_df, threshold_cost_curve,
         probability_bins,
         final_eval)
    """
    X, y, timestamps = load_modeling_data(connection_string=connection_string)
    feature_sets = build_feature_sets(connection_string=connection_string)
    # Add dynamic feature set placeholders (resolved inside CV)
    feature_sets["top_20_effect"] = []
    feature_sets["top_50_effect"] = []
    feature_sets["top_100_effect"] = []
    feature_sets["correlation_pruned_070"] = []
    feature_sets["correlation_pruned_085"] = []
    feature_sets["top_25_mutual_info"] = []
    feature_sets["top_50_mutual_info"] = []
    feature_sets["top_25_auc_gap"] = []
    feature_sets["top_50_auc_gap"] = []
    feature_sets["missingness_indicators_keep"] = []

    # Chronological dev/test split at whole-date boundaries
    X_dev, y_dev, X_test, y_test = split_dev_test(X, y, timestamps, test_size=0.15)
    dev_timestamps = timestamps.loc[X_dev.index]

    # Walk-forward CV on development set only
    cv_results, oof_df = run_walk_forward_cv(
        X_dev, y_dev, dev_timestamps, feature_sets, n_splits=4, min_fails=8
    )

    best_info = find_best_model(cv_results)
    best_model_name = best_info["model"]
    best_feature_set_name = best_info["feature_set"]

    oof_col = f"oof_risk_{best_model_name}_{best_feature_set_name}"
    threshold, threshold_df = select_threshold(
        oof_df["y_true"].values,
        oof_df[oof_col].values,
    )
    threshold_cost_curve = build_threshold_cost_curve(
        oof_df["y_true"].values,
        oof_df[oof_col].values,
    )

    static_feature_sets = {
        "keep_only": feature_sets["keep_only"],
        "keep_plus_review": feature_sets["keep_plus_review"],
    }

    final_eval = evaluate_final_model(
        X_dev=X_dev,
        y_dev=y_dev,
        X_test=X_test,
        y_test=y_test,
        best_model_name=best_model_name,
        best_feature_set_name=best_feature_set_name,
        static_feature_sets=static_feature_sets,
        threshold=threshold,
        artifact_dir=os.environ.get("SECOM_ARTIFACT_DIR", "artifacts"),
    )

    test_scores = np.asarray(final_eval["results"]["test_scores"])
    probability_bins = build_probability_bins(y_test.values, test_scores)

    return (
        X, y, timestamps,
        feature_sets,
        cv_results, oof_df,
        X_dev, y_dev, X_test, y_test,
        best_info, threshold, threshold_df, threshold_cost_curve,
        probability_bins,
        final_eval,
    )


def get_pipeline_results(connection_string: str | None = None) -> dict:
    """Run (or retrieve cached) modeling pipeline and return all artifacts as a dict."""
    (
        X, y, timestamps,
        feature_sets,
        cv_results, oof_df,
        X_dev, y_dev, X_test, y_test,
        best_info, threshold, threshold_df, threshold_cost_curve,
        probability_bins,
        final_eval,
    ) = _run_pipeline_cached(connection_string)

    agg_dict = {
        "mean_pr_auc": ("pr_auc", "mean"),
        "std_pr_auc": ("pr_auc", "std"),
        "mean_roc_auc": ("roc_auc", "mean"),
        "mean_f1": ("f1", "mean"),
        "mean_precision": ("precision", "mean"),
        "mean_recall": ("recall", "mean"),
        "mean_balanced_accuracy": ("balanced_accuracy", "mean"),
        "mean_recall_at_05pct": ("recall_at_05pct", "mean"),
        "mean_precision_at_05pct": ("precision_at_05pct", "mean"),
        "mean_lift_at_05pct": ("lift_at_05pct", "mean"),
        "mean_recall_at_10pct": ("recall_at_10pct", "mean"),
        "mean_precision_at_10pct": ("precision_at_10pct", "mean"),
        "mean_lift_at_10pct": ("lift_at_10pct", "mean"),
        "mean_recall_at_20pct": ("recall_at_20pct", "mean"),
        "mean_precision_at_20pct": ("precision_at_20pct", "mean"),
        "mean_lift_at_20pct": ("lift_at_20pct", "mean"),
    }

    benchmark = cv_results.groupby(["model", "feature_set"]).agg(**agg_dict).reset_index()

    # Merge static metadata back in
    meta = (
        cv_results.groupby(["model", "feature_set"])
        .agg(
            model_family=("model_family", "first"),
            model_kind=("model_kind", "first"),
            final_eligible=("final_eligible", "first"),
            enabled=("enabled", "first"),
        )
        .reset_index()
    )
    benchmark = benchmark.merge(meta, on=["model", "feature_set"], how="left")
    benchmark["rank"] = benchmark["mean_pr_auc"].rank(ascending=False, method="dense").astype(int)

    # Best for inspection policy (separate from PR-AUC rank)
    eligible = benchmark[benchmark["final_eligible"] & benchmark["enabled"]]
    if not eligible.empty:
        best_inspection = eligible.sort_values("mean_recall_at_10pct", ascending=False).iloc[0]
        benchmark["best_for_inspection_policy"] = (
            (benchmark["model"] == best_inspection["model"]) &
            (benchmark["feature_set"] == best_inspection["feature_set"])
        )
    else:
        benchmark["best_for_inspection_policy"] = False

    benchmark = benchmark.sort_values("rank").reset_index(drop=True)

    # Build model registry DataFrame
    registry_rows = []
    for model_id, spec in MODEL_REGISTRY.items():
        registry_rows.append({
            "model_id": model_id,
            "model_family": spec.family,
            "model_kind": spec.model_kind,
            "fit_mode": spec.fit_mode,
            "score_method": spec.score_method,
            "final_eligible": spec.final_eligible,
            "enabled": spec.optional_dependency is None or _is_installed(spec.optional_dependency),
            "skip_reason": "optional dependency missing" if (spec.optional_dependency is not None and not _is_installed(spec.optional_dependency)) else "",
        })
    model_registry_df = pd.DataFrame(registry_rows)

    feature_importance_df = final_eval.get("feature_importance", pd.DataFrame())
    inspection_curve_df = final_eval.get("inspection_curve", pd.DataFrame())
    inspection_metrics_dict = final_eval.get("inspection_metrics", {})

    return {
        "X": X,
        "y": y,
        "timestamps": timestamps,
        "feature_sets": feature_sets,
        "cv_results": cv_results,
        "oof_df": oof_df,
        "X_dev": X_dev,
        "y_dev": y_dev,
        "X_test": X_test,
        "y_test": y_test,
        "best_info": best_info,
        "threshold": threshold,
        "threshold_df": threshold_df,
        "threshold_cost_curve": threshold_cost_curve,
        "probability_bins": probability_bins,
        "final_eval": final_eval,
        "benchmark": benchmark,
        "model_registry": model_registry_df,
        "feature_importance": feature_importance_df,
        "inspection_curve": inspection_curve_df,
        "inspection_metrics": inspection_metrics_dict,
    }
