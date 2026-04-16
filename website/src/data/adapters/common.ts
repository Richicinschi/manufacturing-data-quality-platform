import landingSummary from "../generated/landing_summary.json"

const roundToTwo = (value: number) => Math.round(value * 100) / 100

export const DATASET_METRICS = {
  entityCount: landingSummary.overview.entity_count,
  featureCount: landingSummary.overview.feature_count,
  passCount: landingSummary.overview.pass_count,
  failCount: landingSummary.overview.fail_count,
  passPct: roundToTwo(landingSummary.overview.pass_pct * 100),
  failPct: roundToTwo(landingSummary.overview.fail_pct * 100),
  dateRange: {
    start: String(landingSummary.overview.min_timestamp).split(" ")[0],
    end: String(landingSummary.overview.max_timestamp).split(" ")[0],
  },
}

export const SIGNAL_ROWS = landingSummary.signal_rows

export const REPO_URL = "https://github.com/Richicinschi/manufacturing-data-quality-platform"
