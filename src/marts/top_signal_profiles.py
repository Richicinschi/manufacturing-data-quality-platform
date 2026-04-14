"""Build the top signal profiles mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine

EXCLUDED_COLUMNS = {"entity_id", "test_timestamp", "yield_label", "pass_fail"}


def build_top_signal_profiles(
    top_n: int = 20,
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    ranking_schema: str = "mart",
    ranking_table: str = "top_signal_fail_separation",
    target_schema: str = "mart",
    target_table: str = "top_signal_profiles",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Compute per-class summary stats for the top N signal features.

    Args:
        top_n: Number of top features to profile.
        source_schema: Schema containing the source entity table.
        source_table: Name of the source entity table.
        ranking_schema: Schema containing the ranking table.
        ranking_table: Name of the ranking table.
        target_schema: Schema where the result table will be written.
        target_table: Name of the result table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame with per-class summary statistics for each top feature.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    ranking_fq = f"{ranking_schema}.{ranking_table}" if dialect != "sqlite" else ranking_table

    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)
    ranking = pd.read_sql(f"SELECT * FROM {ranking_fq}", engine)

    top_features = (
        ranking.sort_values(by="effect_size", ascending=False)
        .head(top_n)["feature_name"]
        .tolist()
    )

    records = []
    for col in top_features:
        for yield_label, yield_class in [(-1, "pass"), (1, "fail")]:
            series = df.loc[df["yield_label"] == yield_label, col]
            count = int(series.notna().sum())
            missing_count = int(series.isna().sum())
            mean = series.mean()
            stddev = series.std(ddof=0)
            min_val = series.min()
            p25 = series.quantile(0.25)
            median = series.quantile(0.50)
            p75 = series.quantile(0.75)
            max_val = series.max()

            records.append(
                {
                    "feature_name": col,
                    "yield_class": yield_class,
                    "count": count,
                    "missing_count": missing_count,
                    "mean": mean,
                    "stddev": stddev,
                    "min": min_val,
                    "p25": p25,
                    "median": median,
                    "p75": p75,
                    "max": max_val,
                }
            )

    result = pd.DataFrame(records)

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
