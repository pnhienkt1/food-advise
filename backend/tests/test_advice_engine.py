import pytest

from app.schemas.product import ProductOut, UserProfile
from app.services.advice_engine import AdviceEngine, evaluate_rules


def _make_product(**kwargs) -> ProductOut:
    defaults = {
        "barcode": "8934564010014",
        "name": "Mì Hảo Hảo",
        "brand": "Acecook",
        "category": "Instant noodles",
        "source": "manual",
        "source_url": None,
        "image_url": None,
        "ingredients_text": "Bột mì, muối, đường, MSG (E621)",
        "allergens": "gluten",
        "nutri_score": "d",
        "nova_group": 4,
    }
    defaults.update(kwargs)
    return ProductOut(**defaults)


def test_diabetes_high_sugar_warning():
    product = _make_product()
    profile = UserProfile(conditions=["diabetes"])
    nutrients = {"sugars": 15, "sodium": 1400, "proteins": 9, "energy_kcal": 450}

    warnings, _, score = evaluate_rules(product, profile, nutrients)

    assert score < 70
    assert any(w["rule_id"] == "diabetes_high_sugar" for w in warnings)


def test_hypertension_high_sodium():
    product = _make_product()
    profile = UserProfile(conditions=["hypertension"])
    nutrients = {"sodium": 1400, "sugars": 3, "salt": 3.5}

    warnings, _, score = evaluate_rules(product, profile, nutrients)

    assert score < 70
    assert any(w["rule_id"] == "hypertension_high_sodium" for w in warnings)


def test_healthy_product_positive():
    product = _make_product(nutri_score="a", nova_group=1, name="Yến mạch")
    profile = UserProfile(goals=["healthy_eating"])
    nutrients = {"fiber": 10, "sugars": 1, "sodium": 2}

    warnings, positives, score = evaluate_rules(product, profile, nutrients)

    assert score > 70
    assert len(positives) > 0


def test_allergen_match():
    product = _make_product(allergens="en:gluten", ingredients_text="Bột mì, muối")
    profile = UserProfile(allergens=["gluten"])
    nutrients = {}

    warnings, _, score = evaluate_rules(product, profile, nutrients)

    assert score < 50
    assert any(w["rule_id"] == "allergen_match" for w in warnings)


def test_advice_engine_summary():
    product = _make_product()
    profile = UserProfile(conditions=["diabetes"])
    nutrients = {"sugars": 15, "sodium": 1400}

    engine = AdviceEngine()
    result = engine.evaluate(product, profile, nutrients)

    assert "suitability_score" in result
    assert result["summary"]
    assert len(result["warnings"]) > 0


def test_age_6_12_nova4_warning():
    product = _make_product(nova_group=4)
    profile = UserProfile(age_group="age_6_12")
    nutrients = {"sodium": 700}

    warnings, _, _ = evaluate_rules(product, profile, nutrients)

    assert any(w["rule_id"] in ("young_child_nova4", "age_6_12_high_sodium") for w in warnings)


def test_toddler_nova4_is_caution_not_danger():
    # A NOVA-4 toddler snack should be "limit intake" (caution), not a severe danger label
    product = _make_product(nova_group=4, nutri_score="c", ingredients_text="gạo, dâu, táo", allergens=None)
    profile = UserProfile(age_group="age_1_2", goals=["healthy_eating"])

    warnings, _, score = evaluate_rules(product, profile, {})

    assert all(w["severity"] != "danger" for w in warnings)
    assert score >= 50
    # Only a single NOVA warning should fire (no double/triple counting)
    nova_warnings = [w for w in warnings if "nova" in w["rule_id"]]
    assert len(nova_warnings) == 1


def test_newborn_instant_noodle_danger():
    product = _make_product(ingredients_text="Bột mì ăn liền, muối", nova_group=4)
    profile = UserProfile(age_group="newborn")
    nutrients = {"sodium": 200}

    warnings, _, score = evaluate_rules(product, profile, nutrients)

    assert score < 40
    assert any("newborn" in w["rule_id"] or "instant" in w["rule_id"] for w in warnings)
