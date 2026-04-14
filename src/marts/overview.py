"""Build the SECOM overview mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_secom_overview(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    target_schema: str = "mart",
    target_table: str = "secom_overview",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a single-row summary of the SECOM dataset.

    Args:
        source_schema: Schema containing the source entity table.
        source_table: Name of the source entity table.
        target_schema: Schema where the overview table will be written.
        target_table: Name of the overview table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame containing a single row with dataset summary metrics.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    entity_count = len(df)
    pass_count = int((df["yield_label"] == -1).sum())
    fail_count = int((df["yield_label"] == 1).sum())
    pass_pct = pass_count / entity_count if entity_count > 0 else 0.0
    fail_pct = fail_count / entity_count if entity_count > 0 else 0.0
    min_timestamp = pd.to_datetime(df["test_timestamp"]).min()
    max_timestamp = pd.to_datetime(df["test_timestamp"]).max()

    overview = pd.DataFrame(
        {
            "entity_count": [entity_count],
            "feature_count": [len(feature_cols)],
            "pass_count": [pass_count],
            "fail_count": [fail_count],
            "pass_pct": [pass_pct],
            "fail_pct": [fail_pct],
            "min_timestamp": [min_timestamp],
            "max_timestamp": [max_timestamp],
        }
    )

    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    overview.to_sql(
        target_table,
        con=engine,
        schema=target_schema if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )

    return overview
