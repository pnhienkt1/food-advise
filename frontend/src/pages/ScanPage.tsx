import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarcodeScanner } from '../components/BarcodeScanner'
import { IngredientLookup } from '../components/IngredientLookup'
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

      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          Hoặc quét theo thành phần
        </span>
        <span className="h-px flex-1 bg-slate-200" />
      </div>
      <p className="text-sm text-slate-600">
        Không có barcode hoặc không quét được? Quét/nhập thành phần để đánh giá song song.
      </p>
      <IngredientLookup />

      <Disclaimer />
    </div>
  )
}
