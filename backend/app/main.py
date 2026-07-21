from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import advice, health, ocr, products, recommendations
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.product_search import initialize_product_search

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db = SessionLocal()
    try:
        if settings.database_url.startswith("sqlite"):
            initialize_product_search(db, database_url=settings.database_url)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Food Advise API",
    description="API tra cứu thực phẩm và đánh giá dinh dưỡng cá nhân hóa",
    version="1.0.0",
    lifespan=lifespan,
)

_cors_kwargs: dict = {
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.cors_allow_cloudflare:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.trycloudflare\.com",
        **_cors_kwargs,
    )
else:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, **_cors_kwargs)

app.include_router(health.router)
app.include_router(products.router, prefix="/api/v1")
app.include_router(advice.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(ocr.router, prefix="/api/v1")

# Profile presets at /api/v1/profiles/presets
from app.api.advice import get_profile_presets

app.add_api_route("/api/v1/profiles/presets", get_profile_presets, methods=["GET"], tags=["profiles"])
