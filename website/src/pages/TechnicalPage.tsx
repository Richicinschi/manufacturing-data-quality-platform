import {
  Code2,
  Database,
  Plug,
  Search,
  ArrowRightLeft,
  BarChart3,
  TestTube,
  RefreshCw,
  FileCode,
  Terminal,
  Github,
  ArrowRight,
  FileJson,
} from 'lucide-react'
import type { ElementType } from 'react'
import { REPO_URL, TECH_STACK, MART_TABLES } from '../data/generatedData'

const stackIcons: Record<string, ElementType> = {
  python: Code2,
  database: Database,
  plug: Plug,
  search: Search,
  'arrow-right-left': ArrowRightLeft,
  'bar-chart': BarChart3,
  'test-tube': TestTube,
}

const sqlExample = `-- Create analytical mart for feature missingness
CREATE TABLE mart.feature_missingness AS
SELECT
    feature_name,
    null_count,
    null_pct,
    distinct_count,
    is_constant,
    recommended_action
FROM staging.feature_catalog
ORDER BY null_pct DESC;`

const pythonExample = `# Build feature catalog with profiling
def build_feature_catalog(df):
    records = []
    for col in feature_cols:
        series = df[col]
        null_pct = series.isna().sum() / len(df)
        distinct = series.nunique(dropna=True)
        is_constant = distinct <= 1

        records.append({
            'feature': col,
            'null_pct': null_pct,
            'distinct': distinct,
            'is_constant': is_constant,
            'action': get_action(null_pct, is_constant)
        })
    return pd.DataFrame(records)`

const jsonExportExample = `# Export warehouse marts to JSON for the website
python scripts/generate_web_data.py

# Outputs:
# website/src/data/generated/mart_data.json
# Includes: overview, label_distribution, feature_missingness,
# feature_catalog, action_summary, top_signals, daily_trend,
# feature_correlation_to_failure, top_signal_profiles,
# daily_failure_summary, feature_groups,
# model_cv_results, model_benchmark, model_threshold_analysis,
# final_model_test_results, model_confusion_summary,
# selected_signal_shortlist`

