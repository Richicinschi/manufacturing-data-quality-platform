"""Build the top signal fail separation mart table."""

from __future__ import annotations

import math

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine

EXCLUDED_COLUMNS = {"entity_id", "test_timestamp", "yield_label", "pass_fail"}


def build_top_signal_fail_separation(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    catalog_schema: str = "staging",
    catalog_table: str = "feature_catalog",
    target_schema: str = "mart",
    target_table: str = "top_signal_fail_separation",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Compute effect sizes for feature separation between pass and fail labels.

    Args:
        source_schema: Schema containing the source entity table.
        source_table: Name of the source entity table.
        catalog_schema: Schema containing the feature catalog table.
        catalog_table: Name of the feature catalog table.
        target_schema: Schema where the result table will be written.
        target_table: Name of the result table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame ordered by effect_size DESC with separation statistics per feature.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    catalog_fq = f"{catalog_schema}.{catalog_table}" if dialect != "sqlite" else catalog_table

    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)
    catalog = pd.read_sql(f"SELECT * FROM {catalog_fq}", engine)

    total_rows = len(df)
    feature_cols = [c for c in df.columns if c not in EXCLUDED_COLUMNS]

    records = []
    for col in feature_cols:
        pass_series = df.loc[df["yield_label"] == -1, col]
        fail_series = df.loc[df["yield_label"] == 1, col]

        pass_count = int(pass_series.notna().sum())
        fail_count = int(fail_series.notna().sum())
        pass_mean = pass_series.mean()
        fail_mean = fail_series.mean()
        pass_stddev = pass_series.std(ddof=0)
        fail_stddev = fail_series.std(ddof=0)

        denominator = math.sqrt(((pass_stddev**2) + (fail_stddev**2)) / 2)
        if denominator == 0 or pd.isna(denominator):
            effect_size = float("nan")
        else:
            effect_size = abs(pass_mean - fail_mean) / denominator

        records.append(
            {
                "feature_name": col,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "pass_mean": pass_mean,
                "fail_mean": fail_mean,
                "pass_stddev": pass_stddev,
                "fail_stddev": fail_stddev,
                "effect_size": effect_size,
            }
        )

    result = pd.DataFrame(records)

    # Filter out features with pass_count == 0 or fail_count == 0
    result = result[(result["pass_count"] > 0) & (result["fail_count"] > 0)].copy()

    # Filter out all-null or constant features using catalog
    catalog_exclusions = catalog[
        (catalog["is_constant"] == True) | (catalog["null_count"] == total_rows)
    ]["feature_name"].tolist()

    result = result[~result["feature_name"].isin(catalog_exclusions)].copy()

    result = result.sort_values(by="effect_size", ascending=False).reset_index(drop=True)

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
