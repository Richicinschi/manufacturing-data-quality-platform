import martData from "../generated/mart_data.json"

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

export const FEATURE_GROUPS = (martData.feature_groups?.buckets ?? []).map((row: any) => ({
  groupName: row.bucket_name,
  count: row.feature_count,
  features: row.features ?? [],
}))

export const LABEL_DISTRIBUTION = martData.label_distribution.map((row: any) => ({
  name: row.pass_fail === "pass" ? "Pass" : "Fail",
  value: row.entity_count,
  percentage: roundToTwo(row.entity_pct * 100),
  color: row.pass_fail === "pass" ? "#b4d273" : "#b05279",
}))

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
