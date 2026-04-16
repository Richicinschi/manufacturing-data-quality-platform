import martData from "../generated/mart_data.json"

const roundToTwo = (value: number) => Math.round(value * 100) / 100

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
