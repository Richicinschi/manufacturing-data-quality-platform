"""Build the model_feature_selection_summary mart."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine
from src.modeling.pipeline_runner import get_pipeline_results


def build_model_feature_selection_summary(
    target_schema: str = "mart",
    target_table: str = "model_feature_selection_summary",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of per-fold feature selection counts and examples."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    results = get_pipeline_results(connection_string)
    cv = results["cv_results"].copy()

    if "selected_features" not in cv.columns or cv.empty:
        df = pd.DataFrame(
            columns=[
                "model",
                "feature_set",
                "mean_n_selected",
                "min_n_selected",
                "max_n_selected",
                "example_features",
            ]
        )
    else:
        import json

        cv["n_selected"] = cv["n_features_selected"]
        # Collect first fold's selected features as an example
        examples = (
            cv.groupby(["model", "feature_set"])
            .apply(lambda g: json.loads(g.iloc[0]["selected_features"])[:10])
            .reset_index(name="example_features")
        )

        stats = (
            cv.groupby(["model", "feature_set"])
            .agg(
                mean_n_selected=("n_selected", "mean"),
                min_n_selected=("n_selected", "min"),
                max_n_selected=("n_selected", "max"),
            )
            .reset_index()
        )

        df = stats.merge(examples, on=["model", "feature_set"], how="left")
        df["example_features"] = df["example_features"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else x
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
