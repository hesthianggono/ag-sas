# Verification & Validation Framework AG-SAS

> **Disclaimer:** AG-SAS adalah engineering calculation assistant.
> Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.
> Framework ini memverifikasi konsistensi formula internal — bukan sertifikasi software.

---

## Tujuan

Memastikan bahwa setiap solver yang dikembangkan dalam AG-SAS menghasilkan
hasil yang konsisten dengan:

1. Solusi analitik eksak (matematika)
2. Contoh manual dari buku teks standar
3. Hasil uji silang dengan metode independen

**SAP2000/ETABS digunakan sebagai pembanding tambahan, BUKAN sumber
kebenaran tunggal.** Sumber kebenaran primer adalah solusi analitik
yang dapat diturunkan secara matematis.

---

## Hierarki Level V&V

| Level | Kode | Deskripsi | Contoh |
|-------|------|-----------|--------|
| 1 | `L1_analytical` | Solusi analitik eksak | δ = PL³/3EI |
| 2 | `L2_textbook` | Contoh manual dari buku teks | Hibbeler, Kassimali |
| 3 | `L3_comparison` | Uji silang dengan software lain | SAP2000, ETABS (tambahan) |
| 4 | `L4_benchmark` | Benchmark komunitas resmi | NAFEMS, AISC |

Semakin rendah angka level, semakin kuat dasar verifikasinya.
Mulailah selalu dari L1 sebelum naik ke L2+.

---

## Toleransi Numerik

| Jenis Analisis | Toleransi Relatif | Catatan |
|----------------|-------------------|---------|
| Reaksi statis (statics check) | 1 × 10⁻⁶ | Eksak dari keseimbangan |
| Defleksi balok sederhana | 0.1% | Euler-Bernoulli |
| Gaya batang truss | 0.1% | Method of joints |
| Portal frame dengan DSM | 0.1% | Perlu solver FEM |
| Analisis dinamik | 1.0% | Eigenvalue solver |
| Analisis nonlinear | 2.0% | Iterasi konvergensi |

Toleransi ini adalah **minimum** — hasil yang lebih akurat selalu lebih baik.

---

## Struktur Folder

```
backend/app/verification/
├── __init__.py              # Public API
├── models.py                # BenchmarkCase, BenchmarkResult, QuantityCheck, ...
├── compare.py               # compare_quantity(), compare_result()
├── benchmarks/
│   ├── __init__.py
│   ├── simply_supported_beam.py  # SSB-UDL-01
│   ├── cantilever_beam.py        # CANT-PL-01
│   ├── portal_2d.py              # PORTAL-2D-01
│   ├── truss_2d.py               # TRUSS-2D-01
│   └── registry.py               # ALL_BENCHMARKS, get_benchmark(), list_benchmarks()
├── manual_cases/            # Contoh manual dari standar desain (SNI)
├── regression/
│   └── runner.py            # run_benchmark(), run_all()
└── reports/
    └── formatter.py         # format_session_report(), result_to_api_dict()
```

---

## Struktur Data

### BenchmarkCase

```python
@dataclass
class BenchmarkCase:
    benchmark_id: str          # slug unik, e.g. "ssb_udl_01"
    title: str
    description: str
    structure_type: StructureType
    level: VerificationLevel
    source_reference: str      # referensi buku / pasal
    input_data: dict           # semua parameter input
    expected_values: list[ExpectedValue]
    tags: list[str]
    active: bool
```

### ExpectedValue

```python
@dataclass
class ExpectedValue:
    quantity: str         # e.g. "midspan_deflection_mm"
    value: float          # nilai yang diharapkan
    unit: str             # satuan display
    tolerance_rel: float  # 0.001 = 0.1%
    tolerance_abs: float  # fallback untuk nilai mendekati nol
    notes: str
```

### BenchmarkResult

