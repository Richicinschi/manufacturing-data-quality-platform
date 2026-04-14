#!/usr/bin/env python3
"""Build staging tables for the manufacturing data quality platform."""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

from src.etl.secom_join import build_secom_entities, save_secom_entities
from src.etl.feature_catalog import build_feature_catalog
from src.etl.build_signals import build_signal_values_long


def main() -> None:
    print("Building staging.secom_entities...")
    df_entities = build_secom_entities(schema="raw")
    rows = save_secom_entities(df_entities, target_schema="staging", target_table="secom_entities")
    print(f"  Written {rows:,} rows to staging.secom_entities")

    print("Building staging.feature_catalog...")
    build_feature_catalog(
        source_schema="staging",
        source_table="secom_entities",
        target_schema="staging",
        target_table="feature_catalog",
    )
    print("  Built staging.feature_catalog")

    print("Building staging.signal_values_long...")
    rows = build_signal_values_long(
        source_schema="staging",
        source_table="secom_entities",
        target_schema="staging",
        target_table="signal_values_long",
    )
    print(f"  Written {rows:,} rows to staging.signal_values_long")

    print("Staging build complete.")


if __name__ == "__main__":
    main()
