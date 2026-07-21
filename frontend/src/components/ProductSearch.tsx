import { useEffect, useRef, useState } from 'react'
import { searchProducts } from '../api/client'
import type { ProductSearchResult } from '../types'

interface ProductSearchProps {
  onSelect: (barcode: string) => void
  disabled?: boolean
}

export function ProductSearch({ onSelect, disabled }: ProductSearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<ProductSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    abortRef.current?.abort()

    const trimmed = query.trim()
    if (trimmed.length < 2) {
      setResults([])
      setOpen(false)
      setLoading(false)
      return
    }

    setLoading(true)
    debounceRef.current = setTimeout(() => {
      const controller = new AbortController()
      abortRef.current = controller

      searchProducts(trimmed, 10, controller.signal)
        .then((items) => {
          if (controller.signal.aborted) return
          setResults(items)
          setOpen(items.length > 0)
          setActiveIndex(-1)
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          if (controller.signal.aborted) return
          setResults([])
          setOpen(false)
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false)
        })
    }, 150)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      abortRef.current?.abort()
    }
  }, [query])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectProduct = (item: ProductSearchResult) => {
    setQuery(item.name)
    setOpen(false)
    onSelect(item.barcode)
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || results.length === 0) {
      if (event.key === 'Enter' && results.length === 1) {
        selectProduct(results[0])
      }
      return
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((prev) => (prev + 1) % results.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((prev) => (prev <= 0 ? results.length - 1 : prev - 1))
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault()
      selectProduct(results[activeIndex])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div ref={containerRef} className="relative rounded-2xl border border-slate-200 bg-white p-4">
      <label htmlFor="product-search" className="block text-sm font-medium text-slate-700">
        Tìm sản phẩm theo tên
      </label>
      <div className="relative mt-2">
        <input
          id="product-search"
          type="search"
          value={query}
          disabled={disabled}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => results.length > 0 && setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="VD: Mì Hảo Hảo, Vinamilk..."
          autoComplete="off"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 pr-10 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-50"
        />
        {loading && (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
            ...
          </span>
        )}
      </div>

      {open && results.length > 0 && (
        <ul
          role="listbox"
          className="absolute left-4 right-4 z-20 mt-1 max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg"
        >
          {results.map((item, index) => (
            <li key={item.barcode} role="option" aria-selected={index === activeIndex}>
              <button
                type="button"
                onClick={() => selectProduct(item)}
                onMouseEnter={() => setActiveIndex(index)}
                className={`flex w-full items-start gap-3 px-3 py-2.5 text-left text-sm hover:bg-emerald-50 ${
                  index === activeIndex ? 'bg-emerald-50' : ''
                }`}
              >
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt=""
                    className="mt-0.5 h-10 w-10 shrink-0 rounded object-contain"
                  />
                ) : (
                  <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded bg-slate-100 text-xs text-slate-400">
                    SP
                  </div>
                )}
                <span className="min-w-0 flex-1">
                  <span className="block font-medium text-slate-900">{item.name}</span>
                  <span className="block text-xs text-slate-500">
                    {[item.brand, item.barcode].filter(Boolean).join(' · ')}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {!loading && query.trim().length >= 2 && results.length === 0 && open && (
        <p className="mt-2 text-xs text-slate-500">Không tìm thấy sản phẩm phù hợp.</p>
      )}
    </div>
  )
}
