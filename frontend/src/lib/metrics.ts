import type { MetricMeta } from '@/api/types'

// All positive-directed stat metrics in canonical display order, with rendering
// metadata. Each maps 1:1 to a real player_season_stats column exposed by the API.
// Rate metrics are stored 0–100, so they render with `isPercent`.
// Negative indicators (dispossessed, dribbled past, fouls committed, defcon) are
// intentionally excluded because the percentile engine assumes higher = better.
export const METRICS: MetricMeta[] = [
  // ── Attacking ──────────────────────────────────────────────────────────────
  { key: 'npxg_per90', label: 'Non-Penalty xG', short: 'npxG', isPercent: false, unit: '/90' },
  { key: 'shots_per90', label: 'Shots', short: 'Shots', isPercent: false, unit: '/90' },
  { key: 'shots_on_target_per90', label: 'Shots on Target', short: 'SoT', isPercent: false, unit: '/90' },
  { key: 'headed_shots_per90', label: 'Headed Shots', short: 'Head Shots', isPercent: false, unit: '/90' },
  { key: 'xa_per90', label: 'Expected Assists', short: 'xA', isPercent: false, unit: '/90' },
  { key: 'chances_created_per90', label: 'Chances Created', short: 'Chances', isPercent: false, unit: '/90' },
  { key: 'big_chances_created_per90', label: 'Big Chances Created', short: 'Big Chances', isPercent: false, unit: '/90' },
  { key: 'successful_crosses_per90', label: 'Successful Crosses', short: 'Crosses', isPercent: false, unit: '/90' },
  { key: 'successful_cross_rate', label: 'Successful Crosses %', short: 'Cross %', isPercent: true, unit: '%' },
  { key: 'opposition_box_touches_per90', label: 'Touches in Opposition Box', short: 'Box Touches', isPercent: false, unit: '/90' },
  // ── Possession & progression ──────────────────────────────────────────────
  { key: 'successful_passes_per90', label: 'Successful Passes', short: 'Passes', isPercent: false, unit: '/90' },
  { key: 'successful_pass_rate', label: 'Successful Passes %', short: 'Pass %', isPercent: true, unit: '%' },
  { key: 'accurate_long_balls_per90', label: 'Accurate Long Balls', short: 'Long Balls', isPercent: false, unit: '/90' },
  { key: 'accurate_long_balls_rate', label: 'Accurate Long Balls %', short: 'Long Ball %', isPercent: true, unit: '%' },
  { key: 'successful_dribbles_per90', label: 'Successful Dribbles', short: 'Dribbles', isPercent: false, unit: '/90' },
  { key: 'successful_dribble_rate', label: 'Successful Dribbles %', short: 'Dribble %', isPercent: true, unit: '%' },
  { key: 'touches_per90', label: 'Touches', short: 'Touches', isPercent: false, unit: '/90' },
  { key: 'duels_won_per90', label: 'Duels Won', short: 'Duels Won', isPercent: false, unit: '/90' },
  { key: 'duel_success_rate', label: 'Duels Won %', short: 'Duel %', isPercent: true, unit: '%' },
  { key: 'fouls_won_per90', label: 'Fouls Won', short: 'Fouls Won', isPercent: false, unit: '/90' },
  { key: 'dispossessed_per90', label: 'Dispossessed', short: 'Dispossessed', isPercent: false, unit: '/90' },
  // ── Defending & physical ──────────────────────────────────────────────────
  { key: 'tackles_per90', label: 'Tackles', short: 'Tackles', isPercent: false, unit: '/90' },
  { key: 'interceptions_per90', label: 'Interceptions', short: 'Interceptions', isPercent: false, unit: '/90' },
  { key: 'blocks_per90', label: 'Blocked Shots', short: 'Blocks', isPercent: false, unit: '/90' },
  { key: 'clearances_per90', label: 'Clearances', short: 'Clear', isPercent: false, unit: '/90' },
  { key: 'recoveries_per90', label: 'Recoveries', short: 'Recoveries', isPercent: false, unit: '/90' },
  { key: 'aerial_duels_won_per90', label: 'Aerial Duels Won', short: 'Aerial Won', isPercent: false, unit: '/90' },
  { key: 'aerial_duel_success_rate', label: 'Aerial Duels Won %', short: 'Aerial %', isPercent: true, unit: '%' },
  { key: 'defcon_per90', label: 'Defensive Contributions', short: 'Defcon', isPercent: false, unit: '/90' },
  { key: 'possession_won_final_third_per90', label: 'Possession Won in Final 3rd', short: 'Poss Final 3rd', isPercent: false, unit: '/90' },
  { key: 'fouls_committed_per90', label: 'Fouls Committed', short: 'Fouls Committed', isPercent: false, unit: '/90' },
  { key: 'dribbled_past_per90', label: 'Dribbled Past', short: 'Dribbled Past', isPercent: false, unit: '/90' },
]

