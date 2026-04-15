"""Walk-forward cross-validation engine with fold-validation guards."""

from __future__ import annotations

import numpy as np
import pandas as pd


def expanding_window_splits(
    X: pd.DataFrame,
    y: pd.Series,
    timestamps: pd.Series,
    n_splits: int = 4,
    min_fails: int = 8,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Generate chronological expanding-window train/test indices at whole-date boundaries.

    Args:
        X: Feature DataFrame (used only for length and index alignment).
        y: Binary labels.
        timestamps: Timestamps for sorting (already assumed sorted).
        n_splits: Target number of splits; may degrade if fail counts are too low.
        min_fails: Minimum required fail-class samples in both train and test of a fold.

    Returns:
        List of (train_indices, test_indices) tuples as numpy arrays.
    """
    n_samples = len(X)
    indices = np.arange(n_samples)
    total_fails = int(y.sum())

    # Group indices by calendar date (timestamps are already sorted)
    dates = pd.Series(timestamps).dt.date
    date_groups = []
    for d in dates.unique():
        mask = dates == d
        date_groups.append(indices[mask])

    n_groups = len(date_groups)

    for current_splits in range(n_splits, 0, -1):
        needed_fails = (current_splits + 1) * min_fails
        if total_fails < needed_fails:
            continue

        # Need at least current_splits + 1 groups to form current_splits folds
        if n_groups < current_splits + 1:
            continue

        split_points = np.linspace(0, n_groups, current_splits + 2, dtype=int)

        valid = True
        folds = []
        for i in range(1, current_splits + 1):
            train_groups = date_groups[: split_points[i]]
            test_groups = date_groups[split_points[i] : split_points[i + 1]]

            if len(train_groups) == 0 or len(test_groups) == 0:
                valid = False
                break

            train_idx = np.concatenate(train_groups)
            test_idx = np.concatenate(test_groups)

            if len(train_idx) == 0 or len(test_idx) == 0:
                valid = False
                break

            y_train = y.iloc[train_idx]
            y_test = y.iloc[test_idx]

            if int(y_train.sum()) < min_fails or int(y_test.sum()) < min_fails:
                valid = False
                break

            folds.append((train_idx.copy(), test_idx.copy()))

        if valid:
            if current_splits != n_splits:
                print(
                    f"[cv_engine] Degraded n_splits from {n_splits} to {current_splits} "
                    f"to maintain >= {min_fails} fails per fold."
                )
            return folds

    raise ValueError(
        f"Unable to create any valid split with >= {min_fails} fails per fold."
    )
