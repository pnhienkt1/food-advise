import type {
  Advice,
  OcrIngredientsResult,
  Product,
  ProductListResponse,
  ProductSearchResult,
  ProfilePreset,
  UserProfile,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL || ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
  }
  return res.json()
}

export function getProduct(barcode: string): Promise<Product> {
  return request(`/api/v1/products/${encodeURIComponent(barcode)}`)
}

export function searchProducts(
  q: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<ProductSearchResult[]> {
  const params = new URLSearchParams({ q, limit: String(limit) })
  return request(`/api/v1/products/search?${params}`, { signal })
}

export function evaluateAdvice(barcode: string, profile: UserProfile): Promise<Advice> {
  return request('/api/v1/advice/evaluate', {
    method: 'POST',
    body: JSON.stringify({ barcode, profile }),
  })
}

export function listProducts(params: {
  q?: string
  ingredient?: string
  limit?: number
  offset?: number
  signal?: AbortSignal
}): Promise<ProductListResponse> {
  const search = new URLSearchParams()
  if (params.q?.trim()) search.set('q', params.q.trim())
  if (params.ingredient?.trim()) search.set('ingredient', params.ingredient.trim())
  search.set('limit', String(params.limit ?? 24))
  search.set('offset', String(params.offset ?? 0))
  return request(`/api/v1/products?${search.toString()}`, { signal: params.signal })
}

export function getProfilePresets(): Promise<ProfilePreset[]> {
  return request('/api/v1/profiles/presets')
}

export interface QuickNutrients {
  sugars?: number
  salt?: number
  sodium?: number
  saturated_fat?: number
  energy_kcal?: number
  proteins?: number
}

export function evaluateIngredientsAdvice(
  ingredientsText: string,
  profile: UserProfile,
  nutrients?: QuickNutrients,
): Promise<Advice> {
  return request('/api/v1/advice/evaluate-ingredients', {
    method: 'POST',
    body: JSON.stringify({ ingredients_text: ingredientsText, profile, ...(nutrients ?? {}) }),
  })
}

export async function uploadIngredientsImage(file: File): Promise<OcrIngredientsResult> {
  const formData = new FormData()
  formData.append('image', file)
  const res = await fetch(`${API_BASE}/api/v1/ocr/ingredients`, { method: 'POST', body: formData })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
  }
  return res.json()
}

export function getAlternatives(barcode: string, profile: UserProfile): Promise<Product[]> {
  const profileParam = encodeURIComponent(JSON.stringify(profile))
  return request(`/api/v1/products/${barcode}/alternatives?profile=${profileParam}`)
}

export function healthCheck(): Promise<{ status: string }> {
  return request('/health')
}
