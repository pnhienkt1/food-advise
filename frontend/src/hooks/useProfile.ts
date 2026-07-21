import { useCallback, useState } from 'react'
import type { UserProfile } from '../types'

const PROFILE_KEY = 'food_advise_profile'

export const DEFAULT_PROFILE: UserProfile = {
  age_group: 'adult',
  conditions: [],
  goals: ['healthy_eating'],
  allergens: [],
}

export function useProfile() {
  const [profile, setProfileState] = useState<UserProfile>(() => {
    try {
      const saved = localStorage.getItem(PROFILE_KEY)
      return saved ? JSON.parse(saved) : DEFAULT_PROFILE
    } catch {
      return DEFAULT_PROFILE
    }
  })

  const setProfile = useCallback((p: UserProfile) => {
    setProfileState(p)
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p))
  }, [])

  return { profile, setProfile }
}

export function useScanHistory() {
  const HISTORY_KEY = 'food_advise_history'

  const [history, setHistory] = useState<{ barcode: string; productName: string; score: number; scannedAt: string }[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
    } catch {
      return []
    }
  })

  const addToHistory = useCallback((item: { barcode: string; productName: string; score: number }) => {
    setHistory((prev) => {
      const filtered = prev.filter((h) => h.barcode !== item.barcode)
      const next = [{ ...item, scannedAt: new Date().toISOString() }, ...filtered].slice(0, 20)
      localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
      return next
    })
  }, [])

  const clearHistory = useCallback(() => {
    setHistory([])
    localStorage.removeItem(HISTORY_KEY)
  }, [])

  return { history, addToHistory, clearHistory }
}
