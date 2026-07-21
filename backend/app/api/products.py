from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import AdviceOut, AdviceRequest, ProductOut, ProductSearchResult, UserProfile
from app.services.advice_engine import AdviceEngine
from app.services.product_lookup import ProductLookupService, _product_to_schema
from app.services.product_search import ProductSearchService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/search", response_model=list[ProductSearchResult])
def search_products(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return ProductSearchService(db).search(q, limit=limit)


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
