# SECOM Modeling Findings

## What this phase adds

The modeling phase transforms the project from a data-quality analytics platform into a **yield-failure detection and signal-selection case study**. It trains imbalance-aware classifiers on the UCI SECOM dataset, evaluates them with walk-forward cross-validation, and produces a shortlist of signals that survive selection without data leakage.

## Dataset reminder

- **1,567 entities** with **590 features**
- **104 fails** (6.6%) vs **1,463 passes** (93.4%)
- Strong class imbalance means accuracy is misleading; PR-AUC and fail-class F1 are the primary metrics.

## Why walk-forward CV?

SECOM has a natural time ordering (`test_timestamp`). A random train/test split would leak future information into the training set and overstate performance. We use **expanding-window walk-forward CV** on the development set (oldest 85%):

- Fold 1 trains on the earliest data, tests on the next slice.
- Each subsequent fold expands the training window forward in time.
- If any fold has fewer than 8 fail-class samples, the engine gracefully degrades to fewer splits.

## Models evaluated

All models are evaluated across five feature sets:

1. `keep_only` — features cataloged as `keep`
2. `keep_plus_review` — `keep` + `review_high_missing`
3. `top_20_effect` — top 20 by Cohen's d computed **inside each training fold**
4. `top_50_effect` — top 50 by Cohen's d computed inside each training fold
5. `top_100_effect` — top 100 by Cohen's d computed inside each training fold

The fold-time computation of top-N effect sizes prevents leakage: the ranking is derived only from data seen during training.

### Classifiers

- **DummyClassifier** (`stratified`) — baseline
- **LogisticRegression** (`class_weight="balanced"`, L1 penalty, `liblinear` solver, `C=1.0`)
- **RandomForestClassifier** (`class_weight="balanced"`, 300 trees, `max_depth=8`, `min_samples_leaf=2`)

No hyper-parameter tuning grid is used; parameters are hard-coded to keep the scope focused.

## Threshold selection

The probability threshold is chosen to **maximize fail-class F1** on the development out-of-fold (OOF) predictions from the best-performing model. This threshold is then locked and applied to the final holdout evaluation.

## Final evaluation protocol

- **Development**: oldest 85% of chronologically sorted data
- **Final holdout**: newest 15%
- Best model/feature set is selected by mean CV PR-AUC on the development set.
- The best model is retrained on the full development set and evaluated on the holdout.

## What the modeling marts capture

Six new analytical marts support the `/modeling` website route:

| Mart | Purpose |
|------|---------|
| `mart.model_cv_results` | Per-fold metrics (PR-AUC, ROC-AUC, precision, recall, F1) |
| `mart.model_benchmark` | Mean/std PR-AUC per model × feature set with rank |
| `mart.model_threshold_analysis` | Threshold sweep (precision, recall, F1) with selected flag |
| `mart.final_model_test_results` | Single-row final holdout metrics |
| `mart.model_confusion_summary` | Confusion matrices for dev-OOF and test sets |
| `mart.selected_signal_shortlist` | Winning feature set with effect rank, null %, and catalog action |

## Key takeaways for process engineering

- **Effect size is a reliable pre-modeling filter**: Cohen's d ranks signals consistently even before training, making it useful for diagnostic dashboards and root-cause discussions.
- **Dynamic feature selection prevents leakage**: Computing top-N effect sizes inside each CV fold ensures the shortlist is honest and generalizable.
- **Imbalance-aware evaluation matters**: PR-AUC focuses on the rare fail class and is more informative than ROC-AUC in this heavily imbalanced setting.
- **The final shortlist is actionable**: Every selected signal is annotated with its catalog `recommended_action`, so process engineers can immediately see whether a signal is clean (`keep`) or requires review (`review_high_missing`).

## Scope boundaries

Consistent with the project's focus on data engineering and reproducible analytics, the modeling phase explicitly does **not** include:

- Deep learning or neural networks
- XGBoost or gradient-boosted ensembles
- SHAP or model-agnostic explainability
- Real-time inference or production deployment
- Synthetic factory context beyond the UCI SECOM data
