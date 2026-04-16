// Generated data from Python marts
// Run: python scripts/generate_web_data.py

import martData from "./generated/mart_data.json"

const roundToTwo = (value: number) => Math.round(value * 100) / 100

const actionDefinitions = [
  {
    action: "keep",
    label: "Keep",
    description: "Features with null_pct < 50% and distinct_count > 1",
    color: "green",
    chartColor: "#b4d273",
  },
  {
    action: "review_high_missing",
    label: "Review",
    description: "Features with null_pct >= 50%",
    color: "yellow",
    chartColor: "#e5b567",
  },
  {
    action: "drop_constant",
    label: "Drop (Constant)",
    description: "Features with distinct_count <= 1",
    color: "orange",
    chartColor: "#e87d3e",
  },
  {
    action: "drop_all_null",
    label: "Drop (All Null)",
    description: "Features where all values are null",
    color: "pink",
    chartColor: "#b05279",
  },
] as const

const actionSummaryMap = new Map(
  martData.action_summary.map((row: any) => [
    row.recommended_action,
    {
      count: row.feature_count,
      pct: roundToTwo(row.feature_pct * 100),
    },
  ]),
)

const reviewCount = actionSummaryMap.get("review_high_missing")?.count ?? 0
const constantCount = actionSummaryMap.get("drop_constant")?.count ?? 0

export const DATASET_METRICS = {
  entityCount: martData.overview.entity_count,
  featureCount: martData.overview.feature_count,
  passCount: martData.overview.pass_count,
  failCount: martData.overview.fail_count,
  passPct: roundToTwo(martData.overview.pass_pct * 100),
  failPct: roundToTwo(martData.overview.fail_pct * 100),
  dateRange: {
    start: String(martData.overview.min_timestamp).split(" ")[0],
    end: String(martData.overview.max_timestamp).split(" ")[0],
  },
}

export const SIGNAL_ROWS = DATASET_METRICS.entityCount * DATASET_METRICS.featureCount

export const LABEL_DISTRIBUTION = martData.label_distribution.map((row: any) => ({
  name: row.pass_fail === "pass" ? "Pass" : "Fail",
  value: row.entity_count,
  percentage: roundToTwo(row.entity_pct * 100),
  color: row.pass_fail === "pass" ? "#b4d273" : "#b05279",
}))

export const FEATURE_MISSINGNESS = martData.feature_missingness.map((row: any) => ({
  feature: row.feature_name,
  nullPct: roundToTwo(row.null_pct * 100),
  nullCount: row.null_count,
  distinctCount: row.distinct_count,
  isConstant: row.is_constant,
  action: row.recommended_action,
}))

export const FEATURE_CATALOG = (martData.feature_catalog ?? []).map((row: any) => ({
  feature: row.feature_name,
  nullCount: row.null_count,
  nullPct: roundToTwo(row.null_pct * 100),
  distinctCount: row.distinct_count,
  mean: row.mean,
  stddev: row.stddev,
  minValue: row.min_value,
  maxValue: row.max_value,
  isConstant: row.is_constant,
  isHighMissing: row.is_high_missing,
  action: row.recommended_action,
}))

export const ACTION_SUMMARY = actionDefinitions.map((definition) => {
  const current = actionSummaryMap.get(definition.action)
  return {
    action: definition.action,
    label: definition.label,
    count: current?.count ?? 0,
    pct: current?.pct ?? 0,
    color: definition.chartColor,
  }
})

export const TOP_SIGNALS = martData.top_signals.map((row: any) => ({
  feature: row.feature_name,
  effectSize: roundToTwo(row.effect_size),
  passMean: roundToTwo(row.pass_mean),
  failMean: roundToTwo(row.fail_mean),
  passStd: roundToTwo(row.pass_stddev),
  failStd: roundToTwo(row.fail_stddev),
  passCount: row.pass_count,
  failCount: row.fail_count,
}))

