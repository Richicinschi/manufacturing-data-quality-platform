#!/usr/bin/env python3
"""Run raw SECOM ingestion into PostgreSQL."""

from pathlib import Path

from src.etl.raw_ingest import ingest_secom


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data" / "raw" / "secom"

    data_path = data_dir / "secom.data"
    labels_path = data_dir / "secom_labels.data"

    print("Ingesting SECOM raw data...")
    results = ingest_secom(
        data_path=data_path,
        labels_path=labels_path,
        schema="raw",
    )

    for table_name, row_count in results.items():
        print(f"  Loaded {row_count:,} rows into {table_name}")

    print("Done.")


if __name__ == "__main__":
    main()
