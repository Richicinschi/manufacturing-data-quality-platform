import { useMemo, useState } from 'react'
import type { ElementType } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { Search, Filter, AlertTriangle, CheckCircle, XCircle, Minus } from 'lucide-react'
import {
  ACTION_SUMMARY,
  DATASET_METRICS,
  FEATURE_ACTIONS,
  FEATURE_MISSINGNESS,
  LABEL_DISTRIBUTION,
} from '../data/generatedData'

type FilterType = 'all' | 'keep' | 'review' | 'drop'
type FeatureActionKey = keyof typeof FEATURE_ACTIONS

const actionIcons: Record<FeatureActionKey, ElementType> = {
  keep: CheckCircle,
  review_high_missing: AlertTriangle,
  drop_constant: Minus,
  drop_all_null: XCircle,
}

const actionColors: Record<FeatureActionKey, string> = {
  keep: 'text-green bg-green/20 border-green/30',
  review_high_missing: 'text-yellow bg-yellow/20 border-yellow/30',
  drop_constant: 'text-orange bg-orange/20 border-orange/30',
  drop_all_null: 'text-pink bg-pink/20 border-pink/30',
}

export default function DataQualityPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<FilterType>('all')

  const filteredFeatures = useMemo(() => {
    return FEATURE_MISSINGNESS.filter((feature) => {
      const matchesSearch = feature.feature.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesFilter =
        activeFilter === 'all' ||
        (activeFilter === 'keep' && feature.action === 'keep') ||
        (activeFilter === 'review' && feature.action === 'review_high_missing') ||
        (activeFilter === 'drop' &&
          (feature.action === 'drop_constant' || feature.action === 'drop_all_null'))

      return matchesSearch && matchesFilter
    })
  }, [activeFilter, searchQuery])

  const topMissingFeatures = FEATURE_MISSINGNESS.slice(0, 20)

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Data Quality</h1>
          <p className="text-white/60 max-w-2xl">
            Real mart outputs from the SECOM feature catalog, including label balance,
            missingness ranking, and recommended feature actions.
          </p>
        </div>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Label Distribution</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Pass vs Fail</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={LABEL_DISTRIBUTION}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {LABEL_DISTRIBUTION.map((entry) => (
                        <Cell key={entry.name} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#2e2e2e',
                        border: '1px solid #797979',
                        borderRadius: '4px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-6 mt-4">
                {LABEL_DISTRIBUTION.map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-white/70">{item.name}:</span>
                    <span className="text-white font-mono">{item.value.toLocaleString()}</span>
                    <span className="text-comment text-sm">({item.percentage}%)</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Class Imbalance</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-green/10 rounded-lg border border-green/30">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green" />
                    <span className="text-white">Pass</span>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-mono font-bold text-white">
                      {DATASET_METRICS.passCount.toLocaleString()}
                    </div>
                    <div className="text-sm text-green">{DATASET_METRICS.passPct}%</div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 bg-pink/10 rounded-lg border border-pink/30">
                  <div className="flex items-center gap-3">
                    <XCircle className="w-5 h-5 text-pink" />
                    <span className="text-white">Fail</span>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-mono font-bold text-white">
                      {DATASET_METRICS.failCount.toLocaleString()}
                    </div>
                    <div className="text-sm text-pink">{DATASET_METRICS.failPct}%</div>
                  </div>
                </div>
                <div className="p-4 bg-yellow/10 rounded-lg border border-yellow/30">
                  <div className="flex items-center gap-2 text-yellow mb-1">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm font-medium">Insight</span>
                  </div>
                  <p className="text-white/70 text-sm">
                    Failures represent only {DATASET_METRICS.failPct}% of entities, so any
                    downstream modeling needs imbalance-aware evaluation.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Feature Action Summary</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Actions by Count</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ACTION_SUMMARY}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                    <XAxis dataKey="label" tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#d6d6d6', fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        background: '#2e2e2e',
                        border: '1px solid #797979',
                        borderRadius: '4px',
                      }}
                      formatter={(value: number) => [value, 'Features']}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {ACTION_SUMMARY.map((entry) => (
                        <Cell key={entry.action} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
              <h3 className="text-lg font-medium text-white mb-4">Action Legend</h3>
              <div className="space-y-3">
                {Object.entries(FEATURE_ACTIONS).map(([key, config]) => {
                  const typedKey = key as FeatureActionKey
                  const Icon = actionIcons[typedKey]
                  return (
                    <div key={key} className="flex items-start gap-3 p-3 bg-comment/10 rounded-lg">
                      <div className={`p-2 rounded ${actionColors[typedKey]}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-white font-medium">{config.label}</div>
                        <div className="text-white/50 text-sm">{config.description}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-2xl font-bold text-white mb-6">Top 20 Most Missing Features</h2>
          <div className="bg-comment/5 rounded-lg p-6 border border-comment/30">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topMissingFeatures} layout="vertical" margin={{ left: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#797979" opacity={0.3} />
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                    tick={{ fill: '#d6d6d6', fontSize: 12 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="feature"
                    tick={{ fill: '#d6d6d6', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                    width={70}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#2e2e2e',
                      border: '1px solid #797979',
                      borderRadius: '4px',
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Null %']}
                  />
                  <Bar dataKey="nullPct" fill="#e5b567" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-white mb-2">Full Feature Catalog</h2>
          <p className="text-white/50 text-sm mb-6">
            This website now ships the full exported SECOM feature set, so all {FEATURE_MISSINGNESS.length} profiled features remain available for filtering and future visualizations.
          </p>

          <div className="flex flex-wrap gap-4 mb-6">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-comment" />
              <input
                type="text"
                placeholder="Search features..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-bg border border-comment/30 rounded-lg text-white placeholder:text-comment focus:border-yellow focus:outline-none"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-comment" />
              {(['all', 'keep', 'review', 'drop'] as FilterType[]).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeFilter === filter
                      ? 'bg-yellow text-bg'
                      : 'bg-comment/10 text-white/70 hover:text-white hover:bg-comment/20'
                  }`}
                >
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-comment/5 rounded-lg border border-comment/30 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-comment/30 bg-comment/10">
                  <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Feature</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Null %</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Distinct</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Constant</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-white/70">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredFeatures.map((feature) => {
                  const typedAction = feature.action as FeatureActionKey
                  const Icon = actionIcons[typedAction]
                  const label = FEATURE_ACTIONS[typedAction]?.label ?? typedAction

                  return (
                    <tr
                      key={feature.feature}
                      className="border-b border-comment/20 last:border-b-0 hover:bg-comment/5"
                    >
                      <td className="px-4 py-3 font-mono text-white text-sm">{feature.feature}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-comment/30 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-yellow rounded-full"
                              style={{ width: `${feature.nullPct}%` }}
                            />
                          </div>
                          <span className="text-white/70 text-sm">{feature.nullPct.toFixed(2)}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-white/70 text-sm">{feature.distinctCount}</td>
                      <td className="px-4 py-3">
                        {feature.isConstant ? (
                          <span className="px-2 py-1 bg-pink/20 text-pink text-xs rounded">Yes</span>
                        ) : (
                          <span className="px-2 py-1 bg-green/20 text-green text-xs rounded">No</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${actionColors[typedAction]}`}
                        >
                          <Icon className="w-3 h-3" />
                          {label}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-comment">
            Showing {filteredFeatures.length} of {FEATURE_MISSINGNESS.length} exported features
          </div>
        </section>
      </div>
    </div>
  )
}
