# manufacturing-data-quality-platform

A manufacturing data quality platform built around the UCI SECOM dataset.

## Current State

- **SECOM dataset** loaded: 1,567 production entities with 590 measurement features from `secom.data`, with pass/fail labels stored separately, matching the official 591-attribute description
- **PostgreSQL warehouse** running locally with `manufacturing_dw` database
- **Raw layer** ingested: `raw.secom_measurements`, `raw.secom_labels`, `raw.ingestion_log`
- **Staging layer** created: `staging.secom_entities` joins stable `entity_id` with `test_timestamp`, `yield_label`, `pass_fail`, and all measurement features
- **Connection manager** (`src/db/connection.py`) supports PostgreSQL with SQLite fallback
- **Ingestion pipeline** tested and verified end-to-end against real PostgreSQL 16

## Quick Test

```bash
cd workspace/manufacturing-data-quality-platform
export MDQP_DB_PASSWORD=postgres
python -m pytest tests/ -v
```

back to roasting beans ☕
