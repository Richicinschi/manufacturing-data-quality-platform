"""Threshold selection on development OOF predictions."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score


def select_threshold(
    y_true: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    thresholds: np.ndarray | None = None,
) -> tuple[float, pd.DataFrame]:
    """Select probability threshold that maximizes fail-class F1.

    Args:
        y_true: Ground-truth binary labels.
        probabilities: Predicted probabilities for the positive class.
        thresholds: Array of thresholds to evaluate. Default: 0.01 to 0.99 step 0.01.

    Returns:
        (best_threshold, threshold_analysis_df)
    """
    if thresholds is None:
        thresholds = np.arange(0.01, 1.0, 0.01)

    valid_mask = ~np.isnan(probabilities)
    y = np.asarray(y_true)[valid_mask]
    probs = probabilities[valid_mask]

    records = []
    best_f1 = -1.0
    best_threshold = 0.5

    for thresh in thresholds:
        preds = (probs >= thresh).astype(int)
        prec = precision_score(y, preds, zero_division=0)
        rec = recall_score(y, preds, zero_division=0)
        f1 = f1_score(y, preds, zero_division=0)
        records.append(
            {
                "threshold": round(float(thresh), 2),
                "precision": prec,
                "recall": rec,
                "f1": f1,
            }
        )
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh

    analysis_df = pd.DataFrame(records)
    analysis_df["selected"] = analysis_df["threshold"] == round(float(best_threshold), 2)

    return float(best_threshold), analysis_df
