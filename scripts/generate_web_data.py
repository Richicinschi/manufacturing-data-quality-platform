#!/usr/bin/env python3
"""Export mart data to JSON for the website.

Run this script from the repo root:
    python scripts/generate_web_data.py

This will create website/src/data/generated/mart_data.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add repo root to path so `src.*` imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.marts.daily_failure_rollup import build_daily_failure_rollup
from src.marts.daily_yield_trend import build_daily_yield_trend
from src.marts.feature_action_summary import build_feature_action_summary
from src.marts.feature_failure_relationship import build_feature_failure_relationship
from src.marts.feature_missingness import build_feature_missingness
from src.marts.feature_priority_index import build_feature_priority_index
from src.marts.label_distribution import build_label_distribution
from src.marts.overview import build_secom_overview
from src.marts.top_signal_fail_separation import build_top_signal_fail_separation
from src.marts.top_signal_profiles import build_top_signal_profiles
from src.marts.model_cv_results import build_model_cv_results
from src.marts.model_benchmark import build_model_benchmark
from src.marts.model_threshold_analysis import build_model_threshold_analysis
from src.marts.final_model_test_results import build_final_model_test_results
from src.marts.model_confusion_summary import build_model_confusion_summary
from src.marts.selected_signal_shortlist import build_selected_signal_shortlist
from src.marts.model_registry import build_model_registry
from src.marts.model_feature_importance import build_model_feature_importance
from src.marts.model_threshold_cost_curve import build_model_threshold_cost_curve
from src.marts.model_probability_bins import build_model_probability_bins
from src.marts.model_inspection_metrics import build_model_inspection_metrics
from src.marts.model_feature_selection_summary import build_model_feature_selection_summary
from src.marts.anomaly_model_benchmark import build_anomaly_model_benchmark
from src.marts.final_model_inspection_curve import build_final_model_inspection_curve
from src.marts.public_notebook_comparison import build_public_notebook_comparison
from src.etl.feature_catalog import build_feature_catalog
from src.db.connection import get_engine
from src.modeling.pipeline_runner import get_pipeline_results
import pandas as pd


def _read_mart(table: str, schema: str = "mart") -> pd.DataFrame:
    engine = get_engine()
    dialect = engine.dialect.name
    fq = f"{schema}.{table}" if dialect != "sqlite" else table
    return pd.read_sql(f"SELECT * FROM {fq}", engine)


def export_to_json() -> Path:
    """Export mart data to the generated website bundle."""

    print("Building marts from database...")

    overview = build_secom_overview()
    label_dist = build_label_distribution()
    feature_missing = build_feature_missingness()
    feature_catalog = build_feature_catalog()
    action_summary = build_feature_action_summary()
    top_signals = build_top_signal_fail_separation()
    daily_trend = build_daily_yield_trend()

    # New expanded exports
    top_signal_profiles = build_top_signal_profiles(top_n=20)
    feature_correlation_to_failure = build_feature_failure_relationship()

    # feature_coverage_summary
    total_rows = int(overview["entity_count"].iloc[0])
    coverage_df = feature_catalog[[
        "feature_name",
        "null_pct",
        "null_count",
        "distinct_count",
        "recommended_action",
    ]].copy()
    coverage_df["non_null_count"] = total_rows - coverage_df["null_count"]
    feature_coverage_summary = coverage_df[[
        "feature_name",
        "null_pct",
        "non_null_count",
        "distinct_count",
        "recommended_action",
    ]].to_dict(orient="records")

    daily_failure_summary = build_daily_failure_rollup()

    # Modeling marts: read from DB if already built by run_modeling_pipeline.py
    model_cv_results = _read_mart("model_cv_results")
    model_benchmark = _read_mart("model_benchmark")
    model_threshold_analysis = _read_mart("model_threshold_analysis")
    final_model_test_results = _read_mart("final_model_test_results")
    model_confusion_summary = _read_mart("model_confusion_summary")
    selected_signal_shortlist = _read_mart("selected_signal_shortlist")
    model_registry = _read_mart("model_registry")
    model_feature_importance = _read_mart("model_feature_importance")
    model_threshold_cost_curve = _read_mart("model_threshold_cost_curve")
    model_probability_bins = _read_mart("model_probability_bins")
    model_inspection_metrics = _read_mart("model_inspection_metrics")
    model_feature_selection_summary = _read_mart("model_feature_selection_summary")
    anomaly_model_benchmark = _read_mart("anomaly_model_benchmark")
    final_model_inspection_curve = _read_mart("final_model_inspection_curve")
    try:
        public_notebook_comparison = _read_mart("public_notebook_comparison")
    except Exception:
        public_notebook_comparison = pd.DataFrame()

    # Phase 3 inspection artifacts from DB marts (avoid re-running pipeline)
    inspection_curve_df = _read_mart("final_model_inspection_curve")
    # Read final inspection metrics from artifact metadata if available
    import json as _json
    metadata_path = Path("artifacts/secom_model_metadata.json")
    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = _json.load(f)
        inspection_metrics_dict = metadata.get("inspection_metrics", {})
    else:
        inspection_metrics_dict = {}

    # feature_groups
    priority_index = build_feature_priority_index()
    grouped = priority_index.groupby("priority_bucket")
    feature_groups_buckets = []
    for bucket_name, g in grouped:
        features = g["feature_name"].tolist()
        feature_groups_buckets.append({
            "bucket_name": bucket_name,
            "feature_count": len(features),
            "features": features,
        })

    keep_review_buckets = {"standard_keep", "review_high_missing", "top_separator"}
    feature_groups = {
        "buckets": feature_groups_buckets,
        "top_separators": top_signal_profiles["feature_name"].unique().tolist()[:20],
        "high_missing_count": int((priority_index["priority_bucket"] == "review_high_missing").sum()),
        "constant_count": int((priority_index["priority_bucket"] == "excluded_constant").sum()),
        "keep_review_priority_count": int(priority_index["priority_bucket"].isin(keep_review_buckets).sum()),
    }

    output_dir = Path(__file__).parent.parent / "website" / "src" / "data" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "overview": overview.to_dict(orient="records")[0],
        "label_distribution": label_dist.to_dict(orient="records"),
        "feature_missingness": feature_missing.to_dict(orient="records"),
        "feature_catalog": feature_catalog.to_dict(orient="records"),
        "action_summary": action_summary.to_dict(orient="records"),
        "top_signals": top_signals.to_dict(orient="records"),
        "daily_trend": daily_trend.to_dict(orient="records"),
        "top_signal_profiles": top_signal_profiles.to_dict(orient="records"),
        "feature_correlation_to_failure": feature_correlation_to_failure.to_dict(orient="records"),
        "daily_failure_summary": daily_failure_summary.to_dict(orient="records"),
        "feature_groups": feature_groups,
        "model_cv_results": model_cv_results.to_dict(orient="records"),
        "model_benchmark": model_benchmark.to_dict(orient="records"),
        "model_threshold_analysis": model_threshold_analysis.to_dict(orient="records"),
        "final_model_test_results": final_model_test_results.to_dict(orient="records"),
        "model_confusion_summary": model_confusion_summary.to_dict(orient="records"),
        "selected_signal_shortlist": selected_signal_shortlist.to_dict(orient="records"),
        "model_registry": model_registry.to_dict(orient="records"),
        "model_feature_importance": model_feature_importance.to_dict(orient="records"),
        "model_threshold_cost_curve": model_threshold_cost_curve.to_dict(orient="records"),
        "model_probability_bins": model_probability_bins.to_dict(orient="records"),
        "inspection_curve": inspection_curve_df.to_dict(orient="records"),
        "inspection_metrics": inspection_metrics_dict,
        "model_inspection_metrics": model_inspection_metrics.to_dict(orient="records"),
        "model_feature_selection_summary": model_feature_selection_summary.to_dict(orient="records"),
        "anomaly_model_benchmark": anomaly_model_benchmark.to_dict(orient="records"),
        "final_model_inspection_curve": final_model_inspection_curve.to_dict(orient="records"),
        "public_notebook_comparison": public_notebook_comparison.to_dict(orient="records"),
    }

    output_file = output_dir / "mart_data.json"
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, default=str)

    # Build lightweight landing summary
    overview_record = overview.to_dict(orient="records")[0]
    entity_count = int(overview_record["entity_count"])
    feature_count = int(overview_record["feature_count"])

    action_map = {row["recommended_action"]: int(row["feature_count"]) for row in action_summary.to_dict(orient="records")}

    top_models = (
        model_benchmark
        .copy()
        .sort_values("mean_pr_auc", ascending=False)
        .head(5)[["model", "feature_set", "mean_pr_auc"]]
        .to_dict(orient="records")
    )

    def _find_inspection(rate: float):
        row = inspection_curve_df[
            inspection_curve_df["inspection_rate"].apply(lambda x: abs(float(x) - rate) < 0.001)
        ]
        if row.empty:
            return {"recall": 0.0, "precision": 0.0, "lift": 0.0, "captured_fails": 0}
        r = row.iloc[0]
        return {
            "recall": float(r["recall"]),
            "precision": float(r["precision"]),
            "lift": float(r["lift"]),
            "captured_fails": int(r["captured_fails"]),
        }

    final_model_row = final_model_test_results.to_dict(orient="records")[0] if not final_model_test_results.empty else {}

    landing_summary = {
        "overview": {
            "entity_count": entity_count,
            "feature_count": feature_count,
            "pass_count": int(overview_record["pass_count"]),
            "fail_count": int(overview_record["fail_count"]),
            "pass_pct": float(overview_record["pass_pct"]),
            "fail_pct": float(overview_record["fail_pct"]),
            "min_timestamp": str(overview_record["min_timestamp"]),
            "max_timestamp": str(overview_record["max_timestamp"]),
        },
        "signal_rows": entity_count * feature_count,
        "ranked_separator_count": len(feature_correlation_to_failure),
        "feature_actions": {
            "keep": action_map.get("keep", 0),
            "drop_constant": action_map.get("drop_constant", 0),
            "review_high_missing": action_map.get("review_high_missing", 0),
            "drop_all_null": action_map.get("drop_all_null", 0),
        },
        "benchmark_scale": {
            "model_configs": len(model_benchmark),
            "cv_rows": len(model_cv_results),
        },
        "final_model": {
            "model": str(final_model_row.get("model", "-")),
            "feature_set": str(final_model_row.get("feature_set", "-")),
            "test_pr_auc": float(final_model_row.get("test_pr_auc", 0.0)),
            "test_roc_auc": float(final_model_row.get("test_roc_auc", 0.0)),
            "test_precision": float(final_model_row.get("test_precision", 0.0)),
            "test_recall": float(final_model_row.get("test_recall", 0.0)),
            "test_f1": float(final_model_row.get("test_f1", 0.0)),
        },
        "top_models_by_pr_auc": [
            {"model": str(r["model"]), "feature_set": str(r["feature_set"]), "mean_pr_auc": round(float(r["mean_pr_auc"]), 4)}
            for r in top_models
        ],
        "inspection_policy": {
            "top_05": _find_inspection(0.05),
            "top_10": _find_inspection(0.10),
            "top_20": _find_inspection(0.20),
        },
    }

    landing_file = output_dir / "landing_summary.json"
    with landing_file.open("w", encoding="utf-8") as handle:
        json.dump(landing_summary, handle, indent=2, default=str)

    print(f"Data exported to: {output_file}")
    print(f"Landing summary exported to: {landing_file}")
    print("")
    print("Summary:")
    print(f"  - Entities: {data['overview']['entity_count']}")
    print(f"  - Features: {data['overview']['feature_count']}")
    print(f"  - Pass: {data['overview']['pass_count']}")
    print(f"  - Fail: {data['overview']['fail_count']}")
    print(f"  - Top signals: {len(data['top_signals'])}")
    print(f"  - Daily records: {len(data['daily_trend'])}")
    print(f"  - Top signal profiles: {len(data['top_signal_profiles'])}")
    print(f"  - Feature correlation to failure: {len(data['feature_correlation_to_failure'])}")
    print(f"  - Daily failure summary: {len(data['daily_failure_summary'])}")
    print(f"  - Feature groups buckets: {len(data['feature_groups']['buckets'])}")
    print(f"  - Model CV results: {len(data['model_cv_results'])}")
    print(f"  - Model benchmark rows: {len(data['model_benchmark'])}")
    print(f"  - Threshold analysis rows: {len(data['model_threshold_analysis'])}")
    print(f"  - Final model test results: {len(data['final_model_test_results'])}")
    print(f"  - Model confusion summary: {len(data['model_confusion_summary'])}")
    print(f"  - Selected signal shortlist: {len(data['selected_signal_shortlist'])}")
    print(f"  - Model registry: {len(data['model_registry'])}")
    print(f"  - Model feature importance: {len(data['model_feature_importance'])}")
    print(f"  - Model threshold cost curve: {len(data['model_threshold_cost_curve'])}")
    print(f"  - Model probability bins: {len(data['model_probability_bins'])}")
    print(f"  - Inspection curve: {len(data['inspection_curve'])}")
    print(f"  - Inspection metrics: {list(data['inspection_metrics'].keys())}")
    print(f"  - Model inspection metrics: {len(data['model_inspection_metrics'])}")
    print(f"  - Model feature selection summary: {len(data['model_feature_selection_summary'])}")
    print(f"  - Anomaly model benchmark: {len(data['anomaly_model_benchmark'])}")
    print(f"  - Final model inspection curve: {len(data['final_model_inspection_curve'])}")
    print(f"  - Public notebook comparison: {len(data['public_notebook_comparison'])}")

    return output_file


if __name__ == "__main__":
    try:
        export_to_json()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
