from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import RecommendationsOut, UserProfile
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationsOut)
def get_recommendations(
    profile: UserProfile,
    limit: int = Query(20, ge=1, le=50),
    min_score: int = Query(70, ge=0, le=100),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    service = RecommendationService(db)
    return service.recommend(profile, limit=limit, min_score=min_score, category=category)
