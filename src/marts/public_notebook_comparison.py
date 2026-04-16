"""Build the public_notebook_comparison mart."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine


def build_public_notebook_comparison(
    target_schema: str = "mart",
    target_table: str = "public_notebook_comparison",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of random-split comparison results if available."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    comparison_path = Path("artifacts/public_notebook_comparison.json")
    if comparison_path.exists():
        with comparison_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data.get("results", []))
    else:
        df = pd.DataFrame(
            columns=[
                "model",
                "feature_set",
                "evaluation_protocol",
                "test_pr_auc",
                "test_roc_auc",
                "test_precision",
                "test_recall",
                "test_f1",
            ]
        )

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
