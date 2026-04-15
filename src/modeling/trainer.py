"""Model trainer with walk-forward CV and per-fold feature selection."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.modeling.cv_engine import expanding_window_splits
from src.modeling.features import compute_top_n_effect_features

MODEL_REGISTRY = {
    "dummy": lambda: DummyClassifier(strategy="stratified", random_state=42),
    "logistic_l1": lambda: LogisticRegression(
        class_weight="balanced",
        solver="liblinear",
        max_iter=1000,
        C=1.0,
        random_state=42,
    ),
    "random_forest": lambda: RandomForestClassifier(
        class_weight="balanced",
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    ),
}


def run_walk_forward_cv(
    X: pd.DataFrame,
    y: pd.Series,
    timestamps: pd.Series,
    feature_sets: dict[str, list[str]],
    n_splits: int = 4,
    min_fails: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run walk-forward CV for all models and feature sets.

    Args:
        X: Feature DataFrame with NaNs preserved.
        y: Binary labels.
        timestamps: Timestamps.
        feature_sets: Dict of feature set name -> list of feature names.
                      Must include 'keep_only' and 'keep_plus_review'.
                      'top_20_effect', 'top_50_effect', 'top_100_effect' are handled dynamically.
        n_splits: Target CV splits.
        min_fails: Minimum fails per fold.

    Returns:
        (cv_results_df, oof_predictions_df)
            cv_results_df: one row per (model, feature_set, fold)
            oof_predictions_df: one row per sample with OOF probability columns
    """
    splits = expanding_window_splits(X, y, timestamps, n_splits=n_splits, min_fails=min_fails)
    actual_n_splits = len(splits)

    # Ensure OOF predictions align with original index, keyed by (model, feature_set)
    oof_keys = [(name, fs) for name in MODEL_REGISTRY for fs in feature_sets]
    oof_probs = {key: np.full(len(X), np.nan) for key in oof_keys}

    records = []

    for model_name, model_factory in MODEL_REGISTRY.items():
        for fs_name, fs_features in feature_sets.items():
            for fold_idx, (train_idx, test_idx) in enumerate(splits, start=1):
                X_train_full = X.iloc[train_idx]
                y_train = y.iloc[train_idx]
                X_test_full = X.iloc[test_idx]
                y_test = y.iloc[test_idx]

                # Resolve feature list (dynamic effect-size lists computed inside fold)
                if fs_name == "top_20_effect":
                    selected_features = compute_top_n_effect_features(X_train_full, y_train, 20)
                elif fs_name == "top_50_effect":
                    selected_features = compute_top_n_effect_features(X_train_full, y_train, 50)
                elif fs_name == "top_100_effect":
                    selected_features = compute_top_n_effect_features(X_train_full, y_train, 100)
                else:
                    selected_features = fs_features

                if len(selected_features) == 0:
                    continue

                # Fit imputer on training fold only
                imputer = SimpleImputer(strategy="median")
                X_train_imp = imputer.fit_transform(X_train_full[selected_features])
                X_test_imp = imputer.transform(X_test_full[selected_features])
                imputed_features = imputer.get_feature_names_out().tolist()
                X_train = pd.DataFrame(
                    X_train_imp,
                    columns=imputed_features,
                    index=X_train_full.index,
                )
                X_test = pd.DataFrame(
                    X_test_imp,
                    columns=imputed_features,
                    index=X_test_full.index,
                )

                model = model_factory()
                model.fit(X_train, y_train)

                probs = model.predict_proba(X_test)[:, 1]
                preds = (probs >= 0.5).astype(int)

                # Store OOF probabilities per (model, feature_set)
                oof_probs[(model_name, fs_name)][test_idx] = probs

                records.append(
                    {
                        "model": model_name,
                        "feature_set": fs_name,
                        "fold": fold_idx,
                        "n_splits": actual_n_splits,
                        "n_features": len(selected_features),
                        "pr_auc": average_precision_score(y_test, probs),
                        "roc_auc": roc_auc_score(y_test, probs) if len(np.unique(y_test)) > 1 else np.nan,
                        "precision": precision_score(y_test, preds, zero_division=0),
                        "recall": recall_score(y_test, preds, zero_division=0),
                        "f1": f1_score(y_test, preds, zero_division=0),
                    }
                )

    cv_results = pd.DataFrame(records)

    oof_df = pd.DataFrame(
        {
            "entity_index": np.arange(len(X)),
            "timestamp": timestamps.values,
            "y_true": y.values,
        }
    )
    for (model_name, fs_name), probs in oof_probs.items():
        col_name = f"oof_prob_{model_name}_{fs_name}"
        oof_df[col_name] = probs

    return cv_results, oof_df
