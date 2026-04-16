"""Tests for src/modeling/inspection.py."""

from __future__ import annotations

import numpy as np
import pytest

from src.modeling.inspection import compute_inspection_metrics, build_inspection_curve


def test_compute_inspection_metrics_perfect_ranking():
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    scores = np.array([0.1, 0.2, 0.3, 0.4, 0.9, 0.8, 0.7, 0.6])
    metrics = compute_inspection_metrics(y_true, scores)
    assert metrics["recall_at_10pct"] == 0.25
    assert metrics["precision_at_10pct"] == 1.0
    assert metrics["lift_at_10pct"] == 2.0
    assert metrics["captured_fails_at_10pct"] == 1


def test_compute_inspection_metrics_all_failures_in_top_20pct():
    y_true = np.array([0] * 80 + [1] * 20)
    scores = np.array([0.1] * 80 + [0.9] * 20)
    metrics = compute_inspection_metrics(y_true, scores)
    assert metrics["recall_at_20pct"] == 1.0
    assert metrics["precision_at_20pct"] == 1.0


def test_compute_inspection_metrics_with_nan_scores():
    y_true = np.array([0, 0, 1, 1])
    scores = np.array([0.1, np.nan, 0.9, 0.8])
    metrics = compute_inspection_metrics(y_true, scores)
    # After dropping NaN, 3 samples remain
    assert metrics["precision_at_10pct"] == 1.0


def test_build_inspection_curve_has_expected_columns():
    y_true = np.array([0] * 50 + [1] * 10)
    scores = np.array([0.1] * 50 + [0.9] * 10)
    curve = build_inspection_curve(y_true, scores, n_points=20)
    assert list(curve.columns) == ["inspection_rate", "recall", "precision", "lift", "captured_fails"]
    assert len(curve) == 20
    assert curve["inspection_rate"].iloc[-1] == 1.0
