"""Build the final_model_test_results mart."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine
from src.modeling.pipeline_runner import get_pipeline_results


def build_final_model_test_results(
    target_schema: str = "mart",
    target_table: str = "final_model_test_results",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of final holdout evaluation."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    results = get_pipeline_results(connection_string)
    row = results["final_eval"]["results"]
    df = pd.DataFrame([row])

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
