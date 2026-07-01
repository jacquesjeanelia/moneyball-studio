import type { MetricMeta } from '@/api/types'

// The 12 stat metrics in canonical display order, with rendering metadata.
// Each maps 1:1 to a real player_season_stats column exposed by the API.
// Rate metrics are stored 0–100, so they render with `isPercent`.
export const METRICS: MetricMeta[] = [
  // Attacking
  { key: 'npxg_per90', label: 'Non-Penalty xG', short: 'npxG', isPercent: false, unit: '/90' },
  { key: 'shots_on_target_per90', label: 'Shots on Target', short: 'SoT', isPercent: false, unit: '/90' },
  { key: 'xa_per90', label: 'Expected Assists', short: 'xA', isPercent: false, unit: '/90' },
  { key: 'big_chances_created_per90', label: 'Big Chances Created', short: 'Big Chs', isPercent: false, unit: '/90' },
  // Possession & progression
  { key: 'successful_passes_per90', label: 'Successful Passes', short: 'Passes', isPercent: false, unit: '/90' },
  { key: 'successful_pass_rate', label: 'Pass Completion', short: 'Pass %', isPercent: true, unit: '%' },
  { key: 'successful_dribbles_per90', label: 'Successful Dribbles', short: 'Dribbles', isPercent: false, unit: '/90' },
  { key: 'accurate_long_balls_per90', label: 'Accurate Long Balls', short: 'Long Balls', isPercent: false, unit: '/90' },
  // Defending & duels
  { key: 'tackles_per90', label: 'Tackles', short: 'Tackles', isPercent: false, unit: '/90' },
  { key: 'interceptions_per90', label: 'Interceptions', short: 'Int', isPercent: false, unit: '/90' },
  { key: 'recoveries_per90', label: 'Ball Recoveries', short: 'Recov', isPercent: false, unit: '/90' },
  { key: 'aerial_duel_success_rate', label: 'Aerial Duels Won', short: 'Aerial %', isPercent: true, unit: '%' },
]

// Group metrics for the stat-table layout.
export const METRIC_GROUPS: { title: string; keys: MetricMeta['key'][] }[] = [
  { title: 'Attacking', keys: ['npxg_per90', 'shots_on_target_per90', 'xa_per90', 'big_chances_created_per90'] },
  { title: 'Possession & Progression', keys: ['successful_passes_per90', 'successful_pass_rate', 'successful_dribbles_per90', 'accurate_long_balls_per90'] },
  { title: 'Defending & Duels', keys: ['tackles_per90', 'interceptions_per90', 'recoveries_per90', 'aerial_duel_success_rate'] },
]
