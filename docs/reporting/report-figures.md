# Report Figures — Dokumentasi Teknis

## Ringkasan

Modul `app/reporting/figures/` menghasilkan gambar teknik (engineering figures)
secara otomatis dari data perhitungan struktur menggunakan **Matplotlib**.
Gambar disimpan sebagai **snapshot immutable** per laporan di tabel
`figure_snapshots`, dan di-embed ke **laporan PDF** (Seksi 12).

---

## Arsitektur

```
backend/app/reporting/figures/
├── __init__.py              eksporkan FigureSpec, FigureCaptionBuilder, build_figures_for_calc
├── base.py                  FigureSpec, FigureCaptionBuilder, FIG_STYLE, helpers PNG/SVG
├── model_view.py            Model struktur (undeformed beam + supports + cross-section)
├── load_diagram.py          Diagram pembebanan UDL (panah + nilai wu)
├── internal_force_diagram.py Diagram V(x), M(x), N(x)
├── reaction_diagram.py      Diagram reaksi tumpuan RA, RB
├── deformed_shape.py        Bentuk deformasi (kurva elastika skala visual)
├── utilization_map.py       Gauge utilisasi Mu/φMn + tabel ringkasan
└── figure_builder.py        Orkestrasi: build_figures_for_calc() → list[FigureSpec]

backend/app/
├── models/figure_snapshot.py   SQLModel FigureSnapshot (tabel DB)
├── schemas/figure.py           Pydantic schemas request/response
├── services/figure_service.py  CRUD + generate logic
└── api/v1/endpoints/figures.py REST API endpoints
```

---

## Gambar yang Dihasilkan

| Nomor | `figure_key`        | Keterangan                                    |
|-------|---------------------|-----------------------------------------------|
| 12.1  | `model_view`        | Model struktur balok sederhana                |
| 12.2  | `load_diagram`      | Diagram pembebanan UDL terfaktor              |
| 12.3  | `reaction_diagram`  | Diagram reaksi tumpuan RA dan RB              |
| 12.4  | `shear_diagram`     | Diagram gaya geser V(x)                       |
| 12.5  | `moment_diagram`    | Diagram momen lentur M(x) (sagging ke bawah)  |
| 12.6  | `deformed_shape`    | Bentuk deformasi (faktor skala 50× default)   |
| 12.7  | `utilization_map`   | Peta rasio utilisasi Mu/φMn                   |

---

## FigureSpec

```python
@dataclass
class FigureSpec:
    figure_key: str              # identifier unik gambar
    title: str                   # "Diagram Momen Lentur"
    caption: str                 # "Gambar 12.5  Diagram momen lentur M(x) — Kombinasi 1.2D + 1.6L"
    figure_number: str           # "12.5"
    section: str                 # "12"
    load_case: str | None        # "DL+LL"
    load_combination: str | None # "1.2D + 1.6L"
    scale_factor: float | None   # deformed shape: 50.0
    unit: str                    # "kN·m"
    timestamp: datetime
    source_result_id: int | None
    source: str                  # "backend" | "frontend"
    png_bytes: bytes             # PNG image bytes (DPI=150)
    svg_data: str | None
    json_data: dict | None       # data mentah diagram
    order_index: int
```

---

## FigureCaptionBuilder

```python
cb = FigureCaptionBuilder(section="12")

# Returns (figure_number, caption)
num, cap = cb.next("model_view", "Model Struktur")
# → "12.1", "Gambar 12.1  Model Struktur"

num, cap = cb.next("moment_diagram", "Diagram Momen Lentur",
                   suffix="Kombinasi 1.2D + 1.6L")
# → "12.2", "Gambar 12.2  Diagram Momen Lentur — Kombinasi 1.2D + 1.6L"
```

---

## build_figures_for_calc()

```python
from app.reporting.figures import build_figures_for_calc

specs: list[FigureSpec] = build_figures_for_calc(
    calc_type="concrete_beam",     # atau "steel_beam"
    input_data=calc.input_data,
    output_data=calc.output_data,
    calc_title="Balok B1",
    source_result_id=calc.id,
    section="12",                  # nomor seksi laporan
    deform_scale=50.0,             # faktor skala deformasi visual
)
```

---

## API Endpoints

```
POST  /api/v1/figures/generate          Generate semua gambar backend
POST  /api/v1/figures/upload            Upload gambar dari frontend
GET   /api/v1/figures/report/{id}       Daftar gambar satu laporan
GET   /api/v1/figures/{id}              Detail + PNG base64
GET   /api/v1/figures/{id}/png          Stream PNG (image/png)
PATCH /api/v1/figures/{id}              Update caption / visibility / urutan
DELETE/api/v1/figures/{id}              Hapus gambar
```

### POST /figures/generate

