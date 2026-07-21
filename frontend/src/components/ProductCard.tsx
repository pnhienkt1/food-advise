import type { Product } from '../types'
import { AdditiveBadge, SourceBadge } from './ui'

export function ProductCard({ product }: { product: Product }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex gap-4">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="h-24 w-24 rounded-xl object-cover" />
        ) : (
          <div className="flex h-24 w-24 items-center justify-center rounded-xl bg-slate-100 text-3xl">🍜</div>
        )}
        <div className="flex-1">
          <h2 className="text-xl font-bold text-slate-900">{product.name}</h2>
          {product.brand && <p className="text-slate-600">{product.brand}</p>}
          <div className="mt-2 flex flex-wrap gap-2">
            <SourceBadge source={product.source} url={product.source_url} />
            {product.nutri_score && (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium">
                Nutri-Score: {product.nutri_score.toUpperCase()}
              </span>
            )}
            {product.nova_group && (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium">
                NOVA {product.nova_group}
              </span>
            )}
          </div>
        </div>
      </div>

      {product.ingredients_text && (
        <div className="mt-4">
          <h3 className="font-semibold text-slate-800">Thành phần</h3>
          <p className="mt-1 text-sm text-slate-600">{product.ingredients_text}</p>
        </div>
      )}

      {product.nutrients.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold text-slate-800">Dinh dưỡng (trên 100g/ml)</h3>
          <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {product.nutrients.map((n) => (
              <div key={n.nutrient_code} className="rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span className="text-slate-500">{n.label || n.nutrient_code}</span>
                <p className="font-medium">
                  {n.amount ?? '—'} {n.unit}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {product.additives.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold text-slate-800">Phụ gia thực phẩm</h3>
          <div className="mt-1 flex flex-wrap gap-2">
            {product.additives.map((a) => (
              <AdditiveBadge key={a.e_number} eNumber={a.e_number} name={a.name} risk={a.risk_level} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
