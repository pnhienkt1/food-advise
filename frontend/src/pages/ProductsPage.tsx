import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listProducts } from '../api/client'
import { SourceBadge } from '../components/ui'
import type { ProductListItem, ProductListResponse } from '../types'

const PAGE_SIZE = 24

function NutriBadge({ grade }: { grade: string | null }) {
  if (!grade) return null
  const colors: Record<string, string> = {
    a: 'bg-emerald-600',
    b: 'bg-green-500',
    c: 'bg-yellow-500',
    d: 'bg-orange-500',
    e: 'bg-red-600',
  }
  const cls = colors[grade.toLowerCase()] || 'bg-slate-400'
  return (
    <span className={`inline-flex h-5 w-5 items-center justify-center rounded text-xs font-bold uppercase text-white ${cls}`}>
      {grade}
    </span>
  )
}

export function ProductsPage() {
  const navigate = useNavigate()
  const [nameQuery, setNameQuery] = useState('')
  const [ingredientQuery, setIngredientQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<ProductListResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    setOffset(0)
  }, [nameQuery, ingredientQuery])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    abortRef.current?.abort()

    setLoading(true)
    setError(null)
    debounceRef.current = setTimeout(() => {
      const controller = new AbortController()
      abortRef.current = controller
      listProducts({
        q: nameQuery,
        ingredient: ingredientQuery,
        limit: PAGE_SIZE,
        offset,
        signal: controller.signal,
      })
        .then((res) => {
          if (controller.signal.aborted) return
          setData(res)
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          if (controller.signal.aborted) return
          setError(err instanceof Error ? err.message : 'Không tải được danh sách sản phẩm')
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, 250)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      abortRef.current?.abort()
    }
  }, [nameQuery, ingredientQuery, offset])

  const total = data?.total ?? 0
  const items: ProductListItem[] = data?.items ?? []
  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + PAGE_SIZE, total)
  const canPrev = offset > 0
  const canNext = offset + PAGE_SIZE < total

  return (
    <div className="mx-auto max-w-5xl space-y-5 p-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">Quản lý sản phẩm</h2>
        <p className="mt-1 text-sm text-slate-600">
          Xem toàn bộ sản phẩm đang có trên nền tảng. Tìm kiếm theo tên/thương hiệu hoặc theo thành phần.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="name-q" className="block text-sm font-medium text-slate-700">
              Tìm theo tên / thương hiệu
            </label>
            <input
              id="name-q"
              type="search"
              value={nameQuery}
              onChange={(e) => setNameQuery(e.target.value)}
              placeholder="VD: Hảo Hảo, Vinamilk..."
              autoComplete="off"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label htmlFor="ing-q" className="block text-sm font-medium text-slate-700">
              Tìm theo thành phần
            </label>
            <input
              id="ing-q"
              type="search"
              value={ingredientQuery}
              onChange={(e) => setIngredientQuery(e.target.value)}
              placeholder="VD: đường, muối, dầu cọ..."
              autoComplete="off"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
          <span>
            {loading ? 'Đang tải...' : `${total} sản phẩm`}
            {total > 0 && !loading && ` · hiển thị ${from}-${to}`}
          </span>
          {(nameQuery || ingredientQuery) && (
            <button
              type="button"
              onClick={() => {
                setNameQuery('')
                setIngredientQuery('')
              }}
              className="text-emerald-700 hover:underline"
            >
              Xóa bộ lọc
            </button>
          )}
        </div>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      {!loading && items.length === 0 && !error && (
        <p className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
          Không tìm thấy sản phẩm phù hợp.
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((p) => (
          <button
            key={p.barcode}
            type="button"
            onClick={() => navigate(`/result/${encodeURIComponent(p.barcode)}`)}
            className="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-emerald-300 hover:shadow"
          >
            <div className="flex items-start gap-3">
              {p.image_url ? (
                <img src={p.image_url} alt="" className="h-14 w-14 shrink-0 rounded object-contain" />
              ) : (
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded bg-slate-100 text-xs text-slate-400">
                  SP
                </div>
              )}
              <div className="min-w-0 flex-1">
                <p className="line-clamp-2 font-medium text-slate-900">{p.name}</p>
                <p className="mt-0.5 truncate text-xs text-slate-500">
                  {[p.brand, p.barcode].filter(Boolean).join(' · ')}
                </p>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <SourceBadge source={p.source} />
              {p.nutri_score && (
                <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                  Nutri <NutriBadge grade={p.nutri_score} />
                </span>
              )}
              {p.nova_group != null && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  NOVA {p.nova_group}
                </span>
              )}
            </div>

            {p.ingredients_text && (
              <p className="mt-2 line-clamp-2 text-xs text-slate-500">
                <span className="font-medium text-slate-600">Thành phần:</span> {p.ingredients_text}
              </p>
            )}
          </button>
        ))}
      </div>

      {total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            type="button"
            disabled={!canPrev || loading}
            onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-40"
          >
            ← Trước
          </button>
          <span className="text-sm text-slate-500">
            {from}-{to} / {total}
          </span>
          <button
            type="button"
            disabled={!canNext || loading}
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-40"
          >
            Sau →
          </button>
        </div>
      )}
    </div>
  )
}
