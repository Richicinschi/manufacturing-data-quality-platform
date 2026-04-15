"""Load and prepare modeling data from the warehouse."""

from __future__ import annotations

import pandas as pd

from src.db.connection import get_engine


def load_modeling_data(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    connection_string: str | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Load SECOM entities, sort chronologically, and encode labels.

    Returns:
        Tuple of (X, y, timestamps) where:
            X: DataFrame of feature columns with NaNs preserved (no imputation)
            y: Series of binary labels (0 = pass, 1 = fail)
            timestamps: Series of test_timestamp values
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name
    table_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table

    df = pd.read_sql(f"SELECT * FROM {table_fq}", engine)
    df["test_timestamp"] = pd.to_datetime(df["test_timestamp"])
    df = df.sort_values("test_timestamp").reset_index(drop=True)

    # Encode labels: pass (-1) -> 0, fail (1) -> 1
    y = (df["yield_label"] == 1).astype(int)
    timestamps = df["test_timestamp"]

    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    X = df[feature_cols].copy()

    return X, y, timestamps
