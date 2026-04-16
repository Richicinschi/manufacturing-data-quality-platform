"""Final evaluation: holdout split, best model selection, artifact saving."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.modeling.features import compute_top_n_effect_features
from src.modeling.inspection import build_inspection_curve, compute_inspection_metrics
from src.modeling.trainer import (
    MODEL_REGISTRY,
    _resolve_feature_set,
    is_model_enabled,
    preprocess_fold,
    ModelSpec,
    _get_risk_scores,
)


def split_dev_test(
    X: pd.DataFrame,
    y: pd.Series,
    timestamps: pd.Series,
    test_size: float = 0.15,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Chronological split at whole-date boundaries: oldest (1-test_size) = dev, newest test_size = test."""
    dates = pd.to_datetime(timestamps).dt.date
    unique_dates = dates.unique()
    n_test_dates = max(1, int(round(len(unique_dates) * test_size)))
    n_dev_dates = len(unique_dates) - n_test_dates
    if n_dev_dates <= 0:
        n_dev_dates = len(unique_dates) - 1
        n_test_dates = len(unique_dates) - n_dev_dates

    dev_dates = set(unique_dates[:n_dev_dates])
    test_dates = set(unique_dates[n_dev_dates:])

    dev_mask = dates.isin(dev_dates)
    test_mask = dates.isin(test_dates)

    return (
        X.loc[dev_mask].reset_index(drop=True),
        y.loc[dev_mask].reset_index(drop=True),
        X.loc[test_mask].reset_index(drop=True),
        y.loc[test_mask].reset_index(drop=True),
    )


def find_best_model(cv_results: pd.DataFrame) -> dict[str, str]:
    """Identify best (model, feature_set) by mean PR-AUC across folds among final-eligible models."""
    eligible = cv_results[cv_results["final_eligible"] & cv_results["enabled"]]
    if eligible.empty:
        raise ValueError("No final-eligible, enabled models found in CV results.")

    benchmark = (
        eligible.groupby(["model", "feature_set"])["pr_auc"]
        .mean()
        .reset_index()
        .sort_values("pr_auc", ascending=False)
    )
    best = benchmark.iloc[0]
    return {
        "model": str(best["model"]),
        "feature_set": str(best["feature_set"]),
        "mean_pr_auc": float(best["pr_auc"]),
    }