```python
@dataclass
class BenchmarkResult:
    result_id: str         # UUID
    benchmark_id: str
    title: str
    timestamp_utc: str
    checks: list[QuantityCheck]
    overall_status: CheckStatus    # PASS | FAIL | SKIP | ERROR
    solver_name: str
    solver_version: str
```

### CheckStatus

| Nilai | Kondisi |
|-------|---------|
| `PASS` | `rel_error ≤ tolerance_rel` ATAU `abs_error ≤ tolerance_abs` |
| `FAIL` | Error melebihi toleransi |
| `SKIP` | Solver belum tersedia (actual = None) |
| `ERROR` | Exception saat menjalankan solver |

---

## Cara Penggunaan

### Jalankan semua benchmark

```python
from app.verification import run_all, format_session_report

session = run_all()
print(format_session_report(session))
```

### Jalankan satu benchmark

```python
from app.verification import run_benchmark

result = run_benchmark("ssb_udl_01")
print(result.overall_status)   # "PASS"
```

### Tambah benchmark baru

1. Buat file di `benchmarks/my_new_case.py`:

```python
from app.verification.models import BenchmarkCase, ExpectedValue, StructureType, VerificationLevel

BENCHMARK = BenchmarkCase(
    benchmark_id="my_case_01",
    title="...",
    structure_type=StructureType.BEAM_2D,
    level=VerificationLevel.L1_ANALYTICAL,
    source_reference="...",
    input_data={...},
    expected_values=[
        ExpectedValue(quantity="deflection_mm", value=12.34, unit="mm", tolerance_rel=0.001),
    ],
)
```

2. Daftarkan di `benchmarks/registry.py`:

```python
from app.verification.benchmarks.my_new_case import BENCHMARK as MY_CASE_01

ALL_BENCHMARKS = [..., MY_CASE_01]
```

3. Tambahkan solver di `regression/runner.py`:

```python
SOLVER_REGISTRY["my_case_01"] = lambda input_data: my_solver(input_data)
```

---

## API Endpoints

| Method | URL | Deskripsi |
|--------|-----|-----------|
| `GET` | `/api/v1/verification/benchmarks` | Daftar semua benchmark |
| `GET` | `/api/v1/verification/benchmarks/{id}` | Detail satu benchmark |
| `POST` | `/api/v1/verification/run` | Jalankan verifikasi |
| `GET` | `/api/v1/verification/results/{id}` | Ambil hasil berdasarkan ID |

### POST /verification/run

```json
{
  "benchmark_id": "ssb_udl_01",   // null = jalankan semua
  "active_only": true
}
```

---

## Unit Tests

```bash
cd backend
pytest tests/verification/test_benchmarks.py -v
```

Test yang ada:
- Verifikasi formula analitik SSB, Cantilever, Portal, Truss
- Test fungsi compare_quantity() dan compare_result()
- Test registry (list, get, filter)
- Test regression runner (run satu, run semua)
- Test formatter (text report, API dict)

---

## Regression CI

Benchmark suite harus dijalankan otomatis di CI pada setiap commit
yang mempengaruhi:
- `backend/app/verification/`
- `backend/app/engineering_kernel/`
- Solver FEM (ketika tersedia)

Jika ada benchmark yang berubah status dari PASS ke FAIL,
pipeline CI harus gagal dan tim harus memeriksa penyebabnya.

---

## Catatan Penting

1. **Jangan ubah expected values tanpa dokumentasi alasan yang jelas.**
   Setiap perubahan expected value harus disertai referensi yang menjelaskan
   mengapa nilai lama salah.

2. **SKIP bukan kegagalan.** SKIP berarti solver belum diimplementasi,
   bukan ada kesalahan. Ganti SKIP ke PASS/FAIL saat solver tersedia.

3. **SAP2000/ETABS adalah pembanding, bukan hakim.**
   Jika hasil AG-SAS berbeda dengan SAP2000, periksa dulu apakah
   input dan asumsi kedua software benar-benar identik sebelum
   menyimpulkan ada bug.
