# SECOM Analytical Findings

## What SECOM is

SECOM is a public semiconductor manufacturing dataset from the UCI Machine Learning Repository. It contains sensor and measurement readings collected during the production of wafers on a fabrication line. Each row represents a single production entity (a wafer lot or chip), and the columns represent hundreds of signals captured by process-monitoring equipment. The goal of the dataset is to predict which wafers will pass or fail quality control based on these readings alone.

## The 590 vs 591 question

The file `secom.data` contains exactly **590 measurement columns** for every production entity. The 591st attribute—the pass/fail label—is stored separately in `secom_labels.data`. During ingestion the two files are joined on row order (entity id) to produce the complete dataset. This separation is by design in the original UCI release.

## Class imbalance

The dataset is heavily imbalanced toward passing wafers:

- **Pass**: 1,463 entities (93.4%)
- **Fail**: 104 entities (6.6%)

This ~14:1 imbalance means any downstream model must be evaluated with care (e.g., precision-recall, F1, or AUC-PR) rather than simple accuracy.

## Feature sparsity profile

Across all 590 signals the overall missingness rate is roughly **4.5%**.

- **28 features** are high-missing (≥ 50% null values)
- **116 features** are constant (zero variance, all identical values)
- **0 features** are entirely null in the current dataset

These issues are typical of real-world industrial sensor data where instruments go offline, are recalibrated, or are not relevant to every process step.

## Strongest separating signals

Univariate effect size (Cohen's d) ranks signals reliably even before any modeling. The top separators—features whose distributions differ the most between pass and fail classes—are available in the warehouse table `mart.top_signal_fail_separation`. These signals can be used for:

- Quick diagnostic dashboards
- Feature-selection shortlists
- Root-cause discussions with process engineers

## What this project proves technically

This repository demonstrates an end-to-end data-quality and analytics pipeline:

- **ETL**: raw SECOM data ingestion, cleaning, and join logic
- **Warehouse design**: three-layer architecture (raw / staging / mart)
- **Feature profiling**: null rates, distinct counts, constant-value detection, recommended actions
- **Long-format transformation**: signals pivoted for time-series and analytical queries
- **Analytical marts**: overview, missingness, action summaries, effect-size rankings, daily yield trends
- **Static website generation**: JSON export contract feeding a React + TypeScript frontend

## What this project does not claim

The project focuses on data engineering, quality, and reproducible analytics. Machine-learning model training has been added as a case-study layer; see [`docs/secom_modeling_findings.md`](secom_modeling_findings.md) for walk-forward CV results, benchmark metrics, and the selected signal shortlist. The project explicitly does **not** include:

- Synthetic factory context or domain-specific sensor naming (the original features are anonymous)
- Deep learning, XGBoost, or SHAP explainability
- Real-time inference or production deployment
- Causal inference beyond observational effect sizes; correlations are not proof of causation
