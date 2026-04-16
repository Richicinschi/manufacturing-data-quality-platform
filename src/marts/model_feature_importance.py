"""Build the model_feature_importance mart."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine
from src.modeling.pipeline_runner import get_pipeline_results


def build_model_feature_importance(
    target_schema: str = "mart",
    target_table: str = "model_feature_importance",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of final-model feature importance."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    results = get_pipeline_results(connection_string)
    df = results["final_eval"]["feature_importance"].copy()

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
