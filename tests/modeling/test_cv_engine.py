"""Tests for src/modeling/cv_engine.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.modeling.cv_engine import expanding_window_splits


def test_expanding_window_splits_respects_time_order():
    # 5 days, 20 samples per day, with fails distributed across all dates
    timestamps = pd.to_datetime(
        [d for day in pd.date_range("2024-01-01", periods=5, freq="D") for d in [day] * 20]
    )
    X = pd.DataFrame({"a": range(len(timestamps))})
    # 4 fails per day (20 fails total)
    y_values = []
    for _ in range(5):
        y_values.extend([1] * 4 + [0] * 16)
    y = pd.Series(y_values)

    splits = expanding_window_splits(X, y, timestamps, n_splits=4, min_fails=2)
    assert len(splits) == 4
    for train_idx, test_idx in splits:
        assert len(train_idx) > 0
        assert len(test_idx) > 0
        assert train_idx.max() < test_idx.max() or len(test_idx) == 0
        # All train indices are before or at start of test
        assert train_idx[-1] <= test_idx[0] or len(train_idx) == 0


def test_expanding_window_splits_respects_date_boundaries():
    # 4 days, 12 samples per day, with fails distributed across all dates
    timestamps = pd.to_datetime(
        [d for day in pd.date_range("2024-01-01", periods=4, freq="D") for d in [day] * 12]
    )
    X = pd.DataFrame({"a": range(len(timestamps))})
    # 2 fails per day (8 fails total)
    y_values = []
    for _ in range(4):
        y_values.extend([1] * 2 + [0] * 10)
    y = pd.Series(y_values)

    splits = expanding_window_splits(X, y, timestamps, n_splits=2, min_fails=1)
    assert len(splits) == 2
    for train_idx, test_idx in splits:
        ts_series = pd.Series(timestamps)
        train_dates = set(ts_series.iloc[train_idx].dt.date.unique())
        test_dates = set(ts_series.iloc[test_idx].dt.date.unique())
        assert train_dates.isdisjoint(test_dates), "No date should appear in both train and test"


def test_expanding_window_splits_degrades_gracefully():
    # 6 days, 1 fail per day (6 fails total), 4 splits requested but min_fails=2
    # means we need at least 10 fails for 4 splits; should degrade to 2 splits.
    timestamps = pd.to_datetime(
        [d for day in pd.date_range("2024-01-01", periods=6, freq="D") for d in [day] * 5]
    )
    X = pd.DataFrame({"a": range(len(timestamps))})
    y_values = []
    for _ in range(6):
        y_values.extend([1] + [0] * 4)
    y = pd.Series(y_values)

    splits = expanding_window_splits(X, y, timestamps, n_splits=4, min_fails=2)
    assert 1 <= len(splits) < 4


def test_expanding_window_splits_enforces_min_fails():
    X = pd.DataFrame({"a": range(20)})
    y = pd.Series([0] * 19 + [1] * 1)
    timestamps = pd.date_range("2024-01-01", periods=20, freq="h")

    with pytest.raises(ValueError):
        expanding_window_splits(X, y, timestamps, n_splits=4, min_fails=2)
