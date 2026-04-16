"""Tests for src/modeling/features.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modeling.features import (
    build_feature_sets,
    build_missingness_indicator_features,
    compute_correlation_pruned_features,
    compute_top_n_auc_gap_features,
    compute_top_n_effect_features,
    compute_top_n_mutual_info_features,
)


def test_build_feature_sets_returns_non_empty_lists():
    feature_sets = build_feature_sets()
    assert "keep_only" in feature_sets
    assert "keep_plus_review" in feature_sets
    assert len(feature_sets["keep_only"]) > 0
    assert len(feature_sets["keep_plus_review"]) >= len(feature_sets["keep_only"])
    # All features are strings starting with feature_
    for name in feature_sets["keep_plus_review"]:
        assert name.startswith("feature_")


def test_compute_top_n_effect_features_returns_expected_count():
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    X = pd.DataFrame(np.random.randn(n_samples, n_features), columns=[f"feat_{i}" for i in range(n_features)])
    # Make feat_0 strongly separated
    y = pd.Series([0] * 50 + [1] * 50)
    X.iloc[:50, 0] += 2.0
    X.iloc[50:, 0] -= 2.0

    top_3 = compute_top_n_effect_features(X, y, 3)
    assert len(top_3) == 3
    assert "feat_0" in top_3


def test_compute_top_n_effect_features_respects_n():
    np.random.seed(7)
    X = pd.DataFrame(np.random.randn(20, 5), columns=[f"f{i}" for i in range(5)])
    y = pd.Series([0] * 10 + [1] * 10)
    top_2 = compute_top_n_effect_features(X, y, 2)
    assert len(top_2) == 2
    top_10 = compute_top_n_effect_features(X, y, 10)
    assert len(top_10) == 5


def test_correlation_pruning_drops_correlated_features():
    X = pd.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": [1.0, 2.0, 3.0, 4.0, 5.0],  # perfectly correlated with a
        "c": [5.0, 4.0, 3.0, 2.0, 1.0],  # perfectly anti-correlated
    })
    kept = compute_correlation_pruned_features(X, threshold=0.90)
    assert "a" in kept
    # b should be dropped because it is highly correlated with a
    assert "b" not in kept
    # c is also perfectly correlated in absolute terms
    assert "c" not in kept


def test_correlation_pruning_085_keeps_more_than_070():
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(50, 5), columns=[f"f{i}" for i in range(5)])
    # Make f0 and f1 correlated
    X["f1"] = X["f0"] + np.random.randn(50) * 0.1
    kept_070 = compute_correlation_pruned_features(X, threshold=0.70)
    kept_085 = compute_correlation_pruned_features(X, threshold=0.85)
    assert len(kept_085) >= len(kept_070)


def test_mutual_info_selector_returns_exactly_top_n():
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(100, 5), columns=[f"f{i}" for i in range(5)])
    y = pd.Series([0] * 50 + [1] * 50)
    # Make f0 strongly predictive
    X.iloc[:50, 0] += 3.0
    X.iloc[50:, 0] -= 3.0
    top = compute_top_n_mutual_info_features(X, y, n=3, random_state=42)
    assert len(top) == 3
    assert "f0" in top


def test_mutual_info_selector_deterministic():
    np.random.seed(7)
    X = pd.DataFrame(np.random.randn(60, 4), columns=[f"f{i}" for i in range(4)])
    y = pd.Series([0] * 30 + [1] * 30)
    top_a = compute_top_n_mutual_info_features(X, y, n=2, random_state=42)
    top_b = compute_top_n_mutual_info_features(X, y, n=2, random_state=42)
    assert top_a == top_b


def test_auc_gap_selector_ranks_predictive_above_noise():
    np.random.seed(42)
    X = pd.DataFrame({
        "noise": np.random.randn(100),
        "predictive": np.concatenate([np.random.randn(50) - 1.0, np.random.randn(50) + 1.0]),
    })
    y = pd.Series([0] * 50 + [1] * 50)
    top = compute_top_n_auc_gap_features(X, y, n=1)
    assert top[0] == "predictive"


def test_missingness_indicators_created_from_training_missingness():
    X_train = pd.DataFrame({
        "a": [1.0, 2.0, np.nan, 4.0],
        "b": [1.0, 2.0, 3.0, 4.0],
    })
    X_out, features = build_missingness_indicator_features(X_train, ["a", "b"])
    assert "a_missing" in features
    assert "b_missing" not in features
    assert X_out["a_missing"].tolist() == [0, 0, 1, 0]
