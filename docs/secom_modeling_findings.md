# SECOM Modeling Findings

## Business Context

Semiconductor manufacturing tools generate hundreds of process signals — temperature, pressure, voltage, chemical concentrations — for every wafer or entity that passes through. Most of these signals are noisy, many are redundant, and only a small fraction are directly actionable. The business problem is twofold:

1. **Detect rare yield failures early** so that process engineers can intervene before bad lots propagate downstream.
2. **Prioritize the most useful signals** so that root-cause investigations are focused rather than overwhelming.

This modeling phase treats the UCI SECOM dataset as a representative high-dimensional sensor stream. The goal is not to claim a production-ready classifier, but to demonstrate a reproducible, leakage-safe pipeline that compares model families and produces a ranked, explainable signal shortlist.

## What this phase adds

The modeling phase transforms the project from a data-quality analytics platform into a **yield-failure detection and signal-selection case study**. It trains imbalance-aware classifiers on the UCI SECOM dataset, evaluates them with walk-forward cross-validation, and produces a shortlist of signals that survive selection without data leakage.

## Dataset reminder

- **1,567 entities** with **590 features**
- **104 fails** (6.6%) vs **1,463 passes** (93.4%)
- Strong class imbalance means accuracy is misleading; PR-AUC and fail-class F1 are the primary metrics.

## Results in Context

The final benchmark results are modest: test PR-AUC **0.1354**, ROC-AUC **0.6067**, precision **0.5000**, recall **0.0667**, F1 **0.1176** (1 true positive, 14 false negatives, 1 false positive, 248 true negatives). These numbers are not a bug — they reflect the genuine difficulty of the SECOM problem under severe class imbalance with raw, unengineered sensor signals. The value of this phase is **not** a production-ready defect detector; it is a **reproducible, leakage-safe benchmark** that compares model families, prioritizes signals, and demonstrates how to structure a modeling pipeline from warehouse marts to deployable artifacts.

## Why walk-forward CV?

SECOM has a natural time ordering (`test_timestamp`). A random train/test split would leak future information into the training set and overstate performance. We use **expanding-window walk-forward CV** on the development set (oldest 85%):

- Fold 1 trains on the earliest data, tests on the next slice.
- Each subsequent fold expands the training window forward in time.
- Splits respect **whole calendar dates** so that no single date appears in both train and test.
- If any fold has fewer than 8 fail-class samples, the engine gracefully degrades to fewer splits.

## Feature sets evaluated

All models are evaluated across twelve feature sets:

1. `keep_only` — features cataloged as `keep`
2. `keep_plus_review` — `keep` + `review_high_missing`
3. `top_20_effect` — top 20 by Cohen's d computed **inside each training fold**
4. `top_50_effect` — top 50 by Cohen's d computed inside each training fold
5. `top_100_effect` — top 100 by Cohen's d computed inside each training fold
6. `correlation_pruned_070` — drops one feature from each pair with |r| ≥ 0.70
7. `correlation_pruned_085` — drops one feature from each pair with |r| ≥ 0.85
8. `top_25_mutual_info` — top 25 by mutual information after median imputation
9. `top_50_mutual_info` — top 50 by mutual information after median imputation
10. `top_25_auc_gap` — top 25 by absolute univariate ROC-AUC distance from 0.5
11. `top_50_auc_gap` — top 50 by absolute univariate ROC-AUC distance from 0.5
12. `missingness_indicators_keep` — `keep_only` plus `_missing` indicator columns for any training-fold NaNs

The fold-time computation of all dynamic selectors prevents leakage: the ranking is derived only from data seen during training.

## Model selection rationale

**Primary metric: fail-class PR-AUC**
- ROC-AUC is misleading when the positive class is rare because it weights true-negative performance too heavily.
- PR-AUC focuses exclusively on the precision-recall tradeoff for failures, which is what a process engineer cares about.

**Threshold selection: business tradeoff, not a fixed 0.5**
- The selected threshold maximizes fail-class F1 on development out-of-fold predictions.
- In practice, a process team might prefer a lower threshold (more recalls, higher inspection volume) or a higher threshold (fewer false alarms) depending on the cost of missing a failure versus the cost of unnecessary inspection.

**Final model eligibility**
- Only models marked `final_eligible=true` can win the benchmark and be evaluated on the untouched test set.
- Baseline and contrast models (`dummy_stratified`, `knn_scaled`) are trained for comparison but excluded from final selection.

## Classifiers evaluated

| Model | Family | Final Eligible | Notes |
|-------|--------|----------------|-------|
| `dummy_stratified` | baseline | no | Minimum benchmark under class imbalance |
| `logistic_l1` | linear | yes | Sparse, interpretable coefficient baseline |
| `logistic_l2` | linear | yes | Stable regularized linear probability model |
| `random_forest` | bagged trees | yes | Nonlinear interactions, built-in feature importance |
| `hist_gradient_boosting` | boosted trees | yes | Sklearn-native, handles NaNs without imputation |
| `xgboost_hist` | boosted trees | yes* | Industry-standard gradient boosting comparator |
| `lightgbm_gbdt` | boosted trees | yes* | Fast gradient boosting comparator |
| `knn_scaled` | distance-based | no | Contrast model; high-dimensional distance methods are weak here |

