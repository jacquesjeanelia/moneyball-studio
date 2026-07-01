import { useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAllPlayers, usePlayer, cohortFor } from '@/hooks/usePlayers'
import { buildPercentileTable, overallRating, radarFor, type RadarPoint } from '@/lib/percentiles'
import type { PlayerDetail } from '@/api/types'
import { PageTransition } from '@/components/PageTransition'
import { SmartImage } from '@/components/SmartImage'
import { PositionPill } from '@/components/primitives'
import { RadarChart } from '@/components/RadarChart'
import { ErrorState, Spinner } from '@/components/states'
import { METRICS } from '@/lib/metrics'
import { formatStat, topPercent } from '@/lib/format'

const COLOR_A = 'var(--color-signal-400)'
const COLOR_B = 'var(--color-cyan)'

export function ComparePage() {
  const { idA, idB } = useParams()
  const navigate = useNavigate()
  const a = idA ? Number(idA) : undefined
  const b = idB ? Number(idB) : undefined

  const qa = usePlayer(a)
  const qb = usePlayer(b)
  const { data: allPlayers } = useAllPlayers()

  const playerA = qa.data
  const playerB = qb.data

  // Percentiles are computed against player A's category cohort so the
  // axes share a consistent baseline (most comparisons are same-role).
  const cohort = useMemo(() => cohortFor(allPlayers, playerA?.category), [allPlayers, playerA?.category])
  const table = useMemo(() => buildPercentileTable(cohort), [cohort])

  const radarA = useMemo(() => radarFor(playerA?.season_stats ?? null, table), [playerA, table])
  const radarB = useMemo(() => radarFor(playerB?.season_stats ?? null, table), [playerB, table])

  const isLoading = qa.isLoading || qb.isLoading
  const isError = qa.isError || qb.isError

  if (isLoading)
    return (
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-20">
        <Spinner label="Loading comparison…" />
      </div>
    )
  if (isError || !playerA || !playerB)
    return (
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-20">
        <ErrorState
          message={(qa.error as Error)?.message ?? (qb.error as Error)?.message ?? 'Could not load both players.'}
          onRetry={() => {
            qa.refetch()
            qb.refetch()
          }}
        />
      </div>
    )

  const ratingA = overallRating(radarA)
  const ratingB = overallRating(radarB)

  return (
    <PageTransition>
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-8">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-chalk-dim hover:text-chalk transition-colors mb-6"
        >
          <BackGlyph /> Back
        </button>

        <h1 className="font-display font-extrabold text-3xl sm:text-4xl tracking-tight mb-1">Head to head</h1>

        {/* Player headers */}
        <div className="grid grid-cols-[1fr_auto_1fr] gap-3 sm:gap-6 items-center mb-8">
          <PlayerHeader player={playerA} color={COLOR_A} rating={ratingA} align="left" />
          <div className="font-display font-extrabold text-2xl sm:text-4xl text-chalk-faint select-none">VS</div>
          <PlayerHeader player={playerB} color={COLOR_B} rating={ratingB} align="right" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,460px)_1fr] gap-8 lg:gap-12">
          {/* Overlaid radar */}
          <div className="lg:sticky lg:top-24 self-start">
            <div className="rounded-2xl surface p-4">
              <RadarChart
                series={[
                  { name: playerA.name, color: COLOR_A, points: radarA },
                  { name: playerB.name, color: COLOR_B, points: radarB },
                ]}
                height={400}
              />
              <div className="flex items-center justify-center gap-5 text-xs">
                <LegendDot color={COLOR_A} label={playerA.name} />
                <LegendDot color={COLOR_B} label={playerB.name} />
              </div>
            </div>
          </div>

          {/* Metric-by-metric comparison */}
          <div>
            <h2 className="flex items-center gap-2.5 font-display font-bold text-2xl mb-4">
              <span className="h-5 w-1 accent-bar rounded-full" />
              Metric breakdown
            </h2>
            <div className="rounded-xl surface divide-y divide-ink-700/70">
              {METRICS.map((m, i) => (
                <CompareRow
                  key={m.key}
                  label={m.label}
                  isPercent={m.isPercent}
                  pointA={radarA[i]}
                  pointB={radarB[i]}
                  rawA={playerA.season_stats?.[m.key] ?? null}
                  rawB={playerB.season_stats?.[m.key] ?? null}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}

// ---------------------------------------------------------------------------

function PlayerHeader({
  player,
  color,
  rating,
  align,
}: {
  player: PlayerDetail
  color: string
  rating: number
  align: 'left' | 'right'
}) {
  const right = align === 'right'
  return (
    <Link
      to={`/players/${player.id}`}
      className={`group flex flex-col items-center text-center gap-2 sm:gap-4 sm:flex-row sm:text-left ${right ? 'sm:flex-row-reverse sm:text-right' : ''}`}
    >
      <div className="relative shrink-0">
        <div className="h-14 w-14 sm:h-20 sm:w-20 rounded-xl overflow-hidden ring-2" style={{ borderColor: color, boxShadow: `0 0 0 2px ${color}` }}>
          <SmartImage src={player.photo_url} alt={player.name} fallbackName={player.name} className="h-full w-full" imgClassName="object-top" />
        </div>
        {player.club?.logo_url && (
          <div className={`absolute -bottom-2 h-6 w-6 sm:h-7 sm:w-7 rounded-md bg-ink-900 p-1 ring-1 ring-white/10 shadow-card ${right ? '-left-2' : '-right-2'}`}>
            <SmartImage src={player.club.logo_url} alt={player.club.name} fallback="icon" fit="contain" className="h-full w-full" />
          </div>
        )}
      </div>
      <div className={`min-w-0 w-full flex flex-col items-center sm:items-start ${right ? 'sm:items-end' : ''}`}>
        <div className={`flex items-center gap-2 ${right ? 'sm:flex-row-reverse' : ''}`}>
          <PositionPill position={player.main_position} category={player.category} />
        </div>
        <h3 className="font-display font-bold text-base sm:text-xl text-chalk truncate max-w-full group-hover:text-signal-400 transition-colors mt-1">
          {player.name}
        </h3>
        <div className={`flex items-center gap-2 text-xs text-chalk-faint max-w-full ${right ? 'sm:flex-row-reverse' : ''}`}>
          <span className="truncate">{player.club?.name}</span>
        </div>
        <div className={`mt-1.5 flex items-center gap-2 ${right ? 'sm:flex-row-reverse' : ''}`}>
          <span className="font-display font-extrabold text-xl sm:text-2xl tnum whitespace-nowrap" style={{ color }}>
            Top {topPercent(rating)}%
          </span>
        </div>
      </div>
    </Link>
  )
}

function CompareRow({
  label,
  isPercent,
  pointA,
  pointB,
  rawA,
  rawB,
}: {
  label: string
  isPercent: boolean
  pointA: RadarPoint
  pointB: RadarPoint
  rawA: number | null
  rawB: number | null
}) {
  const aWins = pointA.value > pointB.value
  const bWins = pointB.value > pointA.value
  const total = Math.max(pointA.value + pointB.value, 1)
  const aShare = (pointA.value / total) * 100

  return (
    <div className="px-3.5 py-3">
      <div className="flex items-center justify-between text-sm mb-1.5">
        <span className={`font-display font-bold tnum ${aWins ? 'text-chalk' : 'text-chalk-faint'}`}>
          {formatStat(rawA, isPercent)}
        </span>
        <span className="text-xs font-semibold text-chalk-dim uppercase tracking-wide text-center px-2">{label}</span>
        <span className={`font-display font-bold tnum ${bWins ? 'text-chalk' : 'text-chalk-faint'}`}>
          {formatStat(rawB, isPercent)}
        </span>
      </div>
      {/* dual bar */}
      <div className="flex items-center gap-1 h-2">
        <div className="flex-1 flex justify-end">
          <div className="h-full rounded-l-full transition-[width] duration-500" style={{ width: `${aShare}%`, background: COLOR_A, opacity: aWins ? 1 : 0.5 }} />
        </div>
        <div className="flex-1">
          <div className="h-full rounded-r-full transition-[width] duration-500" style={{ width: `${100 - aShare}%`, background: COLOR_B, opacity: bWins ? 1 : 0.5 }} />
        </div>
      </div>
      <div className="flex items-center justify-between text-[10px] text-chalk-faint tnum mt-1">
        <span>Top {topPercent(pointA.value)}%</span>
        <span>Top {topPercent(pointB.value)}%</span>
      </div>
    </div>
  )
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-chalk-dim">
      <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
      <span className="truncate max-w-[140px]">{label}</span>
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
