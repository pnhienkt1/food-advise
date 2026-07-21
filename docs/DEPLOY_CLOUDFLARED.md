# Food Advise — Cloudflare Tunnel (cloudflared)

## Yêu cầu

- Backend chạy port **8001**
- Frontend (Vite) chạy port **5173** — proxy `/api` → backend
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) đã cài

## Quick tunnel (demo công khai, URL tạm)

```powershell
# Terminal 1 — backend
cd D:\AWork\food_advise\backend
uvicorn app.main:app --host 127.0.0.1 --port 8001

# Terminal 2 — frontend
cd D:\AWork\food_advise\frontend
npm run dev

# Terminal 3 — tunnel (chỉ cần expose frontend, Vite proxy API)
cd D:\AWork\food_advise
.\scripts\start-cloudflared.ps1
```

URL dạng `https://xxxx.trycloudflare.com` sẽ in ra console.

## Import dữ liệu VN hàng loạt (trước khi demo)

```powershell
cd D:\AWork\food_advise\backend
# Tải dump OFF (~900MB) + import sản phẩm VN
python -m app.sync.import_off_bulk --download --limit 5000

# Hoặc chỉ API crawl thương hiệu VN
python -m app.sync.import_off --max-pages 15 --page-size 100
```

Chi tiết nguồn dữ liệu: [docs/DATA_SOURCES_PLAN.md](../docs/DATA_SOURCES_PLAN.md)

## Lưu ý

- Quick tunnel URL **đổi mỗi lần** chạy lại cloudflared
- Tunnel miễn phí không đảm bảo SLA — dùng cho demo
- Production: dùng [Named Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) + domain riêng
