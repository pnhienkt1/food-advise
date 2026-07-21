# Food Advise

Web demo quét barcode/QR thực phẩm, tra cứu thông tin dinh dưỡng từ nguồn chính thức, và đưa ra đánh giá cá nhân hóa dựa trên rule engine (không dùng LLM).

## Tính năng

- Quét barcode qua webcam hoặc nhập mã thủ công
- OCR thành phần từ ảnh (fallback khi không có barcode)
- Tra cứu sản phẩm từ Open Food Facts (fallback USDA FoodData Central)
- Đánh giá phù hợp theo profile: tuổi, bệnh lý, mục tiêu dinh dưỡng, dị ứng
- Cảnh báo thành phần dựa trên rule engine + template tiếng Việt
- Gợi ý sản phẩm thay thế tốt hơn
- Lịch sử quét (localStorage)
- 50 sản phẩm VN demo (Mì Hảo Hảo, Vinamilk, Coca-Cola, ...)

## Tech stack

| Layer | Công nghệ |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |

## Chạy nhanh với Docker

```bash
# Clone và vào thư mục project
cd food_advise

# (Tuỳ chọn) Thêm USDA API key vào .env
cp .env.example .env

# Khởi động toàn bộ stack
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

### Demo flow

1. Mở http://localhost:5173
2. Chọn profile (VD: "Tiểu đường")
3. Nhập barcode `8934564010014` (Mì Hảo Hảo) hoặc quét camera
4. Xem đánh giá, cảnh báo natri/đường/NOVA group

## Chạy local (không Docker)

### Backend

```bash
# Mặc định dùng SQLite (không cần cài PostgreSQL cho demo local)
cd backend
pip install -r requirements.txt

# Migrate + seed
alembic upgrade head
python -m app.sync.seed

# Chạy API
uvicorn app.main:app --reload --port 8001
```

**PostgreSQL (tuỳ chọn):** set `DATABASE_URL=postgresql://foodadvise:foodadvise@localhost:5432/foodadvise` trong `.env` nếu dùng Docker/production.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend proxy `/api` → `http://localhost:8001` qua Vite config.

## API endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/health` | Health check |
| GET | `/api/v1/products/{barcode}` | Tra sản phẩm |
| POST | `/api/v1/advice/evaluate` | Đánh giá theo profile |
| POST | `/api/v1/advice/evaluate-ingredients` | Đánh giá theo ingredients text |
| POST | `/api/v1/ocr/ingredients` | OCR thành phần từ ảnh upload |
| GET | `/api/v1/profiles/presets` | Preset profile demo |
| GET | `/api/v1/products/{barcode}/alternatives` | Gợi ý thay thế |

## Chạy tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Nguồn dữ liệu

Xem kế hoạch chi tiết: [docs/DATA_SOURCES_PLAN.md](docs/DATA_SOURCES_PLAN.md)

### Import hàng loạt (khuyến nghị — nhiều SP VN nhất)

```bash
cd backend
python -m app.sync.import_off_bulk --download --limit 5000
```

Tải dump CSV Open Food Facts (~900MB), lọc sản phẩm `vietnam`, quality gate, import vào DB.

### Import qua API (bổ sung thương hiệu VN)

Script cào sản phẩm Việt Nam từ OFF với **bộ lọc chất lượng** (tên, ≥2 chất dinh dưỡng hoặc thành phần, điểm completeness ≥ 40):

```bash
cd backend
# Tìm kiếm theo quốc gia/thương hiệu VN (5 trang/query)
python -m app.sync.import_off --max-pages 5 --page-size 50

# Hoặc import barcode cụ thể
python -m app.sync.import_off --barcodes 8934564010014,8938503920012
```

Nguồn tin cậy: chỉ lưu sản phẩm từ **Open Food Facts** (ODbL) và **USDA FDC** (CC0), kèm badge nguồn trên UI.

### Import nguồn mở rộng (BXH/Teko/AEON/BigC)

```bash
cd backend

# Bách Hóa Xanh (cần danh sách product id)
python -m app.sync.import_bachhoaxanh \
  --product-ids 228705,228706 \
  --province-id 46 --district-id 564 --ward-id 20665 --store-id 1549 \
  --category-url mi-goi --product-url mi-tron \
  --min-delay 0.4 --max-delay 1.0 --max-rps 0.8

# Teko discovery (cần danh sách sku)
python -m app.sync.import_teko \
  --skus 250100162,20618432 \
  --terminal-code 509_sgc --location "" \
  --min-delay 0.4 --max-delay 1.0 --max-rps 0.8

# AEON crawler best-effort (public sitemap/pages)
python -m app.sync.import_aeon --limit 30

# BigC/GO crawler best-effort (public sitemap/pages)
python -m app.sync.import_bigc --limit 100
```

Các importer đều có quality gate, skip bản ghi thiếu dữ liệu, merge theo `barcode`, và ghi log tiến trình import.

### Safe crawling defaults (chống block IP)

- Dùng delay ngẫu nhiên giữa request: `--min-delay 0.4 --max-delay 1.0`
- Giới hạn tốc độ: `--max-rps 0.8` (không quá ~1 request/giây)
- Importer có retry exponential backoff + jitter cho timeout/`429`/`5xx`
- Khi gặp burst `429/403`, importer tự cooldown để giảm nguy cơ block
- Mặc định chạy tuần tự (concurrency = 1), ưu tiên ổn định hơn tốc độ

## OCR local setup

Backend dùng `pytesseract` + tiền xử lý ảnh (grayscale/threshold/denoise/resize).  
Ngoài `pip install -r requirements.txt`, cần cài thêm binary Tesseract OCR:

- Windows: cài Tesseract và thêm vào `PATH`
- Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-vie`
- macOS: `brew install tesseract tesseract-lang`

## Gợi ý thực phẩm

- **API:** `POST /api/v1/recommendations` — body = profile, trả về top sản phẩm phù hợp (score ≥ 70, không cảnh báo nguy hiểm)
- **UI:** tab **Gợi ý** trên web app

## Nhóm tuổi trẻ em

Hỗ trợ chi tiết: trẻ sơ sinh, 1-2, 2-4, 4-6, 6-12 tuổi — mỗi nhóm có ngưỡng muối/đường/NOVA riêng theo WHO/UNICEF.


- **Open Food Facts** — nguồn chính, API v2/v3
- **USDA FoodData Central** — fallback sản phẩm branded (cần API key miễn phí)
- **Manual seed** — 50 sản phẩm VN phổ biến cho demo offline

## Deploy demo (Cloudflare Tunnel)

```powershell
.\scripts\start-cloudflared.ps1
```

Chi tiết: [docs/DEPLOY_CLOUDFLARED.md](docs/DEPLOY_CLOUDFLARED.md)

## Disclaimer

Thông tin trên app chỉ mang tính tham khảo, không thay thế tư vấn y tế chuyên môn.
