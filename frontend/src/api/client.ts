import type { Category, PlayerDetail, PlayerSummary, SimilarPlayer } from './types'

// ============================================================================
// API client
// Base URL strategy:
//   - VITE_API_BASE_URL set  -> talk to that origin (deployed split frontend/API)
//   - unset                  -> same-origin "/api" (nginx proxy / vite dev proxy)
// ============================================================================

const BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export const DEFAULT_SEASON = '2024/2025'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${BASE}${path}`, BASE ? undefined : window.location.origin)
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v))
    }
  }

  let res: Response
  try {
    res = await fetch(url.toString(), { headers: { Accept: 'application/json' } })
  } catch {
    throw new ApiError('Network error — is the API reachable?', 0)
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(detail || `Request failed (${res.status})`, res.status)
  }

  return res.json() as Promise<T>
}

export interface ListPlayersParams {
  season?: string
  category?: Category
  country_id?: number
  club_id?: number
}

export const api = {
  listPlayers(params: ListPlayersParams = {}): Promise<PlayerSummary[]> {
    return request<PlayerSummary[]>('/api/players/', {
      season: params.season ?? DEFAULT_SEASON,
      category: params.category,
      country_id: params.country_id,
      club_id: params.club_id,
    })
  },

  getPlayer(id: number, season: string = DEFAULT_SEASON): Promise<PlayerDetail> {
    return request<PlayerDetail>(`/api/players/${id}`, { season })
  },

  getSimilar(id: number, limit = 100, season: string = DEFAULT_SEASON): Promise<SimilarPlayer[]> {
    return request<SimilarPlayer[]>(`/api/players/${id}/similar`, { season, limit })
  },
}