export const DAILY_TREND = martData.daily_trend.map((row: any) => ({
  date: row.event_date,
  entityCount: row.entity_count,
  passCount: row.pass_count,
  failCount: row.fail_count,
  passRate: roundToTwo(row.pass_rate * 100),
  failRate: roundToTwo(row.fail_rate * 100),
}))

// New expanded mart exports
export const TOP_SIGNAL_PROFILES = (martData.top_signal_profiles ?? []).map((row: any) => ({
  feature: row.feature_name,
  yieldClass: row.yield_class,
  count: row.count,
  missingCount: row.missing_count,
  mean: roundToTwo(row.mean),
  stddev: roundToTwo(row.stddev),
  min: roundToTwo(row.min),
  p25: roundToTwo(row.p25),
  median: roundToTwo(row.median),
  p75: roundToTwo(row.p75),
  max: roundToTwo(row.max),
}))

export const FEATURE_CORRELATION_TO_FAILURE = (martData.feature_correlation_to_failure ?? []).map((row: any) => ({
  feature: row.feature_name,
  effectSize: roundToTwo(row.effect_size),
  passMean: roundToTwo(row.pass_mean),
  failMean: roundToTwo(row.fail_mean),
  meanGap: roundToTwo(row.mean_gap),
  validPassCount: row.valid_pass_count,
  validFailCount: row.valid_fail_count,
}))

export const DAILY_FAILURE_SUMMARY = (martData.daily_failure_summary ?? []).map((row: any) => ({
  date: row.event_date,
  entityCount: row.entity_count,
  failCount: row.fail_count,
  failRate: roundToTwo(row.fail_rate * 100),
  rolling7dFailRate: roundToTwo(row.rolling_7d_fail_rate * 100),
}))

export const FEATURE_GROUPS = (martData.feature_groups?.buckets ?? []).map((row: any) => ({
  groupName: row.bucket_name,
  count: row.feature_count,
  features: row.features ?? [],
}))

export const REPO_URL = "https://github.com/Richicinschi/manufacturing-data-quality-platform"

export const PIPELINE_STAGES = [
  { name: "raw.secom_measurements", description: "Raw measurements from secom.data", schema: "raw", file: "src/etl/raw_ingest.py" },
  { name: "raw.secom_labels", description: "Pass/fail labels from secom_labels.data", schema: "raw", file: "src/etl/raw_ingest.py" },
  { name: "staging.secom_entities", description: "Joined entities with stable entity_id", schema: "staging", file: "src/etl/secom_join.py" },
  { name: "staging.feature_catalog", description: "Feature profiling with null counts and action flags", schema: "staging", file: "src/etl/feature_catalog.py" },
  { name: "staging.signal_values_long", description: "Long-format signal transformation", schema: "staging", file: "src/etl/build_signals.py" },
  { name: "mart.*", description: "Analytical marts for reporting", schema: "mart", file: "src/marts/" },
]

export const MODEL_CV_RESULTS = (martData.model_cv_results ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  fold: row.fold,
  nSplits: row.n_splits,
  nFeaturesRequested: row.n_features_requested,
  nFeaturesUsed: row.n_features_used,
  prAuc: roundToTwo(row.pr_auc),
  rocAuc: roundToTwo(row.roc_auc),
  precision: roundToTwo(row.precision),
  recall: roundToTwo(row.recall),
  f1: roundToTwo(row.f1),
}))

export const MODEL_BENCHMARK = (martData.model_benchmark ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  meanPrAuc: roundToTwo(row.mean_pr_auc),
  stdPrAuc: roundToTwo(row.std_pr_auc),
  meanRocAuc: roundToTwo(row.mean_roc_auc),
  meanF1: roundToTwo(row.mean_f1),
  meanPrecision: roundToTwo(row.mean_precision ?? 0),
  meanRecall: roundToTwo(row.mean_recall ?? 0),
  meanRecallAt10Pct: roundToTwo(row.mean_recall_at_10pct ?? 0),
  meanPrecisionAt10Pct: roundToTwo(row.mean_precision_at_10pct ?? 0),
  meanLiftAt10Pct: roundToTwo(row.mean_lift_at_10pct ?? 0),
  rank: row.rank,
  modelFamily: row.model_family,
  modelKind: row.model_kind ?? "classifier",
  finalEligible: row.final_eligible,
  enabled: row.enabled,
  bestForInspectionPolicy: row.best_for_inspection_policy ?? false,
}))

