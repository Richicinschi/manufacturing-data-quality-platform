"""Build the model_confusion_summary mart."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import confusion_matrix
from sqlalchemy import text

from src.db.connection import get_engine
from src.modeling.pipeline_runner import get_pipeline_results


def build_model_confusion_summary(
    target_schema: str = "mart",
    target_table: str = "model_confusion_summary",
    connection_string: str | None = None,
) -> pd.DataFrame:
    """Build mart table of confusion matrices for dev-OOF and test sets."""
    engine = get_engine(connection_string)
    dialect = engine.dialect.name

    results = get_pipeline_results(connection_string)

    # Dev OOF confusion (using best model + best feature set OOF on dev set CV)
    oof_df = results["oof_df"]
    best_model = results["best_info"]["model"]
    best_feature_set = results["best_info"]["feature_set"]
    threshold = results["threshold"]
    oof_col = f"oof_prob_{best_model}_{best_feature_set}"
    valid_oof = oof_df.dropna(subset=[oof_col])
    oof_preds = (valid_oof[oof_col] >= threshold).astype(int)
    cm_dev = confusion_matrix(valid_oof["y_true"], oof_preds)

    # Test confusion from final eval
    cm_test = results["final_eval"]["confusion"]

    records = [
        {
            "split": "dev_oof",
            "model": best_model,
            "feature_set": best_feature_set,
            "threshold": threshold,
            "tn": int(cm_dev[0, 0]),
            "fp": int(cm_dev[0, 1]),
            "fn": int(cm_dev[1, 0]),
            "tp": int(cm_dev[1, 1]),
        },
        {
            "split": "test",
            "model": best_model,
            "feature_set": best_feature_set,
            "threshold": threshold,
            "tn": int(cm_test["test_tn"]),
            "fp": int(cm_test["test_fp"]),
            "fn": int(cm_test["test_fn"]),
            "tp": int(cm_test["test_tp"]),
        },
    ]

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
