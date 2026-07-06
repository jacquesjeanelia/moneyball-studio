import { useQuery } from '@tanstack/react-query'
import { api, DEFAULT_SEASON } from '@/api/client'

// ============================================================================
// Query hooks
// The full player list (≈1760 rows, with stats) is fetched once and cached
// aggressively — this powers instant client-side search and filtering
// without per-interaction round-trips.
// ============================================================================

const HOUR = 1000 * 60 * 60

export function useAllPlayers() {
  return useQuery({
    queryKey: ['players', DEFAULT_SEASON],
    queryFn: () => api.listPlayers({ season: DEFAULT_SEASON }),
    staleTime: HOUR,
    gcTime: 2 * HOUR,
  })
}

export function usePlayer(id: number | undefined) {
  return useQuery({
    queryKey: ['player', id, DEFAULT_SEASON],
    queryFn: () => api.getPlayer(id as number),
    enabled: id !== undefined && !Number.isNaN(id),
    staleTime: HOUR,
  })
}

export function useSimilar(id: number | undefined, limit = 100) {
  return useQuery({
    queryKey: ['similar', id, limit, DEFAULT_SEASON],
    queryFn: () => api.getSimilar(id as number, limit),
    enabled: id !== undefined && !Number.isNaN(id),
    staleTime: HOUR,
  })
}