const _md = martData as any

export const MODEL_REGISTRY = (_md.model_registry ?? []).map((row: any) => ({
  modelId: row.model_id,
  modelFamily: row.model_family,
  modelKind: row.model_kind ?? "classifier",
  fitMode: row.fit_mode ?? "all_train",
  scoreMethod: row.score_method ?? "predict_proba",
  finalEligible: row.final_eligible,
  enabled: row.enabled,
  skipReason: row.skip_reason,
}))

export const MODEL_FEATURE_IMPORTANCE = (_md.model_feature_importance ?? []).map((row: any) => ({
  featureName: row.feature_name,
  importance: roundToTwo(row.importance),
  importanceType: row.importance_type,
}))

export const MODEL_THRESHOLD_COST_CURVE = (_md.model_threshold_cost_curve ?? []).map((row: any) => ({
  threshold: roundToTwo(row.threshold),
  precision: roundToTwo(row.precision),
  recall: roundToTwo(row.recall),
  f1: roundToTwo(row.f1),
  predictedFailCount: row.predicted_fail_count,
  falsePositiveCount: row.false_positive_count,
  falseNegativeCount: row.false_negative_count,
  inspectionRate: roundToTwo(row.inspection_rate * 100),
  selected: row.selected,
}))

export const MODEL_PROBABILITY_BINS = (_md.model_probability_bins ?? []).map((row: any) => ({
  binMin: row.bin_min,
  binMax: row.bin_max,
  totalEntities: row.total_entities,
  failCount: row.fail_count,
  failRate: roundToTwo(row.fail_rate * 100),
}))

export const MODEL_THRESHOLD_ANALYSIS = (martData.model_threshold_analysis ?? []).map((row: any) => ({
  threshold: roundToTwo(row.threshold),
  precision: roundToTwo(row.precision),
  recall: roundToTwo(row.recall),
  f1: roundToTwo(row.f1),
  selected: row.selected,
}))

export const FINAL_MODEL_TEST_RESULTS = (martData.final_model_test_results ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  nFeatures: row.n_features,
  threshold: roundToTwo(row.threshold),
  prAuc: roundToTwo(row.test_pr_auc),
  rocAuc: roundToTwo(row.test_roc_auc),
  precision: roundToTwo(row.test_precision),
  recall: roundToTwo(row.test_recall),
  f1: roundToTwo(row.test_f1),
}))[0]

export const MODEL_CONFUSION_SUMMARY = (martData.model_confusion_summary ?? []).map((row: any) => ({
  split: row.split,
  model: row.model,
  threshold: roundToTwo(row.threshold),
  tn: row.tn,
  fp: row.fp,
  fn: row.fn,
  tp: row.tp,
}))

export const SELECTED_SIGNAL_SHORTLIST = (martData.selected_signal_shortlist ?? []).map((row: any) => ({
  feature: row.feature_name,
  effectRank: row.effect_rank,
  effectSize: roundToTwo(row.effect_size),
  nullPct: roundToTwo(row.null_pct * 100),
  action: row.recommended_action,
}))

export const INSPECTION_METRICS = (_md.inspection_metrics ?? {}) as {
  recall_at_10pct?: number
  precision_at_10pct?: number
  lift_at_10pct?: number
  captured_fails_at_10pct?: number
}

