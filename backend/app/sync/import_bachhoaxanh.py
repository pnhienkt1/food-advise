"""
Import products from Bach Hoa Xanh public API.

Usage:
  python -m app.sync.import_bachhoaxanh --product-ids 228705,228706
"""

from __future__ import annotations

import argparse
import asyncio
import os

import httpx

from app.core.database import SessionLocal
from app.sync.import_utils import (
    ImportRequester,
    clean_html_text,
    normalize_barcode,
    parse_header_overrides,
    upsert_product,
)

API_URL = "https://api.bachhoaxanh.com/gw/Product/GetProductDetail"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bachhoaxanh.com/",
}


def map_bxh_product(raw: dict, *, category_url: str | None = None, product_url: str | None = None) -> dict | None:
    product_bo = raw.get("productBo") if isinstance(raw.get("productBo"), dict) else {}
    product_codes = raw.get("listProductCombo") if isinstance(raw.get("listProductCombo"), list) else []
    barcode = normalize_barcode(raw.get("barcode") or raw.get("Barcode") or product_bo.get("barcode"))
    if not barcode:
        for item in product_codes:
            if not isinstance(item, dict):
                continue
            barcode = normalize_barcode(item.get("productCode"))
            if barcode:
                break
    name = raw.get("name") or raw.get("Name") or raw.get("ProductName")
    if not barcode or not name:
        return None
    category_name = raw.get("categoryName") or raw.get("CategoryName") or raw.get("Category")
    feature_html = (
        product_bo.get("featureSpecification")
        if isinstance(product_bo.get("featureSpecification"), str)
        else raw.get("featureSpecification")
    )
    ingredients_text = clean_html_text(feature_html or raw.get("Ingredients"))
    url_from_payload = raw.get("url") or raw.get("Url")
    source_url = url_from_payload
    if product_url and category_url:
        source_url = f"https://www.bachhoaxanh.com/{category_url.strip('/')}/{product_url.strip('/')}"
    elif product_url:
        source_url = f"https://www.bachhoaxanh.com/{product_url.strip('/')}"
    elif category_url and raw.get("id"):
        source_url = f"https://www.bachhoaxanh.com/{category_url.strip('/')}/{raw.get('id')}"
    return {
        "barcode": barcode,
        "name": str(name).strip(),
        "brand": raw.get("brandName") or raw.get("BrandName") or raw.get("Brand"),
        "category": category_name,
        "image_url": raw.get("imageUrl") or raw.get("ImageUrl") or raw.get("Avatar"),
        "ingredients_text": ingredients_text,
        "source_url": source_url,
    }


def build_bxh_params(
    *,
    product_id: int,
    province_id: int,
    district_id: int,
    ward_id: int,
    store_id: int,
    category_url: str = "",
    product_url: str = "",
) -> dict[str, str]:
    params = {
        "appversion": "3.12.13",
        "deviceid": "web",
        "provinceid": str(province_id),
        "districtid": str(district_id),
        "wardid": str(ward_id),
        "storeid": str(store_id),
        "productid": str(product_id),
        "categoryurl": category_url,
        "producturl": product_url,
    }
    return params


async def fetch_product(
    requester: ImportRequester,
    product_id: int,
    *,
    province_id: int,
    district_id: int,
    ward_id: int,
    store_id: int,
    category_url: str = "",
    product_url: str = "",
    headers: dict[str, str],
) -> dict | None:
    params = build_bxh_params(
        product_id=product_id,
        province_id=province_id,
        district_id=district_id,
        ward_id=ward_id,
        store_id=store_id,
        category_url=category_url,
        product_url=product_url,
    )
    resp = await requester.get(API_URL, params=params, headers=headers)
    if not resp:
        return None
    if resp.status_code != 200:
        return None
    data = resp.json()
    if isinstance(data, dict):
        lower_data = data.get("data")
        if isinstance(lower_data, dict):
            return lower_data
        upper_data = data.get("Data")
        if isinstance(upper_data, dict):
            return upper_data
    if isinstance(data, dict):
        return data
    return None


