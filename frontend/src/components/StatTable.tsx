import type { PlayerStats } from '@/api/types'
import type { PercentileTable } from '@/lib/percentiles'
import { percentileOf } from '@/lib/percentiles'
import { METRIC_GROUPS, METRICS } from '@/lib/metrics'
import { formatStat, topPercent, categoryColor } from '@/lib/format'
import { StatBar } from './primitives'

interface StatTableProps {
  stats: PlayerStats | null
  table: PercentileTable
}

/** Grouped stat table: raw value + percentile bar vs positional peers. */
export function StatTable({ stats, table }: StatTableProps) {
  return (
    <div className="space-y-5">
      {METRIC_GROUPS.map((group) => (
        <div key={group.title}>
          <h4 className="text-xs font-bold uppercase tracking-widest mb-2.5" style={{ color: categoryColor(group.category) }}>{group.title}</h4>
          <div className="rounded-xl surface divide-y divide-ink-700/70">
            {group.keys.map((key) => {
              const meta = METRICS.find((m) => m.key === key)!
              const raw = stats?.[key] ?? null
              const sorted = table.get(key) ?? []
              const pct = raw === null ? 0 : percentileOf(sorted, raw)
              return (
                <div key={key} className="flex items-center gap-3 sm:gap-4 px-3 sm:px-3.5 py-2.5">
                  <div className="w-28 sm:w-48 shrink-0">
                    <div className="text-sm font-semibold text-chalk leading-tight">{meta.label}</div>
                    <div className="text-[11px] text-chalk-faint">{meta.unit === '%' ? 'percentage' : 'per 90 mins'}</div>
                  </div>
                  <div className="font-display font-bold text-base text-chalk tnum w-12 sm:w-16 text-right">
                    {formatStat(raw, meta.isPercent)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <StatBar value={pct} />
                  </div>
                  <div className="hidden sm:block w-16 text-right">
                    <span className="text-xs font-bold text-chalk-dim tnum">Top {topPercent(pct)}%</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
