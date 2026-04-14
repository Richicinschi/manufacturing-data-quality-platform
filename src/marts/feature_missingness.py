"""Build the feature missingness mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_feature_missingness(
    source_schema: str = "staging",
    source_table: str = "feature_catalog",
    target_schema: str = "mart",
    target_table: str = "feature_missingness",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a mart table showing feature missingness from the catalog.

    Args:
        source_schema: Schema containing the feature catalog table.
        source_table: Name of the feature catalog table.
        target_schema: Schema where the missingness table will be written.
        target_table: Name of the missingness table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame ordered by null_pct DESC with selected catalog columns.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    columns = [
        "feature_name",
        "null_count",
        "null_pct",
        "distinct_count",
        "is_constant",
        "is_high_missing",
        "recommended_action",
    ]
    result = df[columns].sort_values(by="null_pct", ascending=False).reset_index(drop=True)

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
