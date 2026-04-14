# SECOM Data Dictionary

## Staging Tables

| Table | Purpose |
|-------|---------|
| `staging.secom_entities` | Wide-format entity table with all 590 measurement features joined to pass/fail labels |
| `staging.feature_catalog` | One row per feature with null counts, distinct counts, and recommended data-quality actions |
| `staging.signal_values_long` | Long-format transformation of measurements for time-series or signal-level analytics |

## Mart Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `mart.secom_overview` | Single-row dataset summary | `entity_count`, `feature_count`, `pass_count`, `fail_count`, `pass_pct`, `fail_pct` |
| `mart.label_distribution` | Counts and percentages per class | `yield_label`, `pass_fail`, `entity_count`, `entity_pct` |
| `mart.feature_missingness` | Missingness profile ordered by severity | `feature_name`, `null_count`, `null_pct`, `distinct_count`, `is_constant`, `is_high_missing`, `recommended_action` |
| `mart.feature_action_summary` | Aggregated counts per recommended action | `recommended_action`, `feature_count`, `feature_pct` |
| `mart.top_signal_fail_separation` | Univariate effect-size ranking of signals | `feature_name`, `effect_size`, `pass_mean`, `fail_mean`, `pass_stddev`, `fail_stddev` |
| `mart.daily_yield_trend` | Daily pass/fail rates over time | `event_date`, `entity_count`, `pass_count`, `fail_count`, `pass_rate`, `fail_rate` |
| `mart.top_signal_profiles` | Per-class summary statistics for the top 20 separating signals | `feature_name`, `yield_class`, `count`, `mean`, `stddev`, `min`, `p25`, `median`, `p75`, `max` |
| `mart.feature_failure_relationship` | Failure relationship metrics for each valid feature | `feature_name`, `effect_size`, `pass_mean`, `fail_mean`, `mean_gap`, `valid_pass_count`, `valid_fail_count` |
| `mart.daily_failure_rollup` | Daily failure metrics with 7-day rolling average | `event_date`, `entity_count`, `fail_count`, `fail_rate`, `rolling_7d_fail_rate` |
| `mart.feature_priority_index` | Priority bucket assignment per feature for data-quality triage | `feature_name`, `priority_bucket`, `recommended_action`, `null_pct`, `is_constant`, `is_high_missing` |

## Exported JSON Keys (Website Contract)

The website consumes a single generated JSON bundle at `website/src/data/generated/mart_data.json`. The contract includes the following keys:

- `overview` — dataset summary metrics
- `label_distribution` — class distribution records
- `feature_missingness` — missingness profile records
- `feature_catalog` — full feature catalog records
- `action_summary` — recommended action aggregates
- `top_signals` — effect-size ranked signals
- `daily_trend` — daily yield trend records
- `top_signal_profiles` *(new)* — per-class statistics for top 20 signals
- `feature_correlation_to_failure` *(new)* — failure relationship metrics per feature
- `feature_coverage_summary` *(new)* — coverage-focused catalog view
- `daily_failure_summary` *(new)* — daily failure rollup records
- `feature_groups` *(new)* — features grouped by priority bucket

## Recommended Action Values

The `recommended_action` column in the feature catalog uses a controlled vocabulary:

| Value | Meaning |
|-------|---------|
| `keep` | Feature is clean enough for downstream use |
| `review_high_missing` | Feature has ≥ 50% missing values; review before inclusion |
| `drop_constant` | Feature has zero variance (constant value) and carries no information |
| `drop_all_null` | Feature is 100% null and should be removed |
