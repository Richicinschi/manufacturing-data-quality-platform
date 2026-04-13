"""Raw ingestion pipeline for SECOM data into PostgreSQL."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine, ensure_schema


def _read_secom_labels(labels_path: Path) -> pd.DataFrame:
    """Parse secom_labels.data into a clean DataFrame.

    Each line has the format:
        -1 "19/07/2008 11:55:00"
    """
    rows = []
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Extract integer label and quoted datetime
            match = re.match(r'(-?\d+)\s+"([^"]+)"', line)
            if not match:
                # Fallback: simple split and strip quotes
                parts = line.split()
                label = int(parts[0])
                dt_str = " ".join(parts[1:]).strip('"')
            else:
                label = int(match.group(1))
                dt_str = match.group(2)
            rows.append({
                "yield_label": label,
                "test_timestamp": pd.to_datetime(dt_str, dayfirst=True),
                "pass_fail": "fail" if label == 1 else "pass",
            })

    df = pd.DataFrame(rows)
    df.index = df.index + 1  # entity_id starts at 1
    df.index.name = "entity_id"
    return df.reset_index()


def _read_secom_measurements(data_path: Path) -> pd.DataFrame:
    """Parse secom.data into a wide DataFrame with entity_id."""
    df = pd.read_csv(
        data_path,
        sep=r"\s+",
        header=None,
        engine="python",
        na_values=["NaN", "nan", "", "NA", "N/A"],
    )
    # Build columns cleanly to avoid fragmentation
    cols = {f"feature_{i + 1:03d}": df.iloc[:, i] for i in range(df.shape[1])}
    cols["entity_id"] = range(1, len(df) + 1)
    return pd.DataFrame(cols)


def ingest_secom(
    data_path: Path | str,
    labels_path: Path | str,
    schema: str = "raw",
    connection_string: str | None = None,
) -> dict[str, int]:
    """Ingest SECOM measurements and labels into PostgreSQL.

    Args:
        data_path: Path to secom.data
        labels_path: Path to secom_labels.data
        schema: Target schema name
        connection_string: Optional explicit database connection string

    Returns:
        Dictionary with rows loaded per table
    """
    data_path = Path(data_path)
    labels_path = Path(labels_path)

    engine = get_engine(connection_string)

    # Ensure schema exists
    ensure_schema(engine, schema)

    # SQLite does not support schema prefixes; PostgreSQL does
    dialect = engine.dialect.name
    if dialect == "sqlite":
        measurements_table = "secom_measurements"
        labels_table = "secom_labels"
        ingestion_log_table = "ingestion_log"
        ingestion_log_sql_table = "ingestion_log"
        pg_schema = None
    else:
        measurements_table = "secom_measurements"
        labels_table = "secom_labels"
        ingestion_log_table = "ingestion_log"
        ingestion_log_sql_table = f"{schema}.ingestion_log"
        pg_schema = schema

    # Read and load measurements
    measurements_df = _read_secom_measurements(data_path)
    measurements_df.to_sql(
        measurements_table,
        con=engine,
        schema=pg_schema,
        if_exists="replace",
        index=False,
    )

    # Read and load labels
    labels_df = _read_secom_labels(labels_path)
    labels_df.to_sql(
        labels_table,
        con=engine,
        schema=pg_schema,
        if_exists="replace",
        index=False,
    )

    # Ensure ingestion_log exists
    pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if dialect == "sqlite" else "SERIAL PRIMARY KEY"
    with engine.connect() as conn:
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {ingestion_log_sql_table} (
                    log_id {pk_type},
                    table_name VARCHAR(100) NOT NULL,
                    source_file VARCHAR(500) NOT NULL,
                    rows_loaded INT NOT NULL,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.commit()

    # Log ingestion
    log_rows = {
        measurements_table: len(measurements_df),
        labels_table: len(labels_df),
    }

    with engine.connect() as conn:
        for table_name, rows_loaded in log_rows.items():
            source_file = str(data_path if "measurements" in table_name else labels_path)
            conn.execute(
                text(
                    f"""
                    INSERT INTO {ingestion_log_sql_table} (table_name, source_file, rows_loaded)
                    VALUES (:table_name, :source_file, :rows_loaded)
                    """
                ),
                {
                    "table_name": table_name,
                    "source_file": source_file,
                    "rows_loaded": rows_loaded,
                },
            )
        conn.commit()

    return log_rows
