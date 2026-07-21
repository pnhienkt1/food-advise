import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRecommendations } from '../api/recommendations'
import { ProfilePicker } from '../components/ProfilePicker'
import { Disclaimer, SourceBadge } from '../components/ui'
import { useProfile } from '../hooks/useProfile'
import type { RecommendationItem } from '../types'

export function RecommendPage() {
  const { profile, setProfile } = useProfile()
  const [items, setItems] = useState<RecommendationItem[]>([])
  const [note, setNote] = useState('')
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState('')

  const load = () => {
    setLoading(true)
    setError(null)
    getRecommendations(profile, { limit: 20, minScore: 70, category: category || undefined })
      .then((res) => {
        setItems(res.recommendations)
        setNote(res.profile_note)
        setTotal(res.total_evaluated)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Gợi ý thực phẩm</h1>
        <p className="mt-1 text-sm text-slate-600">
          Sản phẩm phù hợp nhất với hồ sơ sức khỏe của bạn (điểm ≥ 70, không có cảnh báo nguy hiểm)
        </p>
      </div>

      <ProfilePicker profile={profile} onChange={setProfile} />

      <div className="flex gap-2">
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Lọc danh mục (VD: Milk, Water...)"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          onClick={load}
          disabled={loading}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading ? 'Đang tìm...' : 'Tìm gợi ý'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>
      )}

      {note && !loading && (
        <p className="text-sm text-slate-600">
          {note} · Đã đánh giá {total} sản phẩm
        </p>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-500">
          Chưa tìm thấy sản phẩm phù hợp. Thử điều chỉnh hồ sơ hoặc import thêm dữ liệu.
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((item, idx) => (
            <li key={item.barcode}>
              <Link
                to={`/result/${item.barcode}`}
                className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-emerald-300 hover:bg-emerald-50"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <span className="text-xs font-medium text-emerald-600">#{idx + 1}</span>
                    <h3 className="font-semibold text-slate-900">{item.product_name}</h3>
                    {item.brand && <p className="text-sm text-slate-500">{item.brand}</p>}
                    {item.highlight && (
                      <p className="mt-1 text-xs text-emerald-700">{item.highlight}</p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-2">
                      <SourceBadge source={item.source} />
                      {item.nutri_score && (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                          NS: {item.nutri_score.toUpperCase()}
                        </span>
                      )}
                      {item.nova_group && (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                          NOVA {item.nova_group}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-center">
                    <span className="text-2xl font-bold text-emerald-700">{item.suitability_score}</span>
                    <p className="text-xs text-slate-500">{item.suitability_label}</p>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <Disclaimer />
    </div>
  )
}