async def run_import(
    product_ids: list[int],
    *,
    province_id: int = 46,
    district_id: int = 564,
    ward_id: int = 20665,
    store_id: int = 1549,
    category_url: str = "",
    product_url: str = "",
    headers: dict[str, str] | None = None,
    concurrency: int = 1,
    min_delay: float = 0.3,
    max_delay: float = 0.8,
    max_rps: float = 1.0,
) -> dict:
    stats = {"fetched": 0, "imported": 0, "skipped_quality": 0, "failed": 0, "throttled": 0, "requests": 0}
    db = SessionLocal()
    try:
        effective_concurrency = max(1, min(concurrency, 1))
        if concurrency != effective_concurrency:
            print(f"[BXH] concurrency capped to {effective_concurrency} for anti-blocking mode")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            merged_headers = dict(HEADERS)
            if headers:
                merged_headers.update(headers)
            requester = ImportRequester(client, min_delay=min_delay, max_delay=max_delay, max_rps=max_rps)
            for pid in product_ids:
                stats["fetched"] += 1
                try:
                    raw = await fetch_product(
                        requester,
                        pid,
                        province_id=province_id,
                        district_id=district_id,
                        ward_id=ward_id,
                        store_id=store_id,
                        category_url=category_url,
                        product_url=product_url,
                        headers=merged_headers,
                    )
                    if not raw:
                        stats["failed"] += 1
                        print(f"[BXH] product_id={pid} no data / blocked")
                        continue
                    mapped = map_bxh_product(raw, category_url=category_url, product_url=product_url)
                    if not mapped:
                        stats["skipped_quality"] += 1
                        continue
                    ok, reason = upsert_product(db, source="bach_hoa_xanh", **mapped)
                    if ok:
                        stats["imported"] += 1
                    else:
                        stats["skipped_quality"] += 1
                        print(f"[BXH] skip barcode={mapped['barcode']} reason={reason}")
                except Exception as exc:
                    stats["failed"] += 1
                    print(f"[BXH] product_id={pid} error={exc}")
                stats["throttled"] = requester.stats["throttled"]
                stats["requests"] = requester.stats["requests"]
                print(
                    f"[BXH] progress fetched={stats['fetched']} imported={stats['imported']} "
                    f"skipped={stats['skipped_quality']} failed={stats['failed']} "
                    f"requests={stats['requests']} throttled={stats['throttled']}"
                )
    finally:
        db.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Import products from Bach Hoa Xanh")
    parser.add_argument("--product-ids", type=str, required=True, help="Comma-separated BXH product ids")
    parser.add_argument("--province-id", type=int, default=int(os.getenv("BXH_PROVINCE_ID", "46")))
    parser.add_argument("--district-id", type=int, default=int(os.getenv("BXH_DISTRICT_ID", "564")))
    parser.add_argument("--ward-id", type=int, default=int(os.getenv("BXH_WARD_ID", "20665")))
    parser.add_argument("--store-id", type=int, default=int(os.getenv("BXH_STORE_ID", "1549")))
    parser.add_argument("--category-url", type=str, default=os.getenv("BXH_CATEGORY_URL", ""))
    parser.add_argument("--product-url", type=str, default=os.getenv("BXH_PRODUCT_URL", ""))
    parser.add_argument("--user-agent", type=str, default=os.getenv("BXH_USER_AGENT", ""))
    parser.add_argument("--accept", type=str, default=os.getenv("BXH_ACCEPT", ""))
    parser.add_argument("--referer", type=str, default=os.getenv("BXH_REFERER", ""))
    parser.add_argument("--header-overrides", type=str, default=os.getenv("BXH_HEADER_OVERRIDES", ""))
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("IMPORT_CONCURRENCY", "1")))
    parser.add_argument("--min-delay", type=float, default=float(os.getenv("IMPORT_MIN_DELAY", "0.3")))
    parser.add_argument("--max-delay", type=float, default=float(os.getenv("IMPORT_MAX_DELAY", "0.8")))
    parser.add_argument("--max-rps", type=float, default=float(os.getenv("IMPORT_MAX_RPS", "1.0")))
    args = parser.parse_args()
    product_ids = [int(x.strip()) for x in args.product_ids.split(",") if x.strip().isdigit()]
    cli_headers = parse_header_overrides(args.header_overrides)
    if args.user_agent:
        cli_headers["User-Agent"] = args.user_agent
    if args.accept:
        cli_headers["Accept"] = args.accept
    if args.referer:
        cli_headers["Referer"] = args.referer
    stats = asyncio.run(
        run_import(
            product_ids,
            province_id=args.province_id,
            district_id=args.district_id,
            ward_id=args.ward_id,
            store_id=args.store_id,
            category_url=args.category_url,
            product_url=args.product_url,
            headers=cli_headers,
            concurrency=args.concurrency,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_rps=args.max_rps,
        )
    )
    print(f"[BXH] done: {stats}")


if __name__ == "__main__":
    main()
