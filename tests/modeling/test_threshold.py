"""Tests for src/modeling/threshold.py."""

from __future__ import annotations

import numpy as np
import pytest

from src.modeling.threshold import select_threshold


def test_select_threshold_returns_valid_range():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    probs = np.array([0.1, 0.2, 0.3, 0.6, 0.7, 0.8])
    threshold, df = select_threshold(y_true, probs)
    assert 0.0 <= threshold <= 1.0
    assert not df.empty
    assert "selected" in df.columns
    assert df["selected"].sum() == 1


def test_select_threshold_with_nan_probs():
    y_true = np.array([0, 0, 1, 1])
    probs = np.array([0.1, np.nan, 0.7, 0.8])
    threshold, df = select_threshold(y_true, probs)
    assert 0.0 <= threshold <= 1.0
