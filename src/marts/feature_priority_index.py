"""Build the feature priority index mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_feature_priority_index(
    source_schema: str = "staging",
    source_table: str = "feature_catalog",
    ranking_schema: str = "mart",
    ranking_table: str = "top_signal_fail_separation",
    target_schema: str = "mart",
    target_table: str = "feature_priority_index",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a priority index that buckets features by data-quality action and effect size.

    Args:
        source_schema: Schema containing the feature catalog table.
        source_table: Name of the feature catalog table.
        ranking_schema: Schema containing the effect-size ranking table.
        ranking_table: Name of the effect-size ranking table.
        target_schema: Schema where the priority index table will be written.
        target_table: Name of the priority index table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame with one row per feature and its priority bucket.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    ranking_fq = f"{ranking_schema}.{ranking_table}" if dialect != "sqlite" else ranking_table

    catalog = pd.read_sql(f"SELECT * FROM {source_fq}", engine)
    ranking = pd.read_sql(f"SELECT * FROM {ranking_fq}", engine)

    df = catalog.merge(
        ranking[["feature_name", "effect_size"]],
        on="feature_name",
        how="left",
    )

    median_effect_size = df["effect_size"].dropna().median()

    def _bucket(row: pd.Series) -> str:
        if row["recommended_action"] == "drop_all_null":
            return "excluded_all_null"
        if row["recommended_action"] == "drop_constant":
            return "excluded_constant"
        if row["null_pct"] >= 0.50:
            return "review_high_missing"
        if pd.notna(row["effect_size"]) and row["effect_size"] >= median_effect_size:
            return "top_separator"
        return "standard_keep"

    df["priority_bucket"] = df.apply(_bucket, axis=1)

    result = df[[
        "feature_name",
        "recommended_action",
        "null_pct",
        "effect_size",
        "priority_bucket",
    ]].copy()

    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    result.to_sql(
        target_table,
        con=engine,
        schema=target_schema if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )

    return result
