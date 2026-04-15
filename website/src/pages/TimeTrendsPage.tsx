import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Line,
} from 'recharts'
import { Calendar, TrendingDown, Activity, Clock, Info } from 'lucide-react'
import { DAILY_FAILURE_SUMMARY, DATASET_METRICS } from '../data/generatedData'

export default function TimeTrendsPage() {
  const stats = useMemo(() => {
    const totalDays = DAILY_FAILURE_SUMMARY.length
    const totalEntities = DAILY_FAILURE_SUMMARY.reduce((sum, row) => sum + row.entityCount, 0)
    const avgDailyVolume = totalDays ? Math.round(totalEntities / totalDays) : 0
    const avgFailRate = totalDays
      ? (DAILY_FAILURE_SUMMARY.reduce((sum, row) => sum + row.failRate, 0) / totalDays).toFixed(2)
      : '0.00'
    const maxDailyVolume = totalDays ? Math.max(...DAILY_FAILURE_SUMMARY.map((row) => row.entityCount)) : 0
    const minDailyVolume = totalDays ? Math.min(...DAILY_FAILURE_SUMMARY.map((row) => row.entityCount)) : 0

    return {
      totalDays,
      avgDailyVolume,
      avgFailRate,
      maxDailyVolume,
      minDailyVolume,
    }
  }, [])

  const chartData = useMemo(
    () =>
      DAILY_FAILURE_SUMMARY.map((row) => ({
        ...row,
        passCount: row.entityCount - row.failCount,
      })),
    [],
  )

  if (DAILY_FAILURE_SUMMARY.length === 0) {
    return (
      <div className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-white mb-4">Time Trends</h1>
          <p className="text-white/60">
            No daily yield trend data is available yet. Run the mart build and website export first.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Time Trends</h1>
          <p className="text-white/60 max-w-2xl">
            Daily yield metrics and entity volume across the observed SECOM time range
            from {DATASET_METRICS.dateRange.start} to {DATASET_METRICS.dateRange.end}.
          </p>
        </div>

        <div className="mb-12 flex items-center justify-center gap-4 p-6 bg-comment/5 rounded-lg border border-comment/30">
          <Calendar className="w-6 h-6 text-yellow" />
          <div className="text-center">
            <div className="text-white font-mono text-lg">
              {DATASET_METRICS.dateRange.start} to {DATASET_METRICS.dateRange.end}
            </div>
            <div className="text-comment text-sm mt-1">{stats.totalDays} observed days</div>
          </div>
          <Clock className="w-6 h-6 text-yellow" />
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-12">
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-blue" />
              <span className="text-white/50 text-sm">Avg Daily Volume</span>
            </div>
            <div className="text-2xl font-mono font-bold text-white">{stats.avgDailyVolume}</div>
            <div className="text-comment text-xs mt-1">entities per day</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-4 h-4 text-pink" />
              <span className="text-white/50 text-sm">Avg Fail Rate</span>
            </div>
            <div className="text-2xl font-mono font-bold text-white">{stats.avgFailRate}%</div>
            <div className="text-comment text-xs mt-1">daily average</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-green" />
              <span className="text-white/50 text-sm">Max Daily Volume</span>
            </div>
            <div className="text-2xl font-mono font-bold text-white">{stats.maxDailyVolume}</div>
            <div className="text-comment text-xs mt-1">highest single day</div>
          </div>
          <div className="bg-comment/5 rounded-lg p-4 border border-comment/30">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-orange" />
              <span className="text-white/50 text-sm">Min Daily Volume</span>
            </div>
            <div className="text-2xl font-mono font-bold text-white">{stats.minDailyVolume}</div>
            <div className="text-comment text-xs mt-1">lowest single day</div>
          </div>
        </div>

        <div className="mb-8 bg-yellow/10 rounded-lg p-4 border border-yellow/30 flex items-start gap-3">
          <Info className="w-5 h-5 text-yellow mt-0.5" />
          <div>
            <p className="text-white/80 text-sm">
              The observed period spans <span className="font-mono text-white">{stats.totalDays} days</span> with a strong class imbalance: only <span className="font-mono text-white">{DATASET_METRICS.failPct}%</span> of entities failed. The rolling 7-day fail rate smooths daily noise and reflects the underlying imbalance without inventing operational causes. For modeling, the dataset is split chronologically: oldest 85% for development and newest 15% for final holdout evaluation.
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-pink/20 rounded-lg">
                <TrendingDown className="w-5 h-5 text-pink" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Fail Rate Trend</h2>
                <p className="text-white/50 text-sm">Daily fail rate with 7-day rolling average</p>
              </div>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData}>
                  <defs>
                    <linearGradient id="failRateGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#b05279" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#b05279" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#d6d6d6', fontSize: 10 }}
                    tickFormatter={(value) => String(value).slice(5)}
                    minTickGap={24}
                  />
                  <YAxis
                    tick={{ fill: '#d6d6d6', fontSize: 10 }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                    formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, name]}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="rolling7dFailRate"
                    stroke="#b05279"
                    strokeWidth={2}
                    fill="url(#failRateGradient)"
                    name="Rolling 7-day Fail Rate"
                  />
                  <Line
                    type="monotone"
                    dataKey="failRate"
                    stroke="#b05279"
                    strokeWidth={1}
                    strokeOpacity={0.5}
                    dot={false}
                    name="Daily Fail Rate"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue/20 rounded-lg">
                <Activity className="w-5 h-5 text-blue" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Daily Entity Volume</h2>
                <p className="text-white/50 text-sm">Number of entities tested per day</p>
              </div>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#d6d6d6', fontSize: 10 }}
                    tickFormatter={(value) => String(value).slice(5)}
                    minTickGap={24}
                  />
                  <YAxis tick={{ fill: '#d6d6d6', fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                    formatter={(value: number) => [value, 'Entities']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Bar dataKey="entityCount" fill="#6c99bb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-comment/5 rounded-lg p-6 border border-comment/30">
          <h2 className="text-lg font-bold text-white mb-6">Daily Pass/Fail Breakdown</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#d6d6d6', fontSize: 10 }}
                  tickFormatter={(value) => String(value).slice(5)}
                  minTickGap={24}
                />
                <YAxis tick={{ fill: '#d6d6d6', fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    background: '#2e2e2e',
                    border: '1px solid #797979',
                    borderRadius: '4px',
                  }}
                />
                <Bar dataKey="passCount" name="Pass" fill="#b4d273" radius={[4, 4, 0, 0]} />
                <Bar dataKey="failCount" name="Fail" fill="#b05279" radius={[4, 4, 0, 0]} />
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

        <div className="mt-12 grid md:grid-cols-3 gap-6">
          <div className="p-6 bg-green/10 rounded-lg border border-green/30">
            <h3 className="text-green font-medium mb-2">Production Consistency</h3>
            <p className="text-white/60 text-sm">
              The dataset averages {stats.avgDailyVolume} entities per observed day, giving the dashboard a stable daily volume baseline.
            </p>
          </div>
          <div className="p-6 bg-yellow/10 rounded-lg border border-yellow/30">
            <h3 className="text-yellow font-medium mb-2">Yield Stability</h3>
            <p className="text-white/60 text-sm">
              The average fail rate is {stats.avgFailRate}%, which is directionally consistent with the overall dataset imbalance.
            </p>
          </div>
          <div className="p-6 bg-blue/10 rounded-lg border border-blue/30">
            <h3 className="text-blue font-medium mb-2">Temporal Coverage</h3>
            <p className="text-white/60 text-sm">
              The trend mart spans {stats.totalDays} observed days across the full SECOM date range, which is enough to surface daily variation.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
