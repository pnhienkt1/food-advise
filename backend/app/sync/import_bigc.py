"""
Import products from BigC/GO public sitemaps (best-effort crawler).

Usage:
  python -m app.sync.import_bigc --limit 100
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re

import httpx

from app.core.database import SessionLocal
from app.sync.import_utils import normalize_barcode, upsert_product

SITEMAP_URL = "https://sieuthi-go.vn/sitemap.xml"


def map_bigc_jsonld(raw: dict, source_url: str) -> dict | None:
    barcode = normalize_barcode(raw.get("gtin13") or raw.get("gtin12") or raw.get("sku") or raw.get("mpn"))
    name = raw.get("name")
    if not barcode or not name:
        return None
    brand = raw.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")
    return {
        "barcode": barcode,
        "name": str(name).strip(),
        "brand": brand,
        "category": raw.get("category"),
        "image_url": raw.get("image"),
        "ingredients_text": raw.get("description"),
        "source_url": source_url,
    }


async def discover_product_links(client: httpx.AsyncClient, limit: int) -> list[str]:
    resp = await client.get(SITEMAP_URL, timeout=30.0)
    if resp.status_code != 200:
        return []
    child_maps = re.findall(r"<loc>(.*?)</loc>", resp.text)
    candidate_maps = [u for u in child_maps if "/products-" in u]
    links: list[str] = []
    for sm in candidate_maps[:10]:
        try:
            nested = await client.get(sm, timeout=30.0)
            if nested.status_code != 200:
                continue
            links.extend([u for u in re.findall(r"<loc>(.*?)</loc>", nested.text) if "/sitemap/" not in u])
            if len(links) >= limit:
                break
            await asyncio.sleep(0.3)
        except Exception:
            continue
    return links[:limit]


async def extract_jsonld_product(client: httpx.AsyncClient, url: str) -> dict | None:
    resp = await client.get(url, timeout=30.0)
    if resp.status_code != 200:
        return None
    blocks = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>\s*(.*?)\s*</script>',
        resp.text,
        flags=re.S,
    )
    for block in blocks:
        try:
            data = json.loads(block)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            return data
    return None


async def run_import(limit: int = 100) -> dict:
    stats = {"fetched": 0, "imported": 0, "skipped_quality": 0, "failed": 0}
    db = SessionLocal()
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FoodAdviseBot/1.0)"}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            links = await discover_product_links(client, limit=limit)
            if not links:
                print("[BigC] no product links discovered")
                return stats
            for url in links:
                stats["fetched"] += 1
                try:
                    raw = await extract_jsonld_product(client, url)
                    if not raw:
                        stats["failed"] += 1
                        continue
                    mapped = map_bigc_jsonld(raw, source_url=url)
                    if not mapped:
                        stats["skipped_quality"] += 1
                        continue
                    ok, reason = upsert_product(db, source="bigc_go", **mapped)
                    if ok:
                        stats["imported"] += 1
                    else:
                        stats["skipped_quality"] += 1
                        print(f"[BigC] skip barcode={mapped['barcode']} reason={reason}")
                except Exception as exc:
                    stats["failed"] += 1
                    print(f"[BigC] url={url} error={exc}")
                await asyncio.sleep(0.8)
    finally:
        db.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Import products from BigC/GO public pages")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    stats = asyncio.run(run_import(limit=args.limit))
    print(f"[BigC] done: {stats}")


if __name__ == "__main__":
    main()
