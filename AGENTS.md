# AGENTS.md

## Cursor Cloud specific instructions

### Services
- **Backend** — FastAPI (`backend/app/main.py`), served on port `8001`.
- **Frontend** — React + Vite SPA (`frontend/`), dev server on port `5173`. Vite proxies `/api` and `/health` to `http://127.0.0.1:8001`, so both services must run together.

### Environment / dependencies
- Backend uses a Python venv at `backend/.venv` (Python 3.12). The startup update script creates it and installs `backend/requirements.txt`; frontend deps come from `npm install` in `frontend/`.
- System packages required (installed in the VM image, not the update script): `python3.12-venv`, and `tesseract-ocr` + `tesseract-ocr-vie` (only needed for the ingredient-OCR-from-image feature).
- Local dev uses **SQLite** by default (`DATABASE_URL=sqlite:///./foodadvise.db`), so no Postgres/Redis service is required. Redis is optional; the cache layer degrades gracefully when it is absent.
- Copy `.env.example` to `.env` if you need to override defaults (e.g. add a `USDA_API_KEY`); the app runs fine without it using the 50 seeded demo products.

### Database is not committed
- The SQLite DB (`*.db`) is gitignored and NOT created by the update script. Before running the backend on a fresh VM you MUST initialize it from `backend/` with the venv:
  - `.venv/bin/alembic upgrade head`
  - `.venv/bin/python -m app.sync.seed` (seeds ~50 Vietnamese demo products)

### Running (from repo root unless noted)
- Backend: from `backend/`, `.venv/bin/uvicorn app.main:app --reload --port 8001 --host 0.0.0.0`
- Frontend: from `frontend/`, `npm run dev -- --host 0.0.0.0`
- Demo flow: open `http://localhost:5173`, pick a profile (e.g. "Tiểu đường"), enter barcode `8934564010014`, view the advice/warnings. API docs at `http://localhost:8001/docs`.

### Public preview / verify (Cloudflare quick tunnel)
- To expose the running app on a temporary public URL: `cloudflared tunnel --url http://localhost:5173` → prints a `https://<random>.trycloudflare.com` URL. Only the frontend needs to be tunneled (Vite proxies `/api` + `/health` to the backend). `vite.config.ts` already sets `allowedHosts: true` and the backend CORS already allows `*.trycloudflare.com`. The URL is ephemeral (changes each run, tied to the VM session).

### Data / crawlers
- DB starts from `python -m app.sync.seed` (~50 demo products). Safe bulk-ish enrichment: `python -m app.sync.import_off` (Open Food Facts API, VN brands/categories) — legal and reliable.
- Retailer crawlers `import_bigc` / `import_aeon` are best-effort and currently return 0 (BigC/GO `sitemap.xml` responds 302; AEON's index uses `sitemap-products.xml` naming that the crawler's `sitemap_products` filter does not match). `import_bachhoaxanh` / `import_teko` need specific product-ids/SKUs + store/terminal codes and are considered ToS-risky.

### Key API endpoints (beyond README)
- `GET /api/v1/products?q=<name>&ingredient=<thành phần>&limit=&offset=` — list/manage all products, filter by name/brand and/or ingredient (powers the `/products` management page).

### Lint / test / build
- Backend tests: from `backend/`, `.venv/bin/pytest`.
- Frontend lint: from `frontend/`, `npm run lint`. Frontend build: `npm run build`.
- Note: `frontend/package.json` originally declared no ESLint packages and `eslint.config.js` referenced `reactHooks.configs.flat.recommended`, which no released `eslint-plugin-react-hooks` version exposes. The ESLint dev dependencies were added and the reference was corrected to `configs['flat/recommended']` so `npm run lint` works.
