import { useMemo, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { TrendingUp, CheckCircle, XCircle, Info } from 'lucide-react'
import { TOP_SIGNALS } from '../data/generatedData'

function generateHistogramData(signal: typeof TOP_SIGNALS[number]) {
  const bins: { bin: number; pass: number; fail: number }[] = []
  const safePassStd = signal.passStd || 1
  const safeFailStd = signal.failStd || 1
  const min = Math.min(signal.passMean - 3 * safePassStd, signal.failMean - 3 * safeFailStd)
  const max = Math.max(signal.passMean + 3 * safePassStd, signal.failMean + 3 * safeFailStd)
  const binCount = 25
  const binWidth = (max - min) / binCount

  for (let index = 0; index < binCount; index += 1) {
    const binCenter = min + index * binWidth + binWidth / 2
    const passPdf = Math.exp(-0.5 * Math.pow((binCenter - signal.passMean) / safePassStd, 2))
    const failPdf = Math.exp(-0.5 * Math.pow((binCenter - signal.failMean) / safeFailStd, 2))

    bins.push({
      bin: Math.round(binCenter * 10) / 10,
      pass: Math.round(passPdf * 100),
      fail: Math.round(failPdf * 100),
    })
  }

  return bins
}

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
  const [selectedSignal, setSelectedSignal] = useState(0)

  if (TOP_SIGNALS.length === 0) {
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

  const currentSignal = TOP_SIGNALS[selectedSignal]
  const histogramData = useMemo(() => generateHistogramData(currentSignal), [currentSignal])
  const maxEffectSize = TOP_SIGNALS[0].effectSize || 1
  const mediumPlusCount = TOP_SIGNALS.filter((signal) => signal.effectSize >= 0.5).length

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
            <h2 className="text-xl font-bold text-white mb-4">All Ranked Features by Effect Size</h2>
            <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
              <div className="max-h-[500px] overflow-y-auto">
                {TOP_SIGNALS.map((signal, index) => (
                  <button
                    key={signal.feature}
                    onClick={() => setSelectedSignal(index)}
                    className={`w-full text-left p-4 border-b border-comment/20 last:border-b-0 transition-colors ${
                      selectedSignal === index
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
            <h2 className="text-xl font-bold text-white mb-4">Distribution Comparison</h2>

            <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 mb-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-lg text-white">{currentSignal.feature}</span>
                <div className="flex items-center gap-2 px-3 py-1 bg-yellow/20 rounded-lg border border-yellow/30">
                  <TrendingUp className="w-4 h-4 text-yellow" />
                  <span className="font-mono font-bold text-yellow">
                    d = {currentSignal.effectSize.toFixed(2)}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 bg-green/10 rounded-lg border border-green/30">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-4 h-4 text-green" />
                    <span className="text-white/70">Pass</span>
                  </div>
                  <div className="font-mono text-white">mean = {currentSignal.passMean.toFixed(2)}</div>
                  <div className="font-mono text-green text-xs">std = {currentSignal.passStd.toFixed(2)}</div>
                  <div className="font-mono text-comment text-xs">n = {currentSignal.passCount}</div>
                </div>
                <div className="p-3 bg-pink/10 rounded-lg border border-pink/30">
                  <div className="flex items-center gap-2 mb-1">
                    <XCircle className="w-4 h-4 text-pink" />
                    <span className="text-white/70">Fail</span>
                  </div>
                  <div className="font-mono text-white">mean = {currentSignal.failMean.toFixed(2)}</div>
                  <div className="font-mono text-pink text-xs">std = {currentSignal.failStd.toFixed(2)}</div>
                  <div className="font-mono text-comment text-xs">n = {currentSignal.failCount}</div>
                </div>
              </div>
            </div>

            <div className="bg-comment/5 rounded-lg p-4 border border-comment/30">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={histogramData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                    <XAxis dataKey="bin" tick={{ fill: '#d6d6d6', fontSize: 10 }} interval={4} />
                    <YAxis tick={{ fill: '#d6d6d6', fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{
                        background: '#2e2e2e',
                        border: '1px solid #797979',
                        borderRadius: '4px',
                      }}
                    />
                    <ReferenceLine
                      x={currentSignal.passMean}
                      stroke="#b4d273"
                      strokeDasharray="3 3"
                      label={{ value: 'Pass mean', fill: '#b4d273', fontSize: 10 }}
                    />
                    <ReferenceLine
                      x={currentSignal.failMean}
                      stroke="#b05279"
                      strokeDasharray="3 3"
                      label={{ value: 'Fail mean', fill: '#b05279', fontSize: 10 }}
                    />
                    <Bar dataKey="pass" name="Pass" fill="#b4d273" fillOpacity={0.7} />
                    <Bar dataKey="fail" name="Fail" fill="#b05279" fillOpacity={0.7} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-green/70" />
                  <span className="text-white/70 text-sm">Pass distribution</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-pink/70" />
                  <span className="text-white/70 text-sm">Fail distribution</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12 grid md:grid-cols-4 gap-4">
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-yellow">{TOP_SIGNALS.length}</div>
            <div className="text-white/50 text-sm mt-1">Ranked Features Exported</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-green">{mediumPlusCount}</div>
            <div className="text-white/50 text-sm mt-1">Medium+ Effect (d &gt;= 0.5)</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-blue">{TOP_SIGNALS[0].feature}</div>
            <div className="text-white/50 text-sm mt-1">Highest Effect Feature</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30 text-center">
            <div className="text-3xl font-mono font-bold text-orange">{TOP_SIGNALS[0].effectSize.toFixed(2)}</div>
            <div className="text-white/50 text-sm mt-1">Max Cohen&apos;s d</div>
          </div>
        </div>
      </div>
    </div>
  )
}
