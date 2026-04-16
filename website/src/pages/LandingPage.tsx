import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { ElementType } from 'react'
import {
  Database,
  Layers,
  Activity,
  XCircle,
  ArrowRight,
  BarChart3,
  Github,
  Brain,
  Calendar,
} from 'lucide-react'
import { DATASET_METRICS, SIGNAL_ROWS, REPO_URL } from '../data/adapters/common'
import {
  RANKED_SEPARATOR_COUNT,
  BENCHMARK_SCALE,
  ARCHITECTURE_STAGES,
  KEY_FINDINGS,
} from '../data/adapters/landing'

function KPICard({
  icon: Icon,
  value,
  label,
  color = 'yellow',
}: {
  icon: ElementType
  value: string
  label: string
  color?: 'yellow' | 'green' | 'blue' | 'orange' | 'pink' | 'purple'
}) {
  const colorClasses = {
    yellow: 'text-yellow border-yellow/30 bg-yellow/10',
    green: 'text-green border-green/30 bg-green/10',
    blue: 'text-blue border-blue/30 bg-blue/10',
    orange: 'text-orange border-orange/30 bg-orange/10',
    pink: 'text-pink border-pink/30 bg-pink/10',
    purple: 'text-purple border-purple/30 bg-purple/10',
  }

  return (
    <div className={`p-5 rounded-lg border ${colorClasses[color]} hover:shadow-lg transition-all duration-300`}>
      <div className="flex items-center gap-3 mb-2">
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-3xl font-mono font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-white/60">{label}</div>
    </div>
  )
}

const layerStyles: Record<string, string> = {
  raw: 'border-blue/30 bg-blue/10 hover:border-blue/50 hover:bg-blue/20',
  staging: 'border-green/30 bg-green/10 hover:border-green/50 hover:bg-green/20',
  marts: 'border-yellow/30 bg-yellow/10 hover:border-yellow/50 hover:bg-yellow/20',
  modeling: 'border-orange/30 bg-orange/10 hover:border-orange/50 hover:bg-orange/20',
  frontend: 'border-purple/30 bg-purple/10 hover:border-purple/50 hover:bg-purple/20',
}

function ArchitectureCard({ stage, index }: { stage: typeof ARCHITECTURE_STAGES[0]; index: number }) {
  return (
    <div
      className={`min-w-[140px] rounded-lg border p-4 text-center transition-all duration-300 ${layerStyles[stage.layer]}`}
      style={{ animation: 'fadeInUp 0.5s ease-out forwards', animationDelay: `${index * 70}ms`, opacity: 0 }}
    >
      <div className="text-xs font-mono text-white/60 mb-1">{stage.layer}</div>
      <div className="text-sm font-medium text-white mb-1">{stage.label}</div>
      <div className="text-xs text-white/50">{stage.sub}</div>
    </div>
  )
}

