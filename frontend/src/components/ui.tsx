const SOURCE_LABELS: Record<string, string> = {
  open_food_facts: 'Open Food Facts',
  usda_fdc: 'USDA FoodData Central',
  manual: 'Dữ liệu demo',
  bach_hoa_xanh: 'Bách Hóa Xanh',
  teko: 'Teko',
  aeon: 'AEON',
  bigc_go: 'BigC/GO',
  ocr: 'OCR ảnh',
}

export function SourceBadge({ source, url }: { source: string; url?: string | null }) {
  const label = SOURCE_LABELS[source] || source
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
      Nguồn:{' '}
      {url ? (
        <a href={url} target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-900">
          {label}
        </a>
      ) : (
        label
      )}
    </span>
  )
}

export function Disclaimer() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <strong>Lưu ý y tế:</strong> Thông tin trên app chỉ mang tính tham khảo, không thay thế tư vấn của bác sĩ
      hoặc chuyên gia dinh dưỡng. Hãy tham khảo ý kiến chuyên môn trước khi thay đổi chế độ ăn.
    </div>
  )
}

export function ScoreBadge({ score, label }: { score: number; label: string }) {
  let color = 'bg-red-100 text-red-800 border-red-200'
  if (score >= 85) color = 'bg-emerald-100 text-emerald-800 border-emerald-200'
  else if (score >= 70) color = 'bg-green-100 text-green-800 border-green-200'
  else if (score >= 50) color = 'bg-yellow-100 text-yellow-800 border-yellow-200'
  else if (score >= 30) color = 'bg-orange-100 text-orange-800 border-orange-200'

  return (
    <div className={`inline-flex flex-col items-center rounded-2xl border-2 px-6 py-4 ${color}`}>
      <span className="text-4xl font-bold">{score}</span>
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}

const SEVERITY_STYLES = {
  danger: 'border-red-300 bg-red-50 text-red-900',
  warning: 'border-orange-300 bg-orange-50 text-orange-900',
  caution: 'border-yellow-300 bg-yellow-50 text-yellow-900',
  info: 'border-blue-300 bg-blue-50 text-blue-900',
}

export function WarningCard({
  severity,
  title,
  message,
  evidence,
}: {
  severity: keyof typeof SEVERITY_STYLES
  title: string
  message: string
  evidence?: string | null
}) {
  return (
    <div className={`rounded-xl border p-4 ${SEVERITY_STYLES[severity]}`}>
      <h4 className="font-semibold">{title}</h4>
      <p className="mt-1 text-sm">{message}</p>
      {evidence && <p className="mt-2 text-xs opacity-75">Tham chiếu: {evidence}</p>}
    </div>
  )
}
