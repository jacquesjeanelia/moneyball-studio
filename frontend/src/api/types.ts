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
  npxg_percentile: number | null
  shots_per90: number | null
  shots_percentile: number | null
  shots_on_target_per90: number | null
  shots_on_target_percentile: number | null
  headed_shots_per90: number | null
  headed_shots_percentile: number | null
  xa_per90: number | null
  xa_percentile: number | null
  chances_created_per90: number | null
  chances_created_percentile: number | null
  big_chances_created_per90: number | null
  big_chances_created_percentile: number | null
  successful_crosses_per90: number | null
  successful_crosses_percentile: number | null
  successful_cross_rate: number | null
  successful_cross_rate_percentile: number | null
  opposition_box_touches_per90: number | null
  opposition_box_touches_percentile: number | null
  // Possession & progression
  successful_passes_per90: number | null
  successful_passes_percentile: number | null
  successful_pass_rate: number | null
  successful_pass_rate_percentile: number | null
  accurate_long_balls_per90: number | null
  accurate_long_balls_percentile: number | null
  accurate_long_balls_rate: number | null
  accurate_long_balls_rate_percentile: number | null
  successful_dribbles_per90: number | null
  successful_dribbles_percentile: number | null
  successful_dribble_rate: number | null
  successful_dribble_rate_percentile: number | null
  touches_per90: number | null
  touches_percentile: number | null
  dispossessed_per90: number | null
  dispossessed_percentile: number | null
  fouls_won_per90: number | null
  fouls_won_percentile: number | null
  duels_won_per90: number | null
  duels_won_percentile: number | null
  duel_success_rate: number | null
  duel_success_rate_percentile: number | null
  // Defending & physical
  aerial_duels_won_per90: number | null
  aerial_duels_won_percentile: number | null
  aerial_duel_success_rate: number | null
  aerial_duel_success_rate_percentile: number | null
  tackles_per90: number | null
  tackles_percentile: number | null
  interceptions_per90: number | null
  interceptions_percentile: number | null
  blocks_per90: number | null
  blocks_percentile: number | null
  clearances_per90: number | null
  clearances_percentile: number | null
  recoveries_per90: number | null
  recoveries_percentile: number | null
  possession_won_final_third_per90: number | null
  possession_won_final_third_percentile: number | null
  dribbled_past_per90: number | null
  dribbled_past_percentile: number | null
  fouls_committed_per90: number | null
  fouls_committed_percentile: number | null
  defcon_per90: number | null
  defcon_percentile: number | null
}

export interface PlayerSummary {
  id: number
  name: string
  country: Country | null
  /** Broad role for colour-coding + the All·Attackers·Midfielders·Defenders control. */
  category: string | null
  /** Specific role group used for role-specific radar views. */
  role: string | null
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

/** Automatically exclude percentile fields from MetricKey. */
type PercentileKeys = {
  [K in keyof PlayerStats]: K extends `${string}_percentile` ? K : never
}[keyof PlayerStats]

// The 32 radar/stat metrics, in display order, with metadata for rendering.
export type MetricKey = keyof Omit<PlayerStats, 'id' | 'minutes_played' | PercentileKeys>

export interface MetricMeta {
  key: MetricKey
  label: string
  short: string
  /** Whether the raw value is already a percentage (0–100). */
  isPercent: boolean
  unit: string
}
