import { useBarcodeScanner } from '../hooks/useBarcodeScanner'

interface BarcodeScannerProps {
  onScan: (barcode: string) => void
  manualBarcode: string
  onManualChange: (value: string) => void
  onManualSubmit: () => void
  loading?: boolean
}

export function BarcodeScanner({
  onScan,
  manualBarcode,
  onManualChange,
  onManualSubmit,
  loading,
}: BarcodeScannerProps) {
  const { containerId, isScanning, error, startScanning, stopScanning } = useBarcodeScanner(onScan)

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-900">
        <div id={containerId} className={`w-full ${isScanning ? 'min-h-[240px]' : 'hidden'}`} />
        {!isScanning && (
          <div className="flex min-h-[240px] items-center justify-center px-4 text-center text-slate-400">
            Camera chưa bật — nhấn nút bên dưới để quét
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {!isScanning ? (
          <button
            onClick={startScanning}
            disabled={loading}
            className="flex-1 rounded-xl bg-emerald-600 px-4 py-3 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Bật camera quét
          </button>
        ) : (
          <button
            onClick={stopScanning}
            className="flex-1 rounded-xl bg-slate-600 px-4 py-3 font-medium text-white hover:bg-slate-700"
          >
            Tắt camera
          </button>
        )}
      </div>

      {error && <p className="text-sm text-amber-700">{error}</p>}

      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <label className="block text-sm font-medium text-slate-700">Hoặc nhập mã barcode</label>
        <div className="mt-2 flex gap-2">
          <input
            type="text"
            value={manualBarcode}
            onChange={(e) => onManualChange(e.target.value)}
            placeholder="VD: 8934564010014 (Mì Hảo Hảo)"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            onKeyDown={(e) => e.key === 'Enter' && onManualSubmit()}
          />
          <button
            onClick={onManualSubmit}
            disabled={loading || !manualBarcode.trim()}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            Tra cứu
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Demo: thử mã <button type="button" className="text-emerald-600 underline" onClick={() => onManualChange('8934564010014')}>8934564010014</button> (Mì Hảo Hảo)
        </p>
      </div>
    </div>
  )
}
