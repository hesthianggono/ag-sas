# AG-SAS: Roadmap Pengembangan

**Visi:** Platform analisis struktur berbasis web yang mendukung desain elemen, analisis 2D/3D, dan pelaporan terintegrasi untuk engineer struktur Indonesia.

---

## Status Saat Ini (v0.1 MVP)

Fitur aktif:
- Auth (register, login, JWT)
- Manajemen proyek
- Desain lentur balok beton (SNI 2847:2019)
- Desain lentur balok baja WF (SNI 1729:2020)
- Database 34 profil baja
- Laporan PDF
- 3D viewer placeholder (portal frame statis)

Arsitektur saat ini:
- API layer → Service layer → Calculation Engine (pure Python)
- DB layer terpisah (SQLModel + PostgreSQL)
- Unit test untuk semua modul kalkulasi

---

## Phase 1 — Elemen Tambahan (v0.2)

**Target:** Lengkapi modul elemen struktural individual

| Modul | Standar | Status |
|-------|---------|--------|
| Kolom beton (tekan + lentur) | SNI 2847:2019 | Belum |
| Pelat satu arah | SNI 2847:2019 | Belum |
| Sambungan baut baja | SNI 1729:2020 | Belum |
| Fondasi telapak | SNI 2847:2019 | Belum |
| Tangga beton | SNI 2847:2019 | Belum |
| Cek lendutan balok | SNI 2847:2019 / 1729:2020 | Belum |
| Cek geser balok beton | SNI 2847:2019 | Belum |

**Perubahan arsitektur:** Tidak ada — hanya tambah modul di `app/calculation/`

---

## Phase 2 — Analisis 2D Frame (v0.3)

**Target:** Analisis frame 2D menggunakan metode kekakuan (stiffness method)

### Konsep Teknis

```
Nodes (titik kumpul) + Members (batang) + Loads (beban) → K·δ = F → δ, F_member
```

Algoritma:
1. Bangun matriks kekakuan lokal tiap elemen → assembly ke K global
2. Terapkan boundary conditions
3. Solve K·δ = F untuk perpindahan nodal
4. Hitung gaya dalam elemen: M, V, N

Library yang dipertimbangkan:
- `numpy` / `scipy.linalg` — solver matriks
- Atau implementasi custom agar bisa di-audit secara engineering

### Modul Baru yang Diperlukan

```
app/calculation/analysis/
├── frame2d/
│   ├── node.py          # dataclass Node(x, y, dof_x, dof_y, dof_rot)
│   ├── member.py        # dataclass Member(node_i, node_j, E, A, I)
│   ├── stiffness.py     # K_local, K_global assembly
│   ├── solver.py        # K·δ = F
│   └── post_process.py  # M, V, N diagram dari displacement
└── types.py             # Frame2DInput, Frame2DResult
```

### Perubahan Frontend

- Halaman input frame 2D (canvas interaktif untuk menggambar nodes/members)
- Tampilkan diagram M, V, N dengan SVG atau Chart.js
- Upgrade 3D viewer: tampilkan deformed shape

---

## Phase 3 — Analisis 3D Frame (v0.4)

**Target:** Analisis frame 3D ruang (space frame) dengan 6 DOF per node

### Konsep Teknis

Perluasan dari Phase 2:
- 6 DOF per node: Tx, Ty, Tz, Rx, Ry, Rz
- Matriks kekakuan elemen 12×12
- Transformasi koordinat lokal → global dengan matriks rotasi 3D

### Modul Baru

```
app/calculation/analysis/
└── frame3d/
    ├── node3d.py        # Node dengan 6 DOF
    ├── member3d.py      # Elemen 3D dengan A, Ix, Iy, Iz, J
    ├── stiffness3d.py   # K_local 12×12, transformasi 3D
    └── solver3d.py      # Assembly + solve
```

### Integrasi 3D Viewer

- Three.js / React Three Fiber untuk render model struktural interaktif
- Color map untuk gaya dalam (M, V, N) pada elemen
- Mode: wireframe, solid, deformed shape

---

## Phase 4 — Desain Tahan Gempa (v0.5)

**Target:** Analisis beban gempa sesuai SNI 1726:2019 dan SNI 7860:2020

| Fitur | Standar |
|-------|---------|
| Peta gempa (Ss, S1 dari koordinat) | SNI 1726:2019 |
| Response spectrum design | SNI 1726:2019 Pasal 6 |
| Base shear (Equivalent Static) | SNI 1726:2019 Pasal 7.8 |
| Distribusi gaya lateral | SNI 1726:2019 |
| Batas drift antar lantai | SNI 1726:2019 Tabel 12.12-1 |
| SCBF / SMRF (sistem rangka) | SNI 7860:2020 |

### Integrasi Data Gempa

- API publik BMKG atau PUPR untuk spektra desain berdasarkan koordinat lokasi
- Cache hasil respons spectrum per koordinat

---

## Phase 5 — Platform Kolaborasi (v1.0)

**Target:** Multi-user, real-time collaboration, review & approval workflow

| Fitur | Keterangan |
|-------|------------|
| Multi-user per proyek | Role: Owner, Engineer, Reviewer |
| Revisi perhitungan | Versioning tiap CalculationRecord |
| Approval workflow | Status: Draft → In Review → Approved |
| Comment thread | Komentar per perhitungan |
| Audit trail lengkap | Siapa mengubah apa dan kapan |
| Export IFC | Integrasi BIM (Building Information Modeling) |

---

## Keputusan Arsitektur untuk Roadmap

### Calculation Engine

Tetap pure Python tanpa dependensi web. Setiap fase menambah modul di `app/calculation/` yang dapat dipanggil langsung dari unit test.

### Frontend

Upgrade bertahap:
- v0.1–0.2: Form-based input/output
- v0.3: Canvas 2D interaktif (react-konva atau SVG custom)
- v0.4: 3D viewer interaktif (React Three Fiber)
- v1.0: Real-time dengan WebSocket

### Database

- v0.1–0.3: PostgreSQL cukup
- v0.4+: Pertimbangkan time-series DB untuk riwayat beban dinamis
- v1.0: Redis untuk session/cache, event sourcing untuk audit trail

### API

- v0.1–0.3: REST API (FastAPI)
- v0.4+: GraphQL untuk query data frame yang kompleks
- v1.0: WebSocket untuk real-time collaboration

---

## Metrik Kualitas Target

| Metrik | Target |
|--------|--------|
| Test coverage (calculation engine) | ≥ 90% |
| Semua formula punya unit test | Ya |
| Semua field punya satuan eksplisit | Ya |
| Tidak ada teks SNI disalin | Ya (wajib) |
| Waktu respons API (P95) | ≤ 500ms |
| Laporan PDF tergenerate | ≤ 3 detik |
