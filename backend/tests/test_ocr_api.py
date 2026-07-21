from fastapi.testclient import TestClient

from app.main import app


def test_ocr_ingredients_endpoint(monkeypatch):
    def fake_extract(_image_bytes: bytes):
        return {
            "raw_text": "Thành phần: đường, muối, dầu thực vật",
            "ingredients": ["đường", "muối", "dầu thực vật"],
            "confidence": None,
            "notes": "mock",
        }

    monkeypatch.setattr("app.api.ocr.extract_ingredients_text", fake_extract)
    client = TestClient(app)
    files = {"image": ("sample.jpg", b"fake-image-bytes", "image/jpeg")}
    response = client.post("/api/v1/ocr/ingredients", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "raw_text" in data
    assert "ingredients" in data
    assert data["ingredients"][0] == "đường"


def test_evaluate_ingredients_advice():
    client = TestClient(app)
    body = {
        "ingredients_text": "đường, dầu cọ, muối",
        "profile": {"age_group": "adult", "conditions": ["diabetes"], "goals": ["low_sugar"], "allergens": []},
    }
    response = client.post("/api/v1/advice/evaluate-ingredients", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["barcode"] == "ocr-upload"
    assert "suitability_score" in data