export default function TechnicalPage() {
  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Technical Implementation</h1>
          <p className="text-white/60 max-w-2xl">
            Overview of the engineering stack, pipeline architecture, and implementation details
            of the SECOM data quality platform.
          </p>
        </div>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Technology Stack</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {TECH_STACK.map((tech) => {
              const Icon = stackIcons[tech.icon] || Code2
              return (
                <div
                  key={tech.name}
                  className="p-5 bg-comment/5 rounded-lg border border-comment/30 hover:border-yellow/50 transition-colors"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-yellow/20 rounded-lg">
                      <Icon className="w-5 h-5 text-yellow" />
                    </div>
                    <h3 className="text-white font-medium">{tech.name}</h3>
                  </div>
                  <p className="text-white/50 text-sm">{tech.description}</p>
                </div>
              )
            })}
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Pipeline Architecture</h2>
          <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
            <div className="grid md:grid-cols-3 gap-0">
              <div className="p-6 border-b md:border-b-0 md:border-r border-comment/30">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-pink" />
                  <h3 className="text-white font-medium">Raw Layer</h3>
                </div>
                <ul className="space-y-3">
                  <li className="text-sm">
                    <span className="font-mono text-yellow">raw.secom_measurements</span>
                    <p className="text-white/50 mt-1">Measurements from secom.data</p>
                  </li>
                  <li className="text-sm">
                    <span className="font-mono text-yellow">raw.secom_labels</span>
                    <p className="text-white/50 mt-1">Labels from secom_labels.data</p>
                  </li>
                  <li className="text-sm">
                    <span className="font-mono text-yellow">raw.ingestion_log</span>
                    <p className="text-white/50 mt-1">Ingestion tracking</p>
                  </li>
                </ul>
              </div>

              <div className="p-6 border-b md:border-b-0 md:border-r border-comment/30">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-blue" />
                  <h3 className="text-white font-medium">Staging Layer</h3>
                </div>
                <ul className="space-y-3">
                  <li className="text-sm">
                    <span className="font-mono text-yellow">staging.secom_entities</span>
                    <p className="text-white/50 mt-1">Joined entities with stable IDs</p>
                  </li>
                  <li className="text-sm">
                    <span className="font-mono text-yellow">staging.feature_catalog</span>
                    <p className="text-white/50 mt-1">Feature profiling statistics</p>
                  </li>
                  <li className="text-sm">
                    <span className="font-mono text-yellow">staging.signal_values_long</span>
                    <p className="text-white/50 mt-1">Long-format transformation</p>
                  </li>
                </ul>
              </div>

              <div className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-green" />
                  <h3 className="text-white font-medium">Mart Layer</h3>
                </div>
                <ul className="space-y-3">
                  {MART_TABLES.map((mart) => (
                    <li key={mart.name} className="text-sm">
                      <span className="font-mono text-yellow">{mart.name.split('.').pop()}</span>
                      <p className="text-white/50 mt-1">{mart.description}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Code Examples</h2>
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 bg-comment/10 border-b border-comment/30">
                <Terminal className="w-4 h-4 text-yellow" />
                <span className="text-white font-medium">SQL: Mart Creation</span>
              </div>
              <div className="p-4 overflow-x-auto">
                <pre className="text-sm font-mono text-white/70">
                  <code>{sqlExample}</code>
                </pre>
              </div>
            </div>

            <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 bg-comment/10 border-b border-comment/30">
                <FileCode className="w-4 h-4 text-green" />
                <span className="text-white font-medium">Python: Feature Profiling</span>
              </div>
              <div className="p-4 overflow-x-auto">
                <pre className="text-sm font-mono text-white/70">
                  <code>{pythonExample}</code>
                </pre>
              </div>
            </div>

            <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 bg-comment/10 border-b border-comment/30">
                <FileJson className="w-4 h-4 text-blue" />
                <span className="text-white font-medium">JSON Export</span>
              </div>
              <div className="p-4 overflow-x-auto">
                <pre className="text-sm font-mono text-white/70">
                  <code>{jsonExportExample}</code>
                </pre>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Analytical Marts</h2>
          <div className="space-y-4">
            {MART_TABLES.map((mart) => (
              <div
                key={mart.name}
                className="p-5 bg-comment/5 rounded-lg border border-comment/30 hover:border-yellow/30 transition-colors"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <h3 className="font-mono text-yellow mb-1">{mart.name}</h3>
                    <p className="text-white/60 text-sm">{mart.description}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-comment text-xs">{mart.file}</span>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {mart.columns.map((col) => (
                    <span
                      key={col}
                      className="px-2 py-1 bg-comment/20 rounded text-xs font-mono text-white/70"
                    >
                      {col}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Testing & Validation</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 bg-comment/5 rounded-lg border border-comment/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green/20 rounded-lg">
                  <TestTube className="w-5 h-5 text-green" />
                </div>
                <h3 className="text-white font-medium">Pytest Suite</h3>
              </div>
              <ul className="space-y-2 text-white/60 text-sm">
                <li>- test_secom_join.py - Entity join validation</li>
                <li>- test_feature_catalog.py - Catalog accuracy</li>
                <li>- test_build_signals.py - Signal transformation</li>
                <li>- test_marts.py - Mart table reconciliation</li>
              </ul>
            </div>
            <div className="p-6 bg-comment/5 rounded-lg border border-comment/30">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-yellow/20 rounded-lg">
                  <RefreshCw className="w-5 h-5 text-yellow" />
                </div>
                <h3 className="text-white font-medium">Rerunnable Local Workflow</h3>
              </div>
              <p className="text-white/60 text-sm">
                The entire pipeline is idempotent and can be re-run from scratch locally.
                Python ETL builds raw, staging, and mart tables in PostgreSQL (or SQLite),
                and <span className="font-mono text-yellow">scripts/generate_web_data.py</span> exports the mart layer to JSON for the
                React multi-page site.
              </p>
            </div>
          </div>
        </section>

        <section className="text-center">
          <div className="inline-flex flex-col sm:flex-row items-center gap-4 p-6 bg-comment/5 rounded-xl border border-comment/30">
            <Github className="w-8 h-8 text-yellow" />
            <div className="text-center sm:text-left">
              <h3 className="text-white font-medium">View the full source code</h3>
              <p className="text-white/50 text-sm">Explore the complete implementation on GitHub</p>
            </div>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-yellow text-bg font-medium rounded-lg hover:bg-yellow/90 transition-colors"
            >
              View on GitHub
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </section>
      </div>
    </div>
  )
}
