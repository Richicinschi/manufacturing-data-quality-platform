"""Build the feature failure relationship mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine

EXCLUDED_COLUMNS = {"entity_id", "test_timestamp", "yield_label", "pass_fail"}


def build_feature_failure_relationship(
    source_schema: str = "staging",
    source_table: str = "secom_entities",
    catalog_schema: str = "staging",
    catalog_table: str = "feature_catalog",
    target_schema: str = "mart",
    target_table: str = "feature_failure_relationship",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Compute failure relationship metrics for each valid feature.

    Args:
        source_schema: Schema containing the source entity table.
        source_table: Name of the source entity table.
        catalog_schema: Schema containing the feature catalog table.
        catalog_table: Name of the feature catalog table.
        target_schema: Schema where the result table will be written.
        target_table: Name of the result table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame ordered by effect_size DESC (NaNs last) with relationship metrics.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    source_fq = f"{source_schema}.{source_table}" if dialect != "sqlite" else source_table
    catalog_fq = f"{catalog_schema}.{catalog_table}" if dialect != "sqlite" else catalog_table
    ranking_fq = f"mart.top_signal_fail_separation" if dialect != "sqlite" else "top_signal_fail_separation"

    df = pd.read_sql(f"SELECT * FROM {source_fq}", engine)
    catalog = pd.read_sql(f"SELECT * FROM {catalog_fq}", engine)
    ranking = pd.read_sql(f"SELECT * FROM {ranking_fq}", engine)

    total_rows = len(df)
    feature_cols = [c for c in df.columns if c not in EXCLUDED_COLUMNS]

    # Filter out constant or all-null features
    valid_catalog = catalog[
        (catalog["is_constant"] != True) & (catalog["null_count"] != total_rows)
    ]
    valid_features = [c for c in feature_cols if c in valid_catalog["feature_name"].values]

    records = []
    for col in valid_features:
        pass_series = df.loc[df["yield_label"] == -1, col]
        fail_series = df.loc[df["yield_label"] == 1, col]

        valid_pass_count = int(pass_series.notna().sum())
        valid_fail_count = int(fail_series.notna().sum())
        pass_mean = pass_series.mean()
        fail_mean = fail_series.mean()
        mean_gap = abs(pass_mean - fail_mean) if pd.notna(pass_mean) and pd.notna(fail_mean) else float("nan")

        effect_size_row = ranking[ranking["feature_name"] == col]
        effect_size = effect_size_row["effect_size"].iloc[0] if not effect_size_row.empty else float("nan")

        records.append(
            {
                "feature_name": col,
                "effect_size": effect_size,
                "pass_mean": pass_mean,
                "fail_mean": fail_mean,
                "mean_gap": mean_gap,
                "valid_pass_count": valid_pass_count,
                "valid_fail_count": valid_fail_count,
            }
        )

    result = pd.DataFrame(records)
    result = result.sort_values(by="effect_size", ascending=False, na_position="last").reset_index(drop=True)

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
