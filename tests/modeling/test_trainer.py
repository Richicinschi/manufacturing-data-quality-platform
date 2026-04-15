"""Tests for src/modeling/trainer.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modeling.trainer import run_walk_forward_cv


def _make_daily_data(n_days: int, samples_per_day: int, n_fails_per_day: int, n_features: int, seed: int = 42):
    np.random.seed(seed)
    timestamps = pd.to_datetime(
        [d for day in pd.date_range("2024-01-01", periods=n_days, freq="D") for d in [day] * samples_per_day]
    )
    X = pd.DataFrame(
        np.random.randn(len(timestamps), n_features),
        columns=[f"feat_{i}" for i in range(n_features)],
    )
    y_values = []
    for _ in range(n_days):
        y_values.extend([1] * n_fails_per_day + [0] * (samples_per_day - n_fails_per_day))
    y = pd.Series(y_values)
    return X, y, timestamps


def test_run_walk_forward_cv_produces_results_and_oof():
    X, y, timestamps = _make_daily_data(n_days=5, samples_per_day=20, n_fails_per_day=4, n_features=10)

    feature_sets = {
        "keep_only": [f"feat_{i}" for i in range(5)],
        "keep_plus_review": [f"feat_{i}" for i in range(8)],
        "top_20_effect": [],
        "top_50_effect": [],
        "top_100_effect": [],
    }

    cv_results, oof_df = run_walk_forward_cv(
        X, y, timestamps, feature_sets, n_splits=3, min_fails=2
    )

    assert len(cv_results) > 0
    assert "model" in cv_results.columns
    assert "feature_set" in cv_results.columns
    assert "pr_auc" in cv_results.columns
    assert len(oof_df) == len(X)
    assert "y_true" in oof_df.columns

    # Verify per-(model, feature_set) OOF columns exist
    assert "oof_prob_dummy_keep_only" in oof_df.columns
    assert "oof_prob_dummy_keep_plus_review" in oof_df.columns
    assert "oof_prob_logistic_l1_keep_only" in oof_df.columns


def test_oof_predictions_differ_across_feature_sets():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=20, n_fails_per_day=6, n_features=6)

    feature_sets = {
        "fs_a": ["feat_0", "feat_1"],
        "fs_b": ["feat_2", "feat_3", "feat_4"],
    }

    cv_results, oof_df = run_walk_forward_cv(
        X, y, timestamps, feature_sets, n_splits=2, min_fails=2
    )

    # Dummy ignores features, so skip it; real models should differ.
    real_models = [m for m in cv_results["model"].unique() if m != "dummy"]
    assert len(real_models) > 0
    for model in real_models:
        col_a = f"oof_prob_{model}_fs_a"
        col_b = f"oof_prob_{model}_fs_b"
        assert col_a in oof_df.columns
        assert col_b in oof_df.columns
        valid_a = oof_df[col_a].dropna()
        valid_b = oof_df[col_b].dropna()
        if len(valid_a) > 0 and len(valid_b) > 0:
            # OOF values should not be identical across feature sets
            assert not valid_a.equals(valid_b), f"OOF for {model} should differ between feature sets"


def test_all_models_train_without_error():
    X, y, timestamps = _make_daily_data(n_days=3, samples_per_day=10, n_fails_per_day=3, n_features=4, seed=7)

    feature_sets = {
        "keep_only": ["a", "b"],
    }
    # Rename columns to match
    X.columns = ["a", "b", "c", "d"]

    cv_results, _ = run_walk_forward_cv(X, y, timestamps, feature_sets, n_splits=2, min_fails=1)
    models_trained = set(cv_results["model"].unique())
    assert "dummy" in models_trained
    assert "logistic_l1" in models_trained
    assert "random_forest" in models_trained
