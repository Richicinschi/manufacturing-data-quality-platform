import { Link } from 'react-router-dom'
import type { ElementType } from 'react'
import {
  Database,
  Layers,
  Activity,
  CheckCircle,
  XCircle,
  Calendar,
  ArrowRight,
  BarChart3,
  Code2,
  Github,
} from 'lucide-react'
import {
  DATASET_METRICS,
  SIGNAL_ROWS,
  REPO_URL,
  KEY_FINDINGS,
  PIPELINE_STAGES,
  FEATURE_CORRELATION_TO_FAILURE,
} from '../data/generatedData'

function KPICard({
  icon: Icon,
  value,
  label,
  color = 'yellow',
}: {
  icon: ElementType
  value: string
  label: string
  color?: 'yellow' | 'green' | 'blue' | 'orange'
}) {
  const colorClasses = {
    yellow: 'text-yellow border-yellow/30 bg-yellow/10',
    green: 'text-green border-green/30 bg-green/10',
    blue: 'text-blue border-blue/30 bg-blue/10',
    orange: 'text-orange border-orange/30 bg-orange/10',
  }

  return (
    <div className={`p-5 rounded-lg border ${colorClasses[color]} hover:shadow-lg transition-shadow`}>
      <div className="flex items-center gap-3 mb-2">
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-3xl font-mono font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-white/60">{label}</div>
    </div>
  )
}

function PipelineStage({
  stage,
  index,
}: {
  stage: typeof PIPELINE_STAGES[0]
  index: number
}) {
  return (
    <div className="relative">
      <div className="bg-bg border border-comment/30 rounded-lg p-4 hover:border-yellow/50 transition-colors">
        <div className="text-xs font-mono text-comment mb-1">{stage.schema}</div>
        <div className="text-sm font-medium text-white mb-1">
          {stage.name.split('.').pop()}
        </div>
        <div className="text-xs text-white/50">{stage.description}</div>
      </div>
      {index < PIPELINE_STAGES.length - 1 && (
        <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
          <ArrowRight className="w-4 h-4 text-comment" />
        </div>
      )}
    </div>
  )
}

