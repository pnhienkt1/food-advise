"""Benchmark product search before/after optimizations."""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.product import Product
from app.services.product_search import ProductSearchService, clear_search_cache


def benchmark_ilike(db, term: str, iterations: int) -> float:
    pattern = f"%{term}%"
    prefix = f"{term}%"
    for _ in range(3):
        (
            db.query(Product)
            .filter(
                (Product.name.ilike(pattern))
                | (Product.brand.ilike(pattern))
                | (Product.barcode.ilike(prefix))
            )
            .order_by(
                Product.name.ilike(prefix).desc(),
                Product.brand.ilike(prefix).desc(),
                Product.name.asc(),
            )
            .limit(10)
            .all()
        )

    t0 = time.perf_counter()
    for _ in range(iterations):
        (
            db.query(Product)
            .filter(
                (Product.name.ilike(pattern))
                | (Product.brand.ilike(pattern))
                | (Product.barcode.ilike(prefix))
            )
            .order_by(
                Product.name.ilike(prefix).desc(),
                Product.brand.ilike(prefix).desc(),
                Product.name.asc(),
            )
            .limit(10)
            .all()
        )
    return (time.perf_counter() - t0) / iterations * 1000


def benchmark_optimized(db, term: str, iterations: int, *, use_cache: bool) -> float:
    service = ProductSearchService(db)
    for _ in range(3):
        clear_search_cache()
        service.search(term, limit=10)

    timings: list[float] = []
    for i in range(iterations):
        if not use_cache:
            clear_search_cache()
        t0 = time.perf_counter()
        service.search(term, limit=10)
        timings.append((time.perf_counter() - t0) * 1000)
    return sum(timings) / len(timings)


def seed_scaled_db(path: Path, count: int) -> str:
    from app.core.database import Base
    from app.models.product import Product
    from app.services.product_search import initialize_product_search

    url = f"sqlite:///{path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    brands = ["Vinamilk", "Acecook", "Orion", "Kinh Do", "Cholimex"]
    for i in range(count):
        db.add(
            Product(
                barcode=f"scale{i:08d}",
                name=f"Sản phẩm mì gói số {i}",
                brand=brands[i % len(brands)],
                source="bench",
            )
        )
        if i and i % 5000 == 0:
            db.commit()
    db.commit()
    initialize_product_search(db, database_url=url)
    db.close()
    return url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--term", default="mi")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--scale", type=int, default=0, help="Seed N synthetic products into a temp DB")
    args = parser.parse_args()

    if args.scale > 0:
        db_path = Path(__file__).resolve().parent / f"bench_{args.scale}.db"
        if db_path.exists():
            db_path.unlink()
        database_url = seed_scaled_db(db_path, args.scale)
    else:
        database_url = settings.database_url

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()

    count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
    print(f"products: {count}")

    plan = db.execute(
        text(
            """
            EXPLAIN QUERY PLAN
            SELECT barcode FROM products
            WHERE name LIKE :pattern OR brand LIKE :pattern OR barcode LIKE :prefix
            LIMIT 10
            """
        ),
        {"pattern": f"%{args.term}%", "prefix": f"{args.term}%"},
    ).fetchall()
    print("EXPLAIN (ilike):", [row[3] for row in plan])

    ilike_ms = benchmark_ilike(db, args.term, args.iterations)
    print(f"ilike search: {ilike_ms:.3f} ms/req (n={args.iterations})")

    try:
        opt_ms = benchmark_optimized(db, args.term, args.iterations, use_cache=False)
        opt_cached_ms = benchmark_optimized(db, args.term, args.iterations, use_cache=True)
        print(f"optimized search (uncached): {opt_ms:.3f} ms/req (n={args.iterations})")
        print(f"optimized search (cached): {opt_cached_ms:.3f} ms/req (n={args.iterations})")
        if opt_ms > 0:
            print(f"speedup (uncached): {ilike_ms / opt_ms:.1f}x")
    except Exception as exc:
        print(f"optimized search unavailable: {exc}")

    db.close()


if __name__ == "__main__":
    main()
