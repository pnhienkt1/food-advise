import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { BarcodeScanner } from '../components/BarcodeScanner'
import { ProductSearch } from '../components/ProductSearch'
import { ProfilePicker } from '../components/ProfilePicker'
import { Disclaimer } from '../components/ui'
import { useProfile } from '../hooks/useProfile'

export function ScanPage() {
  const navigate = useNavigate()
  const { profile, setProfile } = useProfile()
  const [manualBarcode, setManualBarcode] = useState('')

  const handleScan = (barcode: string) => {
    navigate(`/result/${encodeURIComponent(barcode)}`)
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4">
      <ProductSearch onSelect={handleScan} />
      <BarcodeScanner
        onScan={handleScan}
        manualBarcode={manualBarcode}
        onManualChange={setManualBarcode}
        onManualSubmit={() => {
          if (manualBarcode.trim()) {
            handleScan(manualBarcode.trim())
          }
        }}
      />
      <ProfilePicker profile={profile} onChange={setProfile} />
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
        Không quét được barcode?{' '}
        <Link to="/ocr" className="font-medium text-emerald-700 underline">
          Chuyển sang OCR thành phần từ ảnh
        </Link>
        .
      </div>
      <Disclaimer />
    </div>
  )
}
