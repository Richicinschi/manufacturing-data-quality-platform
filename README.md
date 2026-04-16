# manufacturing-data-quality-platform

A manufacturing data quality platform built around the UCI SECOM dataset, with a PostgreSQL warehouse, profiling pipeline, analytical marts, yield-failure detection modeling, and a multi-page React website.

## Current State

- **SECOM dataset** loaded: `1,567` production entities with `590` measurement features from `secom.data`, with pass/fail labels stored separately
- **PostgreSQL warehouse** running locally with `manufacturing_dw`
- **Raw layer** available: `raw.secom_measurements`, `raw.secom_labels`, `raw.ingestion_log`
- **Staging layer** available: `staging.secom_entities`, `staging.feature_catalog`, `staging.signal_values_long`
- **Mart layer** available: overview, label distribution, feature missingness, action summary, top signals, daily yield trend, feature failure relationship, daily failure rollup, feature groups, and full modeling marts (CV results, benchmark, threshold analysis, cost curve, probability bins, feature importance, final test results, confusion summary, selected signal shortlist)
- **Phase 3 modeling** added: anomaly detection baselines (Isolation Forest, LOF, Elliptic Envelope, One-Class SVM), new fold-local feature selectors (correlation pruning, mutual information, AUC gap, missingness indicators), inspection-rate metrics (recall@10%, precision@10%, lift@10%), and a random-split comparison script for public-notebook reference
- **Website export** available through `scripts/generate_web_data.py`, which writes `website/src/data/generated/mart_data.json`
- **Frontend** available as a multi-page React + TypeScript + Vite app in `website/`
- **Modeling note:** The trained model is a benchmark under severe class imbalance (6.6% fail rate), not a production-ready classifier. The project's value is in the end-to-end pipeline, signal prioritization, and leakage-safe evaluation design.
- **Default benchmark:** 8 enabled models × 12 feature sets = 96 model-feature configs, producing 384 walk-forward CV rows. `elliptic_envelope_pass_only` is registered but disabled by default.
- **Final holdout metrics (random_forest + keep_only):** PR-AUC `0.1354`, ROC-AUC `0.6067`, precision `0.5000`, recall `0.0667`, F1 `0.1176`.

## Quick Test

```bash
cd workspace/manufacturing-data-quality-platform
export MDQP_DB_PASSWORD=postgres
python -m pytest tests/ -v
```

## Full Local Workflow

Run the full data pipeline, then the modeling pipeline, then generate the website data bundle, then build the frontend.

```bash
cd workspace/manufacturing-data-quality-platform
export MDQP_DB_PASSWORD=postgres
python scripts/run_full_pipeline.py
python scripts/run_modeling_pipeline.py
python scripts/run_public_notebook_comparison.py  # optional random-split reference
python scripts/generate_web_data.py
cd website
npm run build
```

Then install and run the website locally:

```bash
cd workspace/manufacturing-data-quality-platform/website
npm install
npm run dev
```

Vite will print a local URL such as `http://localhost:5173/`.

The production assets will be written to `website/dist/`.

## Optional Modeling Boosters

The benchmark includes XGBoost and LightGBM as optional comparators. To enable them:

```bash
cd workspace/manufacturing-data-quality-platform
pip install -e ".[modeling-boosters]"
```

If they are not installed, the pipeline skips them cleanly and records a skip reason in `mart.model_registry`.

## Website Data Contract

The website reads one generated JSON bundle at:

```text
website/src/data/generated/mart_data.json
```

That file is built from the warehouse marts and currently contains:

- `overview`
- `label_distribution`
- `feature_missingness`
- `feature_catalog`
- `action_summary`
- `top_signals`
- `daily_trend`
- `top_signal_profiles`
- `feature_correlation_to_failure`
- `daily_failure_summary`
- `feature_groups`
- `model_registry`
- `model_cv_results`
- `model_benchmark`
- `model_threshold_analysis`
- `model_threshold_cost_curve`
- `model_probability_bins`
- `model_feature_importance`
- `final_model_test_results`
- `model_confusion_summary`
- `selected_signal_shortlist`
- `model_inspection_metrics`
- `model_feature_selection_summary`
- `anomaly_model_benchmark`
- `final_model_inspection_curve`
- `public_notebook_comparison` (empty if not run)

If the generated JSON is missing, the website build should fail clearly rather than silently falling back to placeholder content.

### Random-Split Comparison (Informational Only)

A separate script produces a random 70/30 split benchmark for side-by-side comparison with public notebooks:

```bash
python scripts/run_public_notebook_comparison.py
```

This is explicitly labeled `evaluation_protocol="random_split_reference"` and is **not** used for final model selection. The primary benchmark remains the chronological walk-forward CV.

## Documentation

- `docs/secom_findings.md` — analytical findings from the SECOM dataset
- `docs/secom_modeling_findings.md` — modeling case study, model selection rationale, and scope boundaries
- `docs/secom_data_dictionary.md` — warehouse and export data dictionary
