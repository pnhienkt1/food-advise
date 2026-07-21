"""
Import products from Open Food Facts (Vietnam) with quality filtering.

Usage:
  python -m app.sync.import_off --max-pages 20 --page-size 100
  python -m app.sync.import_off --barcodes 8934564010014,3017624010701
"""

import argparse
import asyncio
import time

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.product import Product
from app.services.product_lookup import _save_product_from_off, fetch_from_off
from app.sync.quality import meets_import_quality, quality_score
from app.sync.vn_barcodes import VN_PRIORITY_BARCODES

OFF_SEARCH = f"{settings.off_api_url}/api/v2/search"
OFF_SEARCH_LEGACY = f"{settings.off_api_url}/cgi/search.pl"
HEADERS = {"User-Agent": "FoodAdvise/1.0 (research demo; contact: local)"}

SEARCH_QUERIES = [
    {"tagtype_0": "countries", "tag_contains_0": "contains", "tag_0": "en:vietnam"},
    {"tagtype_0": "countries", "tag_contains_0": "contains", "tag_0": "vietnam"},
    {"tagtype_1": "brands", "tag_contains_1": "contains", "tag_1": "acecook"},
    {"tagtype_1": "brands", "tag_contains_1": "contains", "tag_1": "vinamilk"},
    {"tagtype_1": "categories", "tag_contains_1": "contains", "tag_1": "instant-noodles"},
]


async def search_off_page(client: httpx.AsyncClient, params: dict, page: int, page_size: int) -> list[str]:
    query = {
        **params,
        "page": page,
        "page_size": page_size,
        "fields": "code,product_name,product_name_vi,nutrition_grades,nova_groups",
        "sort_by": "unique_scans_n",
    }
    resp = await client.get(OFF_SEARCH, params=query, headers=HEADERS, timeout=30.0)
    if resp.status_code == 200:
        try:
            data = resp.json()
            codes = [str(p["code"]) for p in data.get("products", []) if p.get("code")]
            if codes:
                return codes
        except Exception:
            pass

    # Fallback: legacy search API
    legacy_params = {
        "json": 1,
        "page_size": page_size,
        "page": page,
        **params,
    }
    resp = await client.get(OFF_SEARCH_LEGACY, params=legacy_params, headers=HEADERS, timeout=30.0)
    if resp.status_code != 200:
        return []
    try:
        data = resp.json()
        return [str(p["code"]) for p in data.get("products", []) if p.get("code")]
    except Exception:
        return []


async def import_barcodes(
    db: Session,
    barcodes: list[str],
    delay_sec: float = 0.3,
    min_quality_score: int = 40,
) -> dict:
    stats = {"fetched": 0, "imported": 0, "skipped_quality": 0, "skipped_exists": 0, "failed": 0}

    for barcode in barcodes:
        existing = db.query(Product).filter(Product.barcode == barcode).first()
        if existing and existing.source == "open_food_facts":
            stats["skipped_exists"] += 1
            continue

        stats["fetched"] += 1
        try:
            data = await fetch_from_off(barcode)
            if not data:
                stats["failed"] += 1
                continue

            ok, reason = meets_import_quality(data)
            if not ok:
                stats["skipped_quality"] += 1
                continue

            if quality_score(data) < min_quality_score:
                stats["skipped_quality"] += 1
                continue

            _save_product_from_off(db, barcode, data)
            stats["imported"] += 1
        except Exception:
            stats["failed"] += 1

        await asyncio.sleep(delay_sec)

    return stats


async def run_import(max_pages: int = 10, page_size: int = 100, min_quality_score: int = 40) -> dict:
    db = SessionLocal()
    all_barcodes: set[str] = set()
    totals = {"searched": 0, "unique_barcodes": 0, "imported": 0, "skipped_quality": 0, "skipped_exists": 0, "failed": 0}

    try:
        async with httpx.AsyncClient() as client:
            for params in SEARCH_QUERIES:
                for page in range(1, max_pages + 1):
                    codes = await search_off_page(client, params, page, page_size)
                    if not codes:
                        break
                    totals["searched"] += len(codes)
                    all_barcodes.update(codes)
                    await asyncio.sleep(0.5)

        totals["unique_barcodes"] = len(all_barcodes)
        # Always merge curated priority barcodes
        all_barcodes.update(VN_PRIORITY_BARCODES)
        totals["unique_barcodes"] = len(all_barcodes)
        print(f"Found {len(all_barcodes)} unique barcodes (search + curated list)")

        batch_stats = await import_barcodes(db, sorted(all_barcodes), min_quality_score=min_quality_score)
        totals.update({k: totals.get(k, 0) + batch_stats[k] for k in batch_stats})
        print(f"Import done: {totals}")
        return totals
    finally:
        db.close()


async def import_list(barcodes: list[str]) -> dict:
    db = SessionLocal()
    try:
        return await import_barcodes(db, barcodes)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Import quality-filtered products from Open Food Facts")
    parser.add_argument("--max-pages", type=int, default=5, help="Pages per search query")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--min-quality", type=int, default=40)
    parser.add_argument("--barcodes", type=str, default="", help="Comma-separated barcodes to import directly")
    args = parser.parse_args()

    start = time.time()
    if args.barcodes:
        codes = [b.strip() for b in args.barcodes.split(",") if b.strip()]
        stats = asyncio.run(import_list(codes))
    else:
        stats = asyncio.run(run_import(args.max_pages, args.page_size, args.min_quality))

    print(f"Finished in {time.time() - start:.1f}s — {stats}")


if __name__ == "__main__":
    main()
