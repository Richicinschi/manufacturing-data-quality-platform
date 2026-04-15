import { useMemo, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { TrendingUp, CheckCircle, XCircle, Info, Search, ArrowUpDown, Activity } from 'lucide-react'
import { TOP_SIGNAL_PROFILES, FEATURE_CORRELATION_TO_FAILURE } from '../data/generatedData'

function getEffectColor(effectSize: number) {
  if (effectSize >= 0.8) return 'text-green'
  if (effectSize >= 0.5) return 'text-yellow'
  return 'text-orange'
}

function getEffectBarColor(effectSize: number) {
  if (effectSize >= 0.8) return 'bg-green'
  if (effectSize >= 0.5) return 'bg-yellow'
  return 'bg-orange'
}

export default function SignalAnalysisPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortDesc, setSortDesc] = useState(true)
  const top20Features = useMemo(
    () => FEATURE_CORRELATION_TO_FAILURE.slice(0, 20).map((row) => row.feature),
    [],
  )
  const [selectedFeature, setSelectedFeature] = useState(top20Features[0] ?? '')

  const filteredRanking = useMemo(() => {
    const base = FEATURE_CORRELATION_TO_FAILURE.filter((row) =>
      row.feature.toLowerCase().includes(searchQuery.toLowerCase()),
    )
    return sortDesc
      ? base.sort((a, b) => b.effectSize - a.effectSize)
      : base.sort((a, b) => a.effectSize - b.effectSize)
  }, [searchQuery, sortDesc])

  const selectedCorrelation = useMemo(
    () => FEATURE_CORRELATION_TO_FAILURE.find((row) => row.feature === selectedFeature),
    [selectedFeature],
  )

  const passProfile = useMemo(
    () => TOP_SIGNAL_PROFILES.find((p) => p.feature === selectedFeature && p.yieldClass === 'pass'),
    [selectedFeature],
  )
  const failProfile = useMemo(
    () => TOP_SIGNAL_PROFILES.find((p) => p.feature === selectedFeature && p.yieldClass === 'fail'),
    [selectedFeature],
  )

  const quartileChartData = useMemo(() => {
    if (!passProfile || !failProfile) return []
    return [
      { name: 'Min', pass: passProfile.min, fail: failProfile.min },
      { name: 'P25', pass: passProfile.p25, fail: failProfile.p25 },
      { name: 'Median', pass: passProfile.median, fail: failProfile.median },
      { name: 'P75', pass: passProfile.p75, fail: failProfile.p75 },
      { name: 'Max', pass: passProfile.max, fail: failProfile.max },
    ]
  }, [passProfile, failProfile])

  const maxEffectSize = FEATURE_CORRELATION_TO_FAILURE[0]?.effectSize || 1
  const mediumPlusCount = FEATURE_CORRELATION_TO_FAILURE.filter((row) => row.effectSize >= 0.5).length

  if (FEATURE_CORRELATION_TO_FAILURE.length === 0) {
    return (
      <div className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-white mb-4">Signal Analysis</h1>
          <p className="text-white/60">
            No signal separation data is available yet. Run the mart build and website export first.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Signal Analysis</h1>
          <p className="text-white/60 max-w-2xl">
            All ranked features from the pass/fail separation mart, ordered by effect size (Cohen&apos;s d).
            Higher effect sizes indicate stronger discriminative power.
          </p>
        </div>

        <div className="mb-12 bg-comment/5 rounded-lg p-6 border border-comment/30">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-yellow mt-0.5" />
            <div>
              <h3 className="text-white font-medium mb-2">Understanding Effect Size (Cohen&apos;s d)</h3>
              <p className="text-white/60 text-sm mb-3">
                Cohen&apos;s d measures the standardized difference between two means.
                It quantifies how well a feature separates pass from fail outcomes.
              </p>
              <div className="flex flex-wrap gap-4 text-sm">
                <span className="text-white/50">Small: <span className="text-yellow">0.2</span></span>
                <span className="text-white/50">Medium: <span className="text-orange">0.5</span></span>
                <span className="text-white/50">Large: <span className="text-green">0.8+</span></span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white">All Ranked Features by Effect Size</h2>
              <button
                onClick={() => setSortDesc((prev) => !prev)}
                className="inline-flex items-center gap-2 px-3 py-2 bg-comment/10 rounded-lg text-sm text-white/70 hover:text-white hover:bg-comment/20 transition-colors"
              >
                <ArrowUpDown className="w-4 h-4" />
                {sortDesc ? 'Highest first' : 'Lowest first'}
              </button>
            </div>

            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-comment" />
              <input
                type="text"
                placeholder="Search features..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-bg border border-comment/30 rounded-lg text-white placeholder:text-comment focus:border-yellow focus:outline-none"
              />
            </div>

            <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
              <div className="max-h-[500px] overflow-y-auto">
                {filteredRanking.map((signal, index) => (
                  <button
                    key={signal.feature}
                    onClick={() => setSelectedFeature(signal.feature)}
                    className={`w-full text-left p-4 border-b border-comment/20 last:border-b-0 transition-colors ${
                      selectedFeature === signal.feature
                        ? 'bg-yellow/10 border-yellow/30'
                        : 'hover:bg-comment/10'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="text-comment font-mono text-sm">#{index + 1}</span>
                        <span className="font-mono text-white">{signal.feature}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <TrendingUp className={`w-4 h-4 ${getEffectColor(signal.effectSize)}`} />
                        <span className={`font-mono font-bold ${getEffectColor(signal.effectSize)}`}>
                          {signal.effectSize.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div className="w-full h-1.5 bg-comment/30 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${getEffectBarColor(signal.effectSize)}`}
                        style={{ width: `${Math.min((signal.effectSize / maxEffectSize) * 100, 100)}%` }}
                      />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-white mb-4">Feature Drilldown</h2>

            <div className="mb-4">
              <label className="block text-sm text-white/60 mb-2">Select top-20 feature</label>
              <select
                value={selectedFeature}
                onChange={(e) => setSelectedFeature(e.target.value)}
                className="w-full px-4 py-2 bg-bg border border-comment/30 rounded-lg text-white focus:border-yellow focus:outline-none"
              >
                {top20Features.map((feature) => (
                  <option key={feature} value={feature}>
                    {feature}
                  </option>
                ))}
              </select>
            </div>

            {selectedCorrelation && (
              <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-lg text-white">{selectedCorrelation.feature}</span>
                  <div className="flex items-center gap-2 px-3 py-1 bg-yellow/20 rounded-lg border border-yellow/30">
                    <TrendingUp className="w-4 h-4 text-yellow" />
                    <span className="font-mono font-bold text-yellow">
                      d = {selectedCorrelation.effectSize.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="p-3 bg-green/10 rounded-lg border border-green/30">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle className="w-4 h-4 text-green" />
                      <span className="text-white/70">Pass</span>
                    </div>
                    <div className="font-mono text-white">mean = {selectedCorrelation.passMean.toFixed(2)}</div>
                    <div className="font-mono text-green text-xs">gap = {selectedCorrelation.meanGap.toFixed(2)}</div>
                    <div className="font-mono text-comment text-xs">n = {selectedCorrelation.validPassCount}</div>
                  </div>
                  <div className="p-3 bg-pink/10 rounded-lg border border-pink/30">
                    <div className="flex items-center gap-2 mb-1">
                      <XCircle className="w-4 h-4 text-pink" />
                      <span className="text-white/70">Fail</span>
                    </div>
                    <div className="font-mono text-white">mean = {selectedCorrelation.failMean.toFixed(2)}</div>
                    <div className="font-mono text-pink text-xs">gap = {selectedCorrelation.meanGap.toFixed(2)}</div>
                    <div className="font-mono text-comment text-xs">n = {selectedCorrelation.validFailCount}</div>
                  </div>
                </div>
              </div>
            )}

            {passProfile && failProfile && (
              <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 mb-4">
                <h3 className="text-sm font-medium text-white/70 mb-3">Quartiles & Validity</h3>
                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                  <div className="space-y-1">
                    <div className="text-green font-medium">Pass</div>
                    <div className="font-mono text-white/80 text-xs">min: {passProfile.min.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">p25: {passProfile.p25.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">median: {passProfile.median.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">p75: {passProfile.p75.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">max: {passProfile.max.toFixed(2)}</div>
                    <div className="font-mono text-comment text-xs">valid: {passProfile.count} | missing: {passProfile.missingCount}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-pink font-medium">Fail</div>
                    <div className="font-mono text-white/80 text-xs">min: {failProfile.min.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">p25: {failProfile.p25.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">median: {failProfile.median.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">p75: {failProfile.p75.toFixed(2)}</div>
                    <div className="font-mono text-white/80 text-xs">max: {failProfile.max.toFixed(2)}</div>
                    <div className="font-mono text-comment text-xs">valid: {failProfile.count} | missing: {failProfile.missingCount}</div>
                  </div>
                </div>

                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={quartileChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                      <XAxis dataKey="name" tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#d6d6d6', fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          background: '#2e2e2e',
                          border: '1px solid #797979',
                          borderRadius: '4px',
                        }}
                      />
                      <Bar dataKey="pass" name="Pass" fill="#b4d273" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="fail" name="Fail" fill="#b05279" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-green" />
                    <span className="text-white/70 text-sm">Pass</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-pink" />
                    <span className="text-white/70 text-sm">Fail</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 bg-blue/10 rounded-lg p-4 border border-blue/30">
          <div className="flex items-start gap-3">
            <Activity className="w-5 h-5 text-blue mt-0.5" />
            <div>
              <h3 className="text-white font-medium mb-1">From Signals to Selection</h3>
              <p className="text-white/60 text-sm">
                The modeling pipeline turns these effect-size rankings into a selected signal shortlist using walk-forward CV. See the final chosen features on the{' '}
                <a href="#/modeling" className="text-yellow hover:underline">Modeling page</a>.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-12 grid md:grid-cols-4 gap-4">
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-yellow">{FEATURE_CORRELATION_TO_FAILURE.length}</div>
            <div className="text-white/50 text-sm mt-1">Ranked Features Exported</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-green">{mediumPlusCount}</div>
            <div className="text-white/50 text-sm mt-1">Medium+ Effect (d &gt;= 0.5)</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-blue">{FEATURE_CORRELATION_TO_FAILURE[0].feature}</div>
            <div className="text-white/50 text-sm mt-1">Highest Effect Feature</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-orange">{FEATURE_CORRELATION_TO_FAILURE[0].effectSize.toFixed(2)}</div>
            <div className="text-white/50 text-sm mt-1">Max Cohen&apos;s d</div>
          </div>
        </div>
      </div>
    </div>
  )
}
