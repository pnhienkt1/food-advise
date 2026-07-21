# Kế hoạch nguồn dữ liệu chất lượng cao — Ưu tiên Việt Nam

## Mục tiêu

- **10.000+** sản phẩm VN có barcode, thành phần, dinh dưỡng đáng tin cậy
- Mỗi record có **nguồn gốc audit** (URL, license, ngày cập nhật)
- Chỉ lưu record đạt **quality gate** (xem `app/sync/quality.py`)

---

## Ma trận nguồn dữ liệu

| Ưu tiên | Nguồn | Quy mô VN ước tính | Cào được? | Chất lượng | Cách tích hợp |
|---------|-------|-------------------|-----------|------------|---------------|
| **P0** | [Open Food Facts dump CSV/JSONL](https://world.openfoodfacts.org/data) | ~5.000–15.000 SP VN | ✅ Bulk (không dùng API từng SP) | Cao (cộng đồng + Nutri-Score) | `import_off_bulk.py` — lọc `countries_tags` chứa `vietnam` |
| **P0** | OFF Legacy Search API | Hàng nghìn | ✅ Có rate limit | Trung bình–Cao | `import_off.py` (đã có) — bổ sung query thương hiệu VN |
| **P1** | [USDA FoodData Central](https://fdc.nal.usda.gov/) | SP nhập khẩu có GTIN | ✅ API miễn phí | Cao (chính phủ Mỹ) | Fallback theo barcode (đã có) |
| **P1** | GS1 Vietnam / [ma số mã vạch](https://www.gs1vn.org.vn/) | Toàn bộ GTIN đăng ký | ⚠️ Không API công khai | Metadata (tên, DN) | Phase 2: đối tác hoặc CSV hợp tác |
| **P2** | [Cục ATTP — công bố SP](https://congbosanpham.vfa.gov.vn) | Thực phẩm đăng ký | ⚠️ Web form, không barcode | Cao (chính thức BYT) | Scrape theo tên → map barcode thủ công / fuzzy match |
| **P2** | [truyxuatnguongoc.gov.vn](https://truyxuatnguongoc.gov.vn) | ~4.500 SP | ⚠️ QR payload | Cao (Bộ KH&CN) | Parse QR → enrich metadata |
| **P3** | Siêu thị (WinMart, Co.opmart APIs) | Rất lớn | ❌ Không công khai | — | Không cào — vi phạm ToS |
| **P3** | Shopee/Lazada | Rất lớn | ❌ Anti-bot | — | Không khuyến khích |

---

## Chiến lược cào hợp pháp & chất lượng

### Phase 1 — OFF Bulk (triển khai ngay) ⭐

```
openfoodfacts.org/products.csv.gz (~900MB)
    → lọc countries_tags ILIKE '%vietnam%'
    → quality gate (tên + ≥2 nutrients hoặc ingredients)
    → upsert PostgreSQL/SQLite
```

**Ưu điểm:** Không vi phạm OFF API policy (dump được phép), 1 lần tải → hàng nghìn SP VN.

**Lệnh:**
```bash
cd backend
python -m app.sync.import_off_bulk --download
python -m app.sync.import_off_bulk --file data/off.csv.gz
```

### Phase 2 — OFF API bổ sung (theo thương hiệu VN)

Danh sách brand tag cần quét (legacy search):

- acecook, vifon, masan, vinamilk, th-milk, vinasoy, kinh-do, pepsico, coca-cola, unilever, nestle, acesweet, sabeco, tan-hiep-phat

```bash
python -m app.sync.import_off --max-pages 20 --page-size 100
```

### Phase 3 — Enrichment chính thức VN

1. **VFA công bố sản phẩm:** batch crawl theo danh sách tên từ OFF → lưu `product_alerts` / `official_registration`
2. **Cross-check:** barcode có trên OFF nhưng không có trên VFA → flag `verification_status: unverified_vn`

### Phase 4 — Crowdsource (sau MVP)

- Link "Đóng góp lên Open Food Facts" (đã có)
- Admin CSV import cho sản phẩm local chưa có GTIN

---

## Quality gate (bắt buộc mọi nguồn)

| Tiêu chí | Ngưỡng |
|----------|--------|
| Có tên sản phẩm | Bắt buộc |
| Barcode hợp lệ | 8–14 chữ số |
| Dinh dưỡng HOẶC thành phần | ≥2 nutrients **hoặc** ingredients_text |
| Completeness score | ≥ 40/100 |
| Nguồn | Chỉ `open_food_facts`, `usda_fdc`, `manual`, `vfa` |

---

## Lộ trình số lượng

| Tuần | Hành động | SP mục tiêu |
|------|-----------|-------------|
| 1 | OFF bulk import VN | 3.000–8.000 |
| 2 | OFF brand crawl + USDA fallback | +1.000 |
| 3 | VFA enrichment top 500 SP bán chạy | metadata chính thức |
| 4 | Cron weekly refresh OFF delta | duy trì |

---

## Rủi ro & giảm thiểu

| Rủi ro | Giải pháp |
|--------|-----------|
| OFF thiếu SP VN mới | Manual seed + crowdsource |
| Dữ liệu OFF sai | Badge nguồn + Nutri-Score + user report |
| VFA không có barcode | Fuzzy match tên + brand |
| File dump quá lớn | Stream gzip, không load RAM |

---

## Tham chiếu

- OFF Data: https://world.openfoodfacts.org/data
- OFF API policy: 1 API call = 1 user scan; bulk = dùng dump
- USDA API: https://fdc.nal.usda.gov/api-guide
- VFA: https://vfa.gov.vn