function FindingCard({ finding, index }: { finding: typeof KEY_FINDINGS[0]; index: number }) {
  const [flipped, setFlipped] = useState(false)
  const isTopModels = finding.headline === 'Top model comparison'

  return (
    <div
      className="group h-56"
      style={{ animation: 'fadeInUp 0.5s ease-out forwards', animationDelay: `${index * 80}ms`, opacity: 0 }}
    >
      <button
        type="button"
        aria-pressed={flipped}
        onClick={() => setFlipped((v) => !v)}
        className="relative w-full h-full"
        style={{ perspective: '1000px' }}
      >
        <div
          className="relative w-full h-full transition-transform duration-500"
          style={{
            transformStyle: 'preserve-3d',
            transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
          }}
        >
          {/* Front */}
          <div
            className="absolute inset-0 backface-hidden bg-comment/5 rounded-lg border border-comment/30 hover:border-yellow/50 transition-colors p-5 flex flex-col"
            style={{ backfaceVisibility: 'hidden' }}
          >
            <div className="font-medium text-white text-lg mb-3">{finding.headline}</div>
            <p className="text-white/70 text-sm leading-relaxed flex-1">
              {isTopModels ? (
                finding.summary
              ) : (
                finding.summary
              )}
            </p>
            <div className="text-xs text-comment mt-3 text-left">Click to flip</div>
          </div>

          {/* Back */}
          <div
            className="absolute inset-0 backface-hidden bg-comment/10 rounded-lg border border-yellow/40 p-5 flex flex-col overflow-auto"
            style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
          >
            {isTopModels ? (
              <div className="flex-1">
                <div className="text-white/90 text-sm mb-2">Top 5 by mean PR-AUC:</div>
                <div className="space-y-1">
                  {(finding.detail as any[]).map((row, i) => (
                    <div key={i} className="flex items-center justify-between gap-2 text-sm">
                      <span className="text-white/70 truncate flex-1 min-w-0" title={`${row.model} | ${row.featureSet}`}>
                        {row.model} + {row.featureSet}
                      </span>
                      <span className="font-mono text-yellow shrink-0">{row.meanPrAuc.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-white/80 text-sm leading-relaxed flex-1">{finding.detail as string}</p>
            )}
            <div className="text-xs text-comment mt-3 text-left">Click to return</div>
          </div>
        </div>
      </button>
    </div>
  )
}

export default function LandingPage() {
  return (
    <div>
      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Hero */}
      <section className="py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
                SECOM Manufacturing <span className="text-yellow">Data Quality</span> Platform
              </h1>
              <p className="text-lg text-white/70 mb-6">
                A full-stack analytics case study built on the UCI SECOM dataset: PostgreSQL warehouse, data-quality profiling, walk-forward modeling, and a React dashboard.
              </p>
              <ul className="space-y-3 text-white/60 mb-8">
                <li className="flex items-start gap-3">
                  <span className="text-yellow mt-1">-</span>
                  <span>Warehouse built from raw SECOM data with raw, staging, and mart layers</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-yellow mt-1">-</span>
                  <span>Data-quality profiling, feature catalog, and analytical marts</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-yellow mt-1">-</span>
                  <span>Walk-forward modeling benchmark with inspection-rate metrics and anomaly baselines</span>
                </li>
              </ul>

              <div className="flex flex-wrap gap-4">
                <Link
                  to="/data-quality"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-yellow text-bg font-medium rounded-lg hover:bg-yellow/90 transition-colors"
                >
                  <BarChart3 className="w-5 h-5" />
                  View Project Metrics
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <a
                  href={REPO_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
                >
                  <Github className="w-5 h-5" />
                  View on GitHub
                </a>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <KPICard
                icon={Database}
                value={DATASET_METRICS.entityCount.toLocaleString()}
                label="SECOM entities"
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
              <KPICard
                icon={XCircle}
                value={`${DATASET_METRICS.failPct}%`}
                label="failure rate"
                color="pink"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Project Snapshot */}
      <section className="py-12 border-y border-comment/30 bg-comment/5">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 text-sm">
            <div>
              <div className="text-comment text-xs uppercase tracking-wider mb-1">Date range</div>
              <div className="flex items-center gap-2 font-mono text-white">
                <Calendar className="w-4 h-4 text-comment" />
                {DATASET_METRICS.dateRange.start} to {DATASET_METRICS.dateRange.end}
              </div>
            </div>
            <div>
              <div className="text-comment text-xs uppercase tracking-wider mb-1">Export pipeline</div>
              <div className="font-mono text-white">scripts/generate_web_data.py</div>
            </div>
            <div>
              <div className="text-comment text-xs uppercase tracking-wider mb-1">Ranked separators</div>
              <div className="font-mono text-white">{RANKED_SEPARATOR_COUNT.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-comment text-xs uppercase tracking-wider mb-1">Model benchmark</div>
              <div className="font-mono text-white">{BENCHMARK_SCALE.configs} configs / {BENCHMARK_SCALE.cvRows} CV rows</div>
            </div>
          </div>
        </div>
      </section>

      {/* Pipeline Architecture */}
      <section className="py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Pipeline Architecture</h2>
            <p className="text-white/60 max-w-2xl mx-auto">
              From raw files to React dashboard. The pipeline flows through ingestion, transformation, modeling, and export.
            </p>
          </div>

          {/* Desktop diagram */}
          <div className="hidden md:block">
            <div className="flex items-center justify-center gap-2">
              {ARCHITECTURE_STAGES.slice(0, 5).map((stage, i) => (
                <div key={stage.id} className="flex items-center gap-2">
                  <ArchitectureCard stage={stage} index={i} />
                  <ArrowRight className="w-4 h-4 text-comment mx-1" />
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center gap-2 mt-2">
              <ArrowRight className="w-4 h-4 text-comment mx-1" />
              {ARCHITECTURE_STAGES.slice(5).map((stage, i) => (
                <div key={stage.id} className="flex items-center gap-2">
                  <ArchitectureCard stage={stage} index={i + 5} />
                  {i < 3 && <ArrowRight className="w-4 h-4 text-comment mx-1" />}
                </div>
              ))}
            </div>
          </div>

          {/* Mobile diagram */}
          <div className="md:hidden flex flex-col items-center gap-3">
            {ARCHITECTURE_STAGES.map((stage, i) => (
              <div key={stage.id} className="flex flex-col items-center gap-3 w-full max-w-xs">
                <div className="w-full">
                  <ArchitectureCard stage={stage} index={i} />
                </div>
                {i < ARCHITECTURE_STAGES.length - 1 && <ArrowRight className="w-4 h-4 text-comment rotate-90" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Findings */}
      <section className="py-16 md:py-24 border-t border-comment/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Key Findings</h2>
            <p className="text-white/60">Insights from the SECOM warehouse, modeling, and dashboard analysis</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {KEY_FINDINGS.map((finding, index) => (
              <FindingCard key={finding.headline} finding={finding} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* Explore the Data */}
      <section className="py-16 md:py-24 border-t border-comment/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">Explore the Data</h2>
          <p className="text-white/60 mb-8 max-w-2xl mx-auto">
            Dive deeper into the data quality metrics, signal separation analysis, time trends, and modeling results.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/data-quality"
              className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
            >
              <BarChart3 className="w-5 h-5" />
              Data Quality
            </Link>
            <Link
              to="/signal-analysis"
              className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
            >
              <Activity className="w-5 h-5" />
              Signal Separation
            </Link>
            <Link
              to="/time-trends"
              className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
            >
              <Calendar className="w-5 h-5" />
              Yield Timeline
            </Link>
            <Link
              to="/modeling"
              className="inline-flex items-center gap-2 px-6 py-3 border border-comment text-white rounded-lg hover:border-yellow hover:text-yellow transition-colors"
            >
              <Brain className="w-5 h-5" />
              Risk Modeling
            </Link>
          </div>
        </div>
      </section>

      {/* Quiet GitHub footer */}
      <section className="py-12 border-t border-comment/30">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-white/60 text-sm">
            Want to see the code?{' '}
            <a
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-yellow hover:text-green transition-colors font-medium inline-flex items-center gap-1"
            >
              <Github className="w-4 h-4" />
              View on GitHub
            </a>
          </p>
        </div>
      </section>
    </div>
  )
}
