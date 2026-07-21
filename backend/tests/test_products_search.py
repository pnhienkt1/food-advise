import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.product import Product
from app.services.product_search import initialize_product_search


@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "search.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as setup_session:
        initialize_product_search(setup_session, database_url=db_url)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_products(db_session: Session):
    products = [
        Product(barcode="8934564010014", name="Mì Hảo Hảo tôm chua cay", brand="Acecook", source="manual"),
        Product(barcode="8938503920012", name="Sữa tươi Vinamilk", brand="Vinamilk", source="manual"),
        Product(barcode="8934564010021", name="Mì Omachi sườn hầm", brand="Acecook", source="manual"),
    ]
    for p in products:
        db_session.add(p)
    db_session.commit()
    return products


def test_search_products_by_name(client, seeded_products):
    res = client.get("/api/v1/products/search", params={"q": "Hảo Hảo"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert any("Hảo Hảo" in item["name"] for item in data)
    assert all("barcode" in item and "name" in item for item in data)


def test_search_products_by_brand(client, seeded_products):
    res = client.get("/api/v1/products/search", params={"q": "Vinamilk", "limit": 5})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["brand"] == "Vinamilk"


def test_search_products_respects_limit(client, seeded_products):
    res = client.get("/api/v1/products/search", params={"q": "Mì", "limit": 1})
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_search_products_empty_query_rejected(client):
    res = client.get("/api/v1/products/search", params={"q": ""})
    assert res.status_code == 422


def test_search_products_single_char_rejected(client, seeded_products):
    res = client.get("/api/v1/products/search", params={"q": "M"})
    assert res.status_code == 422
