import { useState } from 'react'
import { Link } from 'react-router-dom'
import { evaluateIngredientsAdvice, uploadIngredientsImage } from '../api/client'
import { AdvicePanel } from '../components/AdvicePanel'
import { Disclaimer } from '../components/ui'
import { useProfile } from '../hooks/useProfile'
import type { Advice, OcrIngredientsResult } from '../types'

export function OcrPage() {
  const { profile } = useProfile()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [ocr, setOcr] = useState<OcrIngredientsResult | null>(null)
  const [advice, setAdvice] = useState<Advice | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runOcr = async () => {
    if (!selectedFile) return
    setLoading(true)
    setError(null)
    try {
      const ocrResult = await uploadIngredientsImage(selectedFile)
      setOcr(ocrResult)
      setAdvice(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'OCR thất bại')
    } finally {
      setLoading(false)
    }
  }

  const runAdviceFromOcr = async () => {
    if (!ocr?.raw_text?.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await evaluateIngredientsAdvice(ocr.raw_text, profile)
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
        <h2 className="text-lg font-bold text-slate-900">OCR thành phần từ ảnh</h2>
        <p className="mt-1 text-sm text-slate-600">
          Chụp phần nhãn "Thành phần/Ingredients" để hệ thống đọc chữ và đánh giá phù hợp theo hồ sơ.
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
          disabled={!selectedFile || loading}
          className="mt-3 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? 'Đang OCR...' : 'Đọc thành phần từ ảnh'}
        </button>
        {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      </div>

      {ocr && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-slate-900">Kết quả OCR</h3>
          {ocr.notes && <p className="mt-1 text-xs text-slate-500">{ocr.notes}</p>}
          <p className="mt-3 text-sm whitespace-pre-wrap text-slate-700">{ocr.raw_text || '(Không đọc được chữ)'}</p>
          {ocr.ingredients.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {ocr.ingredients.map((item, idx) => (
                <span key={`${item}-${idx}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                  {item}
                </span>
              ))}
            </div>
          )}
          <button
            onClick={runAdviceFromOcr}
            disabled={loading || !ocr.raw_text}
            className="mt-4 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 disabled:opacity-50"
          >
            Đánh giá theo thành phần OCR
          </button>
        </div>
      )}

      {advice && <AdvicePanel advice={advice} />}

      <Disclaimer />
      <Link to="/scan" className="inline-block text-sm text-emerald-700 hover:underline">
        Quay lại trang quét barcode
      </Link>
    </div>
  )
}