// Role-specific metrics used for the role-based radar view.
export type Role = 'Striker' | 'Creative Attacker' | 'Midfielder' | 'Fullback' | 'Center Back'

export const ROLE_METRICS: Record<Role, MetricMeta['key'][]> = {
  Striker: [
    'npxg_per90', 'shots_per90', 'shots_on_target_per90', 'headed_shots_per90',
    'opposition_box_touches_per90', 'xa_per90', 'big_chances_created_per90',
    'successful_pass_rate', 'successful_dribbles_per90',
    'possession_won_final_third_per90', 'aerial_duels_won_per90',
    'interceptions_per90', 'recoveries_per90',
  ],
  'Creative Attacker': [
    'npxg_per90', 'shots_per90', 'shots_on_target_per90', 'xa_per90',
    'chances_created_per90', 'big_chances_created_per90',
    'successful_crosses_per90', 'successful_dribbles_per90',
    'successful_dribble_rate', 'opposition_box_touches_per90',
    'possession_won_final_third_per90', 'successful_pass_rate',
    'tackles_per90', 'interceptions_per90',
  ],
  Midfielder: [
    'xa_per90', 'chances_created_per90', 'successful_passes_per90',
    'successful_pass_rate', 'accurate_long_balls_per90',
    'accurate_long_balls_rate', 'touches_per90', 'interceptions_per90',
    'recoveries_per90', 'tackles_per90', 'duel_success_rate',
    'possession_won_final_third_per90', 'npxg_per90',
  ],
  Fullback: [
    'tackles_per90', 'interceptions_per90', 'recoveries_per90',
    'successful_pass_rate', 'successful_crosses_per90', 'xa_per90',
    'chances_created_per90', 'possession_won_final_third_per90',
    'opposition_box_touches_per90', 'successful_dribbles_per90',
    'touches_per90', 'duel_success_rate', 'clearances_per90',
  ],
  'Center Back': [
    'tackles_per90', 'interceptions_per90', 'blocks_per90',
    'clearances_per90', 'recoveries_per90', 'aerial_duels_won_per90',
    'aerial_duel_success_rate', 'duel_success_rate',
    'successful_passes_per90', 'successful_pass_rate',
    'accurate_long_balls_per90', 'accurate_long_balls_rate',
    'touches_per90', 'npxg_per90',
  ],
}

// Group metrics for the stat-table layout. The `category` drives the accent
// colour (Attack → signal red, Midfield → cyan, Defender → volt green).
export interface MetricGroup {
  title: string
  category: string
  keys: MetricMeta['key'][]
}

export const METRIC_GROUPS: MetricGroup[] = [
  {
    title: 'Attacking',
    category: 'Attack',
    keys: [
      'npxg_per90',
      'shots_per90',
      'shots_on_target_per90',
      'headed_shots_per90',
      'xa_per90',
      'chances_created_per90',
      'big_chances_created_per90',
      'successful_crosses_per90',
      'successful_cross_rate',
      'opposition_box_touches_per90',
    ],
  },
  {
    title: 'Possession & Progression',
    category: 'Midfield',
    keys: [
      'successful_passes_per90',
      'successful_pass_rate',
      'accurate_long_balls_per90',
      'accurate_long_balls_rate',
      'successful_dribbles_per90',
      'successful_dribble_rate',
      'touches_per90',
      'duels_won_per90',
      'duel_success_rate',
      'fouls_won_per90',
      'dispossessed_per90',
    ],
  },
  {
    title: 'Defending & Physical',
    category: 'Defender',
    keys: [
      'tackles_per90',
      'interceptions_per90',
      'blocks_per90',
      'clearances_per90',
      'recoveries_per90',
      'aerial_duels_won_per90',
      'aerial_duel_success_rate',
      'possession_won_final_third_per90',
      'defcon_per90',
      'fouls_committed_per90',
      'dribbled_past_per90',
    ],
  },
]
