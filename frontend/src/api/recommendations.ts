import type { RecommendationItem, UserProfile } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || ''

export function getRecommendations(
  profile: UserProfile,
  options?: { limit?: number; minScore?: number; category?: string }
): Promise<{ total_evaluated: number; recommendations: RecommendationItem[]; profile_note: string }> {
  const params = new URLSearchParams()
  if (options?.limit) params.set('limit', String(options.limit))
  if (options?.minScore) params.set('min_score', String(options.minScore))
  if (options?.category) params.set('category', options.category)
  const qs = params.toString() ? `?${params}` : ''

  return fetch(`${API_BASE}/api/v1/recommendations${qs}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  }).then(async (res) => {
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  })
}
