"""
Import products via Teko discovery APIs.

Usage:
  python -m app.sync.import_teko --skus 20618432,20478891
"""

from __future__ import annotations

import argparse
import asyncio
import os
from urllib.parse import urlencode

import httpx

from app.core.database import SessionLocal
from app.sync.import_utils import ImportRequester, normalize_barcode, upsert_product

BASE_URL = "https://discovery.tekoapis.com/api/v1"


def _teko_fallback_key(*, sku: str, terminal_code: str) -> str:
    return f"teko:{terminal_code}:{sku}"


def _build_source_url(path: str, params: dict[str, str] | None) -> str:
    if not params:
        return f"{BASE_URL}{path}"
    return f"{BASE_URL}{path}?{urlencode(params)}"


def _unwrap_teko_item(raw: dict) -> dict:
    product = raw.get("product")
    if isinstance(product, dict):
        info = product.get("productInfo")
        if isinstance(info, dict):
            return info
        return product
    return raw


def map_teko_item(
    raw: dict,
    *,
    sku: str,
    terminal_code: str,
    fallback_source_url: str | None = None,
    allow_minimal: bool = False,
) -> dict | None:
    item = _unwrap_teko_item(raw)
    barcode = normalize_barcode(item.get("barcode") or item.get("barCode") or item.get("ean"))
    name = item.get("name") or item.get("displayName")
    source_url = item.get("url") or fallback_source_url
    if not name:
        return None
    if allow_minimal:
        if not source_url:
            return None
        product_key = barcode or _teko_fallback_key(sku=sku, terminal_code=terminal_code)
    else:
        if not barcode:
            return None
        product_key = barcode
    return {
        "barcode": product_key,
        "name": str(name).strip(),
        "brand": (item.get("brand") or {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand"),
        "category": (item.get("category") or {}).get("name")
        if isinstance(item.get("category"), dict)
        else item.get("category"),
        "image_url": item.get("imageUrl") or item.get("thumbnail"),
        "ingredients_text": item.get("ingredients"),
        "source_url": source_url,
    }


def build_teko_query_params(*, sku: str, terminal_code: str, location: str = "") -> dict[str, str]:
    return {"sku": sku, "location": location, "terminalCode": terminal_code}


async def fetch_sku_with_requester(
    requester: ImportRequester, sku: str, terminal_code: str, location: str = ""
) -> tuple[dict, str] | None:
    params = build_teko_query_params(sku=sku, terminal_code=terminal_code, location=location)
    prioritized = [("/product", params)]
    # Teko deployments differ by retailer/tenant. Keep legacy path fallbacks.
    fallback_paths = [f"/products/{sku}", f"/product/{sku}", f"/items/{sku}"]
    requests = prioritized + [(path, None) for path in fallback_paths]
    for path, path_params in requests:
        source_url = _build_source_url(path, path_params)
        resp = await requester.get(f"{BASE_URL}{path}", params=path_params)
        if not resp or resp.status_code != 200:
            continue
        data = resp.json()
        if isinstance(data, dict) and "result" in data:
            result = data["result"]
            return (result, source_url) if isinstance(result, dict) else None
        return (data, source_url) if isinstance(data, dict) else None
    return None


async def run_import(
    skus: list[str],
    *,
    terminal_code: str,
    location: str = "",
    concurrency: int = 1,
    min_delay: float = 0.3,
    max_delay: float = 0.8,
    max_rps: float = 1.0,
    allow_minimal: bool = False,
) -> dict:
    stats = {"fetched": 0, "imported": 0, "skipped_quality": 0, "failed": 0, "throttled": 0, "requests": 0}
    db = SessionLocal()
    try:
        effective_concurrency = max(1, min(concurrency, 1))
        if concurrency != effective_concurrency:
            print(f"[TEKO] concurrency capped to {effective_concurrency} for anti-blocking mode")
        async with httpx.AsyncClient(headers={"User-Agent": "FoodAdvise/1.0"}) as client:
            requester = ImportRequester(client, min_delay=min_delay, max_delay=max_delay, max_rps=max_rps)
            for sku in skus:
                stats["fetched"] += 1
                try:
                    fetched = await fetch_sku_with_requester(requester, sku, terminal_code, location=location)
                    if not fetched:
                        stats["failed"] += 1
                        print(f"[TEKO] sku={sku} unavailable")
                        continue
                    raw, endpoint_source_url = fetched
                    mapped = map_teko_item(
                        raw,
                        sku=sku,
                        terminal_code=terminal_code,
                        fallback_source_url=endpoint_source_url,
                        allow_minimal=allow_minimal,
                    )
                    if not mapped:
                        stats["skipped_quality"] += 1
                        continue
                    ok, reason = upsert_product(
                        db,
                        source="teko",
                        enforce_quality=not allow_minimal,
                        **mapped,
                    )
                    if ok:
                        stats["imported"] += 1
                        if allow_minimal and mapped["barcode"].startswith("teko:"):
                            print(
                                f"[TEKO] minimal_provenance sku={sku} terminal={terminal_code} key={mapped['barcode']}"
                            )
                    else:
                        stats["skipped_quality"] += 1
                        print(
                            f"[TEKO] skip sku={sku} barcode={mapped['barcode']} "
                            f"terminal={terminal_code} reason={reason}"
                        )
                except Exception as exc:
                    stats["failed"] += 1
                    print(f"[TEKO] sku={sku} error={exc}")
                stats["throttled"] = requester.stats["throttled"]
                stats["requests"] = requester.stats["requests"]
                print(
                    f"[TEKO] progress fetched={stats['fetched']} imported={stats['imported']} "
                    f"skipped={stats['skipped_quality']} failed={stats['failed']} "
                    f"requests={stats['requests']} throttled={stats['throttled']}"
                )
    finally:
        db.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Import products from Teko discovery APIs")
    parser.add_argument("--skus", type=str, required=True, help="Comma-separated sku ids")
    parser.add_argument("--terminal-code", type=str, default=os.getenv("TEKO_TERMINAL_CODE", "509_sgc"))
    parser.add_argument("--location", type=str, default=os.getenv("TEKO_LOCATION", ""))
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("IMPORT_CONCURRENCY", "1")))
    parser.add_argument("--min-delay", type=float, default=float(os.getenv("IMPORT_MIN_DELAY", "0.3")))
    parser.add_argument("--max-delay", type=float, default=float(os.getenv("IMPORT_MAX_DELAY", "0.8")))
    parser.add_argument("--max-rps", type=float, default=float(os.getenv("IMPORT_MAX_RPS", "1.0")))
    parser.add_argument(
        "--allow-minimal",
        action="store_true",
        help="Allow minimal Teko records (name + source_url + barcode or sku-derived key)",
    )
    args = parser.parse_args()
    skus = [x.strip() for x in args.skus.split(",") if x.strip()]
    stats = asyncio.run(
        run_import(
            skus,
            terminal_code=args.terminal_code,
            location=args.location,
            concurrency=args.concurrency,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_rps=args.max_rps,
            allow_minimal=args.allow_minimal,
        )
    )
    print(f"[TEKO] done: {stats}")


if __name__ == "__main__":
    main()
