import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.product import Product, ProductNutrient
from app.schemas.product import UserProfile
from app.services.recommendation_service import RecommendationService


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'rec.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(
        Product(
            barcode="111",
            name="Nước suối",
            brand="Test",
            category="Water",
            source="manual",
            nutri_score="a",
            nova_group=1,
        )
    )
    session.add(ProductNutrient(barcode="111", nutrient_code="sodium", amount=5, unit="mg"))
    session.add(
        Product(
            barcode="222",
            name="Mì gói",
            brand="Test",
            category="Instant noodles",
            source="manual",
            nutri_score="d",
            nova_group=4,
            ingredients_text="mì ăn liền, muối, MSG",
        )
    )
    session.add(ProductNutrient(barcode="222", nutrient_code="sodium", amount=1400, unit="mg"))
    session.commit()
    yield session
    session.close()


def test_recommendations_prefers_healthy(db_session):
    service = RecommendationService(db_session)
    profile = UserProfile(age_group="adult", goals=["healthy_eating"])
    result = service.recommend(profile, limit=5, min_score=70)
    assert result.total_evaluated == 2
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].barcode == "111"


def test_recommendations_excludes_danger_for_toddler(db_session):
    service = RecommendationService(db_session)
    profile = UserProfile(age_group="age_2_4", goals=["healthy_eating"])
    result = service.recommend(profile, limit=5, min_score=50)
    barcodes = [r.barcode for r in result.recommendations]
    assert "222" not in barcodes
