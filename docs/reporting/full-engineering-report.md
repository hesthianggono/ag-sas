# Full Engineering Report PDF — Dokumentasi Teknis

## Ringkasan

Modul `app/reporting/full_report/` menghasilkan **laporan rekayasa struktur lengkap**
format konsultan Indonesia (10 bab + lampiran) dalam satu file PDF A4 berkualitas tinggi.

---

## Arsitektur

```
backend/app/reporting/full_report/
├── __init__.py            eksporkan build_full_report, FullReportConfig
├── numbering.py           auto-numbering (bab, tabel, gambar, persamaan, lampiran)
├── template.py            warna, font, styles, header/footer, watermark
├── cover.py               halaman cover profesional
├── toc.py                 daftar isi, daftar tabel, daftar gambar
├── section_builder.py     base helpers (h1/h2/h3, numbered_table, kv_table, status)
├── figure_embedder.py     embed PNG matplotlib ke PDF bernomor
├── report_snapshot.py     FullReportConfig, FullReportData, EngineerInfo
├── report_builder.py      orkestrasi semua section → PDF bytes
├── pdf_exporter.py        entry point (shortcut params)
└── sections/
    ├── __init__.py
    ├── s01_introduction.py    Bab 1 — Pendahuluan
    ├── s02_project_data.py    Bab 2 — Data Proyek
    ├── s03_design_basis.py    Bab 3 — Dasar Perencanaan
    ├── s04_materials.py       Bab 4 — Spesifikasi Material
    ├── s05_loads.py           Bab 5 — Pembebanan
    ├── s06_structural_model.py Bab 6 — Model Struktur
    ├── s07_analysis.py        Bab 7 — Analisis Struktur
    ├── s08_design.py          Bab 8 — Perencanaan Penampang
    ├── s09_serviceability.py  Bab 9 — Kemampuan Layan
    ├── s10_summary.py         Bab 10 — Ringkasan & Kesimpulan
    └── s11_appendix.py        Bab 11 — Gambar Teknik + Lampiran A

backend/app/
├── models/full_report.py        SQLModel FullReportRecord
├── schemas/full_report.py       Pydantic schemas
├── services/full_report_service.py  CRUD + PDF generation
└── api/v1/endpoints/full_reports.py REST API
```

---

## Struktur Laporan

| Bagian          | Konten                                                   |
|-----------------|----------------------------------------------------------|
| Cover           | Judul, proyek, nomor dokumen, tanggal, engineer          |
| Daftar Isi      | TOC auto-generate dari NumberingContext.toc              |
| Daftar Tabel    | Auto-generate dari NumberingContext.lot                  |
| Daftar Gambar   | Auto-generate dari NumberingContext.lof                  |
| Bab 1           | Pendahuluan, latar belakang, ruang lingkup              |
| Bab 2           | Data proyek & tim perencana (dengan SKK)                 |
| Bab 3           | Dasar perencanaan, SNI referensi, asumsi                 |
| Bab 4           | Spesifikasi material (beton/baja tulangan/baja profil)   |
| Bab 5           | Pembebanan (DL, SDL, LL) + kombinasi LRFD               |
| Bab 6           | Model struktur, geometri penampang                       |
| Bab 7           | Analisis struktur (reaksi, V(x), M(x)) + persamaan      |
| Bab 8           | Perencanaan penampang (lentur, geser, tulangan)          |
| Bab 9           | Kemampuan layan (lendutan, retak)                        |
| Bab 10          | Ringkasan tabel kontrol + kesimpulan                     |
| Bab 11          | Gambar teknik (dari FigureSnapshot atau on-the-fly)      |
| Lampiran A      | Tabel referensi material (Ec, fr vs fc)                  |

---

## Penggunaan Cepat

```python
from app.reporting.full_report.pdf_exporter import export_full_report_pdf

pdf_bytes = export_full_report_pdf(
    calc_type="concrete_beam",
    input_data=calc.input_data,
    output_data=calc.output_data,
    calc_title="Balok B-1",
    project_name="Gedung Kantor A",
    status="DRAFT",
    engineers=[{"name": "Ir. Budi", "position": "Ahli Struktur", "skk": "1234"}],
    include_figures=True,
    figure_snapshots=figure_snaps,   # list[FigureSnapshot], opsional
)
```

