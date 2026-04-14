"""Feature catalog builder for the manufacturing data platform."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


EXCLUDED_COLUMNS = {"entity_id", "test_timestamp", "yield_label", "pass_fail"}


def build_feature_catalog(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    target_schema: str = "staging",
    target_table: str = "feature_catalog",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a feature catalog from a wide-format entity table.

    Args:
        source_schema: Schema containing the wide-format entity table.
        source_table: Name of the wide-format entity table.
        target_schema: Schema where the catalog table will be written.
        target_table: Name of the catalog table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame containing one row per feature with computed statistics.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    # Read source table
    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)

    total_rows = len(df)
    feature_cols = [c for c in df.columns if c not in EXCLUDED_COLUMNS]

    records = []
    for col in feature_cols:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = null_count / total_rows if total_rows > 0 else 0.0
        distinct_count = int(series.nunique(dropna=True))
        mean = series.mean()
        stddev = series.std(ddof=0)
        min_value = series.min()
        max_value = series.max()
        is_constant = distinct_count <= 1
        is_high_missing = null_pct >= 0.50

        if (total_rows - null_count) == 0:
            recommended_action = "drop_all_null"
        elif distinct_count <= 1:
            recommended_action = "drop_constant"
        elif null_pct >= 0.50:
            recommended_action = "review_high_missing"
        else:
            recommended_action = "keep"

        records.append(
            {
                "feature_name": col,
                "null_count": null_count,
                "null_pct": null_pct,
                "distinct_count": distinct_count,
                "mean": mean,
                "stddev": stddev,
                "min_value": min_value,
                "max_value": max_value,
                "is_constant": is_constant,
                "is_high_missing": is_high_missing,
                "recommended_action": recommended_action,
            }
        )

    catalog = pd.DataFrame(records)

    # Ensure target schema exists
    if dialect != "sqlite":
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema}"))
            conn.commit()

    catalog.to_sql(
        target_table,
        con=engine,
        schema=target_schema if dialect != "sqlite" else None,
        if_exists="replace",
        index=False,
    )

    return catalog
