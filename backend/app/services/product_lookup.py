import re
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.cache import cache_get, cache_set
from app.core.config import settings
from app.core.constants import NUTRIENT_LABELS, NUTRIENT_OFF_MAP, USDA_NUTRIENT_MAP
from app.models.product import (
    Product,
    ProductAdditive,
    ProductAlert,
    ProductIngredient,
    ProductNutrient,
)
from app.schemas.product import (
    AdditiveOut,
    AlertOut,
    IngredientOut,
    NutrientOut,
    ProductOut,
)


def _parse_off_additives(additives_tags: list[str] | None) -> list[tuple[str, str | None]]:
    if not additives_tags:
        return []
    result = []
    for tag in additives_tags:
        match = re.match(r"en:([eE]\d+[a-zA-Z]?)", tag)
        if match:
            result.append((match.group(1).upper(), tag.replace("en:", "").replace("-", " ").title()))
    return result


def _parse_ingredients(text: str | None) -> list[tuple[int, str]]:
    if not text:
        return []
    parts = re.split(r"[,;]", text)
    return [(i, p.strip()) for i, p in enumerate(parts) if p.strip()]


def _product_to_schema(product: Product) -> ProductOut:
    nutrients = [
        NutrientOut(
            nutrient_code=n.nutrient_code,
            amount=n.amount,
            unit=n.unit,
            label=NUTRIENT_LABELS.get(n.nutrient_code, n.nutrient_code),
        )
        for n in sorted(product.nutrients, key=lambda x: x.nutrient_code)
    ]
    return ProductOut(
        barcode=product.barcode,
        name=product.name,
        brand=product.brand,
        category=product.category,
        source=product.source,
        source_url=product.source_url,
        image_url=product.image_url,
        ingredients_text=product.ingredients_text,
        allergens=product.allergens,
        nutri_score=product.nutri_score,
        nova_group=product.nova_group,
        nutrients=nutrients,
        ingredients=[IngredientOut(position=i.position, name=i.name) for i in product.ingredients],
        additives=[
            AdditiveOut(e_number=a.e_number, name=a.name, risk_level=a.risk_level)
            for a in product.additives
        ],
        alerts=[
            AlertOut(alert_type=a.alert_type, message=a.message, source_url=a.source_url)
            for a in product.alerts
        ],
        last_synced_at=product.last_synced_at,
    )


def _save_product_from_off(db: Session, barcode: str, data: dict) -> Product:
    product_data = data.get("product", data)
    name = (
        product_data.get("product_name_vi")
        or product_data.get("product_name")
        or product_data.get("product_name_en")
        or "Unknown Product"
    )
    brand = product_data.get("brands")
    categories = product_data.get("categories", "")
    category = categories.split(",")[0].strip() if categories else None

    product = Product(
        barcode=barcode,
        name=name,
        brand=brand,
        category=category,
        source="open_food_facts",
        source_url=f"https://world.openfoodfacts.org/product/{barcode}",
        image_url=product_data.get("image_front_url") or product_data.get("image_url"),
        ingredients_text=product_data.get("ingredients_text_vi") or product_data.get("ingredients_text"),
        allergens=", ".join(product_data.get("allergens_tags", []) or []),
        nutri_score=product_data.get("nutrition_grades"),
        nova_group=product_data.get("nova_group"),
        last_synced_at=datetime.now(timezone.utc),
    )
    merged = db.merge(product)

    db.query(ProductNutrient).filter(ProductNutrient.barcode == barcode).delete()
    nutriments = product_data.get("nutriments", {})
    for off_key, code in NUTRIENT_OFF_MAP.items():
        val = nutriments.get(off_key)
        if val is not None:
            unit = "kcal" if code == "energy_kcal" else "g" if code != "sodium" else "mg"
            if code == "salt" and "sodium_100g" in nutriments and nutriments.get("sodium_100g"):
                continue
            db.add(
                ProductNutrient(
                    barcode=barcode,
                    nutrient_code=code,
                    amount=float(val),
                    unit=unit,
                    per_100g=True,
                )
            )

    db.query(ProductIngredient).filter(ProductIngredient.barcode == barcode).delete()
    for pos, ing_name in _parse_ingredients(merged.ingredients_text):
        db.add(ProductIngredient(barcode=barcode, position=pos, name=ing_name, normalized_name=ing_name.lower()))

    db.query(ProductAdditive).filter(ProductAdditive.barcode == barcode).delete()
    for e_num, e_name in _parse_off_additives(product_data.get("additives_tags")):
        db.add(ProductAdditive(barcode=barcode, e_number=e_num, name=e_name, risk_level=None))

    db.commit()
    db.refresh(merged)
    return merged