export const MODEL_INSPECTION_METRICS = (_md.model_inspection_metrics ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  modelFamily: row.model_family,
  modelKind: row.model_kind ?? "classifier",
  finalEligible: row.final_eligible,
  enabled: row.enabled,
  meanRecallAt05Pct: roundToTwo(row.mean_recall_at_05pct ?? 0),
  meanPrecisionAt05Pct: roundToTwo(row.mean_precision_at_05pct ?? 0),
  meanLiftAt05Pct: roundToTwo(row.mean_lift_at_05pct ?? 0),
  meanRecallAt10Pct: roundToTwo(row.mean_recall_at_10pct ?? 0),
  meanPrecisionAt10Pct: roundToTwo(row.mean_precision_at_10pct ?? 0),
  meanLiftAt10Pct: roundToTwo(row.mean_lift_at_10pct ?? 0),
  meanRecallAt20Pct: roundToTwo(row.mean_recall_at_20pct ?? 0),
  meanPrecisionAt20Pct: roundToTwo(row.mean_precision_at_20pct ?? 0),
  meanLiftAt20Pct: roundToTwo(row.mean_lift_at_20pct ?? 0),
}))

export const MODEL_FEATURE_SELECTION_SUMMARY = (_md.model_feature_selection_summary ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  meanNSelected: roundToTwo(row.mean_n_selected ?? 0),
  minNSelected: row.min_n_selected ?? 0,
  maxNSelected: row.max_n_selected ?? 0,
  exampleFeatures: row.example_features ?? [],
}))

export const ANOMALY_MODEL_BENCHMARK = (_md.anomaly_model_benchmark ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  meanPrAuc: roundToTwo(row.mean_pr_auc ?? 0),
  meanRecallAt10Pct: roundToTwo(row.mean_recall_at_10pct ?? 0),
  meanPrecisionAt10Pct: roundToTwo(row.mean_precision_at_10pct ?? 0),
  meanLiftAt10Pct: roundToTwo(row.mean_lift_at_10pct ?? 0),
  rank: row.rank,
  modelFamily: row.model_family,
  finalEligible: row.final_eligible,
  enabled: row.enabled,
}))

export const FINAL_MODEL_INSPECTION_CURVE = (_md.final_model_inspection_curve ?? []).map((row: any) => ({
  inspectionRate: roundToTwo(row.inspection_rate ?? 0),
  recall: roundToTwo(row.recall ?? 0),
  precision: roundToTwo(row.precision ?? 0),
  lift: roundToTwo(row.lift ?? 0),
  capturedFails: row.captured_fails ?? 0,
  model: row.model,
  featureSet: row.feature_set,
}))

export const PUBLIC_NOTEBOOK_COMPARISON = (_md.public_notebook_comparison ?? []).map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  evaluationProtocol: row.evaluation_protocol,
  testPrAuc: roundToTwo(row.test_pr_auc ?? 0),
  testRocAuc: roundToTwo(row.test_roc_auc ?? 0),
  testPrecision: roundToTwo(row.test_precision ?? 0),
  testRecall: roundToTwo(row.test_recall ?? 0),
  testF1: roundToTwo(row.test_f1 ?? 0),
}))

