"""Feature set builders for the modeling pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score

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


def compute_correlation_pruned_features(
    X_train: pd.DataFrame,
    threshold: float = 0.70,
) -> list[str]:
    """Prune features by absolute Pearson correlation on training fold only.

    Drops one feature from each pair with abs(correlation) >= threshold.
    Keeps the first feature in column order to ensure determinism.

    Args:
        X_train: Training features.
        threshold: Correlation threshold for dropping.

    Returns:
        List of retained feature names.
    """
    if X_train.empty:
        return []

    corr_matrix = X_train.corr().abs()
    features = list(X_train.columns)
    to_drop = set()

    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            if corr_matrix.iloc[i, j] >= threshold:
                to_drop.add(features[j])

    return [f for f in features if f not in to_drop]


def compute_top_n_mutual_info_features(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n: int,
    random_state: int = 42,
) -> list[str]:
    """Select top-N features by mutual information inside a training fold.

    Args:
        X_train: Training features.
        y_train: Binary labels.
        n: Number of top features to return.
        random_state: Random state for mutual_info_classif.

    Returns:
        List of feature names sorted by descending mutual information.
    """
    if X_train.empty:
        return []

    # Median imputation for mutual information (MI cannot handle NaNs)
    # Preserve shape by filling all-NaN columns with 0 before imputing.
    X_filled = X_train.copy()
    all_nan_cols = X_filled.columns[X_filled.isna().all()].tolist()
    X_filled[all_nan_cols] = 0.0
    imputer = SimpleImputer(strategy="median")
    X_imp = imputer.fit_transform(X_filled)

    mi_scores = mutual_info_classif(
        X_imp, y_train, random_state=random_state, discrete_features=False
    )
    scored = list(zip(X_filled.columns, mi_scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in scored[:n]]


def compute_top_n_auc_gap_features(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n: int,
) -> list[str]:
    """Select top-N features by absolute univariate ROC-AUC distance from 0.5.

    Args:
        X_train: Training features.
        y_train: Binary labels.
        n: Number of top features to return.

    Returns:
        List of feature names sorted by descending AUC gap.
    """
    if X_train.empty:
        return []

    X_filled = X_train.copy()
    all_nan_cols = X_filled.columns[X_filled.isna().all()].tolist()
    X_filled[all_nan_cols] = 0.0
    imputer = SimpleImputer(strategy="median")
    X_imp = pd.DataFrame(
        imputer.fit_transform(X_filled), columns=X_filled.columns, index=X_filled.index
    )

    auc_gaps = {}
    for col in X_imp.columns:
        col_vals = X_imp[col]
        # Need at least two distinct classes and some variation
        if col_vals.nunique() <= 1 or len(np.unique(y_train)) < 2:
            auc_gaps[col] = 0.0
            continue
        try:
            auc = roc_auc_score(y_train, col_vals)
            auc_gaps[col] = abs(auc - 0.5)
        except ValueError:
            auc_gaps[col] = 0.0

    scored = sorted(auc_gaps.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in scored[:n]]


def build_missingness_indicator_features(
    X_train: pd.DataFrame,
    base_features: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Add missingness indicator columns for features with any missingness in training.

    Args:
        X_train: Training features.
        base_features: Base feature list to preserve.

    Returns:
        Tuple of (transformed DataFrame with indicators appended, combined feature list).
    """
    df = X_train[base_features].copy()
    missing_any = df.columns[df.isna().any()].tolist()

    indicators = {f"{col}_missing": df[col].isna().astype(int) for col in missing_any}
    if indicators:
        df = pd.concat([df, pd.DataFrame(indicators, index=df.index)], axis=1)

    return df, df.columns.tolist()
