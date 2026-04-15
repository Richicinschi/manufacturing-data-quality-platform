"""Tests for src/modeling/features.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modeling.features import build_feature_sets, compute_top_n_effect_features


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
