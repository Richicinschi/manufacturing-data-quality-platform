"""Build the daily yield trend mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_daily_yield_trend(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    target_schema: str = "mart",
    target_table: str = "daily_yield_trend",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a daily yield trend summary from the SECOM entity table.

    Args:
        source_schema: Schema containing the source entity table.
        source_table: Name of the source entity table.
        target_schema: Schema where the trend table will be written.
        target_table: Name of the trend table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame with one row per event_date showing daily yield metrics.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    df["event_date"] = pd.to_datetime(df["test_timestamp"]).dt.date

    grouped = df.groupby("event_date").agg(
        entity_count=("entity_id", "count"),
        pass_count=("yield_label", lambda x: int((x == -1).sum())),
        fail_count=("yield_label", lambda x: int((x == 1).sum())),
    ).reset_index()

    grouped["pass_rate"] = grouped["pass_count"] / grouped["entity_count"]
    grouped["fail_rate"] = grouped["fail_count"] / grouped["entity_count"]

    # Ensure correct column order
    grouped = grouped[[
        "event_date",
        "entity_count",
        "pass_count",
        "fail_count",
        "pass_rate",
        "fail_rate",
    ]]

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
