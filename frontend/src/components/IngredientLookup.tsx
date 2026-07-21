import { useEffect, useRef, useState } from 'react'
import type { QuickNutrients } from '../api/client'
import { evaluateIngredientsAdvice, uploadIngredientsImage } from '../api/client'
import { AdvicePanel } from './AdvicePanel'
import { AdditiveBadge } from './ui'
import { useProfile } from '../hooks/useProfile'
import type { Advice, OcrIngredientsResult } from '../types'

export function IngredientLookup() {
  const { profile } = useProfile()
  const [ingredientsText, setIngredientsText] = useState('')
  const [sugars, setSugars] = useState('')
  const [salt, setSalt] = useState('')
  const [ocr, setOcr] = useState<OcrIngredientsResult | null>(null)
  const [advice, setAdvice] = useState<Advice | null>(null)
  const [loading, setLoading] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [streaming, setStreaming] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [capturedPreview, setCapturedPreview] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const canEvaluate = ingredientsText.trim().length >= 2

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setStreaming(false)
  }

  // Dọn dẹp camera khi rời khỏi trang
  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  const startCamera = async () => {
    setCameraError(null)
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Trình duyệt không hỗ trợ camera. Hãy dùng nút tải ảnh bên dưới.')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      })
      streamRef.current = stream
      setStreaming(true)
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
    } catch {
      setCameraError('Không truy cập được camera (kiểm tra quyền truy cập). Hãy dùng nút tải ảnh bên dưới.')
      setStreaming(false)
    }
  }

  const runOcrOnFile = async (file: File) => {
    setOcrLoading(true)
    setError(null)
    try {
      const ocrResult = await uploadIngredientsImage(file)
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

  const capturePhoto = () => {
    const video = videoRef.current
    if (!video || !video.videoWidth) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    setCapturedPreview(canvas.toDataURL('image/jpeg', 0.92))
    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
        stopCamera()
        runOcrOnFile(file)
      },
      'image/jpeg',
      0.92,
    )
  }

  const runAdvice = async () => {
    if (!canEvaluate) return
    setLoading(true)
    setError(null)
    try {
      const nutrients: QuickNutrients = {}
      const s = parseFloat(sugars.replace(',', '.'))
      const m = parseFloat(salt.replace(',', '.'))
      if (!Number.isNaN(s)) nutrients.sugars = s
      if (!Number.isNaN(m)) nutrients.salt = m
      const result = await evaluateIngredientsAdvice(ingredientsText, profile, nutrients)
      setAdvice(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Đánh giá thất bại')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="font-semibold text-slate-900">Quét thành phần bằng camera (OCR)</h3>
        <p className="mt-1 text-sm text-slate-600">
          Chụp phần nhãn "Thành phần/Ingredients" trực tiếp bằng camera, hoặc tải ảnh có sẵn. Kết quả
          OCR sẽ đưa vào ô thành phần bên dưới để bạn chỉnh sửa trước khi đánh giá.
        </p>

        <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-slate-900">
          <video
            ref={videoRef}
            playsInline
            muted
            className={`w-full ${streaming ? 'min-h-[240px]' : 'hidden'}`}
          />
          {!streaming && (
            <div className="flex min-h-[200px] items-center justify-center px-4 text-center text-slate-400">
              {capturedPreview ? (
                <img src={capturedPreview} alt="Ảnh vừa chụp" className="max-h-[240px] w-auto" />
              ) : (
                'Camera chưa bật — nhấn "Bật camera" để chụp nhãn thành phần'
              )}
            </div>
          )}
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {!streaming ? (
            <button
              onClick={startCamera}
              disabled={ocrLoading}
              className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Bật camera
            </button>
          ) : (
            <>
              <button
                onClick={capturePhoto}
                className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
              >
                Chụp & đọc thành phần
              </button>
              <button
                onClick={stopCamera}
                className="rounded-xl bg-slate-600 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
              >
                Tắt camera
              </button>
            </>
          )}

          <label className="cursor-pointer rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-100">
            Tải ảnh có sẵn
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  setCapturedPreview(URL.createObjectURL(file))
                  runOcrOnFile(file)
                }
              }}
            />
          </label>
        </div>

        {ocrLoading && <p className="mt-2 text-sm text-slate-500">Đang đọc chữ (OCR)...</p>}
        {cameraError && <p className="mt-2 text-sm text-amber-700">{cameraError}</p>}

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
              <p className="mt-2 text-sm text-slate-500">(Không đọc được chữ — hãy nhập tay bên dưới)</p>
            )}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="font-semibold text-slate-900">Hoặc nhập thành phần thủ công</h3>
        <p className="mt-1 text-sm text-slate-600">
          Nhập một hoặc nhiều thành phần (phân tách bằng dấu phẩy hoặc xuống dòng) để đánh giá mức độ
          phù hợp theo hồ sơ sức khỏe của bạn.
        </p>
        <textarea
          value={ingredientsText}
          onChange={(e) => setIngredientsText(e.target.value)}
          rows={4}
          placeholder="VD: đường, muối, bột mì, dầu cọ, chất bảo quản, bột ngọt (E621)..."
          className="mt-4 block w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-800 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
        />
        <details className="mt-3 rounded-xl bg-slate-50 p-3">
          <summary className="cursor-pointer text-sm font-medium text-slate-700">
            Đánh giá sâu hơn (tùy chọn): nhập số liệu dinh dưỡng
          </summary>
          <p className="mt-2 text-xs text-slate-500">
            Vì chỉ có thành phần nên hệ thống thiếu số liệu dinh dưỡng. Nhập nhanh để có cảnh báo chính
            xác hơn theo hồ sơ.
          </p>
          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            <label className="text-sm text-slate-700">
              Đường (g/100g)
              <input
                type="number"
                min="0"
                step="0.1"
                value={sugars}
                onChange={(e) => setSugars(e.target.value)}
                placeholder="VD: 20"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </label>
            <label className="text-sm text-slate-700">
              Muối (g/100g)
              <input
                type="number"
                min="0"
                step="0.1"
                value={salt}
                onChange={(e) => setSalt(e.target.value)}
                placeholder="VD: 1.5"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </label>
          </div>
        </details>
        <button
          onClick={runAdvice}
          disabled={!canEvaluate || loading}
          className="mt-3 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? 'Đang đánh giá...' : 'Đánh giá theo hồ sơ'}
        </button>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}

      {advice && (
        <>
          <AdvicePanel advice={advice} />
          {advice.additives.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="font-semibold text-slate-900">Phụ gia phát hiện trong thành phần</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {advice.additives.map((a) => (
                  <AdditiveBadge key={a.e_number} eNumber={a.e_number} name={a.name} risk={a.risk_level} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
