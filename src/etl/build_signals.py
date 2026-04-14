"""Long-format signal builder for the manufacturing data platform."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


ID_COLUMNS = ["entity_id", "test_timestamp", "yield_label"]
EXCLUDED_COLUMNS = {"entity_id", "test_timestamp", "yield_label", "pass_fail"}


def build_signal_values_long(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    target_schema: str = "staging",
    target_table: str = "signal_values_long",
    connection_string: str | None = None,
) -> int:
    """Unpivot a wide-format entity table into long-format signals.

    Args:
        source_schema: Schema containing the wide-format entity table.
        source_table: Name of the wide-format entity table.
        target_schema: Schema where the long-format table will be written.
        target_table: Name of the long-format table.
        connection_string: Optional explicit DB connection string.

    Returns:
        Number of rows written to the target table.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    # Read source table
    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    feature_cols = [c for c in df.columns if c not in EXCLUDED_COLUMNS]

    long_df = pd.melt(
        df,
        id_vars=ID_COLUMNS,
        value_vars=feature_cols,
        var_name="feature_name",
        value_name="feature_value",
    )

    long_df["is_missing"] = long_df["feature_value"].isna()

    # Ensure correct column order
    long_df = long_df[
        ["entity_id", "test_timestamp", "yield_label", "feature_name", "feature_value", "is_missing"]
    ]

    # Ensure target schema exists
    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    long_df.to_sql(
        target_table,
        con=engine,
        schema=target_schema if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )

    return len(long_df)
