import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ZAxis,
} from 'recharts'
import { useAllPlayers } from '@/hooks/usePlayers'
import { PageTransition } from '@/components/PageTransition'
import { ErrorState, Spinner } from '@/components/states'
import { categoryColor } from '@/lib/format'
import type { PlayerSummary } from '@/api/types'

interface DotData {
  x: number
  y: number
  player: PlayerSummary
}

const CATEGORY_LABELS: Record<string, string> = {
  Attack: 'Attackers',
  Midfield: 'Midfielders',
  Defender: 'Defenders',
}

const CATEGORY_ORDER = ['Attack', 'Midfield', 'Defender']

function DotTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload as DotData | undefined
  if (!d) return null

  const p = d.player
  return (
    <div className="glass border border-ink-600 rounded-lg px-4 py-3 text-sm shadow-card max-w-56">
      <div className="flex items-center gap-2 mb-1">
        {p.photo_url && (
          <img src={p.photo_url} alt="" className="w-6 h-6 rounded-full object-cover" />
        )}
        <span className="font-semibold text-chalk truncate">{p.name}</span>
      </div>
      <div className="flex items-center gap-2 text-chalk-dim">
        <span
          className="inline-block w-2 h-2 rounded-full"
          style={{ backgroundColor: categoryColor(p.category) }}
        />
        <span>{p.category || '—'}</span>
        <span className="text-chalk-faint">·</span>
        <span>{p.main_position || '—'}</span>
      </div>
      {p.club && <div className="text-chalk-faint truncate">{p.club.name}</div>}
    </div>
  )
}

function LegendContent() {
  return (
    <div className="flex items-center justify-center gap-6 text-sm">
      {CATEGORY_ORDER.map((cat) => (
        <div key={cat} className="flex items-center gap-2">
          <span
            className="inline-block w-3 h-3 rounded-full"
            style={{ backgroundColor: categoryColor(cat) }}
          />
          <span className="text-chalk-dim">{CATEGORY_LABELS[cat]}</span>
        </div>
      ))}
    </div>
  )
}

export function UmapPage() {
  const { data: players, isLoading, isError, error, refetch } = useAllPlayers()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const { allDots, domain } = useMemo(() => {
    if (!players) return { allDots: [], domain: { xMin: 0, xMax: 0, yMin: 0, yMax: 0 } }

    const dots: DotData[] = []
    for (const p of players) {
      if (p.umap_x != null && p.umap_y != null) {
        dots.push({ x: p.umap_x, y: p.umap_y, player: p })
      }
    }

    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity
    for (const d of dots) {
      if (d.x < xMin) xMin = d.x
      if (d.x > xMax) xMax = d.x
      if (d.y < yMin) yMin = d.y
      if (d.y > yMax) yMax = d.y
    }
    const xPad = (xMax - xMin) * 0.08 || 1
    const yPad = (yMax - yMin) * 0.08 || 1

    return {
      allDots: dots,
      domain: {
        xMin: xMin - xPad,
        xMax: xMax + xPad,
        yMin: yMin - yPad,
        yMax: yMax + yPad,
      },
    }
  }, [players])

  const grouped = useMemo(() => {
    const groups: Record<string, DotData[]> = { Attack: [], Midfield: [], Defender: [] }
    for (const d of allDots) {
      const cat = d.player.category
      if (cat && groups[cat]) groups[cat].push(d)
    }
    return groups
  }, [allDots])

  const handleCategoryClick = (cat: string | null) => {
    setSelectedCategory((prev) => (prev === cat ? null : cat))
  }

  if (isLoading) return <div className="py-24"><Spinner label="Loading player map…" /></div>
  if (isError) return <ErrorState message={error?.message ?? 'Failed to load players'} onRetry={() => refetch()} />

  return (
    <PageTransition>
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-display font-extrabold text-2xl text-chalk">Player Map</h1>
            <p className="text-chalk-dim text-sm mt-1">
              {allDots.length} players projected into 2D space via UMAP
            </p>
          </div>
        </div>

        {/* Category filter chips */}
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
              selectedCategory === null
                ? 'bg-ink-600 text-chalk'
                : 'text-chalk-dim hover:text-chalk hover:bg-ink-700/60'
            }`}
          >
            All
          </button>
          {CATEGORY_ORDER.map((cat) => (
            <button
              key={cat}
              onClick={() => handleCategoryClick(cat)}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                selectedCategory === cat
                  ? 'bg-ink-600 text-chalk'
                  : 'text-chalk-dim hover:text-chalk hover:bg-ink-700/60'
              }`}
            >
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: categoryColor(cat) }}
              />
              {CATEGORY_LABELS[cat]}
              <span className="text-chalk-faint ml-0.5">({grouped[cat]?.length || 0})</span>
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="glass rounded-xl border border-ink-700 p-4 sm:p-6">
          <ResponsiveContainer width="100%" height={650}>
            <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 20 }}>
              <XAxis
                type="number"
                dataKey="x"
                domain={[domain.xMin, domain.xMax]}
                tick={false}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={[domain.yMin, domain.yMax]}
                tick={false}
                axisLine={false}
                tickLine={false}
              />
              <ZAxis range={[40, 40]} />
              <Tooltip content={<DotTooltip />} cursor={{ strokeDasharray: '3 3' }} />
              <Legend content={<LegendContent />} />

              {CATEGORY_ORDER.map((cat) => {
                const data = selectedCategory && selectedCategory !== cat ? [] : (grouped[cat] || [])
                return (
                  <Scatter
                    key={cat}
                    name={CATEGORY_LABELS[cat]}
                    data={data}
                    fill={categoryColor(cat)}
                    fillOpacity={cat === 'Defender' ? 0.85 : 0.7}
                    stroke="none"
                    shape="circle"
                  />
                )
              })}
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Player grid when a category is selected */}
        {selectedCategory && (() => {
          const catData = grouped[selectedCategory] || []
          return (
            <div className="mt-8">
              <h2 className="font-display font-bold text-lg text-chalk mb-4">
                {CATEGORY_LABELS[selectedCategory]}
                <span className="text-chalk-faint font-normal ml-1">({catData.length})</span>
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {catData.slice(0, 48).map((d) => (
                  <Link
                    key={d.player.id}
                    to={`/players/${d.player.id}`}
                    className="glass rounded-lg border border-ink-700 p-3 hover:border-ink-500 transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      {d.player.photo_url && (
                        <img
                          src={d.player.photo_url}
                          alt=""
                          className="w-8 h-8 rounded-full object-cover"
                        />
                      )}
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-chalk truncate group-hover:text-signal-400 transition-colors">
                          {d.player.name}
                        </div>
                        <div className="text-xs text-chalk-faint">{d.player.main_position}</div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
              {catData.length > 48 && (
                <p className="text-center text-chalk-faint text-sm mt-4">
                  Showing 48 of {catData.length}
                </p>
              )}
            </div>
          )
        })()}
      </div>
    </PageTransition>
  )
}
