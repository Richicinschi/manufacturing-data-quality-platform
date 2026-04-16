import { useMemo, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts'
import {
  Brain,
  Calendar,
  Gauge,
  TrendingUp,
  CheckCircle,
  XCircle,
  Activity,
  Target,
  Layers,
  Filter,
} from 'lucide-react'
import {
  MODEL_BENCHMARK,
  MODEL_THRESHOLD_ANALYSIS,
  MODEL_THRESHOLD_COST_CURVE,
  MODEL_PROBABILITY_BINS,
  FINAL_MODEL_TEST_RESULTS,
  MODEL_CONFUSION_SUMMARY,
  SELECTED_SIGNAL_SHORTLIST,
  MODEL_FEATURE_IMPORTANCE,
  ANOMALY_MODEL_BENCHMARK,
  FINAL_MODEL_INSPECTION_CURVE,
  PUBLIC_NOTEBOOK_COMPARISON,
} from '../data/adapters/modeling'

function MetricCard({
  icon: Icon,
  label,
  value,
  subtext,
  color = 'yellow',
}: {
  icon: React.ElementType
  label: string
  value: string
  subtext?: string
  color?: 'yellow' | 'green' | 'blue' | 'pink' | 'orange'
}) {
  const colorMap = {
    yellow: 'border-yellow/30 bg-yellow/10 text-yellow',
    green: 'border-green/30 bg-green/10 text-green',
    blue: 'border-blue/30 bg-blue/10 text-blue',
    pink: 'border-pink/30 bg-pink/10 text-pink',
    orange: 'border-orange/30 bg-orange/10 text-orange',
  }
  return (
    <div className={`p-5 rounded-lg border ${colorMap[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-5 h-5" />
        <span className="text-white/60 text-sm">{label}</span>
      </div>
      <div className="text-3xl font-mono font-bold text-white mb-1">{value}</div>
      {subtext && <div className="text-white/50 text-xs">{subtext}</div>}
    </div>
  )
}

export default function ModelingPage() {
  const [familyFilter, setFamilyFilter] = useState<string>('all')
  const [featureSetFilter, setFeatureSetFilter] = useState<string>('all')
  const [finalEligibleOnly, setFinalEligibleOnly] = useState<boolean>(false)
  const [kindFilter, setKindFilter] = useState<string>('all')

  const benchmarkData = useMemo(
    () =>
      MODEL_BENCHMARK.map((row: any) => ({
        ...row,
        label: `${row.model} | ${row.featureSet}`,
        modelFamily: row.modelFamily,
        enabled: row.enabled,
        meanPrecision: row.meanPrecision,
        meanRecall: row.meanRecall,
        meanRecallAt10Pct: row.meanRecallAt10Pct,
        meanPrecisionAt10Pct: row.meanPrecisionAt10Pct,
        meanLiftAt10Pct: row.meanLiftAt10Pct,
        finalEligible: row.finalEligible,
        modelKind: row.modelKind,
        bestForInspectionPolicy: row.bestForInspectionPolicy,
      })),
    [],
  )

  const filteredBenchmark = useMemo(() => {
    return benchmarkData.filter((row) => {
      if (familyFilter !== 'all' && row.modelFamily !== familyFilter) return false
      if (featureSetFilter !== 'all' && row.featureSet !== featureSetFilter) return false
      if (kindFilter !== 'all' && row.modelKind !== kindFilter) return false
      if (finalEligibleOnly && !row.finalEligible) return false
      return true
    })
  }, [benchmarkData, familyFilter, featureSetFilter, kindFilter, finalEligibleOnly])

  const familySummary = useMemo(() => {
    const families = Array.from(new Set(MODEL_BENCHMARK.map((r: any) => r.modelFamily)))
    return families.map((family: string) => {
      const rows = MODEL_BENCHMARK.filter((r: any) => r.modelFamily === family && r.enabled)
      return {
        family,
        count: rows.length,
        bestPrAuc: rows.length > 0 ? Math.max(...rows.map((r: any) => r.meanPrAuc)) : 0,
      }
    })
  }, [])

  const thresholdData = useMemo(() => MODEL_THRESHOLD_ANALYSIS, [])
  const selectedThreshold = useMemo(
    () => MODEL_THRESHOLD_ANALYSIS.find((t) => t.selected)?.threshold ?? 0.5,
    [],
  )

  const testConfusion = useMemo(
    () => MODEL_CONFUSION_SUMMARY.find((c: any) => c.split === 'test'),
    [],
  )

  const bestBenchmark = useMemo(
    () =>
      MODEL_BENCHMARK.length > 0
        ? MODEL_BENCHMARK.reduce((best, row) => (row.meanPrAuc > best.meanPrAuc ? row : best))
        : null,
    [],
  )

  const hasData =
    MODEL_BENCHMARK.length > 0 &&
    MODEL_THRESHOLD_ANALYSIS.length > 0 &&
    FINAL_MODEL_TEST_RESULTS != null

  if (!hasData) {
    return (
      <div className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-white mb-4">Risk Modeling</h1>
          <p className="text-white/60">
            No modeling results are available yet. Run{' '}
            <span className="font-mono text-yellow">scripts/run_modeling_pipeline.py</span>{' '}
            first.
          </p>
        </div>
      </div>
    )
  }

  const families = Array.from(new Set(MODEL_BENCHMARK.map((r) => r.modelFamily)))
  const featureSets = Array.from(new Set(MODEL_BENCHMARK.map((r) => r.featureSet)))
  const modelKinds = Array.from(new Set(MODEL_BENCHMARK.map((r) => r.modelKind)))

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Risk Modeling</h1>
          <p className="text-white/60 max-w-2xl">
            Rare-failure risk modeling on SECOM using chronological holdout evaluation, walk-forward CV, supervised classifiers, anomaly baselines, and inspection-rate metrics.
          </p>
        </div>

        {/* Experiment Design */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Experiment Design</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-blue/20 rounded-lg">
                  <Calendar className="w-5 h-5 text-blue" />
                </div>
                <h3 className="text-white font-medium">Chronological Split</h3>
              </div>
              <p className="text-white/60 text-sm">
                Development set = oldest 85%. Final holdout = newest 15%. This preserves temporal order and avoids leakage.
              </p>
            </div>
            <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-green/20 rounded-lg">
                  <Layers className="w-5 h-5 text-green" />
                </div>
                <h3 className="text-white font-medium">Walk-Forward CV</h3>
              </div>
              <p className="text-white/60 text-sm">
                4-fold expanding-window CV on the development set (degrades gracefully if fail counts per fold are low).
              </p>
            </div>
            <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-yellow/20 rounded-lg">
                  <Gauge className="w-5 h-5 text-yellow" />
                </div>
                <h3 className="text-white font-medium">Primary Metric</h3>
              </div>
              <p className="text-white/60 text-sm">
                PR-AUC on the fail class. Threshold is chosen to maximize fail-class F1 on development OOF predictions.
              </p>
            </div>
            <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-pink/20 rounded-lg">
                  <Activity className="w-5 h-5 text-pink" />
                </div>
                <h3 className="text-white font-medium">Anomaly Detection</h3>
              </div>
              <p className="text-white/60 text-sm">
                Isolation Forest and LOF are enabled in the default benchmark; Elliptic Envelope and One-Class SVM are registered reference models. All learn normal-process behavior and flag deviations as risk.
              </p>
            </div>
            <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-orange/20 rounded-lg">
                  <Target className="w-5 h-5 text-orange" />
                </div>
                <h3 className="text-white font-medium">Inspection Metrics</h3>
              </div>
              <p className="text-white/60 text-sm">
                recall@10%, precision@10%, and lift@10% measure how many failures are captured when inspecting only the top 10% riskiest entities.
              </p>
            </div>
          </div>
        </section>

        {/* Model Family Cards */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Model Families</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {familySummary.map((f) => (
              <div key={f.family} className="bg-comment/5 rounded-lg p-5 border border-comment/30">
                <div className="text-white/50 text-xs uppercase tracking-wider mb-1">{f.family.replace(/_/g, ' ')}</div>
                <div className="text-2xl font-mono font-bold text-white mb-1">{f.count}</div>
                <div className="text-white/60 text-sm">configurations trained</div>
                <div className="mt-3 text-yellow font-mono text-sm">Best PR-AUC: {f.bestPrAuc.toFixed(3)}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Supervised vs Anomaly Detection */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Supervised vs Anomaly Detection</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {(() => {
              const sup = MODEL_BENCHMARK.filter((r: any) => r.modelKind === 'classifier' && r.enabled)
              const anom = MODEL_BENCHMARK.filter((r: any) => r.modelKind === 'anomaly_detector' && r.enabled)
              const bestSupPr = sup.length > 0 ? Math.max(...sup.map((r: any) => r.meanPrAuc)) : 0
              const bestAnomPr = anom.length > 0 ? Math.max(...anom.map((r: any) => r.meanPrAuc)) : 0
              const bestSupRec = sup.length > 0 ? Math.max(...sup.map((r: any) => r.meanRecallAt10Pct)) : 0
              const bestAnomRec = anom.length > 0 ? Math.max(...anom.map((r: any) => r.meanRecallAt10Pct)) : 0
              return (
                <>
                  <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
                    <div className="text-white/50 text-xs uppercase tracking-wider mb-2">Best PR-AUC</div>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-white/70 text-sm">Supervised</span>
                        <span className="text-white font-mono">{bestSupPr.toFixed(3)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-white/70 text-sm">Anomaly</span>
                        <span className="text-white font-mono">{bestAnomPr.toFixed(3)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-comment/5 rounded-lg p-5 border border-comment/30">
                    <div className="text-white/50 text-xs uppercase tracking-wider mb-2">Best Recall @ 10%</div>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-white/70 text-sm">Supervised</span>
                        <span className="text-white font-mono">{bestSupRec.toFixed(3)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-white/70 text-sm">Anomaly</span>
                        <span className="text-white font-mono">{bestAnomRec.toFixed(3)}</span>
                      </div>
                    </div>
                  </div>
                </>
              )
            })()}
          </div>
        </section>

        {/* Model Benchmark */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Model Benchmark</h2>
          <div className="grid grid-cols-1 gap-8">
            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Mean PR-AUC by Model by Feature Set</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredBenchmark} layout="vertical" margin={{ left: 120 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                    <XAxis type="number" domain={[0, 1]} tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                    <YAxis
                      type="category"
                      dataKey="label"
                      tick={{ fill: '#d6d6d6', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                      width={110}
                    />
                    <Tooltip
                      contentStyle={{
                        background: '#2e2e2e',
                        border: '1px solid #797979',
                        borderRadius: '4px',
                      }}
                      formatter={(value: number) => [value.toFixed(3), 'Mean PR-AUC']}
                    />
                    <Bar dataKey="meanPrAuc" fill="#e5b567" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30 overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">Benchmark Table</h3>
                <div className="flex items-center gap-2 text-white/60 text-sm">
                  <Filter className="w-4 h-4" />
                  <span>Filters</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-3 mb-4">
                <select
                  className="bg-comment/10 border border-comment/30 rounded px-3 py-1 text-white text-sm"
                  value={familyFilter}
                  onChange={(e) => setFamilyFilter(e.target.value)}
                >
                  <option value="all">All families</option>
                  {families.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                <select
                  className="bg-comment/10 border border-comment/30 rounded px-3 py-1 text-white text-sm"
                  value={featureSetFilter}
                  onChange={(e) => setFeatureSetFilter(e.target.value)}
                >
                  <option value="all">All feature sets</option>
                  {featureSets.map((fs) => (
                    <option key={fs} value={fs}>{fs}</option>
                  ))}
                </select>
                <select
                  className="bg-comment/10 border border-comment/30 rounded px-3 py-1 text-white text-sm"
                  value={kindFilter}
                  onChange={(e) => setKindFilter(e.target.value)}
                >
                  <option value="all">All kinds</option>
                  {modelKinds.map((k) => (
                    <option key={k} value={k}>{k}</option>
                  ))}
                </select>
                <label className="flex items-center gap-2 text-white/70 text-sm">
                  <input
                    type="checkbox"
                    className="rounded border-comment/30"
                    checked={finalEligibleOnly}
                    onChange={(e) => setFinalEligibleOnly(e.target.checked)}
                  />
                  Final eligible only
                </label>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[500px]">
                  <thead>
                    <tr className="border-b border-comment/30 bg-comment/10">
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Rank</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Model</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Family</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Kind</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Feature Set</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Mean PR-AUC</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Mean Prec</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Mean Rec</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Rec@10%</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Lift@10%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBenchmark.sort((a, b) => a.rank - b.rank).map((row) => (
                      <tr
                        key={`${row.model}-${row.featureSet}`}
                        className={`border-b border-comment/20 last:border-b-0 ${
                          row.rank === 1 ? 'bg-yellow/10' : row.bestForInspectionPolicy ? 'bg-pink/10' : 'hover:bg-comment/5'
                        } ${!row.enabled ? 'opacity-50' : ''}`}
                      >
                        <td className="px-3 py-2 text-white font-mono">{row.rank}</td>
                        <td className="px-3 py-2 text-white/80 text-sm">{row.model}</td>
                        <td className="px-3 py-2 text-white/80 text-sm">{row.modelFamily}</td>
                        <td className="px-3 py-2 text-white/80 text-sm">{row.modelKind}</td>
                        <td className="px-3 py-2 text-white/80 text-sm">{row.featureSet}</td>
                        <td className="px-3 py-2 text-white font-mono font-bold">
                          {row.meanPrAuc.toFixed(3)}
                        </td>
                        <td className="px-3 py-2 text-white/70 text-sm">{row.meanPrecision?.toFixed(3) ?? '-'}</td>
                        <td className="px-3 py-2 text-white/70 text-sm">{row.meanRecall?.toFixed(3) ?? '-'}</td>
                        <td className="px-3 py-2 text-white/70 text-sm">{row.meanRecallAt10Pct?.toFixed(3) ?? '-'}</td>
                        <td className="px-3 py-2 text-white/70 text-sm">{row.meanLiftAt10Pct?.toFixed(3) ?? '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-white/50">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-yellow/20 border border-yellow/30" />
                  <span>Best PR-AUC</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-pink/20 border border-pink/30" />
                  <span>Best inspection policy (recall@10%)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Inspection Policy */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Inspection Policy</h2>
          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={FINAL_MODEL_INSPECTION_CURVE}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                  <XAxis
                    dataKey="inspectionRate"
                    tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
                    tick={{ fill: '#d6d6d6', fontSize: 12 }}
                    type="number"
                    domain={[0, 1]}
                  />
                  <YAxis yAxisId="left" tick={{ fill: '#d6d6d6', fontSize: 12 }} domain={[0, 1]} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: '#d6d6d6', fontSize: 12 }} domain={[0, 'auto']} />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                    formatter={(value: number, name: string) => [value.toFixed(3), name]}
                    labelFormatter={(v: number) => `Inspection ${Math.round(v * 100)}%`}
                  />
                  <Line type="monotone" dataKey="recall" yAxisId="left" stroke="#b4d273" strokeWidth={2} dot={false} name="Recall" />
                  <Line type="monotone" dataKey="precision" yAxisId="left" stroke="#6c99bb" strokeWidth={2} dot={false} name="Precision" />
                  <Line type="monotone" dataKey="lift" yAxisId="right" stroke="#e5b567" strokeWidth={2} dot={false} name="Lift" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid sm:grid-cols-3 gap-4">
              {(() => {
                const find = (rate: number) =>
                  FINAL_MODEL_INSPECTION_CURVE.find((r: any) => Math.abs(r.inspectionRate - rate) < 0.001)
                const r05 = find(0.05)
                const r10 = find(0.10)
                const r20 = find(0.20)
                return (
                  <>
                    <div className="p-4 bg-comment/10 rounded-lg border border-comment/30">
                      <div className="text-white/50 text-xs uppercase">Top 5%</div>
                      <div className="text-xl font-mono text-white">{r05 ? `${(r05.recall * 100).toFixed(1)}%` : '-'} recall</div>
                    </div>
                    <div className="p-4 bg-comment/10 rounded-lg border border-comment/30">
                      <div className="text-white/50 text-xs uppercase">Top 10%</div>
                      <div className="text-xl font-mono text-white">{r10 ? `${(r10.recall * 100).toFixed(1)}%` : '-'} recall</div>
                    </div>
                    <div className="p-4 bg-comment/10 rounded-lg border border-comment/30">
                      <div className="text-white/50 text-xs uppercase">Top 20%</div>
                      <div className="text-xl font-mono text-white">{r20 ? `${(r20.recall * 100).toFixed(1)}%` : '-'} recall</div>
                    </div>
                  </>
                )
              })()}
            </div>
          </div>
        </section>

        {/* Threshold Selection */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Threshold Selection</h2>
          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={thresholdData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                  <XAxis
                    dataKey="threshold"
                    tick={{ fill: '#d6d6d6', fontSize: 12 }}
                    type="number"
                    domain={[0, 1]}
                    tickCount={11}
                  />
                  <YAxis tick={{ fill: '#d6d6d6', fontSize: 12 }} domain={[0, 1]} />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                    formatter={(value: number, name: string) => [value.toFixed(3), name]}
                  />
                  <Line type="monotone" dataKey="precision" stroke="#6c99bb" strokeWidth={2} dot={false} name="Precision" />
                  <Line type="monotone" dataKey="recall" stroke="#b4d273" strokeWidth={2} dot={false} name="Recall" />
                  <Line type="monotone" dataKey="f1" stroke="#e5b567" strokeWidth={2} dot={false} name="F1" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-1 rounded bg-blue" />
                <span className="text-white/70">Precision</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-1 rounded bg-green" />
                <span className="text-white/70">Recall</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-1 rounded bg-yellow" />
                <span className="text-white/70">F1</span>
              </div>
              <div className="px-3 py-1 bg-yellow/20 rounded border border-yellow/30 text-yellow">
                Selected threshold: {selectedThreshold.toFixed(2)}
              </div>
            </div>
          </div>
        </section>

        {/* Threshold Cost Curve */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Threshold Tradeoff</h2>
          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={MODEL_THRESHOLD_COST_CURVE.filter((_row: any, i: number) => i % 5 === 0)} margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                  <XAxis dataKey="threshold" tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                  />
                  <Bar dataKey="predictedFailCount" fill="#e5b567" name="Predicted fails" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="falsePositiveCount" fill="#e87d3e" name="False positives" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="falseNegativeCount" fill="#b05279" name="False negatives" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid sm:grid-cols-3 gap-4">
              {(() => {
                const selected = MODEL_THRESHOLD_COST_CURVE.find((t: any) => t.selected)
                if (!selected) return null
                return (
                  <>
                    <div className="p-4 bg-comment/10 rounded-lg border border-comment/30">
                      <div className="text-white/50 text-xs uppercase">Predicted Fails</div>
                      <div className="text-xl font-mono text-white">{selected.predictedFailCount}</div>
                    </div>
                    <div className="p-4 bg-comment/10 rounded-lg border border-comment/30">
                      <div className="text-white/50 text-xs uppercase">Inspection Rate</div>
                      <div className="text-xl font-mono text-white">{selected.inspectionRate}%</div>
                    </div>
                    <div className="p-4 bg-comment/10 rounded-lg border border-comment/30">
                      <div className="text-white/50 text-xs uppercase">False Negatives</div>
                      <div className="text-xl font-mono text-white">{selected.falseNegativeCount}</div>
                    </div>
                  </>
                )
              })()}
            </div>
          </div>
        </section>

        {/* Final Test Results */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Final Chronological Holdout Results</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <MetricCard
              icon={TrendingUp}
              label="Test PR-AUC"
              value={FINAL_MODEL_TEST_RESULTS.prAuc.toFixed(3)}
              color="yellow"
            />
            <MetricCard
              icon={Activity}
              label="Test ROC-AUC"
              value={FINAL_MODEL_TEST_RESULTS.rocAuc.toFixed(3)}
              color="green"
            />
            <MetricCard
              icon={Target}
              label="Test F1"
              value={FINAL_MODEL_TEST_RESULTS.f1.toFixed(3)}
              color="blue"
            />
            <MetricCard
              icon={Brain}
              label="Winning Model"
              value={FINAL_MODEL_TEST_RESULTS.model}
              subtext={FINAL_MODEL_TEST_RESULTS.featureSet}
              color="pink"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Test Confusion Matrix</h3>
              {testConfusion ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-green/10 rounded-lg border border-green/30 text-center">
                    <div className="text-2xl font-mono font-bold text-white">{testConfusion.tn}</div>
                    <div className="text-green text-sm">True Negative</div>
                  </div>
                  <div className="p-4 bg-orange/10 rounded-lg border border-orange/30 text-center">
                    <div className="text-2xl font-mono font-bold text-white">{testConfusion.fp}</div>
                    <div className="text-orange text-sm">False Positive</div>
                  </div>
                  <div className="p-4 bg-pink/10 rounded-lg border border-pink/30 text-center">
                    <div className="text-2xl font-mono font-bold text-white">{testConfusion.fn}</div>
                    <div className="text-pink text-sm">False Negative</div>
                  </div>
                  <div className="p-4 bg-blue/10 rounded-lg border border-blue/30 text-center">
                    <div className="text-2xl font-mono font-bold text-white">{testConfusion.tp}</div>
                    <div className="text-blue text-sm">True Positive</div>
                  </div>
                </div>
              ) : (
                <p className="text-white/60">No confusion data available.</p>
              )}
            </div>

            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Test Metrics Detail</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-comment/10 rounded-lg">
                  <span className="text-white/70">Precision</span>
                  <span className="font-mono text-white">{FINAL_MODEL_TEST_RESULTS.precision.toFixed(3)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-comment/10 rounded-lg">
                  <span className="text-white/70">Recall</span>
                  <span className="font-mono text-white">{FINAL_MODEL_TEST_RESULTS.recall.toFixed(3)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-comment/10 rounded-lg">
                  <span className="text-white/70">Threshold</span>
                  <span className="font-mono text-white">{FINAL_MODEL_TEST_RESULTS.threshold.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-comment/10 rounded-lg">
                  <span className="text-white/70">Features Used</span>
                  <span className="font-mono text-white">{FINAL_MODEL_TEST_RESULTS.nFeatures}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Probability Bins */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Probability Bins</h2>
          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={MODEL_PROBABILITY_BINS} margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                  <XAxis dataKey="binMin" tickFormatter={(v: number) => `${v}-${v + 0.2}`} tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                    formatter={(value: number, name: string) => [name === 'failRate' ? `${value}%` : value, name === 'failRate' ? 'Fail Rate' : 'Total Entities']}
                  />
                  <Bar dataKey="totalEntities" fill="#6c99bb" name="Total Entities" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="failRate" fill="#b05279" name="Fail Rate" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-4 text-white/50 text-sm">
              Shows how actual failures concentrate across predicted probability buckets. This is a diagnostic view, not a calibrated probability claim.
            </p>
          </div>
        </section>

        {/* Feature Importance */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Feature Importance</h2>
          <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[400px]">
                <thead>
                  <tr className="border-b border-comment/30 bg-comment/10">
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Rank</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Feature</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Importance</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {MODEL_FEATURE_IMPORTANCE.slice(0, 20).map((row: any, index: number) => (
                    <tr key={row.featureName} className="border-b border-comment/20 last:border-b-0 hover:bg-comment/5">
                      <td className="px-4 py-3 text-comment font-mono text-sm">{index + 1}</td>
                      <td className="px-4 py-3 font-mono text-white text-sm">{row.featureName}</td>
                      <td className="px-4 py-3 text-white/70 text-sm">{row.importance.toFixed(4)}</td>
                      <td className="px-4 py-3 text-white/70 text-sm">{row.importanceType}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="mt-4 text-sm text-white/50">
            Showing top 20 features by native model importance or absolute coefficient.
          </div>
        </section>

        {/* Feature Selection Battle */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Feature Selection Battle</h2>
          <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[500px]">
                <thead>
                  <tr className="border-b border-comment/30 bg-comment/10">
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Feature Set</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Best PR-AUC</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Best Rec@10%</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Configs</th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    const sets = [
                      'keep_only',
                      'correlation_pruned_070',
                      'top_50_mutual_info',
                      'top_50_auc_gap',
                      'top_50_effect',
                    ]
                    return sets.map((fs) => {
                      const rows = MODEL_BENCHMARK.filter((r: any) => r.featureSet === fs && r.enabled)
                      const bestPr = rows.length > 0 ? Math.max(...rows.map((r: any) => r.meanPrAuc)) : 0
                      const bestRec = rows.length > 0 ? Math.max(...rows.map((r: any) => r.meanRecallAt10Pct)) : 0
                      return (
                        <tr key={fs} className="border-b border-comment/20 last:border-b-0 hover:bg-comment/5">
                          <td className="px-4 py-3 font-mono text-white text-sm">{fs}</td>
                          <td className="px-4 py-3 text-white font-mono">{bestPr.toFixed(3)}</td>
                          <td className="px-4 py-3 text-white font-mono">{bestRec.toFixed(3)}</td>
                          <td className="px-4 py-3 text-white/70 text-sm">{rows.length}</td>
                        </tr>
                      )
                    })
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Public Notebook Comparison */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Public Notebook Comparison</h2>
          <div className="bg-orange/10 rounded-lg p-5 border border-orange/30 mb-6">
            <div className="flex items-start gap-3">
              <div className="text-orange font-bold">(!) Reference Only</div>
              <div className="text-white/70 text-sm">
                Public notebooks often report 70-88% recall using random train/test splits and aggressive resampling.
                The comparison below uses the same random 70/30 split protocol, but it is <strong>not</strong> the production benchmark.
                The primary benchmark uses chronological walk-forward CV to avoid leakage.
              </div>
            </div>
          </div>
          {PUBLIC_NOTEBOOK_COMPARISON.length > 0 ? (
            <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[500px]">
                  <thead>
                    <tr className="border-b border-comment/30 bg-comment/10">
                      <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Model</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Feature Set</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-white/70">PR-AUC</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Recall</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-white/70">F1</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PUBLIC_NOTEBOOK_COMPARISON.slice(0, 10).map((row: any) => (
                      <tr key={`${row.model}-${row.featureSet}`} className="border-b border-comment/20 last:border-b-0 hover:bg-comment/5">
                        <td className="px-4 py-3 text-white text-sm">{row.model}</td>
                        <td className="px-4 py-3 text-white/70 text-sm">{row.featureSet}</td>
                        <td className="px-4 py-3 text-white font-mono">{row.testPrAuc.toFixed(3)}</td>
                        <td className="px-4 py-3 text-white font-mono">{row.testRecall.toFixed(3)}</td>
                        <td className="px-4 py-3 text-white font-mono">{row.testF1.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-white/60">No random-split comparison data available. Run <span className="font-mono text-yellow">scripts/run_public_notebook_comparison.py</span> to generate it.</p>
          )}
        </section>

        {/* Selected Signals */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Selected Signal Shortlist</h2>
          <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px]">
                <thead>
                  <tr className="border-b border-comment/30 bg-comment/10">
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Rank</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Feature</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Effect Size</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Null %</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Catalog Action</th>
                  </tr>
                </thead>
                <tbody>
                  {SELECTED_SIGNAL_SHORTLIST.map((row: any, index: number) => (
                    <tr key={row.feature} className="border-b border-comment/20 last:border-b-0 hover:bg-comment/5">
                      <td className="px-4 py-3 text-comment font-mono text-sm">{index + 1}</td>
                      <td className="px-4 py-3 font-mono text-white text-sm">{row.feature}</td>
                      <td className="px-4 py-3 text-white/70 text-sm">{row.effectSize.toFixed(2)}</td>
                      <td className="px-4 py-3 text-white/70 text-sm">{row.nullPct.toFixed(1)}%</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${
                            row.action === 'keep'
                              ? 'bg-green/20 text-green'
                              : row.action === 'review_high_missing'
                              ? 'bg-yellow/20 text-yellow'
                              : 'bg-comment/20 text-white/70'
                          }`}
                        >
                          {row.action === 'keep' && <CheckCircle className="w-3 h-3" />}
                          {row.action === 'review_high_missing' && <Activity className="w-3 h-3" />}
                          {row.action !== 'keep' && row.action !== 'review_high_missing' && (
                            <XCircle className="w-3 h-3" />
                          )}
                          {row.action}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="mt-4 text-sm text-white/50">
            Showing {SELECTED_SIGNAL_SHORTLIST.length} signals from the winning feature set.
          </div>
        </section>

        {/* What Improved / What Did Not */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">What Improved / What Did Not</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {(() => {
              const baseline = MODEL_BENCHMARK.find((r: any) => r.model === 'random_forest' && r.featureSet === 'keep_only')
              const best = bestBenchmark
              const bestAnom = ANOMALY_MODEL_BENCHMARK.length > 0
                ? ANOMALY_MODEL_BENCHMARK.reduce((a: any, b: any) => (a.meanPrAuc > b.meanPrAuc ? a : b))
                : null
              const prImproved = best && baseline && best.meanPrAuc > baseline.meanPrAuc
              const anomBeat = bestAnom && baseline && bestAnom.meanPrAuc > baseline.meanPrAuc
              return (
                <>
                  <div className="p-5 bg-green/10 rounded-lg border border-green/30">
                    <h3 className="text-green font-medium mb-2">What Improved</h3>
                    <ul className="list-disc list-inside text-white/60 text-sm space-y-1">
                      <li>Added anomaly detection baselines and inspection-rate metrics.</li>
                      <li>Added fold-local feature selectors (correlation pruning, mutual information, AUC gap, missingness indicators).</li>
                      <li>Unified risk-score framework supports classifiers and anomaly detectors.</li>
                      {prImproved && (
                        <li>
                          Best PR-AUC improved from {baseline.meanPrAuc.toFixed(3)} to {best.meanPrAuc.toFixed(3)}.
                        </li>
                      )}
                    </ul>
                  </div>
                  <div className="p-5 bg-pink/10 rounded-lg border border-pink/30">
                    <h3 className="text-pink font-medium mb-2">What Did Not</h3>
                    <ul className="list-disc list-inside text-white/60 text-sm space-y-1">
                      <li>SECOM remains extremely hard: absolute recall stays low under chronological evaluation.</li>
                      {!anomBeat && <li>Anomaly detection did not beat the random_forest + keep_only baseline on PR-AUC.</li>}
                      <li>No hyperparameter tuning was performed; results are architectural, not optimized.</li>
                    </ul>
                  </div>
                </>
              )
            })()}
          </div>
        </section>
      </div>
    </div>
  )
}
