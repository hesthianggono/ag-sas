# Engineering Kernel — Arsitektur AG-SAS

> **Disclaimer:** AG-SAS adalah engineering calculation assistant.
> Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.

---

## Tujuan

Engineering Kernel adalah fondasi teknis AG-SAS — lapisan murni Python
yang tidak bergantung pada web framework, ORM, atau database. Kernel
mendefinisikan:

- Satuan internal solver dan konversi satuan
- Konvensi tanda (sign convention) yang resmi dan terdokumentasi
- Struktur data model struktural (node, elemen, material, profil, beban)
- Sistem traceability untuk setiap run analisis

Semua modul di atas harus dapat diimpor dan digunakan di luar konteks
FastAPI — misalnya dalam script Python biasa, Jupyter Notebook, atau
test runner tanpa server.

---

## Struktur Folder

```
backend/app/engineering_kernel/
├── __init__.py                  # KERNEL_VERSION = "0.1.0"
│
├── units/
│   ├── __init__.py
│   ├── enums.py                 # LengthUnit, ForceUnit, MomentUnit, ...
│   ├── converters.py            # fungsi konversi (mm_to_m, mpa_to_kn_m2, ...)
│   └── quantity.py              # Quantity (frozen dataclass: value + unit)
│
├── conventions/
│   ├── __init__.py
│   ├── sign_convention.py       # konvensi tanda resmi AG-SAS
│   └── coordinate_system.py    # sistem koordinat global 2D/3D
│
├── models/
│   ├── __init__.py
│   ├── geometry.py              # Node, Element, Support
│   ├── material.py              # Material, preset BJ37/BJ41/fc21/fc25/fc30
│   ├── section.py               # SectionProperties, SectionType
│   ├── loads.py                 # NodalLoad, UniformMemberLoad, LoadCase, ...
│   ├── combination.py           # LoadCombination, LoadFactor, template SNI
│   └── results.py               # AnalysisResult, DesignCheckResult, ...
│
└── traceability/
    ├── __init__.py
    ├── trace.py                 # SolverVersion, AnalysisTrace, build_trace()
```

---

## Prinsip Desain

### 1. Zero Web Dependency

Kernel tidak mengimpor FastAPI, SQLModel, atau library database apapun.
Semua kelas adalah Python `@dataclass` atau `@dataclass(frozen=True)`.

### 2. Satuan Internal Konsisten

| Kuantitas        | Satuan Internal |
|------------------|-----------------|
| Panjang          | m               |
| Gaya             | kN              |
| Momen            | kN·m            |
| Tegangan / Modulus | kN/m²         |
| Massa            | kg              |
| Luas penampang   | m²              |
| Momen inersia    | m⁴              |
| Modulus penampang | m³             |

Konversi dilakukan **di batas sistem** — saat menerima input pengguna
(biasanya mm, MPa) atau saat menampilkan output (mm, cm, MPa).
Solver internal tidak pernah menerima satuan campuran.

### 3. Sign Convention Resmi

Referensi: **McGuire, Gallagher, Ziemian — "Matrix Structural Analysis"
2nd Edition, §3.2**

- Gaya aksial N+ = tarik (tension)
- Momen Mz+ = sagging (serat bawah tarik)
- Geser V+ = naik pada muka kiri elemen
- Perpindahan positif = searah sumbu global positif
- Reaksi positif = searah dengan gaya eksternal positif

Lihat: [`docs/calculation-notes/sign-convention.md`](../calculation-notes/sign-convention.md)

### 4. Traceability Wajib

Setiap hasil analisis yang disimpan ke database **harus** disertai
`AnalysisTrace`. Trace adalah `frozen dataclass` — immutable setelah
dibuat. Isi minimal:

| Field              | Keterangan                                    |
|--------------------|-----------------------------------------------|
| `trace_id`         | UUID unik, dibuat sekali                      |
| `project_id`       | ID proyek dari database                       |
| `user_id`          | ID pengguna yang menjalankan analisis         |
| `timestamp_utc`    | Waktu dalam UTC (ISO 8601)                    |
| `solver_version`   | kernel_version, code_check_version, numpy, scipy |
| `input_snapshot`   | JSON string seluruh input model              |
| `output_snapshot`  | JSON string seluruh hasil analisis           |
| `assumptions`      | Daftar asumsi analisis                        |
| `warnings`         | Peringatan dari solver                        |

Dengan trace ini, setiap hasil dapat direproduksi ulang atau diaudit.

---

## Cara Penggunaan

### Import Dasar

```python
from app.engineering_kernel.models.geometry import Node, Element, Support
from app.engineering_kernel.models.material import STEEL_BJ37
from app.engineering_kernel.models.section import SectionProperties, SectionType
from app.engineering_kernel.models.loads import LoadCase, LoadCaseType, NodalLoad
from app.engineering_kernel.traceability import build_trace
from app.engineering_kernel.units.converters import mm_to_m, mpa_to_kn_m2
```

### Contoh: Membuat Node

```python
node = Node(id="N1", x_m=0.0, y_m=0.0)
errors = node.validate()
assert errors == []
```

### Contoh: Material Preset

```python
from app.engineering_kernel.models.material import STEEL_BJ37
print(f"fy = {STEEL_BJ37.fy_mpa} MPa")  # 240.0 MPa
print(f"E  = {STEEL_BJ37.E_gpa} GPa")   # 200.0 GPa
```

### Contoh: SectionProperties dari mm

```python
section = SectionProperties.from_mm_units(
    id="WF400",
    name="WF 400×200×8×13",
    type=SectionType.WF,
    A_mm2=8412.0,
    Ix_mm4=237_000_000.0,
    Iy_mm4=17_400_000.0,
    J_mm4=500_000.0,
    Zx_mm3=1_190_000.0,
    Zy_mm3=174_000.0,
    Sx_mm3=1_190_000.0,
    Sy_mm3=174_000.0,
)
print(f"A  = {section.A_cm2:.2f} cm²")  # 84.12 cm²
print(f"Ix = {section.Ix_cm4:.0f} cm⁴")  # 23700 cm⁴
```

### Contoh: Traceability

```python
trace = build_trace(
    project_id=1,
    user_id=42,
    input_data={"nodes": [...], "elements": [...]},
    output_data={"displacements": [...], "reactions": [...]},
    load_combination_ids=[1, 2, 3],
)
# Simpan trace.to_json() ke database bersama hasil analisis
```

---

## Menjalankan Unit Test

```bash
cd backend
pytest tests/engineering_kernel/ -v
```

Output yang diharapkan:

```
tests/engineering_kernel/test_units.py          PASSED  (≥ 60 tests)
tests/engineering_kernel/test_models.py         PASSED  (≥ 50 tests)
tests/engineering_kernel/test_traceability.py   PASSED  (≥ 30 tests)
```

---

## Versi

| Komponen           | Versi  |
|--------------------|--------|
| kernel_version     | 0.1.0  |
| code_check_version | 0.1.0  |

Versi dinaikkan setiap kali ada perubahan yang mempengaruhi hasil
perhitungan — perubahan formula, konvensi tanda, atau perubahan
struktur data yang mempengaruhi snapshot.
