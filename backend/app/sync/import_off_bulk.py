"""
Bulk import Vietnam products from Open Food Facts CSV dump.

OFF permits bulk download (nightly CSV ~900MB gzip):
  https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz

Usage:
  python -m app.sync.import_off_bulk --download
  python -m app.sync.import_off_bulk --file path/to/off.csv.gz
  python -m app.sync.import_off_bulk --download --limit 5000
"""

import argparse
import csv
import gzip
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# OFF rows can contain very large ingredient/image fields (Windows caps below sys.maxsize)
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)

from app.core.database import SessionLocal
from app.models.product import Product, ProductAdditive, ProductIngredient, ProductNutrient
from app.sync.quality import count_nutrients, quality_score

OFF_CSV_URL = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# OFF CSV column -> our nutrient codes
CSV_NUTRIENT_MAP = {
    "energy-kcal_100g": ("energy_kcal", "kcal"),
    "energy_100g": ("energy_kcal", "kcal"),
    "fat_100g": ("fat", "g"),
    "saturated-fat_100g": ("saturated_fat", "g"),
    "carbohydrates_100g": ("carbohydrates", "g"),
    "sugars_100g": ("sugars", "g"),
    "fiber_100g": ("fiber", "g"),
    "proteins_100g": ("proteins", "g"),
    "salt_100g": ("salt", "g"),
    "sodium_100g": ("sodium", "mg"),
}

VN_MARKERS = ("vietnam", "việt nam", "viet nam", "en:vietnam")


def is_vietnam_product(row: dict) -> bool:
    code = str(row.get("code") or row.get("_id") or "")
    if code.startswith("893"):
        return True
    for field in ("countries", "countries_tags", "countries_en", "origins", "origins_tags"):
        val = (row.get(field) or "").lower()
        if any(m in val for m in VN_MARKERS):
            return True
    return False


def _float(val: str | None) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val.replace(",", "."))
    except ValueError:
        return None


def row_passes_quality(row: dict) -> bool:
    name = row.get("product_name") or row.get("product_name_vi") or row.get("product_name_en")
    if not name or len(name.strip()) < 2:
        return False
    code = row.get("code") or row.get("_id")
    if not code or not str(code).strip().isdigit():
        return False

    nutrient_count = sum(1 for col in CSV_NUTRIENT_MAP if _float(row.get(col)) is not None)
    has_ingredients = bool((row.get("ingredients_text") or row.get("ingredients_text_vi") or "").strip())
    if nutrient_count < 2 and not has_ingredients:
        return False

    pseudo = {
        "product": {
            "code": code,
            "product_name": name,
            "ingredients_text": row.get("ingredients_text"),
            "nutriments": {k: _float(row.get(k)) for k in CSV_NUTRIENT_MAP if _float(row.get(k)) is not None},
            "nutrition_grades": row.get("nutrition_grades") or row.get("nutriscore_grade"),
            "nova_group": _float(row.get("nova_group")),
        }
    }
    return quality_score(pseudo) >= 40


def save_row(db, row: dict) -> bool:
    barcode = str(row.get("code") or row.get("_id")).strip()
    if db.query(Product).filter(Product.barcode == barcode, Product.source == "open_food_facts").first():
        return False

    name = (
        row.get("product_name_vi")
        or row.get("product_name")
        or row.get("product_name_en")
        or "Unknown"
    )
    categories = row.get("categories") or ""
    category = categories.split(",")[0].strip() if categories else None
    nova = row.get("nova_group")
    try:
        nova_group = int(float(nova)) if nova else None
    except (ValueError, TypeError):
        nova_group = None

    product = Product(
        barcode=barcode,
        name=name[:500],
        brand=(row.get("brands") or "")[:200] or None,
        category=category[:200] if category else None,
        source="open_food_facts",
        source_url=f"https://world.openfoodfacts.org/product/{barcode}",
        image_url=row.get("image_url") or row.get("image_front_url"),
        ingredients_text=(row.get("ingredients_text_vi") or row.get("ingredients_text") or "")[:5000] or None,
        allergens=row.get("allergens") or row.get("allergens_tags"),
        nutri_score=(row.get("nutrition_grades") or row.get("nutriscore_grade") or "")[:5] or None,
        nova_group=nova_group,
        last_synced_at=datetime.now(timezone.utc),
    )
    merged = db.merge(product)

    db.query(ProductNutrient).filter(ProductNutrient.barcode == barcode).delete()
    db.flush()
    added_nutrients: set[str] = set()
    for col, (code, unit) in CSV_NUTRIENT_MAP.items():
        if code in added_nutrients:
            continue
        val = _float(row.get(col))
        if val is not None:
            db.add(ProductNutrient(barcode=barcode, nutrient_code=code, amount=val, unit=unit, per_100g=True))
            added_nutrients.add(code)

    db.query(ProductIngredient).filter(ProductIngredient.barcode == barcode).delete()
    ing_text = merged.ingredients_text
    if ing_text:
        for i, part in enumerate(ing_text.split(",")):
            part = part.strip()
            if part:
                db.add(ProductIngredient(barcode=barcode, position=i, name=part[:300], normalized_name=part.lower()[:300]))

    db.query(ProductAdditive).filter(ProductAdditive.barcode == barcode).delete()
    additives = row.get("additives_tags") or row.get("additives") or ""
    for tag in additives.split(","):
        tag = tag.strip()
        if tag.upper().startswith("E") or "e-" in tag.lower():
            e = tag.split(":")[-1].upper().replace("-", "")
            if e.startswith("E"):
                db.add(ProductAdditive(barcode=barcode, e_number=e[:20], name=tag[:200]))

    db.commit()
    return True


