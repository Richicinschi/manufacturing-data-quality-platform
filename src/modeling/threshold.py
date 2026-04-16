"""Threshold selection on development OOF predictions."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


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


def build_threshold_cost_curve(
    y_true: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    thresholds: np.ndarray | None = None,
) -> pd.DataFrame:
    """Build a business-oriented threshold cost curve.

    Columns: threshold, precision, recall, f1, predicted_fail_count,
             false_positive_count, false_negative_count, inspection_rate, selected
    """
    if thresholds is None:
        thresholds = np.arange(0.01, 1.0, 0.01)

    valid_mask = ~np.isnan(probabilities)
    y = np.asarray(y_true)[valid_mask]
    probs = probabilities[valid_mask]
    n_total = len(y)

    records = []
    best_f1 = -1.0
    best_threshold = 0.5

    for thresh in thresholds:
        preds = (probs >= thresh).astype(int)
        prec = precision_score(y, preds, zero_division=0)
        rec = recall_score(y, preds, zero_division=0)
        f1 = f1_score(y, preds, zero_division=0)

        cm = confusion_matrix(y, preds, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        predicted_fail_count = int(tp + fp)
        inspection_rate = predicted_fail_count / n_total if n_total > 0 else 0.0

        records.append(
            {
                "threshold": round(float(thresh), 2),
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "predicted_fail_count": predicted_fail_count,
                "false_positive_count": int(fp),
                "false_negative_count": int(fn),
                "inspection_rate": round(inspection_rate, 4),
            }
        )
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh

    df = pd.DataFrame(records)
    df["selected"] = df["threshold"] == round(float(best_threshold), 2)
    return df


def build_probability_bins(
    y_true: pd.Series | np.ndarray,
    probabilities: np.ndarray,
    n_bins: int = 5,
) -> pd.DataFrame:
    """Bin predicted probabilities and report failure concentration per bin.

    Columns: bin_min, bin_max, total_entities, fail_count, fail_rate
    """
    valid_mask = ~np.isnan(probabilities)
    y = np.asarray(y_true)[valid_mask]
    probs = probabilities[valid_mask]

    records = []
    for i in range(n_bins):
        bin_min = i / n_bins
        bin_max = (i + 1) / n_bins
        if i < n_bins - 1:
            mask = (probs >= bin_min) & (probs < bin_max)
        else:
            mask = (probs >= bin_min) & (probs <= bin_max)

        total_entities = int(mask.sum())
        fail_count = int(y[mask].sum())
        fail_rate = fail_count / total_entities if total_entities > 0 else 0.0

        records.append(
            {
                "bin_min": round(bin_min, 2),
                "bin_max": round(bin_max, 2),
                "total_entities": total_entities,
                "fail_count": fail_count,
                "fail_rate": round(fail_rate, 4),
            }
        )

    return pd.DataFrame(records)
