# Start Cloudflare quick tunnel for Food Advise frontend
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$frontendPort = 5173
$backendPort = 8001

Write-Host "Checking services..."
$fe = Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue
$be = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue

if (-not $fe) {
    Write-Host "WARNING: Frontend not on port $frontendPort. Run: cd frontend; npm run dev -- --host 0.0.0.0" -ForegroundColor Yellow
}
if (-not $be) {
    Write-Host "WARNING: Backend not on port $backendPort. Run: cd backend; uvicorn app.main:app --port $backendPort" -ForegroundColor Yellow
}

Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
if (-not (Test-Path $cloudflared)) {
    $cloudflared = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
}
if (-not $cloudflared) {
    Write-Host "Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting tunnel -> http://127.0.0.1:$frontendPort" -ForegroundColor Green
Write-Host "Look for URL: https://xxxx.trycloudflare.com" -ForegroundColor Cyan
$urlLog = Join-Path $root "data\tunnel_url.txt"
Write-Host "Tunnel URL will be saved to: $urlLog" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop"
Write-Host ""

& $cloudflared tunnel --url "http://127.0.0.1:$frontendPort" 2>&1 | ForEach-Object {
    $_
    if ($_ -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
        $matches[0] | Set-Content -Path $urlLog -Encoding utf8
    }
}
