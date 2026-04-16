"""Build the model_inspection_metrics mart."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine
from src.modeling.pipeline_runner import get_pipeline_results


def build_model_inspection_metrics(
    target_schema: str = "mart",
    target_table: str = "model_inspection_metrics",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of mean CV inspection-rate metrics."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    results = get_pipeline_results(connection_string)
    df = results["benchmark"].copy()

    metric_cols = [
        "model",
        "feature_set",
        "model_family",
        "model_kind",
        "final_eligible",
        "enabled",
        "mean_recall_at_05pct",
        "mean_precision_at_05pct",
        "mean_lift_at_05pct",
        "mean_recall_at_10pct",
        "mean_precision_at_10pct",
        "mean_lift_at_10pct",
        "mean_recall_at_20pct",
        "mean_precision_at_20pct",
        "mean_lift_at_20pct",
    ]
    df = df[[c for c in metric_cols if c in df.columns]]

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
    return df
