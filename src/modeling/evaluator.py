"""Final evaluation: holdout split, best model selection, artifact saving."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.modeling.features import compute_top_n_effect_features
from src.modeling.trainer import MODEL_REGISTRY


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
    """Identify best (model, feature_set) by mean PR-AUC across folds."""
    benchmark = (
        cv_results.groupby(["model", "feature_set"])["pr_auc"]
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

    Returns dict with results, confusion matrices, and artifact path.
    """
    artifact_path = Path(artifact_dir)
    artifact_path.mkdir(parents=True, exist_ok=True)

    # Resolve feature list
    if best_feature_set_name == "top_20_effect":
        selected_features = compute_top_n_effect_features(X_dev, y_dev, 20)
    elif best_feature_set_name == "top_50_effect":
        selected_features = compute_top_n_effect_features(X_dev, y_dev, 50)
    elif best_feature_set_name == "top_100_effect":
        selected_features = compute_top_n_effect_features(X_dev, y_dev, 100)
    else:
        selected_features = static_feature_sets.get(best_feature_set_name, X_dev.columns.tolist())

    if len(selected_features) == 0:
        raise ValueError("Selected feature set is empty.")

    # Fit imputer on dev data only
    imputer = SimpleImputer(strategy="median")
    X_dev_imp = pd.DataFrame(
        imputer.fit_transform(X_dev[selected_features]),
        columns=selected_features,
        index=X_dev.index,
    )
    X_test_imp = pd.DataFrame(
        imputer.transform(X_test[selected_features]),
        columns=selected_features,
        index=X_test.index,
    )

    model = MODEL_REGISTRY[best_model_name]()
    model.fit(X_dev_imp, y_dev)

    test_probs = model.predict_proba(X_test_imp)[:, 1]
    test_preds = (test_probs >= threshold).astype(int)

    results = {
        "model": best_model_name,
        "feature_set": best_feature_set_name,
        "n_features": len(selected_features),
        "threshold": threshold,
        "test_pr_auc": float(average_precision_score(y_test, test_probs)),
        "test_roc_auc": float(roc_auc_score(y_test, test_probs)),
        "test_precision": float(precision_score(y_test, test_preds, zero_division=0)),
        "test_recall": float(recall_score(y_test, test_preds, zero_division=0)),
        "test_f1": float(f1_score(y_test, test_preds, zero_division=0)),
    }

    cm_test = confusion_matrix(y_test, test_preds)
    confusion = {
        "test_tn": int(cm_test[0, 0]),
        "test_fp": int(cm_test[0, 1]),
        "test_fn": int(cm_test[1, 0]),
        "test_tp": int(cm_test[1, 1]),
    }

    # Save artifact
    joblib.dump(model, artifact_path / "secom_model.joblib")
    metadata = {
        "model": best_model_name,
        "feature_set": best_feature_set_name,
        "features": selected_features,
        "threshold": threshold,
        "results": results,
    }
    with open(artifact_path / "secom_model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    return {
        "results": results,
        "confusion": confusion,
        "artifact_path": str(artifact_path / "secom_model.joblib"),
        "features": selected_features,
    }
