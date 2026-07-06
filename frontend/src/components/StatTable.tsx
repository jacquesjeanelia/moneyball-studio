import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { PlayerStats } from '@/api/types'
import { percentileKey } from '@/lib/percentiles'
import { METRIC_GROUPS, METRICS } from '@/lib/metrics'
import { formatStat, topPercent, categoryColor } from '@/lib/format'
import { StatBar } from './primitives'

interface StatTableProps {
  stats: PlayerStats | null
}

type StatView = 'per90' | 'total'

/** Format a total stat (per90 × minutes/90) for display. */
function formatTotal(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return value.toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 0 })
}

/** Compute total value from a per90 stat and minutes played. */
function toTotal(raw: number | null, minutes: number | null): number | null {
  if (raw === null || minutes === null || minutes <= 0) return null
  return (raw * minutes) / 90
}

const VIEW_OPTIONS: { key: StatView; label: string }[] = [
  { key: 'total', label: 'Total' },
  { key: 'per90', label: 'Per 90' },
]

/** Grouped stat table: raw value + percentile bar (per90 only). */
export function StatTable({ stats }: StatTableProps) {
  const [view, setView] = useState<StatView>('total')
  const minutes = stats?.minutes_played ?? null

  return (
    <div className="space-y-4">
      {/* View toggle — right-aligned */}
      <div className="flex justify-end">
        <div className="inline-flex items-center rounded-lg surface p-0.5">
          {VIEW_OPTIONS.map((opt) => {
            const active = view === opt.key
            return (
              <button
                key={opt.key}
                onClick={() => setView(opt.key)}
                aria-pressed={active}
                className="relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors"
                style={{ color: active ? '#fff' : 'var(--color-chalk-dim)' }}
              >
                {active && (
                  <motion.span
                    layoutId="stat-view-pill"
                    className="absolute inset-0 rounded-md"
                    style={{ background: 'var(--color-ink-600)' }}
                    transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                  />
                )}
                <span className="relative">{opt.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Stat groups */}
      <div className="space-y-5">
        {METRIC_GROUPS.map((group) => (
          <div key={group.title}>
            <h4 className="text-xs font-bold uppercase tracking-widest mb-2.5" style={{ color: categoryColor(group.category) }}>{group.title}</h4>
            <div className="rounded-xl surface divide-y divide-ink-700/70">
              {group.keys.map((key) => {
                const meta = METRICS.find((m) => m.key === key)!
                const raw = stats?.[key] ?? null
                const pctKey = percentileKey(key)
                const pct = view === 'per90' ? (stats?.[pctKey] ?? 0) : 0
                const displayValue = view === 'total' && !meta.isPercent
                  ? formatTotal(toTotal(raw, minutes))
                  : formatStat(raw, meta.isPercent)
                return (
                  <motion.div
                    key={key}
                    layout
                    initial={false}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex items-center gap-3 sm:gap-4 px-3 sm:px-3.5 py-2.5"
                  >
                    <div className="w-28 sm:w-48 shrink-0">
                      <div className="text-sm font-semibold text-chalk leading-tight">{meta.label}</div>
                    </div>
                    <div className="font-display font-bold text-base text-chalk tnum w-24 sm:w-28 text-right overflow-hidden">
                      <AnimatePresence mode="popLayout">
                        <motion.span
                          key={`${key}-${view}`}
                          initial={{ opacity: 0, y: -6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 6 }}
                          transition={{ duration: 0.18 }}
                          className="block"
                        >
                          {displayValue}
                        </motion.span>
                      </AnimatePresence>
                    </div>
                    {view === 'per90' && (
                      <>
                        <div className="flex-1 min-w-0">
                          <StatBar value={pct} />
                        </div>
                        <div className="hidden sm:block w-16 text-right">
                          <span className="text-xs font-bold text-chalk-dim tnum">Top {topPercent(pct)}%</span>
                        </div>
                      </>
                    )}
                  </motion.div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
