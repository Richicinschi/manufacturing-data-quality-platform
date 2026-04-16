"""Build the model_registry mart."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine
from src.modeling.trainer import MODEL_REGISTRY, is_model_enabled


def build_model_registry(
    target_schema: str = "mart",
    target_table: str = "model_registry",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of registered models with eligibility and availability."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    records = []
    for model_id, spec in MODEL_REGISTRY.items():
        enabled = is_model_enabled(spec)
        skip_reason = ""
        if not enabled:
            if not spec.enabled_by_default:
                skip_reason = "disabled by default"
            elif spec.optional_dependency:
                skip_reason = "optional dependency missing"
        records.append(
            {
                "model_id": model_id,
                "model_family": spec.family,
                "model_kind": spec.model_kind,
                "fit_mode": spec.fit_mode,
                "score_method": spec.score_method,
                "final_eligible": spec.final_eligible,
                "enabled": enabled,
                "skip_reason": skip_reason,
            }
        )

    df = pd.DataFrame(records)

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