def _extract_feature_importance(model, feature_names: list[str]) -> pd.DataFrame:
    """Extract feature importance from a fitted model."""
    importance_type = "not_available"
    importances = None

    if hasattr(model, "feature_importances_"):
        importances = np.asarray(model.feature_importances_)
        importance_type = "native"
    elif hasattr(model, "coef_"):
        importances = np.abs(np.asarray(model.coef_)).ravel()
        importance_type = "abs_coefficient"

    if importances is None or len(importances) != len(feature_names):
        importances = np.zeros(len(feature_names))
        importance_type = "not_available"

    df = pd.DataFrame(
        {
            "feature_name": feature_names,
            "importance": importances,
            "importance_type": importance_type,
        }
    )
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def evaluate_final_model(
    X_dev: pd.DataFrame,
    y_dev: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    best_model_name: str,
    best_feature_set_name: str,
    static_feature_sets: dict[str, list[str]],
    threshold: float,
    artifact_dir: str | Path = "artifacts",
) -> dict:
    """Retrain best model on full dev set and evaluate on test set.

    Returns dict with results, confusion matrices, artifact path, and feature importance.
    """
    artifact_path = Path(artifact_dir)
    artifact_path.mkdir(parents=True, exist_ok=True)

    model_spec = MODEL_REGISTRY.get(best_model_name)
    if model_spec is None:
        raise ValueError(f"Unknown model: {best_model_name}")

    # Resolve feature list on full dev set
    fallback_features = static_feature_sets.get(best_feature_set_name, X_dev.columns.tolist())
    selected_features, X_dev_resolved, _ = _resolve_feature_set(
        best_feature_set_name, X_dev, y_dev, fallback_features, static_feature_sets
    )

    if best_feature_set_name == "missingness_indicators_keep":
        base = static_feature_sets.get("keep_only", X_dev.columns.tolist())
        X_test_resolved = X_test[base].copy()
        indicators = {
            f"{col}_missing": X_test_resolved[col].isna().astype(int)
            for col in base
            if f"{col}_missing" in selected_features
        }
        if indicators:
            X_test_resolved = pd.concat(
                [X_test_resolved, pd.DataFrame(indicators, index=X_test_resolved.index)], axis=1
            )
    else:
        X_test_resolved = X_test

    if len(selected_features) == 0:
        raise ValueError("Selected feature set is empty.")

    # Fold-local preprocessing on dev data
    preprocessed = preprocess_fold(X_dev_resolved, X_test_resolved, selected_features, model_spec)
    X_dev_imp = preprocessed["X_train"]
    X_test_imp = preprocessed["X_test"]
    imputed_features = X_dev_imp.columns.tolist()
    dropped_features = preprocessed["dropped_all_missing_features"]
    imputer = preprocessed.get("imputer")
    scaler = preprocessed.get("scaler")

    model = model_spec.factory(y_dev)

    if model_spec.model_kind == "anomaly_detector":
        if model_spec.fit_mode == "pass_only":
            pass_mask = y_dev.values == 0
            if pass_mask.sum() == 0:
                raise ValueError("No pass-class samples for pass-only anomaly detector.")
            model.fit(X_dev_imp.iloc[pass_mask])
        else:
            model.fit(X_dev_imp)
    else:
        model.fit(X_dev_imp, y_dev)

    test_scores = _get_risk_scores(model, X_test_imp, model_spec)
    test_preds = (test_scores >= threshold).astype(int)

    results = {
        "model": best_model_name,
        "feature_set": best_feature_set_name,
        "n_features": len(imputed_features),
        "threshold": threshold,
        "test_pr_auc": float(average_precision_score(y_test, test_scores)),
        "test_roc_auc": float(roc_auc_score(y_test, test_scores)) if len(np.unique(y_test)) > 1 else float("nan"),
        "test_precision": float(precision_score(y_test, test_preds, zero_division=0)),
        "test_recall": float(recall_score(y_test, test_preds, zero_division=0)),
        "test_f1": float(f1_score(y_test, test_preds, zero_division=0)),
        "test_scores": test_scores.tolist(),
    }

    cm_test = confusion_matrix(y_test, test_preds)
    confusion = {
        "test_tn": int(cm_test[0, 0]),
        "test_fp": int(cm_test[0, 1]),
        "test_fn": int(cm_test[1, 0]),
        "test_tp": int(cm_test[1, 1]),
    }

    feature_importance = _extract_feature_importance(model, imputed_features)

    # Inspection curve on final test set
    inspection_curve = build_inspection_curve(y_test, test_scores, n_points=20)
    inspection_metrics = compute_inspection_metrics(y_test, test_scores)

    # Save deployable artifact with model + preprocessing + selector metadata
    artifact = {
        "model": model,
        "imputer": imputer,
        "scaler": scaler,
        "features": imputed_features,
        "dropped_features": dropped_features,
        "model_name": best_model_name,
        "feature_set_name": best_feature_set_name,
        "threshold": threshold,
        "model_kind": model_spec.model_kind,
        "score_method": model_spec.score_method,
        "higher_score_is_failure_risk": model_spec.higher_score_is_failure_risk,
        "selector_metadata": {
            "feature_set_name": best_feature_set_name,
            "n_features_selected": len(imputed_features),
            "selected_features": imputed_features,
            "dropped_features": dropped_features,
        },
    }
    joblib.dump(artifact, artifact_path / "secom_model.joblib")
    metadata = {
        "model": best_model_name,
        "feature_set": best_feature_set_name,
        "features": imputed_features,
        "dropped_features": dropped_features,
        "threshold": threshold,
        "results": results,
        "inspection_metrics": inspection_metrics,
    }
    with open(artifact_path / "secom_model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    return {
        "results": results,
        "confusion": confusion,
        "artifact_path": str(artifact_path / "secom_model.joblib"),
        "features": imputed_features,
        "feature_importance": feature_importance,
        "imputer": imputer,
        "scaler": scaler,
        "inspection_curve": inspection_curve,
        "inspection_metrics": inspection_metrics,
    }
