"""Build the canonical SECOM table by joining measurements with labels."""

from __future__ import annotations

from sqlalchemy import text

from src.db.connection import get_engine


def _get_feature_columns(engine, schema: str, table: str) -> list[str]:
    """Query the database for column names of a table, excluding entity_id."""
    dialect = engine.dialect.name
    if dialect == "sqlite":
        # SQLite: PRAGMA table_info
        result = engine.connect().execute(text(f"PRAGMA table_info({table})"))
        cols = [row[1] for row in result if row[1] != "entity_id"]
    else:
        # PostgreSQL: information_schema.columns
        result = engine.connect().execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table
                  AND column_name != 'entity_id'
                ORDER BY ordinal_position
                """
            ),
            {"schema": schema, "table": table},
        )
        cols = [row[0] for row in result]
    return cols


def build_canonical_secom(
    source_schema: str = "raw",
    target_schema: str = "raw",
    target_table: str = "secom_canonical",
    connection_string: str | None = None,
) -> int:
    """Create a canonical SECOM table with stable entity_id, timestamp, label, and all features.

    Args:
        source_schema: Schema containing secom_measurements and secom_labels.
        target_schema: Schema where the canonical table will be created.
        target_table: Name of the canonical table.
        connection_string: Optional explicit DB connection string.

    Returns:
        Number of rows written to the canonical table.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    # Ensure target schema exists on PostgreSQL
    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    source_measurements = (
        f"{source_schema}.secom_measurements" if dialect != "sqlite" else "secom_measurements"
    )
    source_labels = (
        f"{source_schema}.secom_labels" if dialect != "sqlite" else "secom_labels"
    )
    target_fq = f"{target_schema}.{target_table}" if dialect != "sqlite" else target_table

    feature_cols = _get_feature_columns(engine, source_schema, "secom_measurements")
    if not feature_cols:
        raise RuntimeError("Could not determine feature columns from secom_measurements")

    feature_select = ",\n            ".join([f"m.{c}" for c in feature_cols])

    drop_sql = text(f"DROP TABLE IF EXISTS {target_fq}")
    create_sql = text(
        f"""
        CREATE TABLE {target_fq} AS
        SELECT
            m.entity_id,
            l.test_timestamp,
            l.yield_label,
            l.pass_fail,
            {feature_select}
        FROM {source_measurements} AS m
        INNER JOIN {source_labels} AS l
            ON m.entity_id = l.entity_id
        ORDER BY l.test_timestamp
        """
    )

    with engine.connect() as conn:
        conn.execute(drop_sql)
        conn.commit()
        conn.execute(create_sql)
        conn.commit()

        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {target_fq}"))
        row_count = count_result.scalar()

    return row_count


if __name__ == "__main__":
    import os

    rows = build_canonical_secom()
    print(f"Created raw.secom_canonical with {rows:,} rows")
