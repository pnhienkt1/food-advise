from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import IS_SQLITE, get_db, strip_diacritics
from app.models.product import Product, ProductAdditive, ProductIngredient
from app.schemas.product import (
    AdviceOut,
    AdviceRequest,
    ProductListItem,
    ProductListOut,
    ProductOut,
    ProductSearchResult,
    UserProfile,
)
from app.services.advice_engine import AdviceEngine
from app.services.product_lookup import ProductLookupService, _product_to_schema
from app.services.product_search import ProductSearchService

router = APIRouter(prefix="/products", tags=["products"])


def _accent_insensitive(column, term: str) -> list:
    """Build LIKE conditions for `term` on `column`, accent-insensitive on SQLite."""
    cleaned = term.strip().lower()
    conditions = [func.lower(column).like(f"%{cleaned}%")]
    if IS_SQLITE:
        stripped = strip_diacritics(cleaned)
        conditions.append(func.unaccent(func.lower(column)).like(f"%{stripped}%"))
    return conditions


@router.get("/search", response_model=list[ProductSearchResult])
def search_products(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return ProductSearchService(db).search(q, limit=limit)


@router.get("", response_model=ProductListOut)
def list_products(
    q: str | None = Query(None, max_length=200, description="Lọc theo tên/thương hiệu"),
    ingredient: str | None = Query(None, max_length=200, description="Lọc theo thành phần"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Product)

    if q and q.strip():
        query = query.filter(or_(*_accent_insensitive(Product.name, q), *_accent_insensitive(Product.brand, q)))

    if ingredient and ingredient.strip():
        matching_ingredients = db.query(ProductIngredient.barcode).filter(
            or_(*_accent_insensitive(ProductIngredient.normalized_name, ingredient))
        )
        # Phụ gia (E-number) được lưu ở bảng riêng nên phải tra cả e_number và tên phụ gia
        matching_additives = db.query(ProductAdditive.barcode).filter(
            or_(
                func.lower(ProductAdditive.e_number).like(f"%{ingredient.strip().lower()}%"),
                *_accent_insensitive(ProductAdditive.name, ingredient),
            )
        )
        query = query.filter(
            or_(
                Product.barcode.in_(matching_ingredients),
                Product.barcode.in_(matching_additives),
                *_accent_insensitive(Product.ingredients_text, ingredient),
            )
        )

    total = query.count()
    rows = query.order_by(Product.name).offset(offset).limit(limit).all()
    return ProductListOut(
        total=total,
        limit=limit,
        offset=offset,
        items=[ProductListItem.model_validate(row) for row in rows],
    )


@router.get("/{barcode}", response_model=ProductOut)
async def get_product(barcode: str, db: Session = Depends(get_db)):
    lookup = ProductLookupService(db)
    product = await lookup.lookup(barcode)
    if not product:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Không tìm thấy sản phẩm trong cơ sở dữ liệu",
                "barcode": barcode,
                "contribute_url": f"https://world.openfoodfacts.org/cgi/product.pl?type=edit&code={barcode}",
            },
        )
    return product


@router.get("/{barcode}/alternatives", response_model=list[ProductOut])
async def get_alternatives(
    barcode: str,
    profile_json: str | None = Query(None, alias="profile"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    lookup = ProductLookupService(db)
    current = await lookup.lookup(barcode)
    if not current:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    profile = UserProfile()
    if profile_json:
        import json

        profile = UserProfile(**json.loads(profile_json))

    category = current.category
    query = db.query(Product).filter(Product.barcode != barcode)
    if category:
        query = query.filter(Product.category.ilike(f"%{category.split(',')[0].strip()}%"))

    candidates = query.limit(50).all()
    engine = AdviceEngine()
    scored = []

    for candidate in candidates:
        schema = _product_to_schema(candidate)
        nutrients = lookup.get_nutrient_map(schema)
        result = engine.evaluate(schema, profile, nutrients)
        scored.append((result["suitability_score"], schema))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:limit]]
