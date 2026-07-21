"""Quality gates for imported product data — only trusted, complete records pass."""

REQUIRED_NUTRIENT_KEYS = [
    "energy-kcal_100g",
    "proteins_100g",
    "fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "salt_100g",
    "sodium_100g",
]

TRUSTED_SOURCES = {
    "open_food_facts",
    "usda_fdc",
    "manual",
    "bach_hoa_xanh",
    "teko",
    "aeon",
    "bigc_go",
}


def _product_payload(data: dict) -> dict:
    return data.get("product", data)


def count_nutrients(nutriments: dict) -> int:
    if not nutriments:
        return 0
    return sum(
        1
        for key, val in nutriments.items()
        if (key.endswith("_100g") or key.endswith("_serving")) and val is not None
    )


def meets_import_quality(data: dict) -> tuple[bool, str]:
    """Return (passes, reason). Used before persisting OFF/USDA imports."""
    p = _product_payload(data)
    code = p.get("code") or data.get("code")
    if not code:
        return False, "missing_barcode"

    name = p.get("product_name_vi") or p.get("product_name") or p.get("product_name_en")
    if not name or len(name.strip()) < 2:
        return False, "missing_name"

    nutriments = p.get("nutriments") or {}
    nutrient_count = count_nutrients(nutriments)
    has_ingredients = bool(
        (p.get("ingredients_text_vi") or p.get("ingredients_text") or "").strip()
    )

    if nutrient_count < 2 and not has_ingredients:
        return False, "incomplete_nutrition"

    # Reject obvious non-food or stub entries
    if p.get("nova_group") is None and nutrient_count < 3 and not has_ingredients:
        return False, "low_quality_stub"

    return True, "ok"


def quality_score(data: dict) -> int:
    """0-100 completeness score for ranking imports."""
    p = _product_payload(data)
    score = 0
    if p.get("product_name_vi") or p.get("product_name"):
        score += 15
    if p.get("ingredients_text_vi") or p.get("ingredients_text"):
        score += 20
    if p.get("nutrition_grades"):
        score += 15
    if p.get("nova_group"):
        score += 10
    score += min(30, count_nutrients(p.get("nutriments") or {}) * 5)
    if p.get("image_front_url") or p.get("image_url"):
        score += 10
    return min(100, score)
