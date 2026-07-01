import { useMemo } from 'react'
import type { Category, MetricKey, PlayerSummary } from '@/api/types'
import { METRICS } from '@/lib/metrics'

// ============================================================================
// Client-side search + filter + sort over the cached player list.
// Designed for instant, as-you-type interaction (futbin-style).
// ============================================================================

export interface FilterState {
  query: string
  /** Broad role (Attack/Midfield/Defender) — the segmented control. */
  category: Category | null
  /** Specific role (CM, LW, CB...) — matches main OR alternate positions. */
  position: string | null
  leagueId: number | null
  countryId: number | null
  clubId: number | null
  maxPrice: number | null
  sort: SortKey
}

// Stat sorts are namespaced "stat:<metricKey>" so they coexist with the
// built-in sorts without widening every switch arm.
export type SortKey =
  | 'name'
  | 'value_desc'
  | 'value_asc'
  | 'age_asc'
  | 'age_desc'
  | `stat:${MetricKey}`

export const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: 'value_desc', label: 'Value: High → Low' },
  { key: 'value_asc', label: 'Value: Low → High' },
  { key: 'name', label: 'Name: A → Z' },
  { key: 'age_asc', label: 'Age: Youngest' },
  { key: 'age_desc', label: 'Age: Oldest' },
  // One descending sort per stat (best performers first).
  ...METRICS.map((m) => ({ key: `stat:${m.key}` as SortKey, label: `Stat: ${m.label}` })),
]

export const EMPTY_FILTERS: FilterState = {
  query: '',
  category: null,
  position: null,
  leagueId: null,
  countryId: null,
  clubId: null,
  maxPrice: null,
  sort: 'value_desc',
}

/** Normalize for accent-insensitive search ("rodri" matches "Rodri"). */
function norm(s: string): string {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
}

export interface FacetOption {
  id: number
  name: string
  logo?: string | null
  count: number
  /** Owning league id — set for club options so the club filter can be league-gated. */
  leagueId?: number | null
}

export interface Facets {
  leagues: FacetOption[]
  countries: FacetOption[]
  clubs: FacetOption[]
  /** Broad roles for the segmented control. */
  categories: { key: Category; count: number }[]
  /** Specific position codes (CM, LW...) for the position dropdown. */
  positions: { key: string; count: number }[]
}

/** Every specific role a player can fill (main + alternates), de-duplicated. */
function playerPositions(p: PlayerSummary): string[] {
  const set = new Set<string>()
  if (p.main_position) set.add(p.main_position)
  for (const alt of p.alternate_positions ?? []) set.add(alt)
  return [...set]
}

/** Derive available filter options + counts from the full dataset. */
export function useFacets(players: PlayerSummary[] | undefined): Facets {
  return useMemo(() => {
    const leagues = new Map<number, FacetOption>()
    const countries = new Map<number, FacetOption>()
    const clubs = new Map<number, FacetOption>()
    const categories = new Map<Category, number>()
    const positions = new Map<string, number>()

    for (const p of players ?? []) {
      const lg = p.club?.league
      if (lg) {
        const e = leagues.get(lg.id) ?? { id: lg.id, name: lg.name, logo: lg.logo_url, count: 0 }
        e.count++
        leagues.set(lg.id, e)
      }
      if (p.club) {
        const e = clubs.get(p.club.id) ?? { id: p.club.id, name: p.club.name, logo: p.club.logo_url, count: 0, leagueId: p.club.league?.id ?? null }
        e.count++
        clubs.set(p.club.id, e)
      }
      if (p.country) {
        const e = countries.get(p.country.id) ?? { id: p.country.id, name: p.country.name, logo: p.country.flag_url, count: 0 }
        e.count++
        countries.set(p.country.id, e)
      }
      if (p.category) {
        const k = p.category as Category
        categories.set(k, (categories.get(k) ?? 0) + 1)
      }
      // A player counts once per distinct role he can play (main or alternate).
      for (const pos of playerPositions(p)) {
        positions.set(pos, (positions.get(pos) ?? 0) + 1)
      }
    }

    return {
      leagues: [...leagues.values()].sort((a, b) => b.count - a.count),
      countries: [...countries.values()].sort((a, b) => b.count - a.count),
      clubs: [...clubs.values()].sort((a, b) => a.name.localeCompare(b.name)),
      categories: (['Attack', 'Midfield', 'Defender'] as Category[])
        .map((key) => ({ key, count: categories.get(key) ?? 0 }))
        .filter((x) => x.count > 0),
      positions: [...positions.entries()]
        .map(([key, count]) => ({ key, count }))
        .sort((a, b) => b.count - a.count),
    }
  }, [players])
}

/** Apply filters + search + sort. */
export function useFilteredPlayers(players: PlayerSummary[] | undefined, f: FilterState): PlayerSummary[] {
  return useMemo(() => {
    if (!players) return []
    const q = norm(f.query.trim())
    const terms = q.split(/\s+/).filter(Boolean)

    let out = players.filter((p) => {
      if (f.category && p.category !== f.category) return false
      // Specific position matches the main role OR any alternate role.
      if (f.position && !playerPositions(p).includes(f.position)) return false
      if (f.leagueId && p.club?.league?.id !== f.leagueId) return false
      if (f.countryId && p.country?.id !== f.countryId) return false
      if (f.clubId && p.club?.id !== f.clubId) return false
      if (f.maxPrice != null && (p.current_market_value_eur ?? 0) > f.maxPrice) return false
      if (terms.length) {
        // Search matches the player name only.
        const hay = norm(p.name)
        if (!terms.every((t) => hay.includes(t))) return false
      }
      return true
    })

    out = sortPlayers(out, f.sort)
    return out
  }, [players, f])
}

function sortPlayers(players: PlayerSummary[], sort: SortKey): PlayerSummary[] {
  const arr = [...players]
  if (sort.startsWith('stat:')) {
    const key = sort.slice(5) as MetricKey
    // Best first; players missing the stat sink to the bottom.
    return arr.sort((a, b) => (b.season_stats?.[key] ?? -Infinity) - (a.season_stats?.[key] ?? -Infinity))
  }
  switch (sort) {
    case 'name':
      return arr.sort((a, b) => a.name.localeCompare(b.name))
    case 'value_desc':
      return arr.sort((a, b) => (b.current_market_value_eur ?? 0) - (a.current_market_value_eur ?? 0))
    case 'value_asc':
      return arr.sort((a, b) => (a.current_market_value_eur ?? 0) - (b.current_market_value_eur ?? 0))
    case 'age_asc':
      return arr.sort((a, b) => (a.age ?? 999) - (b.age ?? 999))
    case 'age_desc':
      return arr.sort((a, b) => (b.age ?? 0) - (a.age ?? 0))
    default:
      return arr
  }
}
