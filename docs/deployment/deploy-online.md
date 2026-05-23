# Panduan Deploy AG-SAS Online
## Stack: Vercel (Frontend) + Render (Backend) + Neon (PostgreSQL)

Semua gratis — tidak perlu kartu kredit untuk paket free tier.

---

## Persiapan: Push ke GitHub

Sebelum deploy, kode harus ada di GitHub.

```powershell
# Di folder ag-sas
git init
git add .
git commit -m "Initial commit — AG-SAS v1.0"
```

Buat repo baru di https://github.com/new (nama: `ag-sas`), lalu:

```powershell
git remote add origin https://github.com/USERNAME/ag-sas.git
git branch -M main
git push -u origin main
```

---

## Langkah 1 — Database di Neon (PostgreSQL Gratis)

1. Buka https://neon.tech → **Sign Up** (gratis, pakai GitHub)
2. Klik **New Project** → nama: `ag-sas` → region: **Singapore**
3. Setelah dibuat, klik **Connection Details**
4. Salin **Connection String** format:
   ```
   postgresql://username:password@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
5. **Simpan string ini** — akan dipakai di Render

---

## Langkah 2 — Backend di Render

1. Buka https://render.com → **Sign Up** (gratis, pakai GitHub)
2. Klik **New** → **Web Service**
3. **Connect Repository** → pilih repo `ag-sas`
4. Isi settings:
   - **Name**: `ag-sas-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Docker`
   - **Region**: Singapore
   - **Plan**: Free
5. Di bagian **Environment Variables**, tambahkan:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | *(connection string Neon dari Langkah 1)* |
   | `SECRET_KEY` | *(string random 32+ karakter, generate di https://generate-secret.vercel.app/32)* |
   | `ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
   | `ENVIRONMENT` | `production` |
   | `ALLOWED_ORIGINS` | *(isi setelah Vercel deploy — lihat Langkah 3)* |

6. Klik **Create Web Service**
7. Tunggu build selesai (~5-10 menit pertama kali)
8. URL backend akan muncul: `https://ag-sas-backend.onrender.com`

> **Catatan Free Tier Render**: Service akan "tidur" setelah 15 menit tidak ada request.
> Request pertama setelah tidur butuh ~30 detik (cold start). Ini normal untuk free tier.

---

## Langkah 3 — Frontend di Vercel

1. Buka https://vercel.com → **Sign Up** (gratis, pakai GitHub)
2. Klik **Add New** → **Project**
3. **Import** repo `ag-sas`
4. Isi settings:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
5. Di bagian **Environment Variables**, tambahkan:

   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_URL` | `https://ag-sas-backend.onrender.com` |

6. Klik **Deploy**
7. Tunggu build selesai (~3-5 menit)
8. URL frontend: `https://ag-sas-frontend.vercel.app` (atau custom domain)

---

## Langkah 4 — Update CORS di Render

Setelah frontend deploy dan dapat URL Vercel:

1. Buka Render dashboard → service `ag-sas-backend`
2. Klik **Environment**
3. Edit variable `ALLOWED_ORIGINS`:
   ```
   https://ag-sas-frontend.vercel.app,https://ag-sas.vercel.app
   ```
   *(sesuaikan dengan URL Vercel Anda)*
4. Service akan auto-redeploy

---

## Langkah 5 — Verifikasi

Cek backend hidup:
```
https://ag-sas-backend.onrender.com/health
```
Response: `{"status": "ok", "app": "AG Structural Analysis Suite", "version": "1.0.0"}`

Cek API docs:
```
https://ag-sas-backend.onrender.com/docs
```

Buka frontend:
```
https://ag-sas-frontend.vercel.app
```

---

## Update Kode (Setelah Perubahan)

Setiap kali push ke GitHub, Vercel dan Render akan **auto-deploy**:

```powershell
git add .
git commit -m "Deskripsi perubahan"
git push
```

---

## Troubleshooting

### Backend error "could not connect to server"
→ Cek `DATABASE_URL` di Render sudah benar (dari Neon)

### Frontend "Network Error" / "CORS"
→ Cek `NEXT_PUBLIC_API_URL` di Vercel sudah benar
→ Cek `ALLOWED_ORIGINS` di Render sudah include URL Vercel

### Cold start lambat (~30 detik)
→ Normal untuk Render free tier. Gunakan UptimeRobot (gratis) untuk ping setiap 14 menit:
  - Buka https://uptimerobot.com → Add Monitor
  - URL: `https://ag-sas-backend.onrender.com/health`
  - Interval: 14 menit
  - Ini mencegah service "tidur"

### Database tidak ter-inisialisasi
→ Cek logs Render: `start.sh` menjalankan `init_db()` otomatis saat startup

---

## Biaya

| Layanan | Plan | Biaya |
|---------|------|-------|
| Vercel | Hobby (gratis) | $0 |
| Render | Free | $0 (tidur 15 menit idle) |
| Neon | Free | $0 (0.5 GB storage) |
| **Total** | | **$0/bulan** |

Untuk production serius, upgrade Render ke **Starter ($7/bulan)** agar tidak ada cold start.
