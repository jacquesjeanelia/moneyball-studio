import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePlayer } from '@/hooks/usePlayers'
import { METRICS, METRIC_GROUPS, ROLE_METRICS, type Role } from '@/lib/metrics'
import { radarFor } from '@/lib/percentiles'
import type { MetricKey } from '@/api/types'
import { PageTransition } from '@/components/PageTransition'
import { SmartImage } from '@/components/SmartImage'
import { PositionPill, StatBar } from '@/components/primitives'
import { PositionPitch } from '@/components/PositionPitch'
import { StatTable } from '@/components/StatTable'
import { RadarChart } from '@/components/RadarChart'
import { ErrorState, Spinner } from '@/components/states'
import { formatMarketValue, categoryColor, topPercent, CATEGORY_COLORS } from '@/lib/format'

export function PlayerPage() {
  const { id } = useParams()
  const playerId = id ? Number(id) : undefined
  const navigate = useNavigate()

  const { data: player, isLoading, isError, error, refetch } = usePlayer(playerId)

  // Radar view toggle
  const playerRole = (player?.role as Role | null) ?? null
  const keyToCategory = useMemo(() => {
    const map = new Map<MetricKey, string>()
    for (const g of METRIC_GROUPS) {
      for (const k of g.keys) map.set(k, g.category)
    }
    return map
  }, [])
  const radarViews = useMemo(() => {
    const views: { key: string; label: string; keys: MetricKey[] }[] = []
    if (playerRole && ROLE_METRICS[playerRole]) {
      views.push({ key: playerRole, label: playerRole, keys: ROLE_METRICS[playerRole] })
    }
    METRIC_GROUPS.forEach((g) => {
      const short = g.title === 'Possession & Progression' ? 'Possession'
        : g.title === 'Defending & Physical' ? 'Defending'
        : g.title
      views.push({ key: g.category, label: short, keys: g.keys })
    })
    return views
  }, [playerRole])
  const [radarView, setRadarView] = useState(radarViews[0]?.key ?? '')
  const categoryOrder = ['Attack', 'Midfield', 'Defender']
  const activeRadarKeys = useMemo(() => {
    const keys = radarViews.find((v) => v.key === radarView)?.keys ?? []
    // Role view: reorder keys so attacking stats group together, then possession, then defending
    if (radarView === playerRole) {
      return [...keys].sort((a, b) => {
        const ca = categoryOrder.indexOf(keyToCategory.get(a) ?? '')
        const cb = categoryOrder.indexOf(keyToCategory.get(b) ?? '')
        return ca - cb
      })
    }
    return keys
  }, [radarView, radarViews, playerRole, keyToCategory])
  // Build a map from metric short label -> colour for the role view axis labels
  const activeTickColors = useMemo(() => {
    const map: Record<string, string> = {}
    if (radarView === playerRole) {
      for (const g of METRIC_GROUPS) {
        const color = CATEGORY_COLORS[g.category] ?? 'var(--color-chalk-dim)'
        for (const k of activeRadarKeys) {
          if (keyToCategory.get(k) === g.category) {
            const meta = METRICS.find((m) => m.key === k)
            if (meta) map[meta.short] = color
          }
        }
      }
    }
    return map
  }, [radarView, playerRole, activeRadarKeys, keyToCategory])
  const activeRadarSeries = useMemo(() => {
    const pts = radarFor(player?.season_stats ?? null, activeRadarKeys)
    const color = categoryColor(player?.category ?? null)
    return [{ name: player?.name ?? '', color, points: pts }]
  }, [player, activeRadarKeys])

  // All stats percentile points for standout traits
  const radarPoints = useMemo(() => radarFor(player?.season_stats ?? null), [player])

  if (isLoading) return <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-20"><Spinner label="Loading profile…" /></div>
  if (isError || !player)
    return (
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-20">
        <ErrorState message={(error as Error)?.message ?? 'Player not found.'} onRetry={() => refetch()} />
      </div>
    )

  const accent = categoryColor(player.category)

  return (
    <PageTransition>
      {/* Hero band */}
      <section className="relative overflow-hidden border-b border-ink-700">
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-ink-850 via-ink-900 to-ink-900" />
          <div
            className="absolute -top-20 -right-10 h-80 w-80 rounded-full blur-3xl opacity-25"
            style={{ background: accent }}
          />
        </div>

        <div className="max-w-[1400px] mx-auto px-5 sm:px-8 pt-6 pb-8">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-chalk-dim hover:text-chalk transition-colors mb-6"
          >
            <BackGlyph /> Back
          </button>

          <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
            {/* Photo */}
            <motion.div
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="relative shrink-0"
            >
              <div className="h-32 w-32 sm:h-44 sm:w-44 lg:h-48 lg:w-48 rounded-2xl overflow-hidden surface-raised ring-1 ring-white/10">
                <SmartImage
                  src={player.photo_url}
                  alt={player.name}
                  fallbackName={player.name}
                  className="h-full w-full"
                  imgClassName="object-cover object-top"
                />
              </div>
              {player.club?.logo_url && (
                <div className="absolute -bottom-3 -right-3 h-12 w-12 sm:h-14 sm:w-14 rounded-xl bg-ink-900 p-1.5 ring-1 ring-white/10 shadow-card">
                  <SmartImage src={player.club.logo_url} alt={player.club.name} fallback="icon" fit="contain" className="h-full w-full" />
                </div>
              )}
            </motion.div>

            {/* Identity */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <PositionPill position={player.main_position} category={player.category} />
                {player.country?.flag_url && (
                  <div className="flex items-center gap-1.5">
                    <span className="h-5 w-7">
                      <SmartImage src={player.country.flag_url} alt={player.country.name} fallback="hidden" fit="contain" className="h-full w-full" />
                    </span>
                    <span className="text-sm text-chalk-dim">{player.country.name}</span>
                  </div>
                )}
              </div>

              <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-5xl tracking-tight text-balance break-words">
                {player.name}
              </h1>

              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-chalk-dim">
                {player.club && (
                  <span className="font-semibold text-chalk">{player.club.name}</span>
                )}
                {player.club?.league && <Meta label={player.club.league.name} />}
                {player.age != null && <Meta label={`${player.age} years`} />}
                {player.height_cm != null && <Meta label={`${player.height_cm} cm`} />}
                {player.preferred_foot && <Meta label={`${cap(player.preferred_foot)} footed`} />}
              </div>

              {/* Stat ribbon */}
              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
                <RibbonStat label="Market value" value={formatMarketValue(player.current_market_value_eur)} accent={accent} />
              </div>
            </div>

            {/* Similar CTA */}
            <div className="w-full lg:w-auto">
              <Link
                to={`/players/${player.id}/similar`}
                className="group flex items-center justify-center gap-2 rounded-xl accent-bar px-5 py-3 font-bold text-white shadow-glow hover:brightness-110 transition w-full lg:w-auto"
              >
                <SparkGlyph />
                Find similar players
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Body */}
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-10 grid grid-cols-1 lg:grid-cols-[1fr_minmax(360px,420px)] gap-8 lg:gap-12">
        {/* Stat table */}
        <div>
          <SectionTitle>Season breakdown</SectionTitle>
          <div className="text-[11px] text-chalk-faint font-semibold uppercase tracking-wider mb-3">
            {player.season_stats?.minutes_played
              ? `${player.season_stats.minutes_played.toLocaleString()} minutes played`
              : 'No minutes recorded'}
          </div>
          {player.season_stats ? (
            <StatTable stats={player.season_stats} />
          ) : (
            <div className="rounded-xl surface p-8 text-center text-chalk-faint">No stats recorded for this season.</div>
          )}
        </div>

        {/* Right column: positions + radar */}
        <div className="lg:sticky lg:top-24 self-start w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-x-8 gap-y-7">
          {/* Positions */}
          <div>
            <SectionTitle>Positions</SectionTitle>
            <div className="rounded-2xl surface p-5 mt-1">
              <PositionPitch main={player.main_position} alternates={player.alternate_positions} category={player.category} />
            </div>
          </div>

          {/* Performance profile — single chart with view toggle */}
          <div>
            <SectionTitle>Performance profile</SectionTitle>
            <div className="rounded-2xl surface p-3 sm:p-4 mt-1">
              <div className="flex justify-center mb-3">
                <div className="inline-flex items-center rounded-lg surface p-0.5">
                  {radarViews.map((v) => {
                    const active = radarView === v.key
                    const isRole = v.key === playerRole
                    const color = isRole
                      ? categoryColor(player?.category ?? null)
                      : CATEGORY_COLORS[v.key] ?? 'var(--color-chalk)'
                    return (
                      <button
                        key={v.key}
                        onClick={() => setRadarView(v.key)}
                        aria-pressed={active}
                        className="relative px-3 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap"
                        style={{ color: active ? '#fff' : 'var(--color-chalk-dim)' }}
                      >
                        {active && (
                          <motion.span
                            layoutId="radar-view-pill"
                            className="absolute inset-0 rounded-md"
                            style={{ background: `color-mix(in srgb, ${color} 30%, var(--color-ink-600))` }}
                            transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                          />
                        )}
                        <span className="relative">{v.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
              <RadarChart
                series={activeRadarSeries}
                tickColors={radarView === playerRole ? activeTickColors : undefined}
                height={340}
              />
            </div>

            {/* Standout traits */}
            <div className="mt-6">
              <h4 className="text-xs font-bold uppercase tracking-widest text-chalk-faint mb-2.5">Standout traits</h4>
              <div className="space-y-2">
                {[...radarPoints]
                  .sort((a, b) => b.value - a.value)
                  .slice(0, 3)
                  .map((p) => (
                    <div key={p.key} className="flex items-center gap-3">
                      <span className="w-32 sm:w-40 shrink-0 text-sm text-chalk leading-tight">{p.label}</span>
                      <StatBar value={p.value} text={`Top ${topPercent(p.value)}%`} />
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}

function Meta({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-1 w-1 rounded-full bg-ink-500" />
      {label}
    </span>
  )
}

function RibbonStat({ label, value, accent, hint }: { label: string; value: string; accent: string; hint?: string }) {
  return (
    <div className="rounded-xl surface px-3.5 py-3" title={hint}>
      <div className="flex items-center gap-1 text-[11px] uppercase tracking-wider text-chalk-faint mb-0.5">
        {label}
        {hint && <InfoGlyph />}
      </div>
      <div className="font-display font-bold text-lg text-chalk tnum" style={{ color: accent }}>
        {value}
      </div>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="flex items-center gap-2.5 font-display font-bold text-2xl mb-1">
      <span className="h-5 w-1 accent-bar rounded-full" />
      {children}
    </h2>
  )
}

function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function BackGlyph() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SparkGlyph() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
    </svg>
  )
}

function InfoGlyph() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" className="opacity-60">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" strokeLinecap="round" />
    </svg>
  )
}
