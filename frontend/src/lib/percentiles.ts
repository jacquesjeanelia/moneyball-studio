import type { MetricKey, PlayerStats, PlayerSummary } from '@/api/types'
import { METRICS } from './metrics'

// ============================================================================
// Percentile engine
// Radars are most meaningful when a player's raw stats are expressed as
// percentile ranks against positional peers (the FBref/StatsBomb convention).
// We compute these client-side from the full player list we already cache.
// ============================================================================

export type PercentileTable = Map<MetricKey, number[]> // sorted ascending values per metric

/** Build sorted value arrays per metric for a cohort (e.g. all Attackers). */
export function buildPercentileTable(players: PlayerSummary[]): PercentileTable {
  const table: PercentileTable = new Map()
  for (const { key } of METRICS) {
    const values: number[] = []
    for (const p of players) {
      const v = p.season_stats?.[key]
      if (typeof v === 'number' && !Number.isNaN(v)) values.push(v) 
    }
    values.sort((a, b) => a - b)
    table.set(key, values)
  }
  return table
}

/** Percentile (0–100) of `value` within a sorted ascending array. */
export function percentileOf(sorted: number[], value: number): number {
  if (sorted.length === 0) return 0
  // count of values strictly less + half of equal (mid-rank) for stability
  let lo = 0
  let hi = sorted.length
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (sorted[mid] < value) lo = mid + 1
    else hi = mid
  }
  const below = lo
  let equal = 0
  while (below + equal < sorted.length && sorted[below + equal] === value) equal++
  const rank = below + equal / 2
  return Math.round((rank / sorted.length) * 100)
}

export interface RadarPoint {
  key: MetricKey
  label: string
  short: string
  /** percentile 0–100 */
  value: number
  /** raw stat value */
  raw: number | null
}

/** Produce radar points for one player against a percentile table.
 *  When `keys` is provided, only those metrics are included (used for grouped
 *  radar charts). Otherwise all METRICS are returned. */
export function radarFor(
  stats: PlayerStats | null,
  table: PercentileTable,
  keys?: MetricKey[],
): RadarPoint[] {
  const metrics = keys ? METRICS.filter((m) => keys.includes(m.key)) : METRICS
  return metrics.map((m) => {
    const raw = stats?.[m.key] ?? null
    const sorted = table.get(m.key) ?? []
    const value = raw === null ? 0 : percentileOf(sorted, raw)
    return { key: m.key, label: m.label, short: m.short, value, raw }
  })
}

/** Average percentile across all metrics — a quick "overall" score. */
export function overallRating(points: RadarPoint[]): number {
  if (points.length === 0) return 0
  return Math.round(points.reduce((s, p) => s + p.value, 0) / points.length)
}
