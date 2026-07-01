// ============================================================================
// Formatting + small pure helpers
// ============================================================================

/** Compact market value: 30000000 -> "€30.0M", 850000 -> "€850K", 0 -> "—". */
export function formatMarketValue(eur: number | null | undefined): string {
  if (eur === null || eur === undefined || eur <= 0) return '—'
  if (eur >= 1_000_000) {
    const m = eur / 1_000_000
    return `€${m >= 100 ? Math.round(m) : m.toFixed(1)}M`
  }
  if (eur >= 1_000) return `€${Math.round(eur / 1_000)}K`
  return `€${eur}`
}

/** Full value with thousands separators: "€30,000,000". */
export function formatMarketValueFull(eur: number | null | undefined): string {
  if (eur === null || eur === undefined || eur <= 0) return 'Not available'
  return `€${eur.toLocaleString('en-US')}`
}

/** Format a stat value to a sensible precision. */
export function formatStat(value: number | null | undefined, isPercent: boolean): string {
  if (value === null || value === undefined) return '—'
  if (isPercent) return `${value.toFixed(1)}%`
  return value.toFixed(2)
}

export function formatSimilarity(score: number): string {
  return `${(score * 100).toFixed(1)}%`
}

/**
 * Parse a free-typed price into EUR. A bare number is treated as **thousands**
 * (so "1" means €1K and sub-million players are reachable), while explicit
 * suffixes still win: "850k" -> 850000, "1.5m" -> 1500000.
 * Examples: "1" -> 1000, "500" -> 500000, "30m" -> 30000000, "850k" -> 850000.
 */
export function parsePriceInput(raw: string): number | null {
  const s = raw.trim().toLowerCase().replace(/[€,\s]/g, '')
  if (!s) return null
  const m = s.match(/^(\d*\.?\d+)(m|k|b)?$/)
  if (!m) return null
  const n = parseFloat(m[1])
  if (Number.isNaN(n)) return null
  switch (m[2]) {
    case 'b': return Math.round(n * 1_000_000_000)
    case 'm': return Math.round(n * 1_000_000)
    case 'k': return Math.round(n * 1_000)
    default: return Math.round(n * 1_000) // bare number = thousands
  }
}

/** Initials for avatar fallback. */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/** Deterministic accent colour from a string (for avatar fallbacks). */
export function colorFromString(s: string): string {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360
  return `hsl(${h}, 45%, 28%)`
}

export function cn(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ')
}

// Broad-role colours, keyed by `category` (Attack / Midfield / Defender).
export const CATEGORY_COLORS: Record<string, string> = {
  Attack: 'var(--color-signal-400)',
  Midfield: 'var(--color-cyan)',
  Defender: 'var(--color-volt)',
}

/** Colour for a player's broad role; falls back to neutral chalk. */
export function categoryColor(category: string | null | undefined): string {
  return (category && CATEGORY_COLORS[category]) || 'var(--color-chalk-faint)'
}

/**
 * Convert a percentile rank (0–100, higher = better) into a "top X%" figure
 * where a *smaller* number is better. 99th percentile -> top 1%, 50th -> top 50%.
 * Clamped to a 1% floor so an elite reading never shows the unintuitive "top 0%".
 */
export function topPercent(percentile: number): number {
  return Math.max(1, Math.round(100 - percentile))
}
