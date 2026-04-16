import martData from "../generated/mart_data.json"

const roundToTwo = (value: number) => Math.round(value * 100) / 100

export const DAILY_FAILURE_SUMMARY = (martData.daily_failure_summary ?? []).map((row: any) => ({
  date: row.event_date,
  entityCount: row.entity_count,
  failCount: row.fail_count,
  failRate: roundToTwo(row.fail_rate * 100),
  rolling7dFailRate: roundToTwo(row.rolling_7d_fail_rate * 100),
}))
