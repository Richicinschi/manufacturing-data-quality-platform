"""Build the feature groups mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_feature_groups(
    top_n: int = 20,
    catalog_schema: str = "staging",
    catalog_table: str = "feature_catalog",
    ranking_schema: str = "mart",
    ranking_table: str = "feature_failure_relationship",
    target_schema: str = "mart",
    target_table: str = "feature_groups",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build feature group buckets for the UI priority review view.

    Args:
        top_n: Number of top separator features.
        catalog_schema: Schema containing the feature catalog table.
        catalog_table: Name of the feature catalog table.
        ranking_schema: Schema containing the effect-size ranking table.
        ranking_table: Name of the ranking table.
        target_schema: Schema where the result table will be written.
        target_table: Name of the result table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame with one row per feature group.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    catalog_fq = f"{catalog_schema}.{catalog_table}" if dialect != "sqlite" else catalog_table
    ranking_fq = f"{ranking_schema}.{ranking_table}" if dialect != "sqlite" else ranking_table

    catalog = pd.read_sql(f"SELECT * FROM {catalog_fq}", engine)
    ranking = pd.read_sql(f"SELECT * FROM {ranking_fq}", engine)

    top_features = (
        ranking.sort_values(by="effect_size", ascending=False)
        .head(top_n)["feature_name"]
        .tolist()
    )

    top_set = set(top_features)

    top_count = len(catalog[catalog["feature_name"].isin(top_set)])
    review = catalog[catalog["recommended_action"] == "review_high_missing"]
    keep = catalog[(catalog["recommended_action"] == "keep") & (~catalog["feature_name"].isin(top_set))]
    constant = catalog[catalog["recommended_action"] == "drop_constant"]
    all_null = catalog[catalog["recommended_action"] == "drop_all_null"]

    records = [
        {
            "group_name": "top_separators",
            "count": top_count,
            "description": f"Top {top_n} features by effect size",
            "example_features": ", ".join(top_features[:5]),
        },
        {
            "group_name": "review_high_missing",
            "count": len(review),
            "description": "High missingness (>=50% null)",
            "example_features": ", ".join(review["feature_name"].head(5).tolist()),
        },
        {
            "group_name": "standard_keep",
            "count": len(keep),
            "description": "Standard keep (not in top separators)",
            "example_features": ", ".join(keep["feature_name"].head(5).tolist()),
        },
        {
            "group_name": "excluded_constant",
            "count": len(constant),
            "description": "Excluded due to constant values",
            "example_features": ", ".join(constant["feature_name"].head(5).tolist()),
        },
        {
            "group_name": "excluded_all_null",
            "count": len(all_null),
            "description": "Excluded due to 100% missing values",
            "example_features": ", ".join(all_null["feature_name"].head(5).tolist()),
        },
    ]

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
