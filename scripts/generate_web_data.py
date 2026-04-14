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

from src.marts.daily_yield_trend import build_daily_yield_trend
from src.marts.feature_action_summary import build_feature_action_summary
from src.marts.feature_missingness import build_feature_missingness
from src.marts.label_distribution import build_label_distribution
from src.marts.overview import build_secom_overview
from src.marts.top_signal_fail_separation import build_top_signal_fail_separation
from src.etl.feature_catalog import build_feature_catalog


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
    }

    output_file = output_dir / "mart_data.json"
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, default=str)

    print(f"Data exported to: {output_file}")
    print("")
    print("Summary:")
    print(f"  - Entities: {data['overview']['entity_count']}")
    print(f"  - Features: {data['overview']['feature_count']}")
    print(f"  - Pass: {data['overview']['pass_count']}")
    print(f"  - Fail: {data['overview']['fail_count']}")
    print(f"  - Top signals: {len(data['top_signals'])}")
    print(f"  - Daily records: {len(data['daily_trend'])}")

    return output_file


if __name__ == "__main__":
    try:
        export_to_json()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
