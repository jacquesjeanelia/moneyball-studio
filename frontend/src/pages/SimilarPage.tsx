import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAllPlayers, usePlayer, useSimilar, cohortFor } from '@/hooks/usePlayers'
import { buildPercentileTable, overallRating, radarFor } from '@/lib/percentiles'
import type { PlayerStats, SimilarPlayer } from '@/api/types'
import { PageTransition } from '@/components/PageTransition'
import { SmartImage } from '@/components/SmartImage'
import { PositionPill } from '@/components/primitives'
import { ErrorState, Spinner, EmptyState } from '@/components/states'
import { formatMarketValue, formatSimilarity, categoryColor, parsePriceInput } from '@/lib/format'

/** Every role a player can fill (main + alternates), de-duplicated, main first. */
function playerPositions(p: { main_position: string | null; alternate_positions: string[] }): string[] {
  const out: string[] = []
  if (p.main_position) out.push(p.main_position)
  for (const alt of p.alternate_positions ?? []) if (!out.includes(alt)) out.push(alt)
  return out
}

export function SimilarPage() {
  const { id } = useParams()
  const playerId = id ? Number(id) : undefined
  const navigate = useNavigate()

  const { data: target } = usePlayer(playerId)
  const { data: similar, isLoading, isError, error, refetch } = useSimilar(playerId, 100)
  const { data: allPlayers } = useAllPlayers()

  const SIMILARITY_THRESHOLD = 0.75

  // Price filter: max market value in EUR.
  const [maxPrice, setMaxPrice] = useState<number | null>(null)

  // Position filter (multi-select). Empty = show every shared-position lookalike.
  const [activePositions, setActivePositions] = useState<string[]>([])

  // The target's own roles — these are the buttons the user can toggle.
  const targetPositions = useMemo(() => (target ? playerPositions(target) : []), [target])

  const togglePosition = (pos: string) =>
    setActivePositions((prev) => (prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]))

  // Overall-rating baseline: rate the target AND every candidate against the
  // target's positional cohort, so the rating *gap* on each row is comparable.
  // (Cosine ranks by style; this adds the quality/level the score can't show.)
  const cohort = useMemo(() => cohortFor(allPlayers, target?.category), [allPlayers, target?.category])
  const table = useMemo(() => buildPercentileTable(cohort), [cohort])
  const statsById = useMemo(() => {
    const m = new Map<number, PlayerStats | null>()
    for (const p of allPlayers ?? []) m.set(p.id, p.season_stats)
    return m
  }, [allPlayers])
  const ratingFor = (stats: PlayerStats | null) => overallRating(radarFor(stats, table))
  const targetRating = target ? ratingFor(target.season_stats) : null

  const filtered = useMemo(
    () =>
      (similar ?? []).filter((s) => {
        if (s.similarity_score < SIMILARITY_THRESHOLD) return false
        if (maxPrice != null && (s.player.current_market_value_eur ?? 0) > maxPrice) return false
        if (activePositions.length === 0) return true
        // Keep candidates who play at least one of the selected positions.
        const roles = playerPositions(s.player)
        return activePositions.some((p) => roles.includes(p))
      }),
    [similar, maxPrice, activePositions],
  )

  const accent = categoryColor(target?.category)

  return (
    <PageTransition>
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-8">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-chalk-dim hover:text-chalk transition-colors mb-6"
        >
          <BackGlyph /> Back
        </button>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-5 mb-7">
          <div>
            <h1 className="font-display font-extrabold text-3xl sm:text-4xl tracking-tight">
              Statistical lookalikes
            </h1>
            {/* <p className="mt-1.5 text-sm text-chalk-faint max-w-xl">
              Ranked by playing style. The <span className="text-chalk-dim font-semibold">vs target</span> figures show how each
              player's overall output and price compare — a close style match at a lower level or price is the value to chase.
            </p> */}
          </div>

          {/* Target chip */}
          {target && (
            <Link
              to={`/players/${target.id}`}
              className="flex items-center gap-3 rounded-xl surface px-3 py-2 hover:border-ink-500 transition-colors shrink-0"
            >
              <div className="h-10 w-10 rounded-lg overflow-hidden">
                <SmartImage src={target.photo_url} alt={target.name} fallbackName={target.name} className="h-full w-full" imgClassName="object-top" />
              </div>
              <div className="pr-1">
                <div className="text-[11px] text-chalk-faint uppercase tracking-wide">Comparing to</div>
                <div className="font-semibold text-chalk text-sm">{target.name}</div>
              </div>
            </Link>
          )}
        </div>

        {/* Position filter buttons */}
        {targetPositions.length > 0 && (
          <PositionFilter
            positions={targetPositions}
            active={activePositions}
            onToggle={togglePosition}
            onClear={() => setActivePositions([])}
            accent={accent}
          />
        )}

        <div className="flex flex-wrap items-stretch gap-2.5">
          <MaxPriceField value={maxPrice} onChange={setMaxPrice} />
        </div>

        {/* Results */}
        <div className="mt-7">
          {isLoading && <Spinner label="Computing similarity…" />}
          {isError && <ErrorState message={(error as Error)?.message ?? 'Could not load similar players.'} onRetry={() => refetch()} />}
          {!isLoading && !isError && filtered.length === 0 && (
            <EmptyState
              title="No players match these filters"
              hint="Lower the similarity threshold, raise the max price, or clear the position filter to surface more lookalikes."
            />
          )}
          {!isLoading && !isError && filtered.length > 0 && (
            <div className="space-y-3">
              {filtered.map((s, i) => (
                <SimilarRow
                  key={s.player.id}
                  item={s}
                  index={i}
                  targetId={target?.id}
                  accent={accent}
                  targetRating={targetRating}
                  candidateRating={ratingFor(statsById.get(s.player.id) ?? null)}
                  targetValue={target?.current_market_value_eur ?? null}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </PageTransition>
  )
}

// ---------------------------------------------------------------------------

function PositionFilter({
  positions,
  active,
  onToggle,
  onClear,
  accent,
}: {
  positions: string[]
  active: string[]
  onToggle: (pos: string) => void
  onClear: () => void
  accent: string
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <span className="text-xs font-bold uppercase tracking-wider text-chalk-faint mr-1">Positions</span>
      {positions.map((pos) => {
        const on = active.includes(pos)
        return (
          <button
            key={pos}
            onClick={() => onToggle(pos)}
            className="rounded-lg px-3 py-1.5 text-sm font-bold tracking-wide transition-colors ring-1"
            style={{
              background: on ? `color-mix(in srgb, ${accent} 22%, var(--color-ink-800))` : 'transparent',
              color: on ? '#fff' : 'var(--color-chalk-dim)',
              borderColor: 'transparent',
              boxShadow: on ? `inset 0 0 0 1px ${accent}` : 'inset 0 0 0 1px var(--color-ink-600)',
            }}
          >
            {pos}
          </button>
        )
      })}
      {active.length > 0 && (
        <button
          onClick={onClear}
          className="text-xs font-semibold text-chalk-faint hover:text-signal-400 transition-colors px-2 py-1.5"
        >
          Clear
        </button>
      )}
    </div>
  )
}


// ---------------------------------------------------------------------------

const MAX_PRICE_EUR = 500_000_000

function MaxPriceField({ value, onChange }: { value: number | null; onChange: (v: number | null) => void }) {
  const [raw, setRaw] = useState('')

  useEffect(() => {
    if (value === null) setRaw('')
  }, [value])

  const commit = (s: string) => {
    setRaw(s)
    const parsed = parsePriceInput(s)
    onChange(parsed === null ? null : Math.min(parsed, MAX_PRICE_EUR))
  }

  return (
    <div className="flex flex-col rounded-lg surface px-3 py-1.5 min-w-[8.5rem] transition-colors hover:border-ink-500 focus-within:border-signal-500/60">
      <span className="text-[10px] font-bold uppercase tracking-wider text-chalk-faint leading-none mb-1">Max price</span>
      <div className="flex items-center gap-1 text-sm font-semibold">
        <span className="text-chalk-faint">€</span>
        <input
          inputMode="numeric"
          value={raw}
          onChange={(e) => commit(e.target.value)}
          placeholder="Any"
          title="In thousands — type 500 for €500K, or use m for millions (e.g. 30m)"
          className="w-12 bg-transparent text-chalk placeholder:text-chalk-dim outline-none tnum"
        />
        {value != null && (
          <span className="ml-1 text-xs text-volt font-bold tnum border-l border-ink-600 pl-1.5">{formatMarketValue(value)}</span>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

function SimilarRow({
  item,
  index,
  targetId,
  accent,
  targetRating,
  candidateRating,
  targetValue,
}: {
  item: SimilarPlayer
  index: number
  targetId?: number
  accent: string
  targetRating: number | null
  candidateRating: number
  targetValue: number | null
}) {
  const p = item.player
  const pct = item.similarity_score
  const ratingGap = targetRating != null ?  candidateRating - targetRating: null
  const value = p.current_market_value_eur ?? null
  const valueGap = targetValue != null && value != null ? value - targetValue : null
  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.32, delay: Math.min(index * 0.03, 0.4) }}
      className="group flex items-center gap-3 sm:gap-4 rounded-xl surface px-3 sm:px-4 py-3 hover:border-ink-500 transition-colors"
    >
      {/* rank */}
      <div className="hidden sm:block w-7 text-center font-display font-bold text-chalk-faint tnum">{index + 1}</div>

      {/* photo + name -> profile */}
      <Link to={`/players/${p.id}`} className="flex items-center gap-3 flex-1 min-w-0">
        <div className="h-12 w-12 rounded-lg overflow-hidden shrink-0">
          <SmartImage src={p.photo_url} alt={p.name} fallbackName={p.name} className="h-full w-full" imgClassName="object-top" />
        </div>
        <div className="min-w-0">
          <div className="font-display font-bold text-chalk truncate group-hover:text-signal-400 transition-colors">
            {p.name}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-chalk-faint">
            {p.club?.logo_url && (
              <span className="h-5 w-5 shrink-0">
                <SmartImage src={p.club.logo_url} alt="" fallback="icon" fit="contain" className="h-full w-full" />
              </span>
            )}
            <span className="truncate">{p.club?.name ?? 'Free agent'}</span>
            {p.age != null && <span className="tnum">· {p.age}y</span>}
            {/* Price inline on phones, where the dedicated value column is hidden. */}
            <span className="sm:hidden font-bold text-volt tnum shrink-0">· {formatMarketValue(value)}</span>
          </div>
          {/* Quality/value gap vs target — inline on phones. */}
          <div className="sm:hidden mt-1 flex items-center gap-2">
            <GapBadge gap={ratingGap} suffix=" pts" />
            <ValueGapBadge gap={valueGap} />
          </div>
        </div>
      </Link>

      {/* position (hidden on small) */}
      <div className="hidden md:block">
        <PositionPill position={p.main_position} category={p.category} />
      </div>

      {/* quality + value gap vs target */}
      <div className="hidden sm:flex flex-col items-end gap-1 w-28">
        <GapBadge gap={ratingGap} suffix=" pts" />
        <ValueGapBadge gap={valueGap} />
        {/* <span className="text-[10px] text-chalk-faint uppercase tracking-wide">vs target</span> */}
      </div>

      {/* value */}
      <div className="hidden sm:block w-20 text-right">
        <div className="font-display font-bold text-volt text-sm tnum">{formatMarketValue(value)}</div>
      </div>

      {/* similarity score */}
      <div className="w-16 sm:w-24 text-right">
        <div className="font-display font-extrabold text-lg tnum" style={{ color: accent }}>
          {formatSimilarity(pct)}
        </div>
      </div>

      {/* compare CTA */}
      {targetId && (
        <Link
          to={`/compare/${targetId}/${p.id}`}
          className="shrink-0 inline-flex items-center gap-1.5 rounded-lg surface-raised px-3 py-2 text-xs font-bold text-chalk hover:bg-ink-700 hover:text-signal-400 transition-colors"
        >
          <CompareGlyph />
          <span className="hidden sm:inline">Compare</span>
        </Link>
      )}
    </motion.div>
  )
}

// Rating delta vs target: green if higher output, amber if lower, neutral if level.
function GapBadge({ gap, suffix = '' }: { gap: number | null; suffix?: string }) {
  if (gap == null) return null
  const sign = gap > 0 ? '+' : ''
  const color = gap > 0 ? 'var(--color-emerald)' : gap < 0 ? 'var(--color-amber)' : 'var(--color-chalk-faint)'
  return (
    <span className="text-xs font-bold tnum whitespace-nowrap" style={{ color }} title="Overall rating vs target">
      {gap === 0 ? 'same level' : `${sign}${gap}${suffix}`}
    </span>
  )
}

// Value delta vs target: green when cheaper (the bargain), amber when pricier.
function ValueGapBadge({ gap }: { gap: number | null }) {
  if (gap == null) return null
  if (gap === 0) return <span className="text-[11px] font-semibold text-chalk-faint whitespace-nowrap">same price</span>
  const cheaper = gap < 0
  const color = cheaper ? 'var(--color-emerald)' : 'var(--color-amber)'
  const sign = cheaper ? '+' : '-'
  const label = `${sign}${formatMarketValue(Math.abs(gap))}`
  return (
    <span className="text-[11px] font-semibold tnum whitespace-nowrap" style={{ color }} title="Market value vs target">
      {label}
    </span>
  )
}

function BackGlyph() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function CompareGlyph() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 3v18M5 8l-3 4 3 4M19 8l3 4-3 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
