// ============================================================================
// API contract types — mirror the FastAPI/pydantic models exactly.
// Source of truth: backend/models.py
// ============================================================================

export interface Country {
  id: number
  name: string
  flag_url: string | null
}

export interface League {
  id: number
  name: string
  country?: Country | null
  logo_url: string | null
}

export interface Club {
  id: number
  name: string
  league?: League | null
  logo_url: string | null
}

export interface PlayerStats {
  id: number
  minutes_played: number | null
  // Attacking
  npxg_per90: number | null
  shots_on_target_per90: number | null
  xa_per90: number | null
  big_chances_created_per90: number | null
  // Possession & progression
  successful_passes_per90: number | null
  successful_pass_rate: number | null
  successful_dribbles_per90: number | null
  accurate_long_balls_per90: number | null
  // Defending & duels
  tackles_per90: number | null
  interceptions_per90: number | null
  recoveries_per90: number | null
  aerial_duel_success_rate: number | null
}

export interface PlayerSummary {
  id: number
  name: string
  country: Country | null
  /** Broad role for colour-coding + the All·Attackers·Midfielders·Defenders control. */
  category: string | null
  /** Specific role shown on cards/pills, e.g. "CM", "LW", "CB". */
  main_position: string | null
  /** Other specific roles the player can fill — used by the position filter. */
  alternate_positions: string[]
  age: number | null
  club: Club | null
  photo_url: string | null
  current_market_value_eur: number | null
  season_stats: PlayerStats | null
}

export interface PlayerDetail extends PlayerSummary {
  date_of_birth: string | null
  preferred_foot: string | null
  height_cm: number | null
}

export interface SimilarPlayer {
  player: PlayerSummary
  similarity_score: number
}

/** Broad player role — drives colour-coding and the category segmented control. */
export type Category = 'Attack' | 'Midfield' | 'Defender'

// The 12 radar/stat metrics, in display order, with metadata for rendering.
export type MetricKey = keyof Omit<PlayerStats, 'id' | 'minutes_played'>

export interface MetricMeta {
  key: MetricKey
  label: string
  short: string
  /** Whether the raw value is already a percentage (0–100). */
  isPercent: boolean
  unit: string
}