```json
{
  "report_id": 42,
  "section": "12",
  "deform_scale": 50.0,
  "overwrite": true
}
```

Response: `list[FigureSnapshotResponse]`

### FigureSnapshotResponse

```json
{
  "id": 1,
  "report_id": 42,
  "calc_id": 7,
  "figure_key": "moment_diagram",
  "figure_number": "12.5",
  "order_index": 5,
  "title": "Diagram Momen Lentur",
  "caption": "Gambar 12.5  Diagram Momen Lentur M(x) — Kombinasi 1.2D + 1.6L",
  "load_case": "DL+LL",
  "load_combination": "1.2D + 1.6L",
  "scale_factor": null,
  "unit": "kN·m",
  "source": "backend",
  "is_visible": true,
  "generated_at": "2026-05-23T09:00:00",
  "json_data": {"M_max": 99.0, "wu": 22.0, "L": 6.0},
  "png_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

---

## Database Schema

```sql
CREATE TABLE figure_snapshots (
    id              SERIAL PRIMARY KEY,
    report_id       INTEGER NOT NULL REFERENCES report_records(id),
    user_id         INTEGER NOT NULL REFERENCES users(id),
    calc_id         INTEGER NOT NULL REFERENCES calculation_records(id),
    figure_key      VARCHAR(80) NOT NULL,
    figure_number   VARCHAR(20) NOT NULL,
    order_index     INTEGER NOT NULL DEFAULT 0,
    title           VARCHAR(255) NOT NULL,
    caption         VARCHAR(512) NOT NULL,
    load_case       VARCHAR(100),
    load_combination VARCHAR(100),
    scale_factor    FLOAT,
    unit            VARCHAR(50) NOT NULL DEFAULT '—',
    png_data        BYTEA NOT NULL,
    svg_data        TEXT,
    json_data       JSON,
    source          VARCHAR(20) NOT NULL DEFAULT 'backend',
    is_visible      BOOLEAN NOT NULL DEFAULT TRUE,
    generated_at    TIMESTAMP NOT NULL
);
```

---

## Snapshot Immutability

Gambar disimpan **sekali saat laporan dibuat**. Jika data kalkulasi berubah
setelah itu, gambar lama tetap tidak berubah karena:

1. Setiap `FigureSnapshot` menyimpan data di `json_data` (snapshot data mentah)
2. PNG disimpan sebagai bytes (`png_data`) di DB, bukan referensi ke file
3. `report_id` FK memastikan gambar terikat pada satu versi laporan
4. Untuk memperbarui, user harus eksplisit memilih **Generate Ulang** (`overwrite=true`)

---

## Gaya Visual (FIG_STYLE)

| Konstanta         | Warna       | Penggunaan                         |
|-------------------|-------------|------------------------------------|
| `NAVY`            | `#1e3a5f`   | Elemen utama, teks, border         |
| `BLUE`            | `#2563eb`   | Balok beton, diagram positif       |
| `STEEL_GRAY`      | `#475569`   | Balok baja, elemen sekunder        |
| `LOAD_COLOR`      | `#ea580c`   | Panah beban                        |
| `DEFORM_COLOR`    | `#7c3aed`   | Kurva deformasi                    |
| `GREEN`           | `#16a34a`   | Reaksi, status aman                |
| `RED`             | `#dc2626`   | Status tidak aman, zona bahaya     |
| `POS_ZONE`        | `#dbeafe`   | Fill zona positif (biru muda)      |
| `NEG_ZONE`        | `#fee2e2`   | Fill zona negatif (merah muda)     |

Semua gambar menggunakan:
- DPI = 150 (kualitas laporan PDF)
- Backend non-interactive: `matplotlib.use("Agg")`
- Tidak ada plt.show() — sepenuhnya headless

---

## Menambah Jenis Gambar Baru

1. Buat fungsi `generate_xxx()` di file baru di `figures/`
2. Fungsi harus return `bytes` (PNG)
3. Tambahkan ke `figure_builder.py` dalam `build_figures_for_calc()`
4. Tambahkan test di `tests/reporting/test_figures.py`
5. Update dokumentasi ini

---

## Unit Tests

```
backend/tests/reporting/test_figures.py   — 45 tests, semua passing
```

Coverage:
- `TestModelView` (4 tests)
- `TestLoadDiagram` (3 tests)
- `TestShearDiagram` (3 tests)
- `TestMomentDiagram` (3 tests)
- `TestDeformedShape` (3 tests)
- `TestReactionDiagram` (3 tests)
- `TestUtilizationMap` (3 tests)
- `TestFigureCaptionBuilder` (5 tests)
- `TestBuildFiguresForCalc` (10 tests)
- `TestPNGValidity` (3 tests)
- `TestFigureSpec` (2 tests)
- `TestSnapshotImmutability` (3 tests)
