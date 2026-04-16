import martData from "../generated/mart_data.json"

const roundToTwo = (value: number) => Math.round(value * 100) / 100

const _md = martData as any

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

export const MODEL_THRESHOLD_ANALYSIS = (martData.model_threshold_analysis ?? []).map((row: any) => ({
  threshold: roundToTwo(row.threshold),
  precision: roundToTwo(row.precision),
  recall: roundToTwo(row.recall),
  f1: roundToTwo(row.f1),
  selected: row.selected,
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

export const FINAL_MODEL_TEST_RESULTS = (_md.final_model_test_results ?? []).map((row: any) => ({
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

export const MODEL_CONFUSION_SUMMARY = (_md.model_confusion_summary ?? []).map((row: any) => ({
  split: row.split,
  model: row.model,
  threshold: roundToTwo(row.threshold),
  tn: row.tn,
  fp: row.fp,
  fn: row.fn,
  tp: row.tp,
}))

export const SELECTED_SIGNAL_SHORTLIST = (_md.selected_signal_shortlist ?? []).map((row: any) => ({
  feature: row.feature_name,
  effectRank: row.effect_rank,
  effectSize: roundToTwo(row.effect_size),
  nullPct: roundToTwo(row.null_pct * 100),
  action: row.recommended_action,
}))

export const MODEL_FEATURE_IMPORTANCE = (_md.model_feature_importance ?? []).map((row: any) => ({
  featureName: row.feature_name,
  importance: roundToTwo(row.importance),
  importanceType: row.importance_type,
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
