import landingSummary from "../generated/landing_summary.json"
import { DATASET_METRICS } from "./common"

const roundToTwo = (value: number) => Math.round(value * 100) / 100

export const FEATURE_COUNTS = {
  keep: landingSummary.feature_actions.keep,
  review: landingSummary.feature_actions.review_high_missing,
  constant: landingSummary.feature_actions.drop_constant,
  allNull: landingSummary.feature_actions.drop_all_null,
}

export const RANKED_SEPARATOR_COUNT = landingSummary.ranked_separator_count

export const INSPECTION_POLICY = landingSummary.inspection_policy

export const FINAL_MODEL = {
  model: landingSummary.final_model.model,
  featureSet: landingSummary.final_model.feature_set,
  prAuc: roundToTwo(landingSummary.final_model.test_pr_auc),
  rocAuc: roundToTwo(landingSummary.final_model.test_roc_auc),
  precision: roundToTwo(landingSummary.final_model.test_precision),
  recall: roundToTwo(landingSummary.final_model.test_recall),
  f1: roundToTwo(landingSummary.final_model.test_f1),
}

export const BENCHMARK_SCALE = {
  configs: landingSummary.benchmark_scale.model_configs,
  cvRows: landingSummary.benchmark_scale.cv_rows,
}

export const TOP_MODELS = landingSummary.top_models_by_pr_auc.map((row: any) => ({
  model: row.model,
  featureSet: row.feature_set,
  meanPrAuc: row.mean_pr_auc,
}))

export const ARCHITECTURE_STAGES = [
  { id: "raw_files", label: "Raw SECOM files", sub: "secom.data + labels", layer: "raw" as const },
  { id: "raw_db", label: "Raw database layer", sub: "PostgreSQL raw schema", layer: "raw" as const },
  { id: "staging_entities", label: "Staging entities", sub: "Joined + timestamped", layer: "staging" as const },
  { id: "feature_catalog", label: "Feature catalog", sub: "Profiling + actions", layer: "staging" as const },
  { id: "signals", label: "Long-format signals", sub: "Entity-feature-value", layer: "staging" as const },
  { id: "marts", label: "Analytical marts", sub: "Reporting views", layer: "marts" as const },
  { id: "modeling", label: "Modeling benchmark", sub: "Walk-forward CV", layer: "modeling" as const },
  { id: "export", label: "JSON export", sub: "scripts/generate_web_data.py", layer: "frontend" as const },
  { id: "dashboard", label: "React dashboard", sub: "Vite + Tailwind", layer: "frontend" as const },
]

export const KEY_FINDINGS = [
  {
    headline: "Severe class imbalance",
    summary: `Only ${DATASET_METRICS.failCount.toLocaleString()} of ${DATASET_METRICS.entityCount.toLocaleString()} entities failed, so accuracy is misleading.`,
    detail: `Failure rate is ${DATASET_METRICS.failPct}%. The project uses PR-AUC, recall, F1, and inspection-rate metrics instead of accuracy because a naive model can look strong by predicting pass.`,
  },
  {
    headline: "Feature quality breakdown",
    summary: `${FEATURE_COUNTS.keep} features kept, ${FEATURE_COUNTS.constant} constant-drop, ${FEATURE_COUNTS.review} high-missing review.`,
    detail: `The feature catalog profiles all ${DATASET_METRICS.featureCount} sensors with null counts, distinct counts, min/max values, and recommended actions. This turns an anonymous sensor matrix into an auditable data-quality workflow.`,
  },
  {
    headline: "Best model",
    summary: `Best default model: ${FINAL_MODEL.model} + ${FINAL_MODEL.featureSet}.`,
    detail: `Final chronological holdout: PR-AUC ${FINAL_MODEL.prAuc}, ROC-AUC ${FINAL_MODEL.rocAuc}, precision ${FINAL_MODEL.precision}, recall ${FINAL_MODEL.recall}, F1 ${FINAL_MODEL.f1}. These are honest rare-failure metrics, not inflated random-split scores.`,
  },
  {
    headline: "Top model comparison",
    summary: `${BENCHMARK_SCALE.configs} model-feature configurations were benchmarked with walk-forward CV.`,
    detail: TOP_MODELS,
  },
  {
    headline: "Inspection policy",
    summary: `Top 20% risk-ranked entities catch ${INSPECTION_POLICY.top_20.captured_fails} holdout failures.`,
    detail: `Top 5% catches ${INSPECTION_POLICY.top_05.captured_fails} failures, top 10% catches ${INSPECTION_POLICY.top_10.captured_fails} failures, and top 20% catches ${INSPECTION_POLICY.top_20.captured_fails} failures. This frames the model as an inspection-prioritization tool, not a production defect detector.`,
  },
  {
    headline: "Dashboard data system",
    summary: "PostgreSQL marts power a React dashboard through generated JSON.",
    detail: `The website is built from generated warehouse exports, not hand-entered screenshots. The local command python scripts/generate_web_data.py refreshes the data contract used by the React app.`,
  },
]
