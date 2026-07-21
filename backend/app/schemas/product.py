from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgeGroup(str, Enum):
    NEWBORN = "newborn"
    AGE_1_2 = "age_1_2"
    AGE_2_4 = "age_2_4"
    AGE_4_6 = "age_4_6"
    AGE_6_12 = "age_6_12"
    TEEN = "teen"
    ADULT = "adult"
    ELDERLY = "elderly"
    PREGNANT = "pregnant"


class HealthCondition(str, Enum):
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    GOUT = "gout"
    KIDNEY = "kidney"
    CELIAC = "celiac"


class NutritionGoal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    HEALTHY_EATING = "healthy_eating"
    LOW_SODIUM = "low_sodium"
    LOW_SUGAR = "low_sugar"
    LOW_SAT_FAT = "low_sat_fat"


class UserProfile(BaseModel):
    age_group: AgeGroup = AgeGroup.ADULT
    conditions: list[HealthCondition] = Field(default_factory=list)
    goals: list[NutritionGoal] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)


class NutrientOut(BaseModel):
    nutrient_code: str
    amount: float | None
    unit: str | None
    label: str | None = None

    model_config = {"from_attributes": True}


class IngredientOut(BaseModel):
    position: int
    name: str

    model_config = {"from_attributes": True}


class AdditiveOut(BaseModel):
    e_number: str
    name: str | None
    risk_level: str | None

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    alert_type: str
    message: str
    source_url: str | None

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    barcode: str
    name: str
    brand: str | None
    category: str | None
    source: str
    source_url: str | None
    image_url: str | None
    ingredients_text: str | None
    allergens: str | None
    nutri_score: str | None
    nova_group: int | None
    nutrients: list[NutrientOut] = Field(default_factory=list)
    ingredients: list[IngredientOut] = Field(default_factory=list)
    additives: list[AdditiveOut] = Field(default_factory=list)
    alerts: list[AlertOut] = Field(default_factory=list)
    last_synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class WarningSeverity(str, Enum):
    INFO = "info"
    CAUTION = "caution"
    WARNING = "warning"
    DANGER = "danger"


class WarningOut(BaseModel):
    rule_id: str
    severity: WarningSeverity
    title: str
    message: str
    evidence: str | None = None


class AdviceOut(BaseModel):
    barcode: str
    product_name: str
    suitability_score: int
    suitability_label: str
    summary: str
    warnings: list[WarningOut]
    positives: list[str] = Field(default_factory=list)


class AdviceRequest(BaseModel):
    barcode: str
    profile: UserProfile


class IngredientsAdviceRequest(BaseModel):
    ingredients_text: str = Field(min_length=2, max_length=10000)
    profile: UserProfile


class OcrIngredientsOut(BaseModel):
    raw_text: str
    ingredients: list[str] = Field(default_factory=list)
    confidence: float | None = None
    notes: str | None = None


class ProfilePreset(BaseModel):
    id: str
    label: str
    description: str
    profile: UserProfile


class ProductSearchResult(BaseModel):
    barcode: str
    name: str
    brand: str | None
    category: str | None
    image_url: str | None = None

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    barcode: str
    name: str
    brand: str | None
    category: str | None
    source: str
    source_url: str | None = None
    image_url: str | None = None
    nutri_score: str | None = None
    nova_group: int | None = None
    ingredients_text: str | None = None

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProductListItem] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    barcode: str
    product_name: str
    brand: str | None
    category: str | None
    source: str
    nutri_score: str | None
    nova_group: int | None
    suitability_score: int
    suitability_label: str
    highlight: str | None = None


class RecommendationsOut(BaseModel):
    total_evaluated: int
    recommendations: list[RecommendationItem]
    profile_note: str
