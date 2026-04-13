"""Join SECOM measurements with labels and timestamps into a unified view."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_production_entities(
    schema: str = "raw",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Join secom_measurements with secom_labels and return a unified DataFrame.

    Args:
        schema: Database schema where raw tables live.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame with entity_id, test_timestamp, yield_label, pass_fail,
        and all 590 measurement features.
    """
    engine = get_engine(connection_string)

    query = text(
        f"""
        SELECT
            m.*,
            l.yield_label,
            l.test_timestamp,
            l.pass_fail
        FROM {schema}.secom_measurements AS m
        INNER JOIN {schema}.secom_labels AS l
            ON m.entity_id = l.entity_id
        ORDER BY l.test_timestamp
        """
    )

    df = pd.read_sql(query, engine)
    return df


def save_production_entities(
    df: pd.DataFrame,
    target_schema: str = "staging",
    target_table: str = "production_entities",
    connection_string: str | None = None,
) -> int:
    """Persist the joined production entities into the staging layer.

    Args:
        df: DataFrame from build_production_entities()
        target_schema: Target schema for the table
        target_table: Target table name
        connection_string: Optional explicit DB connection string

    Returns:
        Number of rows written
    """
    engine = get_engine(connection_string)

    # Ensure target schema exists
    dialect = engine.dialect.name
    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    df.to_sql(
        target_table,
        con=engine,
        schema=target_schema if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )

    return len(df)