\* Only if the optional dependency is installed (`pip install -e ".[modeling-boosters]"`).

No hyper-parameter tuning grid is used; parameters are hard-coded to keep the scope focused on architecture and comparison.

## Threshold selection

The probability threshold is chosen to **maximize fail-class F1** on the development out-of-fold (OOF) predictions from the best-performing model. This threshold is then locked and applied to the final holdout evaluation.

A threshold cost curve is also reported, showing:
- predicted_fail_count
- false_positive_count
- false_negative_count
- inspection_rate

This lets a process engineer choose their own tradeoff if F1-maximization is not the right business objective.

## Final evaluation protocol

- **Development**: oldest 85% of chronologically sorted data
- **Final holdout**: newest 15%
- Best model/feature set is selected by **mean CV PR-AUC on the development set**, restricted to `final_eligible=true` models only.
- The best model is retrained on the full development set and evaluated **exactly once** on the holdout.

## What the modeling marts capture

| Mart | Purpose |
|------|---------|
| `mart.model_registry` | Model metadata: family, kind, fit mode, score method, final eligibility, enabled status, skip reason |
| `mart.model_cv_results` | Per-fold metrics with date ranges, fail counts, honest feature counts, and inspection-rate metrics |
| `mart.model_benchmark` | Mean/std PR-AUC per model by feature set with rank and best-for-inspection-policy flag |
| `mart.model_threshold_analysis` | Threshold sweep (precision, recall, F1) with selected flag |
| `mart.model_threshold_cost_curve` | Business-oriented threshold tradeoffs |
| `mart.model_probability_bins` | Final test probability bins and actual failure concentration |
| `mart.model_feature_importance` | Final-model feature importance or coefficients |
| `mart.final_model_test_results` | Single-row final holdout metrics |
| `mart.model_confusion_summary` | Confusion matrices for dev-OOF and test sets |
| `mart.selected_signal_shortlist` | Winning feature set with effect rank, null %, and catalog action |
| `mart.model_inspection_metrics` | Mean CV precision/recall/lift at 5%, 10%, 20% inspection rates |
| `mart.model_feature_selection_summary` | Per-model/feature-set feature counts and selected-feature examples |
| `mart.anomaly_model_benchmark` | Anomaly detector benchmark subset |
| `mart.final_model_inspection_curve` | Final test top-k inspection curve |
| `mart.public_notebook_comparison` | Optional random-split reference results (informational only) |

## Key takeaways for process engineering

- **Effect size is a reliable pre-modeling filter**: Cohen's d ranks signals consistently even before training, making it useful for diagnostic dashboards and root-cause discussions.
- **Dynamic feature selection prevents leakage**: Computing top-N effect sizes inside each CV fold ensures the shortlist is honest and generalizable.
- **Imbalance-aware evaluation matters**: PR-AUC focuses on the rare fail class and is more informative than ROC-AUC in this heavily imbalanced setting.
- **Model family comparison reveals structure**: Linear models provide interpretable baselines; tree ensembles capture interactions; gradient boosting often leads on tabular sensor data.
- **The final shortlist is actionable**: Every selected signal is annotated with its catalog `recommended_action`, so process engineers can immediately see whether a signal is clean (`keep`) or requires review (`review_high_missing`).

## What not to claim

To keep this project intellectually honest and recruiter-friendly, the following claims are explicitly **out of scope**:

- **Causal findings** — correlations between signals and failures are not proof that changing a signal will change yield.
- **Production deployment** — this is a local/static portfolio case study, not a live API or factory integration.
- **Accuracy headlines** — overall accuracy is meaningless with 6.6% failure rate; PR-AUC and F1 are the only metrics reported.
- **Real sensor names** — SECOM feature IDs (`feature_001`, `feature_002`, etc.) are anonymized; no claim is made that they map to specific physical sensors.
- **Calibrated probabilities** — probability bins are diagnostic only; they should not be treated as well-calibrated risk scores without further validation.

## Phase 3: Anomaly Detection + Inspection Metrics

Phase 3 extends the benchmark with anomaly-detection baselines and business-oriented inspection metrics.

### Default benchmark scale

- **8 enabled models** (excluding baselines/contrast models and disabled anomaly detectors)
- **12 feature sets** evaluated per model
- **96 model-feature configs** in the default benchmark
- **384 walk-forward CV rows** (96 configs × 4 folds)

### Anomaly detection models

Five anomaly detectors are registered; two are enabled by default in the production benchmark under a unified risk-score framework:

