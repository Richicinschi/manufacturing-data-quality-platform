"""Build the feature action summary mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_feature_action_summary(
    source_schema: str = "staging",
    source_table: str = "feature_catalog",
    target_schema: str = "mart",
    target_table: str = "feature_action_summary",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a summary of recommended actions from the feature catalog.

    Args:
        source_schema: Schema containing the feature catalog table.
        source_table: Name of the feature catalog table.
        target_schema: Schema where the summary table will be written.
        target_table: Name of the summary table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame grouped by recommended_action with counts and percentages.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    total = len(df)
    grouped = (
        df.groupby("recommended_action")
        .size()
        .reset_index(name="feature_count")
    )
    grouped["feature_pct"] = grouped["feature_count"] / total if total > 0 else 0.0

    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    grouped.to_sql(
        target_table,
        con=engine,
        schema=target_schema if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )

    return grouped
