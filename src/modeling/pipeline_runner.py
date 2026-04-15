"""Shared modeling pipeline runner with memoization for mart builders."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.modeling.data import load_modeling_data
from src.modeling.evaluator import (
    evaluate_final_model,
    find_best_model,
    split_dev_test,
)
from src.modeling.features import build_feature_sets
from src.modeling.threshold import select_threshold
from src.modeling.trainer import run_walk_forward_cv


@lru_cache(maxsize=1)
def _run_pipeline_cached(connection_string: str | None) -> tuple:
    """Run the full modeling pipeline once and cache results.

    Returns tuple of:
        (X, y, timestamps, feature_sets,
         cv_results, oof_df,
         X_dev, y_dev, X_test, y_test,
         best_info, threshold, threshold_df,
         final_eval)
    """
    X, y, timestamps = load_modeling_data(connection_string=connection_string)
    feature_sets = build_feature_sets(connection_string=connection_string)
    # Add dynamic feature set placeholders (resolved inside CV)
    feature_sets["top_20_effect"] = []
    feature_sets["top_50_effect"] = []
    feature_sets["top_100_effect"] = []

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

    oof_col = f"oof_prob_{best_model_name}_{best_feature_set_name}"
    threshold, threshold_df = select_threshold(
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
    )

    return (
        X, y, timestamps,
        feature_sets,
        cv_results, oof_df,
        X_dev, y_dev, X_test, y_test,
        best_info, threshold, threshold_df,
        final_eval,
    )


def get_pipeline_results(connection_string: str | None = None) -> dict:
    """Run (or retrieve cached) modeling pipeline and return all artifacts as a dict."""
    (
        X, y, timestamps,
        feature_sets,
        cv_results, oof_df,
        X_dev, y_dev, X_test, y_test,
        best_info, threshold, threshold_df,
        final_eval,
    ) = _run_pipeline_cached(connection_string)

    benchmark = (
        cv_results.groupby(["model", "feature_set"])
        .agg(
            mean_pr_auc=("pr_auc", "mean"),
            std_pr_auc=("pr_auc", "std"),
            mean_roc_auc=("roc_auc", "mean"),
            mean_f1=("f1", "mean"),
        )
        .reset_index()
    )
    benchmark["rank"] = benchmark["mean_pr_auc"].rank(ascending=False, method="dense").astype(int)
    benchmark = benchmark.sort_values("rank").reset_index(drop=True)

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
        "final_eval": final_eval,
        "benchmark": benchmark,
    }
