from __future__ import annotations

import asyncio
import os
import random
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.product import Product, ProductIngredient, ProductNutrient
from app.sync.quality import meets_import_quality


def split_ingredients(text: str | None) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;]", text) if part.strip()]


def normalize_barcode(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)
    return digits if len(digits) >= 8 else None


def clean_html_text(value: str | None) -> str | None:
    if not value:
        return None
    # Keep additive codes like E621 while removing formatting/markup noise.
    no_tags = re.sub(r"<[^>]+>", " ", value)
    decoded = unescape(no_tags)
    compact = re.sub(r"\s+", " ", decoded).strip()
    return compact or None


def env_or_default(name: str, default: str) -> str:
    return os.getenv(name, default)


def parse_header_overrides(raw_header: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not raw_header:
        return headers
    for pair in raw_header.split("|"):
        if ":" not in pair:
            continue
        key, value = pair.split(":", 1)
        k = key.strip()
        v = value.strip()
        if k and v:
            headers[k] = v
    return headers


class RateLimiter:
    def __init__(self, *, min_delay: float = 0.3, max_delay: float = 0.8, max_rps: float = 1.0):
        self.min_delay = max(0.0, min_delay)
        self.max_delay = max(self.min_delay, max_delay)
        self.max_rps = max(0.1, max_rps)
        self._tokens = self.max_rps
        self._last_refill = asyncio.get_running_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> float:
        async with self._lock:
            now = asyncio.get_running_loop().time()
            elapsed = max(0.0, now - self._last_refill)
            self._tokens = min(self.max_rps, self._tokens + elapsed * self.max_rps)
            self._last_refill = now
            wait_for_token = 0.0
            if self._tokens < 1.0:
                wait_for_token = (1.0 - self._tokens) / self.max_rps
                await asyncio.sleep(wait_for_token)
                self._tokens = 0.0
                self._last_refill = asyncio.get_running_loop().time()
            else:
                self._tokens -= 1.0
            jitter = random.uniform(self.min_delay, self.max_delay) if self.max_delay > 0 else 0.0
            if jitter > 0:
                await asyncio.sleep(jitter)
            return wait_for_token + jitter


class ImportRequester:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        min_delay: float = 0.3,
        max_delay: float = 0.8,
        max_rps: float = 1.0,
        max_retries: int = 4,
        timeout: float = 30.0,
    ):
        self.client = client
        self.rate_limiter = RateLimiter(min_delay=min_delay, max_delay=max_delay, max_rps=max_rps)
        self.max_retries = max_retries
        self.timeout = timeout
        self.stats = {"requests": 0, "throttled": 0, "cooldowns": 0, "retries": 0}
        self._burst_penalties = 0

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | None:
        for attempt in range(self.max_retries + 1):
            slept = await self.rate_limiter.acquire()
            self.stats["requests"] += 1
            if slept > 0:
                self.stats["throttled"] += 1
            try:
                resp = await self.client.get(url, params=params, headers=headers, timeout=self.timeout)
                if resp.status_code in {429, 500, 502, 503, 504}:
                    if attempt >= self.max_retries:
                        return resp
                    await self._backoff_sleep(attempt, status_code=resp.status_code)
                    self.stats["retries"] += 1
                    continue
                self._burst_penalties = 0
                return resp
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError):
                if attempt >= self.max_retries:
                    return None
                await self._backoff_sleep(attempt, status_code=0)
                self.stats["retries"] += 1
        return None

    async def _backoff_sleep(self, attempt: int, *, status_code: int) -> None:
        base = min(10.0, 0.5 * (2**attempt))
        jitter = random.uniform(0.05, 0.5)
        penalty = 0.0
        if status_code in {429, 403}:
            self._burst_penalties += 1
            penalty = min(15.0, self._burst_penalties * 1.5)
            self.stats["cooldowns"] += 1
        await asyncio.sleep(base + jitter + penalty)


def upsert_product(
    db: Session,
    *,
    source: str,
    barcode: str,
    name: str,
    enforce_quality: bool = True,
    source_url: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    image_url: str | None = None,
    ingredients_text: str | None = None,
    nutrients: dict[str, float] | None = None,
) -> tuple[bool, str]:
    payload = {
        "product": {
            "code": barcode,
            "product_name": name,
            "ingredients_text": ingredients_text,
            "nutriments": {f"{k}_100g": v for k, v in (nutrients or {}).items()},
        }
    }
    if enforce_quality:
        ok, reason = meets_import_quality(payload)
        if not ok:
            return False, reason

    product = Product(
        barcode=barcode,
        name=name,
        brand=brand,
        category=category,
        source=source,
        source_url=source_url,
        image_url=image_url,
        ingredients_text=ingredients_text,
        last_synced_at=datetime.now(timezone.utc),
    )
    merged = db.merge(product)

    db.query(ProductIngredient).filter(ProductIngredient.barcode == barcode).delete()
    for idx, item in enumerate(split_ingredients(ingredients_text)):
        db.add(
            ProductIngredient(
                barcode=barcode,
                position=idx,
                name=item,
                normalized_name=item.lower(),
            )
        )

    if nutrients is not None:
        db.query(ProductNutrient).filter(ProductNutrient.barcode == barcode).delete()
        for code, amount in nutrients.items():
            db.add(
                ProductNutrient(
                    barcode=barcode,
                    nutrient_code=code,
                    amount=float(amount),
                    unit="g" if code != "energy_kcal" else "kcal",
                    per_100g=True,
                )
            )

    db.commit()
    db.refresh(merged)
    return True, "ok"