def _save_product_from_usda(db: Session, barcode: str, food: dict) -> Product | None:
    name = food.get("description") or food.get("brandName") or "Unknown Product"
    product = Product(
        barcode=barcode,
        name=name,
        brand=food.get("brandOwner"),
        category=food.get("brandedFoodCategory"),
        source="usda_fdc",
        source_url=f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{food.get('fdcId')}/nutrients",
        image_url=None,
        ingredients_text=food.get("ingredients"),
        allergens=None,
        nutri_score=None,
        nova_group=None,
        last_synced_at=datetime.now(timezone.utc),
    )
    merged = db.merge(product)

    db.query(ProductNutrient).filter(ProductNutrient.barcode == barcode).delete()
    for nutrient in food.get("foodNutrients", []):
        nid = nutrient.get("nutrientId") or nutrient.get("nutrient", {}).get("id")
        if nid in USDA_NUTRIENT_MAP:
            code, unit = USDA_NUTRIENT_MAP[nid]
            amount = nutrient.get("amount") or nutrient.get("value")
            if amount is not None:
                db.add(
                    ProductNutrient(
                        barcode=barcode,
                        nutrient_code=code,
                        amount=float(amount),
                        unit=unit,
                        per_100g=True,
                    )
                )

    db.query(ProductIngredient).filter(ProductIngredient.barcode == barcode).delete()
    for pos, ing_name in _parse_ingredients(merged.ingredients_text):
        db.add(ProductIngredient(barcode=barcode, position=pos, name=ing_name, normalized_name=ing_name.lower()))

    db.commit()
    db.refresh(merged)
    return merged


async def fetch_from_off(barcode: str) -> dict | None:
    url = f"{settings.off_api_url}/api/v2/product/{barcode}.json"
    headers = {"User-Agent": "FoodAdvise/1.0 (demo app)"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != 1:
            return None
        return data


async def fetch_from_usda(barcode: str) -> dict | None:
    if not settings.usda_api_key:
        return None
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": settings.usda_api_key,
        "query": barcode,
        "dataType": "Branded",
        "pageSize": 1,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None
        data = resp.json()
        foods = data.get("foods", [])
        if not foods:
            return None
        food = foods[0]
        if food.get("gtinUpc") and food["gtinUpc"].lstrip("0") != barcode.lstrip("0"):
            return None
        detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{food['fdcId']}"
        detail_resp = await client.get(detail_url, params={"api_key": settings.usda_api_key})
        if detail_resp.status_code == 200:
            return detail_resp.json()
        return food


class ProductLookupService:
    def __init__(self, db: Session):
        self.db = db

    def get_from_db(self, barcode: str) -> Product | None:
        return self.db.query(Product).filter(Product.barcode == barcode).first()

    async def lookup(self, barcode: str) -> ProductOut | None:
        barcode = barcode.strip()
        cache_key = f"product:{barcode}"
        cached = cache_get(cache_key)
        if cached:
            return ProductOut(**cached)

        product = self.get_from_db(barcode)
        if product and product.last_synced_at:
            schema = _product_to_schema(product)
            cache_set(cache_key, schema.model_dump(mode="json"))
            return schema

        off_data = await fetch_from_off(barcode)
        if off_data:
            product = _save_product_from_off(self.db, barcode, off_data)
            schema = _product_to_schema(product)
            cache_set(cache_key, schema.model_dump(mode="json"))
            return schema

        usda_data = await fetch_from_usda(barcode)
        if usda_data:
            product = _save_product_from_usda(self.db, barcode, usda_data)
            if product:
                schema = _product_to_schema(product)
                cache_set(cache_key, schema.model_dump(mode="json"))
                return schema

        if product:
            return _product_to_schema(product)

        return None

    def get_nutrient_map(self, product: ProductOut) -> dict[str, float]:
        result = {}
        for n in product.nutrients:
            if n.amount is not None:
                result[n.nutrient_code] = n.amount
        if "salt" in result and "sodium" not in result:
            result["sodium"] = result["salt"] * 1000
        return result
