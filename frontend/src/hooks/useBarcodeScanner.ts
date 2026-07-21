import { useCallback, useEffect, useRef, useState } from 'react'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'

const BARCODE_FORMATS = [
  Html5QrcodeSupportedFormats.EAN_13,
  Html5QrcodeSupportedFormats.EAN_8,
  Html5QrcodeSupportedFormats.UPC_A,
  Html5QrcodeSupportedFormats.UPC_E,
  Html5QrcodeSupportedFormats.CODE_128,
  Html5QrcodeSupportedFormats.CODE_39,
  Html5QrcodeSupportedFormats.QR_CODE,
]

export function useBarcodeScanner(onScan: (barcode: string) => void) {
  const [isScanning, setIsScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scannerRef = useRef<Html5Qrcode | null>(null)
  const onScanRef = useRef(onScan)
  const lastScanRef = useRef<string | null>(null)
  const containerId = 'barcode-scanner'

  useEffect(() => {
    onScanRef.current = onScan
  }, [onScan])

  const stopScanning = useCallback(async () => {
    if (scannerRef.current?.isScanning) {
      try {
        await scannerRef.current.stop()
        scannerRef.current.clear()
      } catch {
        /* ignore */
      }
    }
    setIsScanning(false)
  }, [])

  const startScanning = useCallback(async () => {
    setError(null)
    setIsScanning(true)
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
    try {
      if (!scannerRef.current) {
        scannerRef.current = new Html5Qrcode(containerId, {
          formatsToSupport: BARCODE_FORMATS,
          useBarCodeDetectorIfSupported: true,
          verbose: false,
        })
      }
      await scannerRef.current.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: (viewfinderWidth, viewfinderHeight) => {
            const width = Math.min(viewfinderWidth * 0.85, 320)
            const height = Math.min(viewfinderHeight * 0.35, 120)
            return { width: Math.floor(width), height: Math.floor(height) }
          },
          disableFlip: false,
        },
        (decodedText) => {
          const barcode = decodedText.trim()
          if (!barcode || barcode === lastScanRef.current) return
          lastScanRef.current = barcode
          onScanRef.current(barcode)
          stopScanning()
        },
        () => {}
      )
    } catch {
      setError('Không thể truy cập camera. Hãy nhập mã barcode thủ công.')
      setIsScanning(false)
    }
  }, [stopScanning])

  useEffect(() => {
    return () => {
      stopScanning()
    }
  }, [stopScanning])

  return { containerId, isScanning, error, startScanning, stopScanning }
}
