import { useMemo } from 'react'
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
} from 'lucide-react'
import {
  MODEL_BENCHMARK,
  MODEL_THRESHOLD_ANALYSIS,
  FINAL_MODEL_TEST_RESULTS,
  MODEL_CONFUSION_SUMMARY,
  SELECTED_SIGNAL_SHORTLIST,
} from '../data/generatedData'

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
  const benchmarkData = useMemo(
    () =>
      MODEL_BENCHMARK.map((row) => ({
        ...row,
        label: `${row.model} | ${row.featureSet}`,
      })),
    [],
  )

  const thresholdData = useMemo(() => MODEL_THRESHOLD_ANALYSIS, [])
  const selectedThreshold = useMemo(
    () => MODEL_THRESHOLD_ANALYSIS.find((t) => t.selected)?.threshold ?? 0.5,
    [],
  )

  const testConfusion = useMemo(
    () => MODEL_CONFUSION_SUMMARY.find((c) => c.split === 'test'),
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
          <h1 className="text-4xl font-bold text-white mb-4">Modeling</h1>
          <p className="text-white/60">
            No modeling results are available yet. Run{' '}
            <span className="font-mono text-yellow">scripts/run_modeling_pipeline.py</span>{' '}
            first.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Modeling</h1>
          <p className="text-white/60 max-w-2xl">
            Yield-failure detection case study with walk-forward cross-validation,
            imbalance-aware classifiers, and signal selection.
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
          </div>
        </section>

        {/* Model Benchmark */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Model Benchmark</h2>
          <div className="grid lg:grid-cols-2 gap-8">
            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Mean PR-AUC by Model × Feature Set</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={benchmarkData} layout="vertical" margin={{ left: 120 }}>
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
              <h3 className="text-lg font-medium text-white mb-4">Benchmark Table</h3>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[400px]">
                  <thead>
                    <tr className="border-b border-comment/30 bg-comment/10">
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Rank</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Model</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Feature Set</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Mean PR-AUC</th>
                      <th className="px-3 py-2 text-left text-sm font-medium text-white/70">Std</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MODEL_BENCHMARK.sort((a, b) => a.rank - b.rank).map((row) => (
                      <tr
                        key={`${row.model}-${row.featureSet}`}
                        className={`border-b border-comment/20 last:border-b-0 ${
                          row.rank === 1 ? 'bg-yellow/10' : 'hover:bg-comment/5'
                        }`}
                      >
                        <td className="px-3 py-2 text-white font-mono">{row.rank}</td>
                        <td className="px-3 py-2 text-white/80 text-sm">{row.model}</td>
                        <td className="px-3 py-2 text-white/80 text-sm">{row.featureSet}</td>
                        <td className="px-3 py-2 text-white font-mono font-bold">
                          {row.meanPrAuc.toFixed(3)}
                        </td>
                        <td className="px-3 py-2 text-white/70 text-sm">{row.stdPrAuc.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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

        {/* Final Test Results */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-white mb-6">Final Test Results</h2>
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
                  {SELECTED_SIGNAL_SHORTLIST.map((row, index) => (
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

        {/* Quick summary cards */}
        <section className="grid md:grid-cols-3 gap-6">
          <div className="p-5 bg-green/10 rounded-lg border border-green/30">
            <h3 className="text-green font-medium mb-2">Best Model</h3>
            <p className="text-white/60 text-sm">
              {bestBenchmark?.model ?? '-'} with {bestBenchmark?.featureSet ?? '-'} achieved the highest mean PR-AUC.
            </p>
          </div>
          <div className="p-5 bg-yellow/10 rounded-lg border border-yellow/30">
            <h3 className="text-yellow font-medium mb-2">Imbalance Handling</h3>
            <p className="text-white/60 text-sm">
              Models used class_weight=&quot;balanced&quot; and evaluation focused on PR-AUC and fail-class F1 rather than accuracy.
            </p>
          </div>
          <div className="p-5 bg-blue/10 rounded-lg border border-blue/30">
            <h3 className="text-blue font-medium mb-2">Signal Selection</h3>
            <p className="text-white/60 text-sm">
              The final shortlist combines catalog actions and fold-time effect-size ranking without lookahead leakage.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
