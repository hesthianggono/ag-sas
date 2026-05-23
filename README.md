# AG Structural Analysis Suite (AG-SAS)

> **Disclaimer:** Semua hasil perhitungan yang dihasilkan aplikasi ini bersifat indikatif dan WAJIB diperiksa ulang oleh engineer struktur berwenang sebelum digunakan dalam dokumen desain resmi.

---

## Tentang Aplikasi

AG-SAS adalah platform perhitungan dan pelaporan struktur baja dan beton berbasis web yang dirancang untuk engineer struktural di Indonesia. Aplikasi ini mengacu pada standar SNI yang berlaku dan menghasilkan laporan perhitungan terformat yang dapat digunakan sebagai lampiran dokumen teknis.

Aplikasi ini **tidak menggantikan** software analisis struktur besar seperti SAP2000 atau ETABS, namun dirancang modular agar dapat dikembangkan menjadi platform analisis struktur lengkap dengan FEM solver, 3D modeling, dan automatic report generation.

---

## Standar Desain yang Didukung

| Kode | Judul | Ruang Lingkup |
|------|-------|---------------|
| SNI 1727:2020 | Beban Desain Minimum | Beban mati, hidup, angin, salju |
| SNI 1726:2019 | Ketahanan Gempa Gedung | Analisis seismik, respons spektrum |
| SNI 2847:2019 | Beton Struktural Gedung | Desain balok, kolom, pelat beton |
| SNI 1729:2020 | Bangunan Gedung Baja Struktural | Desain elemen baja |
| SNI 7860:2020 | Seismik Bangunan Baja | Ketentuan seismik baja |
| SNI 8369:2020 | Praktik Baku Baja | Fabrikasi dan ereksi baja |

---

## Stack Teknologi

### Frontend
- **Framework:** Next.js 14 (App Router) + TypeScript
- **Styling:** Tailwind CSS + shadcn/ui
- **State Management:** Zustand
- **HTTP Client:** Axios
- **3D Viewer:** React Three Fiber + Three.js (future module)
- **Charts:** Recharts

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Authentication:** JWT (python-jose)
- **PDF Generation:** ReportLab
- **Calculation Engine:** Python (terpisah dari API layer)

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Reverse Proxy:** Nginx (production)

---

## Struktur Folder

```
/ag-sas
  /frontend               # Next.js application
    /app                  # App Router pages
    /components           # Reusable UI components
    /lib                  # Utilities, API client
    /types                # TypeScript type definitions
    /modules              # Feature modules (calculation, report, etc.)
  /backend
    /app
      /api                # FastAPI routers
      /core               # Config, security, dependencies
      /db                 # Database session, base
      /models             # SQLModel table models
      /schemas            # Pydantic request/response schemas
      /services           # Business logic layer
      /calculation        # Pure calculation engine (no DB dependency)
        /concrete         # SNI 2847:2019 calculations
        /steel            # SNI 1729:2020 calculations
        /loads            # SNI 1727:2020 load combinations
        /seismic          # SNI 1726:2019 seismic
        /foundation       # Foundation calculations (future)
      /reporting          # PDF report generator
      /standards          # SNI reference data & formulas registry
    /tests                # Unit tests for calculation engine
  /docs
    /architecture         # Architecture decision records
    /calculation-notes    # Manual derivation notes
    /sni-reference-map    # Article cross-reference index
```

---

## Cara Menjalankan (Development)

### Prasyarat
- Docker Desktop (Windows/Mac/Linux)
- Node.js 18+ (untuk development frontend tanpa Docker)
- Python 3.11+ (untuk development backend tanpa Docker)

### 1. Clone dan Setup