def import_csv(path: Path, limit: int | None = None, skip_rows: int = 0) -> dict:
    db = SessionLocal()
    stats = {"scanned": 0, "vn_matched": 0, "quality_pass": 0, "imported": 0, "skipped_exists": 0}

    try:
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                stats["scanned"] += 1
                if stats["scanned"] <= skip_rows:
                    if stats["scanned"] % 500000 == 0:
                        print(f"  ... skipping to row {skip_rows:,} ({stats['scanned']:,})")
                    continue
                if stats["scanned"] % 50000 == 0:
                    print(f"  ... scanned {stats['scanned']:,} rows, imported {stats['imported']:,} VN products")

                if not is_vietnam_product(row):
                    continue
                stats["vn_matched"] += 1

                if not row_passes_quality(row):
                    continue
                stats["quality_pass"] += 1

                try:
                    if save_row(db, row):
                        stats["imported"] += 1
                    else:
                        stats["skipped_exists"] += 1
                except Exception as e:
                    db.rollback()
                    bc = str(row.get("code") or row.get("_id") or "?")
                    if stats["imported"] < 5:
                        print(f"  save error ({bc}): {e}")

                if limit and stats["imported"] >= limit:
                    break

        print(f"Done: {stats}")
        return stats
    finally:
        db.close()


def download_csv(dest: Path, force: bool = False) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        size_mb = dest.stat().st_size / (1024 * 1024)
        if size_mb < 800:
            print(f"Partial file ({size_mb:.0f}MB) — resuming download...")
        else:
            print(f"Using existing file ({size_mb:.0f}MB): {dest}")
            return dest

    print(f"Downloading OFF CSV dump (~900MB)...")
    print(f"URL: {OFF_CSV_URL}")
    headers = {"User-Agent": "FoodAdvise/1.0 (bulk import)"}
    with httpx.stream("GET", OFF_CSV_URL, headers=headers, timeout=600.0, follow_redirects=True) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as out:
            for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                out.write(chunk)
                downloaded += len(chunk)
                if total and downloaded % (50 * 1024 * 1024) < len(chunk):
                    print(f"  ... {downloaded / (1024*1024):.0f}MB / {total / (1024*1024):.0f}MB")
    print(f"Saved to {dest} ({dest.stat().st_size / (1024*1024):.0f}MB)")
    return dest


def main():
    parser = argparse.ArgumentParser(description="Bulk import VN products from OFF CSV dump")
    parser.add_argument("--download", action="store_true", help="Download OFF CSV.gz first")
    parser.add_argument("--file", type=str, default="", help="Path to local CSV/CSV.gz")
    parser.add_argument("--limit", type=int, default=None, help="Max products to import")
    parser.add_argument("--skip-rows", type=int, default=0, help="Skip first N data rows (resume)")
    args = parser.parse_args()

    csv_path = Path(args.file) if args.file else DATA_DIR / "off.products.csv.gz"

    if args.download:
        download_csv(csv_path, force=False)
    elif not csv_path.exists():
        print(f"File not found: {csv_path}")
        print("Run with --download to fetch OFF dump, or --file PATH")
        sys.exit(1)

    start = time.time()
    import_csv(csv_path, limit=args.limit, skip_rows=args.skip_rows)
    print(f"Elapsed: {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
