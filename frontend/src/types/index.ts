export type AgeGroup =
  | 'newborn'
  | 'age_1_2'
  | 'age_2_4'
  | 'age_4_6'
  | 'age_6_12'
  | 'teen'
  | 'adult'
  | 'elderly'
  | 'pregnant'
export type HealthCondition = 'diabetes' | 'hypertension' | 'gout' | 'kidney' | 'celiac'
export type NutritionGoal = 'weight_loss' | 'muscle_gain' | 'healthy_eating' | 'low_sodium' | 'low_sugar' | 'low_sat_fat'

export interface UserProfile {
  age_group: AgeGroup
  conditions: HealthCondition[]
  goals: NutritionGoal[]
  allergens: string[]
}

export interface Nutrient {
  nutrient_code: string
  amount: number | null
  unit: string | null
  label?: string | null
}

export interface Product {
  barcode: string
  name: string
  brand: string | null
  category: string | null
  source: string
  source_url: string | null
  image_url: string | null
  ingredients_text: string | null
  allergens: string | null
  nutri_score: string | null
  nova_group: number | null
  nutrients: Nutrient[]
  ingredients: { position: number; name: string }[]
  additives: { e_number: string; name: string | null; risk_level: string | null }[]
  alerts: { alert_type: string; message: string; source_url: string | null }[]
}

export interface Warning {
  rule_id: string
  severity: 'info' | 'caution' | 'warning' | 'danger'
  title: string
  message: string
  evidence: string | null
}

export interface Advice {
  barcode: string
  product_name: string
  suitability_score: number
  suitability_label: string
  summary: string
  warnings: Warning[]
  positives: string[]
}

export interface OcrIngredientsResult {
  raw_text: string
  ingredients: string[]
  confidence: number | null
  notes: string | null
}

export interface ProductListItem {
  barcode: string
  name: string
  brand: string | null
  category: string | null
  source: string
  source_url: string | null
  image_url: string | null
  nutri_score: string | null
  nova_group: number | null
  ingredients_text: string | null
}

export interface ProductListResponse {
  total: number
  limit: number
  offset: number
  items: ProductListItem[]
}

export interface ProfilePreset {
  id: string
  label: string
  description: string
  profile: UserProfile
}

export interface ProductSearchResult {
  barcode: string
  name: string
  brand: string | null
  category: string | null
  image_url: string | null
}

export interface ScanHistoryItem {
  barcode: string
  productName: string
  score: number
  scannedAt: string
}

export interface RecommendationItem {
  barcode: string
  product_name: string
  brand: string | null
  category: string | null
  source: string
  nutri_score: string | null
  nova_group: number | null
  suitability_score: number
  suitability_label: string
  highlight: string | null
}
