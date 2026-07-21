import { Link } from 'react-router-dom'
import { Disclaimer } from '../components/ui'
import { useScanHistory } from '../hooks/useProfile'

export function HistoryPage() {
  const { history, clearHistory } = useScanHistory()

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">Lịch sử quét</h2>
        {history.length > 0 && (
          <button onClick={clearHistory} className="text-sm text-red-600 hover:underline">
            Xóa tất cả
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-500">
          Chưa có lịch sử quét. Hãy thử quét một sản phẩm!
        </div>
      ) : (
        <ul className="space-y-2">
          {history.map((item) => (
            <li key={item.barcode}>
              <Link
                to={`/result/${item.barcode}`}
                className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 hover:border-emerald-300 hover:bg-emerald-50"
              >
                <div>
                  <p className="font-medium text-slate-900">{item.productName}</p>
                  <p className="text-xs text-slate-500">
                    {item.barcode} · {new Date(item.scannedAt).toLocaleString('vi-VN')}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-sm font-bold ${
                    item.score >= 70
                      ? 'bg-emerald-100 text-emerald-800'
                      : item.score >= 50
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                  }`}
                >
                  {item.score}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <Disclaimer />

      <Link to="/scan" className="block text-center text-emerald-600 hover:underline">
        Quay lại quét
      </Link>
    </div>
  )
}
