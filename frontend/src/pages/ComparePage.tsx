import { useState } from 'react'
import { getProduct } from '../api/client'
import { ProductSearch } from '../components/ProductSearch'
import { SourceBadge } from '../components/ui'
import type { Nutrient, Product } from '../types'

// Ngưỡng "đèn giao thông" trên 100g/ml (tham khảo UK FSA). null = không xếp hạng.
const TRAFFIC_THRESHOLDS: Record<string, { low: number; high: number } | null> = {
  energy_kcal: null,
  fat: { low: 3, high: 17.5 },
  saturated_fat: { low: 1.5, high: 5 },
  carbohydrates: null,
  sugars: { low: 5, high: 22.5 },
  fiber: null,
  proteins: null,
  salt: { low: 0.3, high: 1.5 },
  sodium: { low: 120, high: 600 },
}

const ROW_ORDER: { code: string; label: string }[] = [
  { code: 'energy_kcal', label: 'Năng lượng' },
  { code: 'fat', label: 'Chất béo' },
  { code: 'saturated_fat', label: 'Chất béo bão hòa' },
  { code: 'carbohydrates', label: 'Carbohydrate' },
  { code: 'sugars', label: 'Đường' },
  { code: 'fiber', label: 'Chất xơ' },
  { code: 'proteins', label: 'Đạm' },
  { code: 'salt', label: 'Muối' },
  { code: 'sodium', label: 'Natri' },
]

function trafficColor(code: string, amount: number | null): string {
  const t = TRAFFIC_THRESHOLDS[code]
  if (!t || amount == null) return 'text-slate-800'
  if (amount <= t.low) return 'text-emerald-700 bg-emerald-50'
  if (amount <= t.high) return 'text-yellow-700 bg-yellow-50'
  return 'text-red-700 bg-red-50'
}

function nutrientMap(product: Product | null): Record<string, Nutrient> {
  const map: Record<string, Nutrient> = {}
  product?.nutrients.forEach((n) => {
    map[n.nutrient_code] = n
  })
  return map
}

function ProductPicker({
  label,
  product,
  onPick,
  onClear,
}: {
  label: string
  product: Product | null
  onPick: (barcode: string) => void
  onClear: () => void
}) {
  return (
    <div>
      <p className="mb-1 text-sm font-medium text-slate-700">{label}</p>
      {product ? (
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3">
          <div className="flex min-w-0 items-center gap-2">
            {product.image_url ? (
              <img src={product.image_url} alt="" className="h-10 w-10 shrink-0 rounded object-contain" />
            ) : (
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-slate-100">🍜</div>
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">{product.name}</p>
              <SourceBadge source={product.source} />
            </div>
          </div>
          <button onClick={onClear} className="ml-2 shrink-0 text-sm text-slate-500 hover:text-red-600">
            Đổi
          </button>
        </div>
      ) : (
        <ProductSearch onSelect={onPick} />
      )}
    </div>
  )
}

export function ComparePage() {
  const [productA, setProductA] = useState<Product | null>(null)
  const [productB, setProductB] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)

  const pick = async (barcode: string, setter: (p: Product | null) => void) => {
    setError(null)
    try {
      setter(await getProduct(barcode))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không tải được sản phẩm')
    }
  }

  const mapA = nutrientMap(productA)
  const mapB = nutrientMap(productB)
  const bothChosen = productA && productB

  return (
    <div className="mx-auto max-w-3xl space-y-5 p-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">So sánh sản phẩm</h2>
        <p className="mt-1 text-sm text-slate-600">
          Chọn 2 sản phẩm để so sánh dinh dưỡng trên 100g/ml theo thang màu "đèn giao thông".
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <ProductPicker
            label="Sản phẩm A"
            product={productA}
            onPick={(bc) => pick(bc, setProductA)}
            onClear={() => setProductA(null)}
          />
          <ProductPicker
            label="Sản phẩm B"
            product={productB}
            onPick={(bc) => pick(bc, setProductB)}
            onClear={() => setProductB(null)}
          />
        </div>
        {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      </div>

      {bothChosen && (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left">
                <th className="px-4 py-3 font-medium text-slate-600">Chỉ số (/100g)</th>
                <th className="px-4 py-3 font-medium text-slate-900">{productA.name}</th>
                <th className="px-4 py-3 font-medium text-slate-900">{productB.name}</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="px-4 py-2 text-slate-600">Nutri-Score</td>
                <td className="px-4 py-2 font-medium">{productA.nutri_score?.toUpperCase() ?? '—'}</td>
                <td className="px-4 py-2 font-medium">{productB.nutri_score?.toUpperCase() ?? '—'}</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="px-4 py-2 text-slate-600">NOVA</td>
                <td className="px-4 py-2 font-medium">{productA.nova_group ?? '—'}</td>
                <td className="px-4 py-2 font-medium">{productB.nova_group ?? '—'}</td>
              </tr>
              {ROW_ORDER.map(({ code, label }) => {
                const a = mapA[code]
                const b = mapB[code]
                if (!a && !b) return null
                return (
                  <tr key={code} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-2 text-slate-600">{label}</td>
                    <td className={`px-4 py-2 font-medium ${trafficColor(code, a?.amount ?? null)}`}>
                      {a?.amount ?? '—'} {a?.unit ?? ''}
                    </td>
                    <td className={`px-4 py-2 font-medium ${trafficColor(code, b?.amount ?? null)}`}>
                      {b?.amount ?? '—'} {b?.unit ?? ''}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="flex flex-wrap gap-4 border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <span className="h-3 w-3 rounded bg-emerald-100" /> Thấp
            </span>
            <span className="flex items-center gap-1">
              <span className="h-3 w-3 rounded bg-yellow-100" /> Trung bình
            </span>
            <span className="flex items-center gap-1">
              <span className="h-3 w-3 rounded bg-red-100" /> Cao
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
