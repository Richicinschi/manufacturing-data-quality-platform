"""Build the selected_signal_shortlist mart."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src.db.connection import get_engine
from src.etl.feature_catalog import build_feature_catalog
from src.marts.top_signal_fail_separation import build_top_signal_fail_separation
from src.modeling.pipeline_runner import get_pipeline_results


def build_selected_signal_shortlist(
    target_schema: str = "mart",
    target_table: str = "selected_signal_shortlist",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of signals in the winning feature set with metadata."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    results = get_pipeline_results(connection_string)
    selected_features = results["final_eval"]["features"]
    catalog = build_feature_catalog(connection_string=connection_string)
    top_signals = build_top_signal_fail_separation(connection_string=connection_string)

    # Build effect-size rank map
    top_signals = top_signals.sort_values("effect_size", ascending=False).reset_index(drop=True)
    top_signals["effect_rank"] = top_signals.index + 1
    effect_map = top_signals.set_index("feature_name")["effect_rank"].to_dict()
    effect_size_map = top_signals.set_index("feature_name")["effect_size"].to_dict()

    catalog_map = catalog.set_index("feature_name").to_dict("index")

    records = []
    for feat in selected_features:
        meta = catalog_map.get(feat, {})
        records.append(
            {
                "feature_name": feat,
                "effect_rank": int(effect_map.get(feat, 9999)),
                "effect_size": float(effect_size_map.get(feat, 0.0)),
                "null_pct": float(meta.get("null_pct", 0.0)),
                "recommended_action": str(meta.get("recommended_action", "unknown")),
            }
        )

    df = pd.DataFrame(records).sort_values("effect_rank").reset_index(drop=True)

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
