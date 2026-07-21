import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { evaluateAdvice, getAlternatives, getProduct } from '../api/client'
import { AdvicePanel } from '../components/AdvicePanel'
import { ProductCard } from '../components/ProductCard'
import { Disclaimer, SourceBadge } from '../components/ui'
import { useProfile, useScanHistory } from '../hooks/useProfile'
import type { Advice, Product } from '../types'

export function ResultPage() {
  const { barcode } = useParams<{ barcode: string }>()
  const { profile } = useProfile()
  const { addToHistory } = useScanHistory()
  const [product, setProduct] = useState<Product | null>(null)
  const [advice, setAdvice] = useState<Advice | null>(null)
  const [alternatives, setAlternatives] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!barcode) return

    setLoading(true)
    setError(null)

    Promise.all([
      getProduct(barcode),
      evaluateAdvice(barcode, profile),
      getAlternatives(barcode, profile).catch(() => [] as Product[]),
    ])
      .then(([prod, adv, alts]) => {
        setProduct(prod)
        setAdvice(adv)
        setAlternatives(alts)
        addToHistory({ barcode, productName: prod.name, score: adv.suitability_score })
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [barcode, profile, addToHistory])

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
          <p className="mt-4 text-slate-600">Đang tra cứu sản phẩm...</p>
        </div>
      </div>
    )
  }

  if (error || !product || !advice) {
    return (
      <div className="mx-auto max-w-lg p-4 text-center">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
          <h2 className="text-lg font-bold text-red-900">Không tìm thấy sản phẩm</h2>
          <p className="mt-2 text-sm text-red-700">{error || 'Mã barcode chưa có trong cơ sở dữ liệu'}</p>
          {barcode && (
            <a
              href={`https://world.openfoodfacts.org/cgi/product.pl?type=edit&code=${barcode}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block text-sm text-emerald-600 underline"
            >
              Đóng góp sản phẩm lên Open Food Facts
            </a>
          )}
        </div>
        <Link to="/scan" className="mt-4 inline-block text-emerald-600 hover:underline">
          Quay lại quét
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <ProductCard product={product} />
      <AdvicePanel advice={advice} />

      {alternatives.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="font-bold text-slate-900">Gợi ý thay thế tốt hơn</h3>
          <ul className="mt-3 space-y-2">
            {alternatives.map((alt) => (
              <li key={alt.barcode}>
                <Link
                  to={`/result/${alt.barcode}`}
                  className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 hover:bg-emerald-50"
                >
                  <span className="font-medium text-slate-800">{alt.name}</span>
                  <div className="flex items-center gap-2">
                    <SourceBadge source={alt.source} />
                    {alt.nutri_score && (
                      <span className="text-xs text-slate-500">NS: {alt.nutri_score.toUpperCase()}</span>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Disclaimer />

      <div className="flex gap-3">
        <Link
          to="/scan"
          className="flex-1 rounded-xl bg-emerald-600 py-3 text-center font-medium text-white hover:bg-emerald-700"
        >
          Quét sản phẩm khác
        </Link>
        <Link
          to="/history"
          className="rounded-xl border border-slate-300 px-4 py-3 font-medium text-slate-700 hover:bg-slate-50"
        >
          Lịch sử
        </Link>
      </div>
    </div>
  )
}
