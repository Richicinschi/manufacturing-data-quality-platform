#!/usr/bin/env python3
"""Run the full manufacturing data quality pipeline end-to-end."""

import importlib.util
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))


def _import_script(name: str):
    scripts_dir = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(name, scripts_dir / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


raw_ingest = _import_script("run_raw_ingest")
build_staging = _import_script("build_staging")
build_marts = _import_script("build_marts")


def main() -> None:
    tables_created = []

    print("=" * 50)
    print("STEP 1: Raw Ingestion")
    print("=" * 50)
    raw_ingest.main()
    tables_created.extend(["raw.secom_measurements", "raw.secom_labels", "raw.ingestion_log"])

    print()
    print("=" * 50)
    print("STEP 2: Staging Build")
    print("=" * 50)
    build_staging.main()
    tables_created.extend([
        "staging.secom_entities",
        "staging.feature_catalog",
        "staging.signal_values_long",
    ])

    print()
    print("=" * 50)
    print("STEP 3: Mart Build")
    print("=" * 50)
    build_marts.main()
    tables_created.extend([
        "mart.secom_overview",
        "mart.label_distribution",
        "mart.feature_missingness",
        "mart.top_signal_fail_separation",
        "mart.top_signal_profiles",
        "mart.feature_failure_relationship",
        "mart.daily_failure_rollup",
        "mart.feature_priority_index",
        "mart.daily_yield_trend",
        "mart.feature_action_summary",
    ])

    print()
    print("=" * 50)
    print("Pipeline Complete")
    print("=" * 50)
    print("Tables created:")
    for table in tables_created:
        print(f"  - {table}")


if __name__ == "__main__":
    main()
