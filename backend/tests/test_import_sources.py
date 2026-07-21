import asyncio

from app.sync.import_aeon import map_aeon_jsonld
from app.sync.import_bachhoaxanh import build_bxh_params, map_bxh_product
from app.sync.import_bigc import map_bigc_jsonld
from app.sync.import_teko import build_teko_query_params, map_teko_item
from app.sync.import_utils import RateLimiter


def test_map_bxh_product():
    payload = {
        "id": 228705,
        "name": "Mì trộn",
        "categoryName": "Mì gói",
        "brandName": "Omachi",
        "productBo": {"featureSpecification": "<p>Bột mì, dầu cọ, chất điều vị E621</p>"},
        "listProductCombo": [{"productCode": "8938506994128"}],
    }
    mapped = map_bxh_product(payload, category_url="mi-goi", product_url="mi-tron")
    assert mapped is not None
    assert mapped["barcode"] == "8938506994128"
    assert mapped["brand"] == "Omachi"
    assert mapped["ingredients_text"] == "Bột mì, dầu cọ, chất điều vị E621"
    assert mapped["source_url"] == "https://www.bachhoaxanh.com/mi-goi/mi-tron"


def test_map_teko_item():
    payload = {
        "barcode": "8934563132120",
        "name": "Nước mắm",
        "brand": {"name": "Nam Ngu"},
        "ingredients": "Cá cơm, muối",
    }
    mapped = map_teko_item(
        payload,
        sku="250100162",
        terminal_code="509_sgc",
        fallback_source_url="https://discovery.tekoapis.com/api/v1/product?sku=250100162&terminalCode=509_sgc",
    )
    assert mapped is not None
    assert mapped["barcode"] == "8934563132120"
    assert mapped["name"] == "Nước mắm"


def test_map_teko_item_minimal_with_fallback_key():
    payload = {
        "name": "Nước mắm",
        "brand": {"name": "Nam Ngu"},
    }
    mapped = map_teko_item(
        payload,
        sku="250100162",
        terminal_code="509_sgc",
        fallback_source_url="https://discovery.tekoapis.com/api/v1/product?sku=250100162&terminalCode=509_sgc",
        allow_minimal=True,
    )
    assert mapped is not None
    assert mapped["barcode"] == "teko:509_sgc:250100162"
    assert mapped["source_url"].startswith("https://discovery.tekoapis.com/")


def test_map_teko_item_minimal_requires_source_url():
    payload = {"name": "Nước mắm"}
    mapped = map_teko_item(
        payload,
        sku="250100162",
        terminal_code="509_sgc",
        fallback_source_url=None,
        allow_minimal=True,
    )
    assert mapped is None


def test_map_teko_item_nested_product_info():
    payload = {
        "product": {
            "productInfo": {
                "barcode": "8934563132120",
                "name": "Nước mắm",
            }
        }
    }
    mapped = map_teko_item(
        payload,
        sku="250100162",
        terminal_code="509_sgc",
        fallback_source_url="https://discovery.tekoapis.com/api/v1/product?sku=250100162&terminalCode=509_sgc",
    )
    assert mapped is not None
    assert mapped["barcode"] == "8934563132120"


def test_build_teko_query_params():
    params = build_teko_query_params(sku="250100162", terminal_code="509_sgc", location="")
    assert params == {"sku": "250100162", "location": "", "terminalCode": "509_sgc"}


def test_build_bxh_params():
    params = build_bxh_params(
        product_id=228705,
        province_id=46,
        district_id=564,
        ward_id=20665,
        store_id=1549,
        category_url="mi-goi",
        product_url="mi-tron",
    )
    assert params["productid"] == "228705"
    assert params["provinceid"] == "46"
    assert params["categoryurl"] == "mi-goi"


def test_rate_limiter_basic_behavior(monkeypatch):
    sleeps: list[float] = []

    async def _fake_sleep(duration: float):
        sleeps.append(duration)

    monkeypatch.setattr("app.sync.import_utils.asyncio.sleep", _fake_sleep)
    monkeypatch.setattr("app.sync.import_utils.random.uniform", lambda a, b: 0.2)

    async def _run():
        limiter = RateLimiter(min_delay=0.1, max_delay=0.3, max_rps=1.0)
        total = await limiter.acquire()
        assert total == 0.2

    asyncio.run(_run())
    assert sleeps == [0.2]


def test_map_aeon_jsonld():
    payload = {
        "@type": "Product",
        "gtin13": "8934588012225",
        "name": "Bánh quy",
        "brand": {"name": "Cosy"},
        "description": "Bột mì, đường, dầu thực vật",
    }
    mapped = map_aeon_jsonld(payload, source_url="https://aeoneshop.com/products/demo")
    assert mapped is not None
    assert mapped["barcode"] == "8934588012225"
    assert mapped["source_url"].startswith("https://")


def test_map_bigc_jsonld():
    payload = {
        "@type": "Product",
        "sku": "8936025771110",
        "name": "Mì ăn liền",
        "brand": {"name": "Hao Hao"},
        "description": "Bột mì, dầu cọ, gia vị",
    }
    mapped = map_bigc_jsonld(payload, source_url="https://sieuthi-go.vn/demo")
    assert mapped is not None
    assert mapped["barcode"] == "8936025771110"
    assert mapped["brand"] == "Hao Hao"
