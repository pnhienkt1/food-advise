import type { Advice } from '../types'
import { ScoreBadge, WarningCard } from './ui'

export function AdvicePanel({ advice }: { advice: Advice }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col items-center gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:flex-row sm:items-start">
        <ScoreBadge score={advice.suitability_score} label={advice.suitability_label} />
        <div className="flex-1 text-center sm:text-left">
          <h3 className="text-lg font-bold text-slate-900">Đánh giá phù hợp</h3>
          <p className="mt-2 text-slate-700">{advice.summary}</p>
        </div>
      </div>

      {advice.positives.length > 0 && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <h3 className="font-semibold text-emerald-900">Điểm tích cực</h3>
          <ul className="mt-2 list-inside list-disc text-sm text-emerald-800">
            {advice.positives.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {advice.warnings.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-900">Cảnh báo & lưu ý</h3>
          {advice.warnings.map((w) => (
            <WarningCard
              key={w.rule_id}
              severity={w.severity}
              title={w.title}
              message={w.message}
              evidence={w.evidence}
            />
          ))}
        </div>
      )}
    </div>
  )
}