export const MART_TABLES = [
  {
    name: "mart.secom_overview",
    description: "Single-row summary with entity and feature counts",
    file: "src/marts/overview.py",
    columns: ["entity_count", "feature_count", "pass_count", "fail_count", "pass_pct", "fail_pct", "min_timestamp", "max_timestamp"],
  },
  {
    name: "mart.label_distribution",
    description: "Label distribution with counts and percentages",
    file: "src/marts/label_distribution.py",
    columns: ["yield_label", "pass_fail", "entity_count", "entity_pct"],
  },
  {
    name: "mart.feature_missingness",
    description: "Features ranked by null percentage",
    file: "src/marts/feature_missingness.py",
    columns: ["feature_name", "null_count", "null_pct", "distinct_count", "is_constant", "is_high_missing", "recommended_action"],
  },
  {
    name: "mart.feature_action_summary",
    description: "Summary of recommended feature actions",
    file: "src/marts/feature_action_summary.py",
    columns: ["recommended_action", "feature_count", "feature_pct"],
  },
  {
    name: "mart.top_signal_fail_separation",
    description: "Top features ranked by effect size",
    file: "src/marts/top_signal_fail_separation.py",
    columns: ["feature_name", "pass_count", "fail_count", "pass_mean", "fail_mean", "pass_stddev", "fail_stddev", "effect_size"],
  },
  {
    name: "mart.daily_yield_trend",
    description: "Daily yield metrics over time",
    file: "src/marts/daily_yield_trend.py",
    columns: ["event_date", "entity_count", "pass_count", "fail_count", "pass_rate", "fail_rate"],
  },
  {
    name: "mart.feature_failure_relationship",
    description: "All valid features ranked by effect size with pass/fail means",
    file: "src/marts/feature_failure_relationship.py",
    columns: ["feature_name", "effect_size", "pass_mean", "fail_mean", "mean_gap", "valid_pass_count", "valid_fail_count"],
  },
  {
    name: "mart.top_signal_profiles",
    description: "Per-class summary statistics for top 20 signals",
    file: "src/marts/top_signal_profiles.py",
    columns: ["feature_name", "yield_class", "count", "missing_count", "mean", "stddev", "min", "p25", "median", "p75", "max"],
  },
  {
    name: "mart.daily_failure_rollup",
    description: "Daily failure metrics with 7-day rolling fail rate",
    file: "src/marts/daily_failure_rollup.py",
    columns: ["event_date", "entity_count", "fail_count", "fail_rate", "rolling_7d_fail_rate"],
  },
  {
    name: "mart.feature_groups",
    description: "Feature buckets for priority review",
    file: "src/marts/feature_groups.py",
    columns: ["group_name", "count", "description", "example_features"],
  },
  {
    name: "mart.model_cv_results",
    description: "Per-fold walk-forward CV results",
    file: "src/marts/model_cv_results.py",
    columns: ["model", "feature_set", "fold", "n_splits", "n_features", "pr_auc", "roc_auc", "precision", "recall", "f1"],
  },
  {
    name: "mart.model_benchmark",
    description: "Aggregated CV benchmark by model and feature set",
    file: "src/marts/model_benchmark.py",
    columns: ["model", "feature_set", "mean_pr_auc", "std_pr_auc", "mean_roc_auc", "mean_f1", "rank"],
  },
  {
    name: "mart.model_threshold_analysis",
    description: "Threshold sweep with F1, precision, recall",
    file: "src/marts/model_threshold_analysis.py",
    columns: ["threshold", "precision", "recall", "f1", "selected"],
  },
  {
    name: "mart.final_model_test_results",
    description: "Final holdout evaluation for the best model",
    file: "src/marts/final_model_test_results.py",
    columns: ["model", "feature_set", "n_features", "threshold", "test_pr_auc", "test_roc_auc", "test_precision", "test_recall", "test_f1"],
  },
  {
    name: "mart.model_confusion_summary",
    description: "Confusion matrix for dev-OOF and test sets",
    file: "src/marts/model_confusion_summary.py",
    columns: ["split", "model", "threshold", "tn", "fp", "fn", "tp"],
  },
  {
    name: "mart.selected_signal_shortlist",
    description: "Signals in the winning feature set with metadata",
    file: "src/marts/selected_signal_shortlist.py",
    columns: ["feature_name", "effect_rank", "effect_size", "null_pct", "recommended_action"],
  },
  {
    name: "mart.model_registry",
    description: "Registered models with eligibility and availability",
    file: "src/marts/model_registry.py",
    columns: ["model_id", "model_family", "final_eligible", "enabled", "skip_reason"],
  },
  {
    name: "mart.model_feature_importance",
    description: "Final-model feature importance",
    file: "src/marts/model_feature_importance.py",
    columns: ["feature_name", "importance", "importance_type"],
  },
  {
    name: "mart.model_threshold_cost_curve",
    description: "Threshold sweep with business-oriented cost metrics",
    file: "src/marts/model_threshold_cost_curve.py",
    columns: ["threshold", "precision", "recall", "f1", "predicted_fail_count", "false_positive_count", "false_negative_count", "inspection_rate", "selected"],
  },
  {
    name: "mart.model_probability_bins",
    description: "Final test probability bins with failure rates",
    file: "src/marts/model_probability_bins.py",
    columns: ["bin_min", "bin_max", "total_entities", "fail_count", "fail_rate"],
  },
  {
    name: "mart.model_inspection_metrics",
    description: "Mean CV inspection-rate metrics by model and feature set",
    file: "src/marts/model_inspection_metrics.py",
    columns: ["model", "feature_set", "mean_recall_at_05pct", "mean_precision_at_05pct", "mean_lift_at_05pct", "mean_recall_at_10pct", "mean_precision_at_10pct", "mean_lift_at_10pct", "mean_recall_at_20pct", "mean_precision_at_20pct", "mean_lift_at_20pct"],
  },
  {
    name: "mart.model_feature_selection_summary",
    description: "Per-fold feature selection counts and example features",
    file: "src/marts/model_feature_selection_summary.py",
    columns: ["model", "feature_set", "mean_n_selected", "min_n_selected", "max_n_selected", "example_features"],
  },
  {
    name: "mart.anomaly_model_benchmark",
    description: "Anomaly detector benchmark subset",
    file: "src/marts/anomaly_model_benchmark.py",
    columns: ["model", "feature_set", "mean_pr_auc", "mean_recall_at_10pct", "rank"],
  },
  {
    name: "mart.final_model_inspection_curve",
    description: "Final model top-k inspection curve",
    file: "src/marts/final_model_inspection_curve.py",
    columns: ["inspection_rate", "recall", "precision", "lift", "captured_fails", "model", "feature_set"],
  },
  {
    name: "mart.public_notebook_comparison",
    description: "Random-split reference results (informational only)",
    file: "src/marts/public_notebook_comparison.py",
    columns: ["model", "feature_set", "evaluation_protocol", "test_pr_auc", "test_recall"],
  },
]

