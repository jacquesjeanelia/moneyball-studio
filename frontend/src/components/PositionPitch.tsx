import { categoryColor } from '@/lib/format'

// ============================================================================
// Position pitch — plots a player's main + alternate roles on a vertical pitch.
// Coordinates are percentages of the pitch box (x: left→right, y: top→bottom,
// where the top is the attacking third). Codes mirror the dataset's vocabulary.
// ============================================================================

const POSITION_COORDS: Record<string, { x: number; y: number }> = {
  // Forwards (attacking third, top)
  ST: { x: 50, y: 12 },
  CF: { x: 50, y: 16 },
  LW: { x: 18, y: 18 },
  RW: { x: 82, y: 18 },
  // Attacking midfield
  CAM: { x: 50, y: 34 },
  AM: { x: 50, y: 34 },
  LM: { x: 14, y: 44 },
  RM: { x: 86, y: 44 },
  // Central / defensive midfield
  CM: { x: 50, y: 50 },
  CDM: { x: 50, y: 64 },
  DM: { x: 50, y: 64 },
  // Wing-backs (wide, between mid and defence)
  LWB: { x: 12, y: 64 },
  RWB: { x: 88, y: 64 },
  // Defence
  LB: { x: 18, y: 80 },
  RB: { x: 82, y: 80 },
  CB: { x: 50, y: 84 },
  // Keeper
  GK: { x: 50, y: 95 },
}

const POSITION_NAMES: Record<string, string> = {
  ST: 'Striker',
  CF: 'Centre Forward',
  LW: 'Left Winger',
  RW: 'Right Winger',
  CAM: 'Attacking Midfield',
  AM: 'Attacking Midfield',
  LM: 'Left Midfield',
  RM: 'Right Midfield',
  CM: 'Central Midfield',
  CDM: 'Defensive Midfield',
  DM: 'Defensive Midfield',
  LWB: 'Left Wing-Back',
  RWB: 'Right Wing-Back',
  LB: 'Left Back',
  RB: 'Right Back',
  CB: 'Centre Back',
  GK: 'Goalkeeper',
}

export function positionName(code: string): string {
  return POSITION_NAMES[code] ?? code
}

interface PositionPitchProps {
  main: string | null
  alternates: string[]
  category?: string | null
}

export function PositionPitch({ main, alternates, category }: PositionPitchProps) {
  const accent = categoryColor(category)

  // De-dupe (a code never appears as both main and alternate) and keep only
  // codes we can actually plot.
  const seen = new Set<string>()
  const spots: { code: string; isMain: boolean }[] = []
  if (main && POSITION_COORDS[main]) {
    spots.push({ code: main, isMain: true })
    seen.add(main)
  }
  for (const code of alternates) {
    if (!seen.has(code) && POSITION_COORDS[code]) {
      spots.push({ code, isMain: false })
      seen.add(code)
    }
  }

  return (
    <div className="flex gap-5">
      {/* Pitch */}
      <div className="relative w-32 sm:w-36 shrink-0">
        <div
          className="relative w-full overflow-hidden rounded-xl ring-1 ring-white/10"
          style={{ aspectRatio: '2 / 3', background: 'linear-gradient(180deg, #11261a, #0c1b13)' }}
        >
          <PitchLines />
          {spots.map((s) => {
            const { x, y } = POSITION_COORDS[s.code]
            return (
              <div
                key={s.code}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${x}%`, top: `${y}%` }}
              >
                <span
                  className="flex items-center justify-center rounded-full font-display font-bold text-[10px] leading-none ring-2 ring-ink-900"
                  style={{
                    width: s.isMain ? 30 : 26,
                    height: s.isMain ? 30 : 26,
                    background: s.isMain ? accent : 'color-mix(in srgb, ' + accent + ' 22%, var(--color-ink-800))',
                    color: s.isMain ? '#06120b' : 'var(--color-chalk)',
                    boxShadow: s.isMain ? `0 0 14px color-mix(in srgb, ${accent} 60%, transparent)` : 'none',
                  }}
                >
                  {s.code}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        <ul className="space-y-2">
          {spots.map((s) => (
            <li key={s.code} className="flex items-center gap-2.5">
              <span
                className="flex items-center justify-center rounded-md font-display font-bold text-[10px] w-9 h-6 shrink-0 ring-1 ring-white/10"
                style={{
                  background: s.isMain ? accent : `color-mix(in srgb, ${accent} 22%, var(--color-ink-800))`,
                  color: s.isMain ? '#06120b' : 'var(--color-chalk)',
                }}
              >
                {s.code}
              </span>
              <span className="text-sm text-chalk truncate">{positionName(s.code)}</span>
              {/* {s.isMain && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-chalk-faint">Main</span>
              )} */}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

// Simple pitch markings drawn as an SVG overlay (halfway line, centre circle,
// both penalty boxes). Uses a 100×150 viewBox to match the 2:3 aspect.
function PitchLines() {
  const line = 'rgba(255,255,255,0.16)'
  return (
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 150" preserveAspectRatio="none" aria-hidden>
      <rect x="3" y="3" width="94" height="144" fill="none" stroke={line} strokeWidth="0.6" />
      <line x1="3" y1="75" x2="97" y2="75" stroke={line} strokeWidth="0.6" />
      <circle cx="50" cy="75" r="11" fill="none" stroke={line} strokeWidth="0.6" />
      <circle cx="50" cy="75" r="0.9" fill={line} />
      {/* top box (attacking) */}
      <rect x="28" y="3" width="44" height="20" fill="none" stroke={line} strokeWidth="0.6" />
      <rect x="40" y="3" width="20" height="8" fill="none" stroke={line} strokeWidth="0.6" />
      {/* bottom box (defending) */}
      <rect x="28" y="127" width="44" height="20" fill="none" stroke={line} strokeWidth="0.6" />
      <rect x="40" y="139" width="20" height="8" fill="none" stroke={line} strokeWidth="0.6" />
    </svg>
  )
}
