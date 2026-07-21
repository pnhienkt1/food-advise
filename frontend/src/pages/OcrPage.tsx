import { Link } from 'react-router-dom'
import { IngredientLookup } from '../components/IngredientLookup'
import { Disclaimer } from '../components/ui'

export function OcrPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <div>
        <h2 className="text-lg font-bold text-slate-900">Tra cứu theo thành phần</h2>
        <p className="mt-1 text-sm text-slate-600">
          Quét nhãn thành phần bằng OCR hoặc nhập thủ công để đánh giá theo hồ sơ sức khỏe.
        </p>
      </div>
      <IngredientLookup />
      <Disclaimer />
      <Link to="/scan" className="inline-block text-sm text-emerald-700 hover:underline">
        Quay lại trang quét barcode
      </Link>
    </div>
  )
}
