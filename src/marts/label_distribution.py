"""Build the label distribution mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_label_distribution(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    target_schema: str = "mart",
    target_table: str = "label_distribution",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a mart table showing label distribution counts and percentages.

    Args:
        source_schema: Schema containing the source entity table.
        source_table: Name of the source entity table.
        target_schema: Schema where the label distribution table will be written.
        target_table: Name of the label distribution table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame grouped by yield_label and pass_fail with counts and percentages.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    total = len(df)
    grouped = (
        df.groupby(["yield_label", "pass_fail"])
        .size()
        .reset_index(name="entity_count")
    )
    grouped["entity_pct"] = grouped["entity_count"] / total if total > 0 else 0.0

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