---

## FullReportConfig

```python
@dataclass
class FullReportConfig:
    doc_number:       str   = "AG-SAS/RPT/001"
    revision:         str   = "A"
    status:           str   = "DRAFT"       # "DRAFT" | "FINAL"
    report_title:     str   = "Laporan Perhitungan Struktur"
    project_name:     str   = ""
    project_location: str   = ""
    owner:            str   = ""
    company_name:     str   = "AG Structural Analysis Suite"
    engineers:        list[EngineerInfo] = []
    show_watermark:   bool  = True
    deform_scale:     float = 50.0
    include_figures:  bool  = True
    show_appendix:    bool  = True
    sni_concrete:     str   = "SNI 2847:2019"
    sni_load:         str   = "SNI 1727:2020"
    sni_steel:        str   = "SNI 1729:2020"
    sni_quake:        str   = "SNI 1726:2019"
```

---

## API Endpoints

```
POST   /api/v1/full-reports               Buat record laporan
GET    /api/v1/full-reports               Daftar laporan (filter: ?calc_id=X)
GET    /api/v1/full-reports/{id}          Detail laporan
PATCH  /api/v1/full-reports/{id}          Update metadata
DELETE /api/v1/full-reports/{id}          Hapus
GET    /api/v1/full-reports/{id}/pdf      Download PDF (StreamingResponse)
```

### POST /full-reports

```json
{
  "calc_id":          42,
  "report_title":     "Laporan Perhitungan Balok B-1",
  "project_name":     "Gedung Kantor",
  "project_location": "Jakarta",
  "status":           "DRAFT",
  "engineers": [
    {"name": "Ir. Budi", "position": "Ahli Struktur", "skk": "1234"}
  ],
  "include_figures": true,
  "show_watermark":  true
}
```

---

## Database Schema

```sql
CREATE TABLE full_report_records (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    calc_id          INTEGER NOT NULL REFERENCES calculation_records(id),
    doc_number       VARCHAR(80)  NOT NULL DEFAULT 'AG-SAS/RPT/001',
    revision         VARCHAR(10)  NOT NULL DEFAULT 'A',
    status           VARCHAR(20)  NOT NULL DEFAULT 'DRAFT',
    report_title     VARCHAR(255) NOT NULL,
    report_subtitle  VARCHAR(255),
    project_name     VARCHAR(255),
    project_location VARCHAR(255),
    owner            VARCHAR(255),
    company_name     VARCHAR(255) NOT NULL,
    config_json      TEXT,          -- engineers list (JSON)
    include_figures  BOOLEAN DEFAULT TRUE,
    show_watermark   BOOLEAN DEFAULT TRUE,
    show_appendix    BOOLEAN DEFAULT TRUE,
    deform_scale     FLOAT   DEFAULT 50.0,
    created_at       TIMESTAMP NOT NULL,
    generated_at     TIMESTAMP
);
```

---

## NumberingContext

Sistem penomoran otomatis dikelola oleh `NumberingContext`:

```python
ctx = NumberingContext()
ctx.chapter(1, "Pendahuluan")         → "1  Pendahuluan"
ctx.subchapter("Latar Belakang")      → "1.1  Latar Belakang"
ctx.subsubchapter("Detail")           → "1.1.1  Detail"
ctx.table("Data Beban")               → "Tabel 1.1  Data Beban"
ctx.figure("Diagram Momen")           → "Gambar 1.1  Diagram Momen"
ctx.equation()                        → "(1.1)"
ctx.appendix("Lampiran Material")     → "Lampiran A  Lampiran Material"
ctx.appendix_table("Tabel Beton")     → "Tabel A.1  Tabel Beton"
```

Setelah semua section selesai:
- `ctx.toc` → list[TocEntry] untuk Daftar Isi
- `ctx.lot` → list[TableEntry] untuk Daftar Tabel
- `ctx.lof` → list[FigureEntry] untuk Daftar Gambar

---

## Unit Tests

```
backend/tests/reporting/test_full_report.py  — 16 tests, semua passing
```

Coverage:
- `TestNumberingContext` (8 tests)
- `TestConcreteReport` (3 tests)
- `TestSteelReport` (1 test)
- `TestReportConfig` (3 tests)
- `TestEmptyData` (1 test)