```bash
git clone <repo-url>
cd ag-sas
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

### 2. Jalankan dengan Docker Compose

```bash
docker-compose up --build
```

Layanan yang berjalan:
| Layanan | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### 3. Migrasi Database (pertama kali)

```bash
docker-compose exec backend python -m app.db.init_db
```

### 4. Jalankan Unit Tests

```bash
docker-compose exec backend pytest tests/ -v
```

### 5a. Jalankan Unit Tests — Engineering Kernel (tanpa Docker)

```bash
cd backend
pytest tests/engineering_kernel/ -v
```

Atau hanya satu file:

```bash
pytest tests/engineering_kernel/test_units.py -v        # konversi satuan
pytest tests/engineering_kernel/test_models.py -v       # data model struktural
pytest tests/engineering_kernel/test_traceability.py -v # sistem traceability
```

### 5. Development Tanpa Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Fitur MVP v1.0

- [x] Autentikasi (Register / Login / JWT)
- [x] Dashboard Proyek
- [x] CRUD Proyek Struktur
- [x] Modul Balok Beton Bertulang (SNI 2847:2019)
- [x] Modul Balok Baja WF (SNI 1729:2020)
- [x] Database Profil Baja (WF, H-Beam, CNP, UNP, Siku, Hollow)
- [x] Generate Laporan PDF
- [x] Riwayat Perhitungan
- [x] Placeholder 3D Viewer

---

## Roadmap

### v1.1 — Beban & Kombinasi
- Kalkulator kombinasi beban SNI 1727:2020
- Input beban angin dan beban gempa sederhana
- Diagram gaya dalam (M, V, N)

### v1.2 — Kolom & Sambungan
- Desain kolom beton bertulang (SNI 2847:2019)
- Desain kolom baja (SNI 1729:2020)
- Desain sambungan baut sederhana

### v1.3 — Seismik
- Input parameter seismik (wilayah, kelas situs)
- Analisis respons spektrum desain (SNI 1726:2019)
- Kategori desain seismik

### v2.0 — Structural Modeler
- 2D frame modeler
- Direct Stiffness Method solver
- Diagram gaya dalam otomatis

### v3.0 — FEM Platform
- 3D modeling dengan React Three Fiber
- FEM solver berbasis Python
- Auto-design optimization

---

## Engineering Kernel (Tahap 0)

Engineering Kernel adalah fondasi teknis AG-SAS — lapisan Python murni
yang tidak bergantung pada web framework, ORM, atau database.

| Modul | Lokasi | Deskripsi |
|-------|--------|-----------|
| Unit System | `backend/app/engineering_kernel/units/` | Enum satuan, fungsi konversi, Quantity |
| Sign Convention | `backend/app/engineering_kernel/conventions/` | Konvensi tanda resmi (McGuire MSA §3.2) |
| Data Models | `backend/app/engineering_kernel/models/` | Node, Element, Material, Section, Load, LoadCombination, Results |
| Traceability | `backend/app/engineering_kernel/traceability/` | AnalysisTrace (immutable), build_trace() |

Dokumentasi lengkap:
- [`docs/architecture/engineering-kernel.md`](docs/architecture/engineering-kernel.md) — arsitektur kernel
- [`docs/calculation-notes/unit-system.md`](docs/calculation-notes/unit-system.md) — sistem satuan
- [`docs/calculation-notes/sign-convention.md`](docs/calculation-notes/sign-convention.md) — konvensi tanda

---

## Prinsip Desain

1. **Clean Architecture** — calculation engine sepenuhnya terpisah dari API layer
2. **Unit-First** — semua input/output harus memiliki satuan yang jelas (N, kN, mm, m, MPa)
3. **Traceable Calculation** — setiap hasil menyimpan versi formula dan referensi pasal
4. **Test-Driven Calc** — semua formula harus memiliki unit test
5. **No Hardcoded Formulas in Frontend** — semua kalkulasi terjadi di backend
6. **Engineering Disclaimer** — setiap output menampilkan peringatan review engineer

---

## Kontribusi

Lihat `docs/architecture/CONTRIBUTING.md` untuk panduan kontribusi dan konvensi kode.

---

## Lisensi

Hak cipta © 2024 AG Engineering. Seluruh konten SNI yang direferensikan adalah milik BSN dan hanya digunakan sebagai indeks referensi nomor pasal.