export const TECH_STACK = [
  { name: "Python", description: "ETL pipeline with Pandas, NumPy and SQLAlchemy", icon: "python" },
  { name: "PostgreSQL", description: "Warehouse with raw, staging, and mart schemas", icon: "database" },
  { name: "SQLAlchemy", description: "Connection layer with SQLite fallback for tests", icon: "plug" },
  { name: "Feature Profiling", description: "Null analysis, distinct counts, and action flags", icon: "search" },
  { name: "Long-format Signals", description: "Entity-feature-value transformation", icon: "arrow-right-left" },
  { name: "Analytical Marts", description: "Reporting-friendly views for the website", icon: "bar-chart" },
  { name: "Pytest", description: "Validated warehouse and mart test suite", icon: "test-tube" },
  { name: "React + Vite", description: "Multi-page website with TypeScript, Tailwind and Recharts", icon: "code" },
]

export const FEATURE_ACTIONS = Object.fromEntries(
  actionDefinitions.map((definition) => [
    definition.action,
    {
      label: definition.label,
      description: definition.description,
      color: definition.color,
    },
  ]),
)

export const KEY_FINDINGS = [
  `The dataset contains ${DATASET_METRICS.entityCount.toLocaleString()} production entities with ${DATASET_METRICS.featureCount} measurement features.`,
  `Strong class imbalance: only ${DATASET_METRICS.failCount} failures (${DATASET_METRICS.failPct}%) out of ${DATASET_METRICS.entityCount.toLocaleString()} entities.`,
  `${reviewCount} features are flagged for high missingness review and ${constantCount} are constant-valued.`,
  "The strongest separating signals can be ranked reliably using univariate effect size (Cohen's d).",
  "The pipeline demonstrates warehouse design, profiling, transformation, and analytical reporting.",
]
