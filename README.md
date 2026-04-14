# manufacturing-data-quality-platform

A manufacturing data quality platform built around the UCI SECOM dataset, with a PostgreSQL warehouse, profiling pipeline, analytical marts, and a multi-page React website.

## Current State

- **SECOM dataset** loaded: `1,567` production entities with `590` measurement features from `secom.data`, with pass/fail labels stored separately
- **PostgreSQL warehouse** running locally with `manufacturing_dw`
- **Raw layer** available: `raw.secom_measurements`, `raw.secom_labels`, `raw.ingestion_log`
- **Staging layer** available: `staging.secom_entities`, `staging.feature_catalog`, `staging.signal_values_long`
- **Mart layer** available: `mart.secom_overview`, `mart.label_distribution`, `mart.feature_missingness`, `mart.feature_action_summary`, `mart.top_signal_fail_separation`, `mart.daily_yield_trend`
- **Website export** available through `scripts/generate_web_data.py`, which writes `website/src/data/generated/mart_data.json`
- **Frontend** available as a multi-page React + TypeScript + Vite app in `website/`

## Quick Test

```bash
cd workspace/manufacturing-data-quality-platform
export MDQP_DB_PASSWORD=postgres
python -m pytest tests/ -v
```

## Full Local Workflow

Run the full data pipeline first, then generate the website data bundle, then start the frontend.

```bash
cd workspace/manufacturing-data-quality-platform
export MDQP_DB_PASSWORD=postgres
python scripts/run_full_pipeline.py
python scripts/generate_web_data.py
```

Then install and run the website locally:

```bash
cd workspace/manufacturing-data-quality-platform/website
npm install
npm run dev
```

Vite will print a local URL such as `http://localhost:5173/`.

## Production Build

```bash
cd workspace/manufacturing-data-quality-platform/website
npm run build
```

The production assets will be written to `website/dist/`.

## Website Data Contract

The website reads one generated JSON bundle at:

```text
website/src/data/generated/mart_data.json
```

That file is built from the warehouse marts and currently contains:

- `overview`
- `label_distribution`
- `feature_missingness`
- `action_summary`
- `top_signals`
- `daily_trend`

If the generated JSON is missing, the website build should fail clearly rather than silently falling back to placeholder content.

## Documentation

- `docs/secom_findings.md` — analytical findings from the SECOM dataset
- `docs/secom_data_dictionary.md` — warehouse and export data dictionary
