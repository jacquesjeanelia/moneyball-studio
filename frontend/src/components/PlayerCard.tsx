import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import type { PlayerSummary } from '@/api/types'
import { SmartImage } from './SmartImage'
import { PositionPill } from './primitives'
import { formatMarketValue, formatStat } from '@/lib/format'
import { METRICS } from '@/lib/metrics'

interface PlayerCardProps {
  player: PlayerSummary
  index: number
}

// Three headline metrics surfaced on hover, chosen per position.
const HOVER_METRICS: Record<string, { key: (typeof METRICS)[number]['key']; short: string }[]> = {
  Attack: [
    { key: 'npxg_per90', short: 'npxG' },
    { key: 'xa_per90', short: 'xA' },
    { key: 'shots_on_target_per90', short: 'SoT' },
  ],
  Midfield: [
    { key: 'xa_per90', short: 'xA' },
    { key: 'successful_pass_rate', short: 'Pass%' },
    { key: 'successful_dribbles_per90', short: 'Drb' },
  ],
  Defender: [
    { key: 'tackles_per90', short: 'Tkl' },
    { key: 'interceptions_per90', short: 'Int' },
    { key: 'aerial_duel_success_rate', short: 'Aerial%' },
  ],
}

export function PlayerCard({ player, index }: PlayerCardProps) {
  const cat = player.category ?? 'Midfield'
  const hoverMetrics = HOVER_METRICS[cat] ?? HOVER_METRICS.Midfield
  const stats = player.season_stats

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index * 0.018, 0.4), ease: [0.22, 1, 0.36, 1] }}
    >
      <Link
        to={`/players/${player.id}`}
        className="group relative block rounded-card surface overflow-hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-signal-500"
      >
        {/* Top: photo + club crest + value */}
        <div className="relative aspect-[4/5] overflow-hidden bg-ink-850">
          <SmartImage
            src={player.photo_url}
            alt={player.name}
            fallbackName={player.name}
            className="absolute inset-0"
            imgClassName="object-cover object-top transition-transform duration-[600ms] ease-out group-hover:scale-[1.06]"
          />
          {/* gradient scrim */}
          <div className="absolute inset-0 bg-gradient-to-t from-ink-900 via-ink-900/10 to-transparent" />

          {/* club crest top-left */}
          {player.club?.logo_url && (
            <div className="absolute top-2.5 left-2.5 h-9 w-9 rounded-md bg-ink-900/70 backdrop-blur p-1 ring-1 ring-white/10">
              <SmartImage src={player.club.logo_url} alt={player.club.name} fallback="icon" fit="contain" className="h-full w-full" />
            </div>
          )}
          {/* market value top-right */}
          <div className="absolute top-2.5 right-2.5 rounded-md bg-ink-900/80 backdrop-blur px-2 py-1 text-xs font-bold text-volt tnum ring-1 ring-white/10">
            {formatMarketValue(player.current_market_value_eur)}
          </div>

          {/* country flag + position bottom row (always visible) */}
          <div className="absolute bottom-2.5 left-2.5 right-2.5 flex items-center justify-between">
            <PositionPill position={player.main_position} category={player.category} />
            {player.country?.flag_url && (
              <div className="h-6 w-9">
                <SmartImage src={player.country.flag_url} alt={player.country.name} fallback="hidden" fit="contain" className="h-full w-full" />
              </div>
            )}
          </div>
        </div>

        {/* Name plate */}
        <div className="px-3 pt-2.5 pb-3">
          <div className="flex items-center gap-1.5 text-[11px] text-chalk-faint mb-0.5">
            <span className="truncate">{player.club?.name ?? 'Free agent'}</span>
            {player.age != null && (
              <>
                <span className="text-ink-500">·</span>
                <span className="tnum shrink-0">{player.age}y</span>
              </>
            )}
          </div>
          <h3 className="font-display font-bold text-[15px] leading-tight text-chalk truncate">{player.name}</h3>
        </div>

        {/* Hover summary overlay */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 translate-y-full opacity-0 transition-all duration-300 ease-out group-hover:translate-y-0 group-hover:opacity-100">
          <div className="m-2 rounded-xl surface-raised shadow-card p-3 backdrop-blur">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase tracking-widest text-chalk-faint">Season 24/25</span>
              <span className="text-[10px] font-bold uppercase tracking-widest text-signal-400">View profile →</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {hoverMetrics.map((m) => {
                const meta = METRICS.find((x) => x.key === m.key)!
                return (
                  <div key={m.key} className="rounded-lg bg-ink-900/60 px-2 py-1.5 text-center">
                    <div className="text-[10px] text-chalk-faint uppercase tracking-wide truncate">{m.short}</div>
                    <div className="font-display font-bold text-sm text-chalk tnum">
                      {formatStat(stats?.[m.key], meta.isPercent)}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* hover ring */}
        <div className="pointer-events-none absolute inset-0 rounded-card ring-0 ring-signal-500/0 transition-all duration-300 group-hover:ring-1 group-hover:ring-signal-500/40" />
      </Link>
    </motion.div>
  )
}
