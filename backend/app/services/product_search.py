"""Fast product name/brand/barcode search using SQLite FTS5 and caching."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from threading import Lock

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.product import ProductSearchResult

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 60
_CACHE_MAX_ENTRIES = 256
_cache: dict[tuple[str, int], tuple[float, list[ProductSearchResult]]] = {}
_cache_lock = Lock()

_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
    name,
    brand,
    content='products',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);
"""

_FTS_TRIGGER_AI = """
CREATE TRIGGER IF NOT EXISTS products_fts_ai AFTER INSERT ON products BEGIN
    INSERT INTO products_fts(rowid, name, brand)
    VALUES (new.rowid, new.name, COALESCE(new.brand, ''));
END
"""

_FTS_TRIGGER_AD = """
CREATE TRIGGER IF NOT EXISTS products_fts_ad AFTER DELETE ON products BEGIN
    INSERT INTO products_fts(products_fts, rowid, name, brand)
    VALUES ('delete', old.rowid, old.name, COALESCE(old.brand, ''));
END
"""

_FTS_TRIGGER_AU = """
CREATE TRIGGER IF NOT EXISTS products_fts_au AFTER UPDATE ON products BEGIN
    INSERT INTO products_fts(products_fts, rowid, name, brand)
    VALUES ('delete', old.rowid, old.name, COALESCE(old.brand, ''));
    INSERT INTO products_fts(rowid, name, brand)
    VALUES (new.rowid, new.name, COALESCE(new.brand, ''));
END
"""

_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS ix_products_name ON products(name);
CREATE INDEX IF NOT EXISTS ix_products_brand ON products(brand);
"""


def _escape_fts_term(term: str) -> str:
    cleaned = re.sub(r'["\'\\]+', " ", term).strip()
    if not cleaned:
        return ""
    tokens = cleaned.split()
    parts = []
    for token in tokens:
        token = token.replace('"', "")
        if not token:
            continue
        parts.append(f'"{token}"*')
    return " AND ".join(parts)


@dataclass(frozen=True)
class _SearchRow:
    barcode: str
    name: str
    brand: str | None
    category: str | None
    image_url: str | None


class ProductSearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(self, term: str, *, limit: int = 10) -> list[ProductSearchResult]:
        normalized = term.strip()
        if not normalized:
            return []

        cache_key = (normalized.casefold(), limit)
        now = time.monotonic()
        with _cache_lock:
            cached = _cache.get(cache_key)
            if cached and now - cached[0] < _CACHE_TTL_SECONDS:
                return list(cached[1])

        rows = self._query(normalized, limit)
        results = [
            ProductSearchResult(
                barcode=row.barcode,
                name=row.name,
                brand=row.brand,
                category=row.category,
                image_url=row.image_url,
            )
            for row in rows
        ]

        with _cache_lock:
            if len(_cache) >= _CACHE_MAX_ENTRIES:
                oldest_key = min(_cache, key=lambda key: _cache[key][0])
                _cache.pop(oldest_key, None)
            _cache[cache_key] = (now, results)

        return results

    def _query(self, term: str, limit: int) -> list[_SearchRow]:
        if term.isdigit():
            barcode_rows = self._search_barcode_prefix(term, limit)
            if barcode_rows:
                return barcode_rows

        fts_rows = self._search_fts(term, limit)
        if fts_rows:
            return fts_rows

        return self._search_prefix_fallback(term, limit)

    def _search_barcode_prefix(self, term: str, limit: int) -> list[_SearchRow]:
        rows = self.db.execute(
            text(
                """
                SELECT barcode, name, brand, category, image_url
                FROM products
                WHERE barcode LIKE :prefix
                ORDER BY barcode
                LIMIT :limit
                """
            ),
            {"prefix": f"{term}%", "limit": limit},
        ).mappings().all()
        return [_SearchRow(**row) for row in rows]

    def _search_fts(self, term: str, limit: int) -> list[_SearchRow]:
        fts_query = _escape_fts_term(term)
        if not fts_query:
            return []

        try:
            rows = self.db.execute(
                text(
                    """
                    SELECT p.barcode, p.name, p.brand, p.category, p.image_url,
                           bm25(products_fts) AS rank_score
                    FROM products_fts
                    JOIN products p ON p.rowid = products_fts.rowid
                    WHERE products_fts MATCH :fts_query
                    ORDER BY rank_score
                    LIMIT :limit
                    """
                ),
                {"fts_query": fts_query, "limit": limit},
            ).mappings().all()
            return [_SearchRow(
                barcode=row["barcode"],
                name=row["name"],
                brand=row["brand"],
                category=row["category"],
                image_url=row["image_url"],
            ) for row in rows]
        except Exception as exc:
            logger.debug("FTS search failed, using prefix fallback: %s", exc)
            self.db.rollback()
            return []

    def _search_prefix_fallback(self, term: str, limit: int) -> list[_SearchRow]:
        prefix = f"{term}%"
        pattern = f"%{term}%"
        rows = self.db.execute(
            text(
                """
                SELECT barcode, name, brand, category, image_url
                FROM products
                WHERE name LIKE :prefix COLLATE NOCASE
                   OR brand LIKE :prefix COLLATE NOCASE
                   OR name LIKE :pattern COLLATE NOCASE
                   OR brand LIKE :pattern COLLATE NOCASE
                   OR barcode LIKE :prefix
                ORDER BY
                    CASE WHEN name LIKE :prefix COLLATE NOCASE THEN 0
                         WHEN brand LIKE :prefix COLLATE NOCASE THEN 1
                         ELSE 2 END,
                    name
                LIMIT :limit
                """
            ),
            {"prefix": prefix, "pattern": pattern, "limit": limit},
        ).mappings().all()
        return [_SearchRow(**row) for row in rows]


def ensure_search_indexes(db: Session) -> None:
    for statement in _INDEX_DDL.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            db.execute(text(stmt))


def ensure_fts(db: Session) -> None:
    db.execute(text(_FTS_DDL))
    for trigger_sql in (_FTS_TRIGGER_AI, _FTS_TRIGGER_AD, _FTS_TRIGGER_AU):
        db.execute(text(trigger_sql))

    fts_count = db.execute(text("SELECT COUNT(*) FROM products_fts")).scalar() or 0
    product_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
    if fts_count < product_count:
        db.execute(text("INSERT INTO products_fts(products_fts) VALUES ('rebuild')"))
    db.commit()


_ready_database_urls: set[str] = set()


def clear_search_cache() -> None:
    with _cache_lock:
        _cache.clear()


def initialize_product_search(db: Session, *, database_url: str) -> None:
    if database_url in _ready_database_urls:
        return
    ensure_search_indexes(db)
    ensure_fts(db)
    _ready_database_urls.add(database_url)
    logger.info("Product search indexes and FTS ready")
