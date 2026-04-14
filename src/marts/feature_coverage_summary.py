"""Build the feature coverage summary mart table."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_feature_coverage_summary(
    catalog_schema: str = "staging",
    catalog_table: str = "feature_catalog",
    target_schema: str = "mart",
    target_table: str = "feature_coverage_summary",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build a coverage summary from the feature catalog.

    Args:
        catalog_schema: Schema containing the feature catalog table.
        catalog_table: Name of the feature catalog table.
        target_schema: Schema where the result table will be written.
        target_table: Name of the result table.
        connection_string: Optional explicit DB connection string.

    Returns:
        DataFrame with coverage summary metrics.
    """
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    catalog_fq = f"{catalog_schema}.{catalog_table}" if dialect != "sqlite" else catalog_table
    catalog = pd.read_sql(f"SELECT * FROM {catalog_fq}", engine)

    total = len(catalog)
    complete = int((catalog["null_pct"] == 0).sum())
    sparse = int((catalog["null_pct"] > 0).sum())
    high_missing = int((catalog["null_pct"] >= 0.5).sum())
    constant = int(catalog["is_constant"].sum())
    all_null = int((catalog["recommended_action"] == "drop_all_null").sum())
    usable = int((catalog["recommended_action"] == "keep").sum())
    review = int((catalog["recommended_action"] == "review_high_missing").sum())

    records = [
        {"metric": "total_features", "count": total, "description": "All profiled features"},
        {"metric": "complete_features", "count": complete, "description": "0% missing values"},
        {"metric": "sparse_features", "count": sparse, "description": ">0% missing values"},
        {"metric": "usable_features", "count": usable, "description": "Recommended to keep"},
        {"metric": "review_features", "count": review, "description": "High missingness review"},
        {"metric": "high_missing_features", "count": high_missing, "description": "Missingness >= 50%"},
        {"metric": "constant_features", "count": constant, "description": "Constant-valued features"},
        {"metric": "all_null_features", "count": all_null, "description": "100% missing values"},
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
