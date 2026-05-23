# AG-SAS Development Server Starter
# Jalankan dengan: powershell -ExecutionPolicy Bypass -File start-dev.ps1

Write-Host "=== AG Structural Analysis Suite — Dev Server ===" -ForegroundColor Cyan
Write-Host ""

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"

# ── 1. Cek PostgreSQL ────────────────────────────────────────────────────────
Write-Host "[1/3] Mengecek PostgreSQL..." -ForegroundColor Yellow
$pgRunning = netstat -ano | Select-String ":5432 "
if ($pgRunning) {
    Write-Host "    PostgreSQL OK (port 5432)" -ForegroundColor Green
} else {
    Write-Host "    PostgreSQL tidak ditemukan! Pastikan PostgreSQL berjalan." -ForegroundColor Red
    exit 1
}

# ── 2. Jalankan Backend ───────────────────────────────────────────────────────
Write-Host "[2/3] Menjalankan Backend FastAPI (port 8000)..." -ForegroundColor Yellow

$backendRunning = netstat -ano | Select-String ":8000 "
if ($backendRunning) {
    Write-Host "    Backend sudah berjalan di port 8000" -ForegroundColor Green
} else {
    Start-Process -FilePath "cmd.exe" `
      -ArgumentList "/K", "title AG-SAS Backend && set PYTHONPATH=$BACKEND && .\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload" `
      -WorkingDirectory $BACKEND `
      -WindowStyle Normal
    Start-Sleep -Seconds 5
    Write-Host "    Backend dimulai di http://localhost:8000" -ForegroundColor Green
    Write-Host "    API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

# ── 3. Jalankan Frontend ──────────────────────────────────────────────────────
Write-Host "[3/3] Menjalankan Frontend Next.js (port 3000)..." -ForegroundColor Yellow

$frontendRunning = netstat -ano | Select-String ":3000 "
if ($frontendRunning) {
    Write-Host "    Frontend sudah berjalan di port 3000" -ForegroundColor Green
} else {
    Start-Process -FilePath "cmd.exe" `
      -ArgumentList "/K", "title AG-SAS Frontend && npm run dev" `
      -WorkingDirectory $FRONTEND `
      -WindowStyle Normal
    Start-Sleep -Seconds 3
    Write-Host "    Frontend dimulai di http://localhost:3000" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Semua service berjalan ===" -ForegroundColor Cyan
Write-Host "   Frontend  : http://localhost:3000" -ForegroundColor White
Write-Host "   Backend   : http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs  : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Tekan Ctrl+C untuk keluar dari script ini (service tetap berjalan di window terpisah)" -ForegroundColor Gray