| Model | Family | Final Eligible | Fit Mode |
|-------|--------|----------------|----------|
| `isolation_forest_pass_only` | anomaly_detection | yes | Trained on pass-class only |
| `local_outlier_factor_pass_only` | anomaly_detection | yes | Trained on pass-class only with `novelty=True` |
| `elliptic_envelope_pass_only` | anomaly_detection | yes | Trained on pass-class only; disabled by default |
| `one_class_svm_pass_only` | anomaly_detection | no | Trained on pass-class only; disabled by default |
| `isolation_forest_all_train` | anomaly_detection | no | Trained on all training data; disabled by default |

Pass-only anomaly detectors learn the distribution of normal (pass) entities and flag deviations as potential failures. Because anomaly detectors do not output probabilities, the pipeline unifies them under a single `risk_score` abstraction: `predict_proba` for classifiers, `decision_function` / `score_samples` for anomaly detectors, with sign flips so that **higher score = higher failure risk** everywhere.

### New dynamic feature selectors

All selectors are computed fold-locally to prevent leakage:

- `correlation_pruned_070` / `correlation_pruned_085` — drops one feature from each high-correlation pair (|r| ≥ 0.70 or 0.85).
- `top_25_mutual_info` / `top_50_mutual_info` — top-N features by `mutual_info_classif` after median imputation.
- `top_25_auc_gap` / `top_50_auc_gap` — top-N features by absolute univariate ROC-AUC distance from 0.5.
- `missingness_indicators_keep` — the `keep_only` base list plus `_missing` indicator columns for any feature with NaNs in the training fold.

### Inspection metrics

Because process engineers often inspect only a small fraction of production entities, the pipeline reports top-k business metrics:

- **recall@10%** — what share of all failures are captured in the top 10% riskiest entities.
- **precision@10%** — fail rate inside that top 10%.
- **lift@10%** — precision@10% divided by the overall fail rate.
- **captured_fails@10%** — absolute number of true positives in the top 10%.

These metrics are computed per fold and aggregated in the benchmark. The pipeline also tracks a **best-for-inspection-policy** model separately from the PR-AUC winner, so business stakeholders can see the tradeoff between ranking quality (PR-AUC) and inspection yield (recall@10%).

### Unified OOF risk scores

Out-of-fold predictions are now stored as `oof_risk_{model}_{feature_set}` rather than `oof_prob_*`, reflecting that anomaly detectors produce scores, not calibrated probabilities.

### Phase 3 scope boundaries

- No new external dependencies beyond sklearn.
- No hyperparameter tuning for anomaly detectors.
- No calibrated-probability claims for anomaly scores.

## FMST Public Notebook Comparison

Many public notebooks (including the popular FMST notebook) report 70–88% recall on SECOM. Those results are **not directly comparable** to this project for three reasons:

1. **Random train/test split** leaks future information into training, inflating performance.
2. **Aggressive resampling / undersampling** artificially rebalances the dataset, which is not representative of real manufacturing yields.
3. **No chronological guardrails** mean the model may be memorizing temporal patterns rather than generalizing.

This project includes a separate `random_split_reference` benchmark (`scripts/run_public_notebook_comparison.py`) to show the magnitude of that gap. The primary benchmark remains the chronological walk-forward CV because that is the only protocol that matches how a real detector would be deployed on a production line.

## Anomaly Detection Findings

- Anomaly detectors are a semiconductor-appropriate idea: failures are rare, so learning the pass distribution and scoring deviations is intuitive.
- Under the strict chronological evaluation, anomaly detectors do not dramatically outperform the best supervised classifier (`random_forest` + `keep_only`).
- `isolation_forest_pass_only` is the most stable anomaly baseline; `local_outlier_factor_pass_only` and `elliptic_envelope_pass_only` are slower on 590 features and produce more variable fold scores.
- The unified risk-score framework successfully makes anomaly scores comparable to classifier probabilities for ranking and metric computation.

## Inspection Policy Findings

- Inspection-rate metrics (recall@5%, 10%, 20%) make the business tradeoff explicit: inspecting the top 10% riskiest entities typically captures only a small share of all failures because the baseline fail rate is ~6.6%.
- Mean recall@10% stays low across all model families under chronological validation, confirming that SECOM is genuinely hard, not just a threshold-selection problem.
- The `best_for_inspection_policy` flag in the benchmark lets stakeholders compare the PR-AUC winner against the model that maximizes recall@10%, even when they are different configurations.

## Recruiter Summary

This project demonstrates end-to-end rigor: a PostgreSQL warehouse, leakage-safe walk-forward cross-validation, multiple model families including anomaly detection, fold-local feature selection, and business-oriented inspection metrics. The numbers are modest because the UCI SECOM problem is genuinely hard under real-world constraints (severe imbalance, anonymized sensors, no feature engineering). The value is in the architecture and the honest evaluation, not in an inflated accuracy headline.

## Scope boundaries

Consistent with the project's focus on data engineering and reproducible analytics, the modeling phase explicitly does **not** include:

- Deep learning or neural networks
- Heavy hyperparameter search or AutoML
- SHAP or model-agnostic explainability (native feature importance and coefficients are used instead)
- Real-time inference or production deployment
- Synthetic factory context beyond the UCI SECOM data