export default function LandingPage() {
  return (
    <div>
      <section className="py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
                SECOM Manufacturing <span className="text-yellow">Data Quality</span> Platform
              </h1>
              <p className="text-lg text-white/70 mb-4">
                A PostgreSQL + Python analytics pipeline built on the UCI SECOM dataset.
              </p>
              <ul className="space-y-2 text-white/60 mb-8">
                <li className="flex items-start gap-2">
                  <span className="text-yellow mt-1">-</span>
                  Loaded and profiled {DATASET_METRICS.entityCount.toLocaleString()} production entities with {DATASET_METRICS.featureCount} process features
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow mt-1">-</span>
                  Built staging, feature catalog, long-format signals, and analytical marts
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow mt-1">-</span>
                  Surfaced data quality, label imbalance, and pass/fail signal separation
                </li>
              </ul>

              <div className="p-4 bg-blue/10 rounded-lg border border-blue/30 mb-8">
                <p className="text-white/80 text-sm">
                  <span className="font-medium text-blue">What this project proves:</span> It demonstrates a complete, rerunnable data-warehouse workflow—from raw SECOM manufacturing data through PostgreSQL marts to a React website—showing how feature profiling, effect-size ranking, and daily yield tracking can be automated and published.
                </p>
              </div>

              <div className="flex flex-wrap gap-4">
                <Link
                  to="/data-quality"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-yellow text-bg font-medium rounded-lg hover:bg-yellow/90 transition-colors"
                >
                  <BarChart3 className="w-5 h-5" />
                  View Project Metrics
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  to="/signal-analysis"
                  className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
                >
                  Explore Signal Separation
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <KPICard
                icon={Database}
                value={DATASET_METRICS.entityCount.toLocaleString()}
                label="production entities"
                color="blue"
              />
              <KPICard
                icon={Layers}
                value={DATASET_METRICS.featureCount.toString()}
                label="measurement features"
                color="green"
              />
              <KPICard
                icon={Activity}
                value={SIGNAL_ROWS.toLocaleString()}
                label="signal rows"
                color="orange"
              />
              <div className="p-5 rounded-lg border border-pink/30 bg-pink/10">
                <div className="flex items-center gap-3 mb-2">
                  <CheckCircle className="w-5 h-5 text-green" />
                  <XCircle className="w-5 h-5 text-pink" />
                </div>
                <div className="text-3xl font-mono font-bold text-white mb-1">
                  {DATASET_METRICS.passCount.toLocaleString()} / {DATASET_METRICS.failCount.toLocaleString()}
                </div>
                <div className="text-sm text-white/60">pass / fail</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-comment/30 bg-comment/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center">
            <div>
              <div className="text-2xl font-mono font-bold text-white">{DATASET_METRICS.entityCount.toLocaleString()}</div>
              <div className="text-xs text-comment uppercase tracking-wider mt-1">Entities</div>
            </div>
            <div>
              <div className="text-2xl font-mono font-bold text-white">{DATASET_METRICS.featureCount}</div>
              <div className="text-xs text-comment uppercase tracking-wider mt-1">Features</div>
            </div>
            <div>
              <div className="text-2xl font-mono font-bold text-white">{SIGNAL_ROWS.toLocaleString()}</div>
              <div className="text-xs text-comment uppercase tracking-wider mt-1">Signal Rows</div>
            </div>
            <div>
              <div className="text-2xl font-mono font-bold text-white">{DATASET_METRICS.failPct}%</div>
              <div className="text-xs text-comment uppercase tracking-wider mt-1">Failure Rate</div>
            </div>
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center justify-center gap-1 text-sm font-mono text-white">
                <Calendar className="w-4 h-4 text-comment" />
                {DATASET_METRICS.dateRange.start} to {DATASET_METRICS.dateRange.end}
              </div>
              <div className="text-xs text-comment uppercase tracking-wider mt-1">Date Range</div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-8 bg-green/5 border-b border-comment/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-center md:text-left">
              <p className="text-white/70 text-sm">
                This website consumes real SECOM outputs exported from the PostgreSQL warehouse via <span className="font-mono text-yellow">scripts/generate_web_data.py</span>.
              </p>
            </div>
            <div className="flex gap-6 text-center">
              <div>
                <div className="text-xl font-mono font-bold text-white">{DATASET_METRICS.entityCount.toLocaleString()}</div>
                <div className="text-xs text-comment">wafers</div>
              </div>
              <div>
                <div className="text-xl font-mono font-bold text-white">{DATASET_METRICS.failPct}%</div>
                <div className="text-xs text-comment">failure rate</div>
              </div>
              <div>
                <div className="text-xl font-mono font-bold text-white">{FEATURE_CORRELATION_TO_FAILURE.length}</div>
                <div className="text-xs text-comment">ranked separators</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Pipeline Architecture</h2>
            <p className="text-white/60 max-w-2xl mx-auto">
              From raw ingest to analytical marts. The data flows through multiple stages
              with transformations at each step.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {PIPELINE_STAGES.map((stage, index) => (
              <PipelineStage key={stage.name} stage={stage} index={index} />
            ))}
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm">
            <div className="flex items-center gap-2 px-4 py-2 bg-green/10 rounded-full border border-green/30">
              <div className="w-2 h-2 rounded-full bg-green" />
              <span className="text-white/70">Join + timestamp</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-blue/10 rounded-full border border-blue/30">
              <div className="w-2 h-2 rounded-full bg-blue" />
              <span className="text-white/70">{DATASET_METRICS.featureCount} features</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-orange/10 rounded-full border border-orange/30">
              <div className="w-2 h-2 rounded-full bg-orange" />
              <span className="text-white/70">{SIGNAL_ROWS.toLocaleString()} rows</span>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24 border-t border-comment/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Key Findings</h2>
            <p className="text-white/60">Insights from the SECOM data quality analysis</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {KEY_FINDINGS.map((finding, index) => (
              <div
                key={index}
                className="p-6 bg-comment/5 rounded-lg border-l-4 border-yellow hover:bg-comment/10 transition-colors"
              >
                <p className="text-white/80">{finding}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 md:py-24 border-t border-comment/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">Explore the Data</h2>
          <p className="text-white/60 mb-8 max-w-2xl mx-auto">
            Dive deeper into the data quality metrics, signal separation analysis,
            and time trends.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/data-quality"
              className="inline-flex items-center gap-2 px-6 py-3 bg-yellow text-bg font-medium rounded-lg hover:bg-yellow/90 transition-colors"
            >
              <BarChart3 className="w-5 h-5" />
              Data Quality
            </Link>
            <Link
              to="/signal-analysis"
              className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
            >
              <Activity className="w-5 h-5" />
              Signal Analysis
            </Link>
            <Link
              to="/time-trends"
              className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
            >
              <Calendar className="w-5 h-5" />
              Time Trends
            </Link>
          </div>
        </div>
      </section>

      <section className="py-16 border-t border-comment/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-3 px-8 py-4 bg-comment/10 rounded-xl border border-comment/30">
            <Code2 className="w-6 h-6 text-yellow" />
            <span className="text-white">Want to see the code?</span>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-yellow hover:text-green transition-colors font-medium"
            >
              <Github className="w-5 h-5" />
              View on GitHub
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}
