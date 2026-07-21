import pytest

from app.sync.quality import meets_import_quality, quality_score


def test_quality_rejects_incomplete():
    ok, reason = meets_import_quality({"product": {"code": "123", "product_name": "Test"}})
    assert not ok
    assert reason == "incomplete_nutrition"


def test_quality_accepts_complete():
    data = {
        "product": {
            "code": "1234567890123",
            "product_name": "Sữa tươi",
            "ingredients_text": "Sữa tươi 100%",
            "nutriments": {"energy-kcal_100g": 60, "proteins_100g": 3, "fat_100g": 3.2},
            "nutrition_grades": "b",
            "nova_group": 1,
        }
    }
    ok, reason = meets_import_quality(data)
    assert ok
    assert quality_score(data) >= 40
