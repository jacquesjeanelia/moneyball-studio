import type { MetricKey, PlayerStats } from '@/api/types'
import { METRICS } from './metrics'

// ============================================================================
// Percentile engine (database-backed)
// Percentiles are pre-computed per-role in the database and served as
// *_percentile fields on PlayerStats. No client-side cohort ranking needed.
// ============================================================================

/** Map a stat key to the per90-percentile field name on PlayerStats.
 *  Keys ending in `_per90` replace that suffix with `_per_90_percentile`;
 *  everything else appends `_percentile`. */
export function percentileKey(key: MetricKey): keyof PlayerStats {
  if (key.endsWith('_per90')) {
    return (key.replace('_per90', '_per_90_percentile') as keyof PlayerStats)
  }
  return (`${key}_percentile` as keyof PlayerStats)
}

/** Map a stat key to the total-percentile field name on PlayerStats.
 *  Keys ending in `_per90` replace that suffix with `_percentile`;
 *  everything else appends `_percentile`. */
export function totalPercentileKey(key: MetricKey): keyof PlayerStats {
  if (key.endsWith('_per90')) {
    return (key.replace('_per90', '_percentile') as keyof PlayerStats)
  }
  return (`${key}_percentile` as keyof PlayerStats)
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

/** Produce radar points for one player using database-stored percentiles.
 *  When `keys` is provided, only those metrics are included. */
export function radarFor(
  stats: PlayerStats | null,
  keys?: MetricKey[],
): RadarPoint[] {
  const metrics = keys ? METRICS.filter((m) => keys.includes(m.key)) : METRICS
  return metrics.map((m) => {
    const raw = stats?.[m.key] ?? null
    const pctKey = percentileKey(m.key)
    const value = stats?.[pctKey] ?? 0
    return { key: m.key, label: m.label, short: m.short, value, raw }
  })
}
