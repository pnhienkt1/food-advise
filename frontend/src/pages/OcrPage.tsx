import { useState } from 'react'
import { Link } from 'react-router-dom'
import { evaluateIngredientsAdvice, uploadIngredientsImage } from '../api/client'
import { AdvicePanel } from '../components/AdvicePanel'
import { Disclaimer } from '../components/ui'
import { useProfile } from '../hooks/useProfile'
import type { Advice, OcrIngredientsResult } from '../types'

export function OcrPage() {
  const { profile } = useProfile()
  const [ingredientsText, setIngredientsText] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [ocr, setOcr] = useState<OcrIngredientsResult | null>(null)
  const [advice, setAdvice] = useState<Advice | null>(null)
  const [loading, setLoading] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canEvaluate = ingredientsText.trim().length >= 2

  const runOcr = async () => {
    if (!selectedFile) return
    setOcrLoading(true)
    setError(null)
    try {
      const ocrResult = await uploadIngredientsImage(selectedFile)
      setOcr(ocrResult)
      setAdvice(null)
      // Đưa kết quả OCR vào ô thành phần để người dùng chỉnh sửa nếu nhận dạng chưa đúng
      if (ocrResult.raw_text?.trim()) {
        setIngredientsText(ocrResult.raw_text.trim())
      } else if (ocrResult.ingredients.length > 0) {
        setIngredientsText(ocrResult.ingredients.join(', '))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'OCR thất bại')
    } finally {
      setOcrLoading(false)
    }
  }

  const runAdvice = async () => {
    if (!canEvaluate) return
    setLoading(true)
    setError(null)
    try {
      const result = await evaluateIngredientsAdvice(ingredientsText, profile)
      setAdvice(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Đánh giá thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">Tra cứu theo thành phần</h2>
        <p className="mt-1 text-sm text-slate-600">
          Nhập một hoặc nhiều thành phần (phân tách bằng dấu phẩy hoặc xuống dòng) để đánh giá mức độ
          phù hợp theo hồ sơ sức khỏe của bạn.
        </p>
        <textarea
          value={ingredientsText}
          onChange={(e) => setIngredientsText(e.target.value)}
          rows={5}
          placeholder="VD: đường, muối, bột mì, dầu cọ, chất bảo quản, bột ngọt (E621)..."
          className="mt-4 block w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-800 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
        />
        <button
          onClick={runAdvice}
          disabled={!canEvaluate || loading}
          className="mt-3 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? 'Đang đánh giá...' : 'Đánh giá theo hồ sơ'}
        </button>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="font-semibold text-slate-900">Hoặc quét thành phần từ ảnh (OCR)</h3>
        <p className="mt-1 text-sm text-slate-600">
          Chụp phần nhãn "Thành phần/Ingredients". Kết quả OCR sẽ được đưa vào ô phía trên để bạn
          chỉnh sửa trước khi đánh giá (hữu ích khi OCR nhận dạng chưa chính xác).
        </p>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          className="mt-4 block w-full text-sm"
          onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
        />
        <button
          onClick={runOcr}
          disabled={!selectedFile || ocrLoading}
          className="mt-3 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 disabled:opacity-50"
        >
          {ocrLoading ? 'Đang OCR...' : 'Đọc thành phần từ ảnh'}
        </button>

        {ocr && (
          <div className="mt-4 border-t border-slate-100 pt-4">
            {ocr.notes && <p className="text-xs text-slate-500">{ocr.notes}</p>}
            {ocr.ingredients.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-2">
                {ocr.ingredients.map((item, idx) => (
                  <span
                    key={`${item}-${idx}`}
                    className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
                  >
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-slate-500">(Không đọc được chữ — hãy nhập tay phía trên)</p>
            )}
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      {advice && <AdvicePanel advice={advice} />}

      <Disclaimer />
      <Link to="/scan" className="inline-block text-sm text-emerald-700 hover:underline">
        Quay lại trang quét barcode
      </Link>
    </div>
  )
}
