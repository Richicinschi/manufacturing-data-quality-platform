"""Inspection-rate metrics for top-k risk evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_inspection_metrics(
    y_true: np.ndarray | pd.Series,
    risk_scores: np.ndarray | pd.Series,
    inspection_rates: list[float] | None = None,
) -> dict[str, float]:
    """Compute precision, recall, lift, and captured fails at given inspection rates.

    Args:
        y_true: Binary ground-truth labels (0 = pass, 1 = fail).
        risk_scores: Risk scores where higher means higher failure risk.
        inspection_rates: List of top-k fractions to evaluate (default: [0.05, 0.10, 0.20]).

    Returns:
        Dict with keys like recall_at_10pct, precision_at_10pct, lift_at_10pct,
        captured_fails_at_10pct for each inspected rate.
    """
    if inspection_rates is None:
        inspection_rates = [0.05, 0.10, 0.20]

    y = np.asarray(y_true)
    scores = np.asarray(risk_scores)
    valid_mask = ~np.isnan(scores)
    y = y[valid_mask]
    scores = scores[valid_mask]

    n_total = len(y)
    n_fails = int(y.sum())
    overall_fail_rate = n_fails / n_total if n_total > 0 else 0.0

    # Sort by descending risk score
    sorted_indices = np.argsort(-scores)
    y_sorted = y[sorted_indices]

    results: dict[str, float] = {}
    for rate in inspection_rates:
        k = max(1, int(round(n_total * rate)))
        top_k = y_sorted[:k]
        fails_caught = int(top_k.sum())
        precision = fails_caught / k if k > 0 else 0.0
        recall = fails_caught / n_fails if n_fails > 0 else 0.0
        lift = (precision / overall_fail_rate) if overall_fail_rate > 0 else 0.0

        pct_label = f"{int(rate * 100):02d}pct"
        results[f"recall_at_{pct_label}"] = round(recall, 4)
        results[f"precision_at_{pct_label}"] = round(precision, 4)
        results[f"captured_fails_at_{pct_label}"] = fails_caught
        results[f"lift_at_{pct_label}"] = round(lift, 4)

    return results


def build_inspection_curve(
    y_true: np.ndarray | pd.Series,
    risk_scores: np.ndarray | pd.Series,
    n_points: int = 20,
) -> pd.DataFrame:
    """Build a top-k inspection curve for plotting.

    Columns: inspection_rate, recall, precision, lift, captured_fails.
    """
    y = np.asarray(y_true)
    scores = np.asarray(risk_scores)
    valid_mask = ~np.isnan(scores)
    y = y[valid_mask]
    scores = scores[valid_mask]

    n_total = len(y)
    n_fails = int(y.sum())
    overall_fail_rate = n_fails / n_total if n_total > 0 else 0.0

    sorted_indices = np.argsort(-scores)
    y_sorted = y[sorted_indices]

    records = []
    for i in range(1, n_points + 1):
        rate = i / n_points
        k = max(1, int(round(n_total * rate)))
        top_k = y_sorted[:k]
        fails_caught = int(top_k.sum())
        precision = fails_caught / k if k > 0 else 0.0
        recall = fails_caught / n_fails if n_fails > 0 else 0.0
        lift = (precision / overall_fail_rate) if overall_fail_rate > 0 else 0.0
        records.append({
            "inspection_rate": round(rate, 2),
            "recall": round(recall, 4),
            "precision": round(precision, 4),
            "lift": round(lift, 4),
            "captured_fails": fails_caught,
        })

    return pd.DataFrame(records)
