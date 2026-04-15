"""Feature set builders for the modeling pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.etl.feature_catalog import build_feature_catalog


def build_feature_sets(
    catalog_df: pd.DataFrame | None = None,
    connection_string: str | None = None,
) -> dict[str, list[str]]:
    """Return static feature lists based on the feature catalog.

    Returns dict with keys:
        keep_only, keep_plus_review
    """
    if catalog_df is None:
        catalog_df = build_feature_catalog(connection_string=connection_string)

    keep_only = catalog_df.loc[
        catalog_df["recommended_action"] == "keep", "feature_name"
    ].tolist()
    keep_plus_review = catalog_df.loc[
        catalog_df["recommended_action"].isin(["keep", "review_high_missing"]),
        "feature_name",
    ].tolist()

    return {
        "keep_only": keep_only,
        "keep_plus_review": keep_plus_review,
    }


def _cohens_d(pass_vals: pd.Series, fail_vals: pd.Series) -> float:
    """Compute Cohen's d between two series (robust to constant groups)."""
    pass_vals = pass_vals.dropna()
    fail_vals = fail_vals.dropna()
    if len(pass_vals) == 0 or len(fail_vals) == 0:
        return 0.0
    mean_diff = pass_vals.mean() - fail_vals.mean()
    pooled_std = np.sqrt(
        ((len(pass_vals) - 1) * pass_vals.var() + (len(fail_vals) - 1) * fail_vals.var())
        / (len(pass_vals) + len(fail_vals) - 2)
    )
    if pooled_std == 0 or np.isnan(pooled_std):
        return 0.0
    return abs(mean_diff / pooled_std)


def compute_top_n_effect_features(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n: int,
) -> list[str]:
    """Compute top-N features by Cohen's d inside a training fold.

    Args:
        X_train: Training features.
        y_train: Binary labels (0 = pass, 1 = fail).
        n: Number of top features to return.

    Returns:
        List of feature names sorted by descending effect size.
    """
    pass_mask = y_train == 0
    fail_mask = y_train == 1

    effect_sizes = {}
    for col in X_train.columns:
        d = _cohens_d(X_train.loc[pass_mask, col], X_train.loc[fail_mask, col])
        effect_sizes[col] = d

    sorted_features = sorted(effect_sizes.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_features[:n]]
