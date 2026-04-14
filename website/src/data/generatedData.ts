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

export const REPO_URL = "https://github.com/Richicinschi/manufacturing-data-quality-platform"

export const PIPELINE_STAGES = [
  { name: "raw.secom_measurements", description: "Raw measurements from secom.data", schema: "raw", file: "src/etl/raw_ingest.py" },
  { name: "raw.secom_labels", description: "Pass/fail labels from secom_labels.data", schema: "raw", file: "src/etl/raw_ingest.py" },
  { name: "staging.secom_entities", description: "Joined entities with stable entity_id", schema: "staging", file: "src/etl/secom_join.py" },
  { name: "staging.feature_catalog", description: "Feature profiling with null counts and action flags", schema: "staging", file: "src/etl/feature_catalog.py" },
  { name: "staging.signal_values_long", description: "Long-format signal transformation", schema: "staging", file: "src/etl/build_signals.py" },
  { name: "mart.*", description: "Analytical marts for reporting", schema: "mart", file: "src/marts/" },
]

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
]

export const TECH_STACK = [
  { name: "Python", description: "ETL pipeline with Pandas and NumPy", icon: "python" },
  { name: "PostgreSQL", description: "Warehouse with raw, staging, and mart schemas", icon: "database" },
  { name: "SQLAlchemy", description: "Connection layer with SQLite fallback for tests", icon: "plug" },
  { name: "Feature Profiling", description: "Null analysis, distinct counts, and action flags", icon: "search" },
  { name: "Long-format Signals", description: "Entity-feature-value transformation", icon: "arrow-right-left" },
  { name: "Analytical Marts", description: "Reporting-friendly views for the website", icon: "bar-chart" },
  { name: "Pytest", description: "Validated warehouse and mart test suite", icon: "test-tube" },
  { name: "React + TypeScript", description: "Multi-page website built with Vite", icon: "code" },
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
