from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.additives_kb import extract_additives_from_text
from app.core.database import get_db
from app.schemas.product import (
    AdditiveOut,
    AdviceOut,
    AdviceRequest,
    IngredientsAdviceRequest,
    NutrientOut,
    ProductOut,
    ProfilePreset,
    UserProfile,
)
from app.services.advice_engine import AdviceEngine
from app.services.product_lookup import ProductLookupService

router = APIRouter(prefix="/advice", tags=["advice"])

PROFILE_PRESETS = [
    ProfilePreset(
        id="healthy_adult",
        label="Người trưởng thành khỏe mạnh",
        description="Không bệnh lý, mục tiêu ăn lành mạnh",
        profile=UserProfile(goals=["healthy_eating"]),
    ),
    ProfilePreset(
        id="diabetes",
        label="Tiểu đường",
        description="Cần hạn chế đường và tinh bột nhanh",
        profile=UserProfile(conditions=["diabetes"], goals=["low_sugar"]),
    ),
    ProfilePreset(
        id="hypertension",
        label="Cao huyết áp",
        description="Cần hạn chế muối/natri",
        profile=UserProfile(conditions=["hypertension"], goals=["low_sodium"]),
    ),
    ProfilePreset(
        id="newborn",
        label="Trẻ sơ sinh (0-12 tháng)",
        description="Chỉ sữa mẹ/công thức theo bác sĩ",
        profile=UserProfile(age_group="newborn", goals=["healthy_eating"]),
    ),
    ProfilePreset(
        id="age_2_4",
        label="Trẻ 2-4 tuổi",
        description="Mầm non, hạn chế đường và đồ siêu chế biến",
        profile=UserProfile(age_group="age_2_4", goals=["healthy_eating"]),
    ),
    ProfilePreset(
        id="age_6_12",
        label="Trẻ 6-12 tuổi",
        description="Tiểu học, kiểm soát muối và đồ ăn vặt",
        profile=UserProfile(age_group="age_6_12", goals=["healthy_eating"]),
    ),
    ProfilePreset(
        id="weight_loss",
        label="Giảm cân",
        description="Ưu tiên ít calo, ít đường",
        profile=UserProfile(goals=["weight_loss", "low_sugar"]),
    ),
]


@router.get("/presets", response_model=list[ProfilePreset])
def get_profile_presets():
    return PROFILE_PRESETS


@router.post("/evaluate", response_model=AdviceOut)
async def evaluate_advice(request: AdviceRequest, db: Session = Depends(get_db)):
    lookup = ProductLookupService(db)
    product = await lookup.lookup(request.barcode)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    nutrients = lookup.get_nutrient_map(product)
    engine = AdviceEngine()
    result = engine.evaluate(product, request.profile, nutrients)

    return AdviceOut(
        barcode=request.barcode,
        product_name=product.name,
        suitability_score=result["suitability_score"],
        suitability_label=result["suitability_label"],
        summary=result["summary"],
        warnings=result["warnings"],
        positives=result["positives"],
    )


@router.post("/evaluate-ingredients", response_model=AdviceOut)
async def evaluate_ingredients_advice(request: IngredientsAdviceRequest):
    normalized_text = request.ingredients_text.replace(";", ",").replace("\n", ",")
    ingredients = [p.strip() for p in normalized_text.split(",") if p.strip()]

    # Nhận diện phụ gia (E-number + tên thông dụng) ngay từ text để rule phụ gia có thể kích hoạt
    detected = extract_additives_from_text(request.ingredients_text)
    additives = [
        AdditiveOut(e_number=a["e_number"], name=a["name"], risk_level=a["risk"]) for a in detected
    ]

    # Số liệu dinh dưỡng tùy chọn: cho phép đánh giá sâu hơn (rule dinh dưỡng)
    nutrients: dict[str, float] = {}
    if request.sugars is not None:
        nutrients["sugars"] = request.sugars
    if request.saturated_fat is not None:
        nutrients["saturated_fat"] = request.saturated_fat
    if request.energy_kcal is not None:
        nutrients["energy_kcal"] = request.energy_kcal
    if request.proteins is not None:
        nutrients["proteins"] = request.proteins
    if request.sodium is not None:
        nutrients["sodium"] = request.sodium
        nutrients.setdefault("salt", round(request.sodium / 400.0, 3))
    if request.salt is not None:
        nutrients["salt"] = request.salt
        # 1g muối ≈ 400mg natri
        nutrients.setdefault("sodium", round(request.salt * 400.0, 1))

    pseudo_product = ProductOut(
        barcode="ocr-upload",
        name="Sản phẩm từ thành phần",
        brand=None,
        category=None,
        source="ocr",
        source_url=None,
        image_url=None,
        ingredients_text=request.ingredients_text,
        allergens=None,
        nutri_score=None,
        nova_group=None,
        nutrients=[
            NutrientOut(nutrient_code=code, amount=amount, unit=None) for code, amount in nutrients.items()
        ],
        ingredients=[{"position": idx, "name": item} for idx, item in enumerate(ingredients)],
        additives=additives,
        alerts=[],
    )
    engine = AdviceEngine()
    result = engine.evaluate(pseudo_product, request.profile, nutrients=nutrients)
    return AdviceOut(
        barcode="ocr-upload",
        product_name="Sản phẩm từ thành phần",
        suitability_score=result["suitability_score"],
        suitability_label=result["suitability_label"],
        summary=result["summary"],
        warnings=result["warnings"],
        positives=result["positives"],
        additives=additives,
    )
