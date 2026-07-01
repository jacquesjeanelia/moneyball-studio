import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAllPlayers } from '@/hooks/usePlayers'
import { useFacets, useFilteredPlayers, type FilterState, type SortKey } from '@/hooks/useFilters'
import { useProgressiveList } from '@/hooks/useProgressiveList'
import { PageTransition } from '@/components/PageTransition'
import { SearchBar } from '@/components/SearchBar'
import { FilterBar } from '@/components/FilterBar'
import { PlayerCard } from '@/components/PlayerCard'
import { EmptyState, ErrorState, GridSkeleton, Spinner } from '@/components/states'
import type { Category } from '@/api/types'

// URL <-> filter state sync, so searches are shareable + back-button friendly.
function parseFilters(sp: URLSearchParams): FilterState {
  const num = (k: string) => {
    const v = sp.get(k)
    return v ? Number(v) : null
  }
  return {
    query: sp.get('q') ?? '',
    category: (sp.get('cat') as Category) || null,
    position: sp.get('pos') || null,
    leagueId: num('league'),
    countryId: num('country'),
    clubId: num('club'),
    maxPrice: num('max'),
    sort: (sp.get('sort') as SortKey) || 'value_desc',
  }
}

export function BrowsePage() {
  const { data: players, isLoading, isError, error, refetch } = useAllPlayers()
  const [searchParams, setSearchParams] = useSearchParams()

  const filters = useMemo(() => parseFilters(searchParams), [searchParams])

  const patchFilters = useCallback(
    (patch: Partial<FilterState>) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          const set = (k: string, v: string | number | null | undefined) => {
            if (v === null || v === '' || v === undefined) next.delete(k)
            else next.set(k, String(v))
          }
          if ('query' in patch) set('q', patch.query!)
          if ('category' in patch) set('cat', patch.category)
          if ('position' in patch) set('pos', patch.position)
          if ('leagueId' in patch) set('league', patch.leagueId)
          if ('countryId' in patch) set('country', patch.countryId)
          if ('clubId' in patch) set('club', patch.clubId)
          if ('maxPrice' in patch) set('max', patch.maxPrice)
          if ('sort' in patch) set('sort', patch.sort!)
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const resetFilters = useCallback(() => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams()
        const q = prev.get('q')
        if (q) next.set('q', q)
        return next
      },
      { replace: true },
    )
  }, [setSearchParams])

  const facets = useFacets(players)
  const filtered = useFilteredPlayers(players, filters)
  const { visible, hasMore, sentinelRef } = useProgressiveList(filtered)

  return (
    <PageTransition>
      <Hero />

      <div className="max-w-[1400px] mx-auto px-5 sm:px-8">
        {/* Search */}
        <div className="relative z-30 -mt-7 sm:-mt-9 mb-8">
          <SearchBar
            value={filters.query}
            onChange={(q) => patchFilters({ query: q })}
            resultCount={filtered.length}
          />
        </div>

        {/* Filters */}
        <div className="relative z-20 mb-7">
          <FilterBar
            facets={facets}
            filters={filters}
            onChange={patchFilters}
            onReset={resetFilters}
            resultCount={filtered.length}
            totalCount={players?.length ?? 0}
          />
        </div>

        {/* Results */}
        {isLoading && <GridSkeleton />}
        {isError && <ErrorState message={(error as Error)?.message ?? 'Failed to load players.'} onRetry={() => refetch()} />}
        {!isLoading && !isError && filtered.length === 0 && (
          <EmptyState title="No players match" hint="Try loosening your filters or clearing the search." />
        )}

        {!isLoading && !isError && filtered.length > 0 && (
          <>
            <motion.div
              layout
              className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4"
            >
              {visible.map((p, i) => (
                <PlayerCard key={p.id} player={p} index={i} />
              ))}
            </motion.div>
            <div ref={sentinelRef} />
            {hasMore && <Spinner label="Loading more players…" />}
          </>
        )}
      </div>
    </PageTransition>
  )
}

function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-ink-700">
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-b from-ink-850 to-ink-900" />
        <div className="absolute -top-24 left-1/2 h-72 w-[140%] -translate-x-1/2 rounded-full bg-signal-500/10 blur-3xl" />
      </div>
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 pt-14 pb-16 sm:pt-20 sm:pb-20">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 rounded-full surface px-3 py-1 mb-5 text-xs font-bold uppercase tracking-widest text-chalk-dim">
            <span className="h-1.5 w-1.5 rounded-full bg-signal-500 animate-pulse" />
            Top 5 European Leagues · 2024/25
          </div>
          <h1 className="font-display font-extrabold text-4xl sm:text-6xl leading-[0.95] tracking-tight text-balance">
            Scout smarter with
            <span className="block text-signal-500">performance data.</span>
          </h1>
          <p className="mt-5 text-lg text-chalk-dim max-w-xl text-balance">
            Search 1,700+ players, break down per-90 metrics against positional peers, and surface statistical
            lookalikes powered by vector similarity.
          </p>
        </motion.div>
      </div>
    </section>
  )
}
