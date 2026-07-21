import { useEffect, useState } from 'react'
import { getProfilePresets } from '../api/client'
import type { AgeGroup, HealthCondition, NutritionGoal, ProfilePreset, UserProfile } from '../types'

const AGE_OPTIONS: { value: AgeGroup; label: string }[] = [
  { value: 'newborn', label: 'Trẻ sơ sinh (0-12 tháng)' },
  { value: 'age_1_2', label: 'Trẻ 1-2 tuổi' },
  { value: 'age_2_4', label: 'Trẻ 2-4 tuổi' },
  { value: 'age_4_6', label: 'Trẻ 4-6 tuổi' },
  { value: 'age_6_12', label: 'Trẻ 6-12 tuổi' },
  { value: 'teen', label: 'Thanh thiếu niên (12-18)' },
  { value: 'adult', label: 'Người trưởng thành' },
  { value: 'elderly', label: 'Người cao tuổi' },
  { value: 'pregnant', label: 'Mang thai / cho con bú' },
]

const CONDITION_OPTIONS: { value: HealthCondition; label: string }[] = [
  { value: 'diabetes', label: 'Tiểu đường' },
  { value: 'hypertension', label: 'Cao huyết áp' },
  { value: 'gout', label: 'Gout' },
  { value: 'kidney', label: 'Bệnh thận' },
  { value: 'celiac', label: 'Celiac (dị ứng gluten)' },
]

const GOAL_OPTIONS: { value: NutritionGoal; label: string }[] = [
  { value: 'healthy_eating', label: 'Ăn lành mạnh' },
  { value: 'weight_loss', label: 'Giảm cân' },
  { value: 'muscle_gain', label: 'Tăng cơ' },
  { value: 'low_sodium', label: 'Hạn chế muối' },
  { value: 'low_sugar', label: 'Hạn chế đường' },
  { value: 'low_sat_fat', label: 'Hạn chế chất béo bão hòa' },
]

const ALLERGEN_OPTIONS = ['gluten', 'sữa', 'tôm', 'cua', 'đậu phộng', 'trứng', 'đậu nành', 'cá']

interface ProfilePickerProps {
  profile: UserProfile
  onChange: (profile: UserProfile) => void
}

export function ProfilePicker({ profile, onChange }: ProfilePickerProps) {
  const [presets, setPresets] = useState<ProfilePreset[]>([])

  useEffect(() => {
    getProfilePresets().then(setPresets).catch(() => {})
  }, [])

  const toggleArray = <T extends string>(arr: T[], value: T): T[] =>
    arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value]

  return (
    <div className="space-y-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h2 className="text-lg font-bold text-slate-900">Hồ sơ sức khỏe</h2>
        <p className="text-sm text-slate-600">Chọn nhanh để nhận đánh giá phù hợp — không cần đăng nhập</p>
      </div>

      {presets.length > 0 && (
        <div>
          <label className="text-sm font-medium text-slate-700">Preset nhanh</label>
          <div className="mt-2 flex flex-wrap gap-2">
            {presets.map((p) => (
              <button
                key={p.id}
                onClick={() => onChange(p.profile)}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-sm hover:border-emerald-500 hover:bg-emerald-50"
                title={p.description}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <label className="text-sm font-medium text-slate-700">Nhóm tuổi</label>
        <select
          value={profile.age_group}
          onChange={(e) => onChange({ ...profile, age_group: e.target.value as AgeGroup })}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {AGE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-sm font-medium text-slate-700">Bệnh lý / hạn chế</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {CONDITION_OPTIONS.map((o) => (
            <button
              key={o.value}
              onClick={() => onChange({ ...profile, conditions: toggleArray(profile.conditions, o.value) })}
              className={`rounded-full px-3 py-1.5 text-sm ${
                profile.conditions.includes(o.value)
                  ? 'bg-red-100 text-red-800 ring-2 ring-red-300'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="text-sm font-medium text-slate-700">Mục tiêu dinh dưỡng</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {GOAL_OPTIONS.map((o) => (
            <button
              key={o.value}
              onClick={() => onChange({ ...profile, goals: toggleArray(profile.goals, o.value) })}
              className={`rounded-full px-3 py-1.5 text-sm ${
                profile.goals.includes(o.value)
                  ? 'bg-emerald-100 text-emerald-800 ring-2 ring-emerald-300'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="text-sm font-medium text-slate-700">Dị ứng thực phẩm</label>
        <div className="mt-2 flex flex-wrap gap-2">
          {ALLERGEN_OPTIONS.map((a) => (
            <button
              key={a}
              onClick={() => onChange({ ...profile, allergens: toggleArray(profile.allergens, a) })}
              className={`rounded-full px-3 py-1.5 text-sm ${
                profile.allergens.includes(a)
                  ? 'bg-orange-100 text-orange-800 ring-2 ring-orange-300'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {a}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
