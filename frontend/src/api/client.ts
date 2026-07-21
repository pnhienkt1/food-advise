import type { Advice, OcrIngredientsResult, Product, ProductSearchResult, ProfilePreset, UserProfile } from '../types'

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

export function getProfilePresets(): Promise<ProfilePreset[]> {
  return request('/api/v1/profiles/presets')
}

export function evaluateIngredientsAdvice(ingredientsText: string, profile: UserProfile): Promise<Advice> {
  return request('/api/v1/advice/evaluate-ingredients', {
    method: 'POST',
    body: JSON.stringify({ ingredients_text: ingredientsText, profile }),
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
