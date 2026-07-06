import {
  Radar,
  RadarChart as ReRadarChart,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { RadarPoint } from '@/lib/percentiles'
import { topPercent } from '@/lib/format'

export interface RadarSeries {
  name: string
  color: string
  points: RadarPoint[]
}

interface RadarChartProps {
  series: RadarSeries[]
  height?: number
  /** Map from metric short label → tick colour (e.g. for role-based multi-colour axes). */
  tickColors?: Record<string, string>
}

/**
 * Percentile radar. Each axis is a metric; values are 0–100 percentile ranks
 * vs positional peers. Supports overlaying multiple players for comparison.
 */
export function RadarChart({ series, height = 360, tickColors }: RadarChartProps) {
  if (series.length === 0) return null

  // Merge series into recharts row format keyed by metric short label.
  const base = series[0].points
  const data = base.map((pt, i) => {
    const row: Record<string, string | number> = { metric: pt.short }
    series.forEach((s, si) => {
      row[`s${si}`] = s.points[i]?.value ?? 0
    })
    return row
  })

  const renderTick = (props: any) => {
    const { payload, x, y } = props
    const color = tickColors?.[payload.value] ?? 'var(--color-chalk-dim)'
    return (
      <text x={x} y={y} fill={color} textAnchor="middle" fontSize={11} fontWeight={600}>
        {payload.value}
      </text>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ReRadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="var(--color-ink-600)" />
        <PolarAngleAxis
          dataKey="metric"
          tick={tickColors ? renderTick : { fill: 'var(--color-chalk-dim)', fontSize: 11, fontWeight: 600 }}
        />
        {series.map((s, si) => (
          <Radar
            key={si}
            name={s.name}
            dataKey={`s${si}`}
            stroke={s.color}
            strokeWidth={2}
            fill={s.color}
            fillOpacity={series.length > 1 ? 0.18 : 0.32}
            isAnimationActive
            animationDuration={650}
          />
        ))}
        <Tooltip content={<RadarTooltip series={series} />} />
      </ReRadarChart>
    </ResponsiveContainer>
  )
}

interface TooltipProps {
  active?: boolean
  label?: string
  series: RadarSeries[]
}

function RadarTooltip({ active, label, series }: TooltipProps) {
  if (!active || !label) return null
  const idx = series[0].points.findIndex((p) => p.short === label)
  if (idx < 0) return null
  const full = series[0].points[idx]
  return (
    <div className="rounded-lg surface-raised shadow-card px-3 py-2 text-xs">
      <div className="font-bold text-chalk mb-1">{full.label}</div>
      {series.map((s, si) => {
        const pt = s.points[idx]
        return (
          <div key={si} className="flex items-center gap-2 tnum">
            <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
            <span className="text-chalk-dim flex-1">{s.name}</span>
            <span className="font-bold text-chalk">Top {topPercent(pt?.value ?? 0)}%</span>
          </div>
        )
      })}
    </div>
  )
}
