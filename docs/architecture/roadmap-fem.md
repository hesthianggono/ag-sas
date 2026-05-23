# AG Structural Analysis Suite — Technical Roadmap: From Calculator to FEM Software

**Versi dokumen:** 2.0  
**Tanggal:** 2026-05-22  
**Status:** Living document — diperbarui setiap milestone selesai

---

## Disclaimer Penggunaan

> **AG-SAS adalah engineering calculation assistant — bukan pengganti engineer struktur.**
>
> Seluruh hasil perhitungan, analisis, dan pemeriksaan desain yang dihasilkan AG-SAS **wajib diperiksa, dievaluasi, dan disetujui oleh engineer struktur berwenang** sebelum digunakan dalam dokumen perencanaan, gambar konstruksi, atau dokumen resmi lainnya. AG-SAS dirancang sebagai alat bantu perhitungan pendamping dan pembelajaran — bukan sebagai otoritas teknis independen.
>
> Penggunaan hasil AG-SAS tanpa verifikasi engineer merupakan tanggung jawab penuh pengguna.

---

## Prinsip Arsitektur

Setiap tahap dibangun di atas tahap sebelumnya. Tidak ada refactor besar di tengah jalan — setiap penambahan fitur adalah **ekstensi**, bukan penggantian.

```
Tahap 0     : Engineering kernel — unit, sign convention, tipe dasar
Tahap 1     : 2D Frame Analysis (Direct Stiffness Method)
Tahap 2     : Verification & Validation Framework untuk 2D solver
Tahap 3     : Matrix Stiffness Infrastructure (sparse, validator)
Tahap 4     : Member Load (FEF)
Tahap 5     : Boundary Condition lengkap
Tahap 6     : Load Combination Engine (rule-based, database-driven)
Tahap 7     : Diagram gaya dalam: N, V, M, T
Tahap 8     : Deformed shape
Tahap 9     : Modal Analysis
Tahap 10    : Response Spectrum Analysis
Tahap 11    : P-Delta Analysis
Tahap 12    : Steel Design Check
Tahap 13    : Concrete Design Check
Tahap 14    : Seismic Design Check
Tahap 15    : Full Report Generation
Tahap 16    : 3D Frame Analysis
```

**Mengapa 3D bukan Tahap 2?**
3D Frame Analysis memerlukan fondasi yang solid: 2D solver yang terverifikasi, load combination engine yang stabil, diagram N/V/M yang bekerja, dan report engine yang dapat menampilkan hasil. Membangun 3D di atas fondasi yang belum stabil hanya akan memindahkan bug ke lapisan yang lebih dalam dan sulit di-trace. 3D adalah ekstensi alami setelah ekosistem 2D matang.

**Invariant yang tidak boleh dilanggar:**
- Solver engine = pure Python (numpy/scipy only). Tidak ada SQLAlchemy, FastAPI, atau React di dalam `app/solver/`.
- Semua unit SI: kN, m, kN·m, kN/m, rad — kecuali modul concrete check (mm, MPa) yang dikonversi di boundary.
- Semua data masuk/keluar solver melalui dataclass yang terdefinisi di `app/solver/kernel/` — tidak ada `dict` telanjang.
- Setiap tahap harus lolos verification suite sebelum merge ke main.
- Setiap hasil analisis harus menyimpan traceability record lengkap (lihat bagian Traceability).

---

## Prinsip Traceability

Setiap hasil analisis yang disimpan ke database **wajib** menyertakan metadata berikut. Tanpa ini, hasil tidak dapat diaudit atau direproduksi.

### Struktur Traceability Record

```python
# app/solver/kernel/traceability.py

@dataclass
class SolverVersion:
    kernel_version: str          # e.g. "0.3.1" — versi app/solver/
    code_check_version: str      # e.g. "1.2.0" — versi app/calculation/
    numpy_version: str
    scipy_version: str

@dataclass
class AnalysisTrace:
    # Identitas
    analysis_id: str             # UUID
    project_id: int
    user_id: int
    timestamp_utc: str           # ISO 8601

    # Versi perangkat lunak
    solver_version: SolverVersion

    # Snapshot input (immutable — tidak berubah meskipun data proyek diedit)
    input_snapshot: dict         # serialisasi lengkap Frame2DModel / Frame3DModel

    # Kombinasi yang digunakan
    load_combination_ids: list[str]   # referensi ke LoadCombinationRule di DB

    # Asumsi yang berlaku saat analisis dijalankan
    assumptions: list[str]       # e.g. ["Linear elastic", "Small displacement theory",
                                 #        "Euler-Bernoulli beam", "No shear deformation"]

    # Peringatan yang dihasilkan solver
    warnings: list[str]          # e.g. ["Element EL-05: L/r = 210 > 200, check slenderness"]

    # Status konvergensi
    converged: bool
    convergence_message: str
```

### Penyimpanan di Database

```python
# app/models/analysis_record.py — SQLModel

class AnalysisRecord(SQLModel, table=True):
    __tablename__ = "analysis_records"
    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_uuid: str = Field(index=True)         # UUID, immutable
    project_id: int = Field(foreign_key="projects.id")
    user_id: int = Field(foreign_key="users.id")
    timestamp_utc: datetime

    # Versi
    kernel_version: str
    code_check_version: str
    numpy_version: str
    scipy_version: str

    # Snapshots (JSON, immutable setelah disimpan)
    input_snapshot: dict = Field(sa_column=Column(JSON))
    result_snapshot: dict = Field(sa_column=Column(JSON))
    load_combination_ids: list = Field(sa_column=Column(JSON))
    assumptions: list = Field(sa_column=Column(JSON))
    warnings: list = Field(sa_column=Column(JSON))

    converged: bool
    convergence_message: str
```

**Aturan traceability:**
- `input_snapshot` dan `result_snapshot` tidak boleh dimodifikasi setelah disimpan — mereka adalah rekaman historis.
- Jika pengguna mengedit model dan menjalankan ulang analisis, dibuat `AnalysisRecord` baru dengan UUID baru.
- Laporan selalu mereferensikan `analysis_uuid`, bukan data proyek langsung.

---

## Tahap 0 — Engineering Kernel Foundation

### Tujuan
Mendefinisikan seluruh kontrak tipe data, konvensi, dan transformasi dasar yang dipakai oleh semua modul solver di tahap berikutnya. Tahap ini adalah "bahasa bersama" seluruh codebase — harus selesai dan stabil sebelum baris kode solver ditulis.

### Mengapa Tahap 0?

Tanpa kernel yang jelas, setiap developer membuat asumsi berbeda:
- Apakah momen positif searah jarum jam atau berlawanan?
- Apakah Y adalah vertikal atau horizontal?
- Unit beban dalam kN atau N?
- Apakah gaya aksial tekan positif atau negatif?

Inkonsistensi ini menjadi bug yang sangat sulit dilacak, karena secara numerik hasilnya tetap "masuk akal" tetapi salah secara fisika.

### Fitur

#### 0.1 — Unit System

```python
# app/solver/kernel/units.py

from enum import Enum

class ForceUnit(Enum):
    KN  = "kN"
    N   = "N"
    KGF = "kgf"

class LengthUnit(Enum):
    M  = "m"
    MM = "mm"
    CM = "cm"

class AngleUnit(Enum):
    RAD = "rad"
    DEG = "deg"

# Konvensi internal AG-SAS:
# Force  : kN
# Length : m
# Moment : kN·m
# Stress : kN/m² (bukan MPa — konversi di boundary modul concrete)
# Mass   : kg (untuk analisis dinamik)

# Faktor konversi eksplisit — tidak boleh ada konversi implisit di solver
FORCE_FACTORS  = {ForceUnit.KN: 1.0, ForceUnit.N: 1e-3, ForceUnit.KGF: 9.80665e-3}
LENGTH_FACTORS = {LengthUnit.M: 1.0, LengthUnit.MM: 1e-3, LengthUnit.CM: 1e-2}
```

#### 0.2 — Sign Convention

```python
# app/solver/kernel/sign_convention.py

"""
AG-SAS Sign Convention — berlaku untuk semua solver dan post-processor.
Dokumen ini adalah referensi tunggal. Jangan mendefinisikan ulang sign
convention di tempat lain.

KOORDINAT GLOBAL:
  X = arah horizontal (→ positif)
  Y = arah vertikal   (↑ positif)
  Z = keluar bidang   (keluar positif, aturan tangan kanan)

GAYA NODAL:
  Fx positif = arah +X
  Fy positif = arah +Y
  Mz positif = berlawanan jarum jam (right-hand rule terhadap Z)

GAYA DALAM ELEMEN (koordinat lokal):
  x_lokal = dari node I ke node J
  N positif  = tarik (tension)
  V positif  = gaya geser yang menyebabkan rotasi searah jarum jam pada potongan kiri
  M positif  = serat bawah tarik (sagging convention untuk balok horizontal)

  Referensi: McGuire, Gallagher, Ziemian — "Matrix Structural Analysis" 2nd Ed., §3.2

DISPLACEMENT:
  ux, uy positif = translasi arah +X, +Y
  rz positif     = rotasi berlawanan jarum jam

PERLETAKAN:
  Reaksi dilaporkan dalam arah yang sama dengan gaya eksternal.
  Reaksi positif berarti perletakan mendorong node ke arah positif.
"""

SIGN_CONVENTION_VERSION = "1.0"
SIGN_CONVENTION_REFERENCE = "McGuire et al. MSA 2nd Ed. §3.2"
```

#### 0.3 — Coordinate System

```python
# app/solver/kernel/coordinate_system.py

import numpy as np
from dataclasses import dataclass

@dataclass(frozen=True)
class CoordinateSystem2D:
    """Sistem koordinat global 2D. X horizontal, Y vertikal."""
    name: str = "Global-2D"
    x_axis: tuple = (1, 0)
    y_axis: tuple = (0, 1)

@dataclass(frozen=True)
class CoordinateSystem3D:
    """Sistem koordinat global 3D (right-hand rule)."""
    name: str = "Global-3D"
    x_axis: tuple = (1, 0, 0)
    y_axis: tuple = (0, 1, 0)    # vertikal (gravitasi -Y)
    z_axis: tuple = (0, 0, 1)

def rotation_matrix_2d(angle_rad: float) -> np.ndarray:
    """Matriks rotasi 2D untuk transformasi lokal-global."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array([[c, s], [-s, c]])
```

#### 0.4 — Local/Global Transformation

```python
# app/solver/kernel/transformation.py

import numpy as np

def transform_2d(K_local: np.ndarray, T: np.ndarray) -> np.ndarray:
    """
    Transformasi stiffness matrix dari lokal ke global.
    K_global = Tᵀ · K_local · T
    """
    return T.T @ K_local @ T

def transformation_matrix_2d(cx: float, cy: float) -> np.ndarray:
    """
    T (6×6) untuk elemen beam 2D.
    cx, cy = direction cosines (cos θ, sin θ) dari elemen.
    Ref: McGuire et al. §4.2
    """
    T = np.zeros((6, 6))
    T[0, 0] = T[1, 1] = cx
    T[0, 1] = cy
    T[1, 0] = -cy
    T[1, 1] = cx  # koreksi: T[1,1] harusnya cy
    T[2, 2] = 1.0
    T[3, 3] = T[4, 4] = cx
    T[3, 4] = cy
    T[4, 3] = -cy
    T[4, 4] = cx
    T[5, 5] = 1.0
    return T

def transformation_matrix_3d(node_i, node_j, local_z=None) -> np.ndarray:
    """
    T (12×12) untuk elemen beam 3D.
    Gunakan block_diag(R, R, R, R) dimana R adalah 3×3 direction cosine matrix.
    Ref: McGuire et al. §9.2
    """
    # Implementasi: lihat Tahap 16
    raise NotImplementedError("3D transformation — lihat Tahap 16")
```

#### 0.5 — Material Model

```python
# app/solver/kernel/material.py

from dataclasses import dataclass, field
from enum import Enum

class MaterialType(Enum):
    STEEL    = "steel"
    CONCRETE = "concrete"
    TIMBER   = "timber"
    CUSTOM   = "custom"

@dataclass
class Material:
    id: str
    name: str
    type: MaterialType
    E_kn_m2: float          # Modulus elastisitas [kN/m²]
    G_kn_m2: float          # Modulus geser [kN/m²]
    nu: float               # Poisson's ratio
    rho_kg_m3: float        # Massa jenis [kg/m³]
    alpha_per_C: float      # Koefisien termal [/°C]

    # Properti kekuatan (opsional — diisi jika digunakan untuk design check)
    fy_kn_m2: float | None = None     # Tegangan leleh [kN/m²] — baja
    fu_kn_m2: float | None = None     # Tegangan ultimate [kN/m²] — baja
    fc_kn_m2: float | None = None     # Kuat tekan [kN/m²] — beton

# Preset material standar
STEEL_BJ41 = Material(
    id="BJ41", name="Baja BJ-41 (SNI 1729:2020)", type=MaterialType.STEEL,
    E_kn_m2=200_000_000,    # 200 GPa
    G_kn_m2=77_000_000,     # 77 GPa
    nu=0.3, rho_kg_m3=7850, alpha_per_C=1.2e-5,
    fy_kn_m2=250_000,       # 250 MPa
    fu_kn_m2=410_000,       # 410 MPa
)

CONCRETE_FC25 = Material(
    id="fc25", name="Beton fc'=25 MPa (SNI 2847:2019)", type=MaterialType.CONCRETE,
    E_kn_m2=23_500_000,     # 4700√25 ≈ 23,500 MPa
    G_kn_m2=9_800_000,
    nu=0.2, rho_kg_m3=2400, alpha_per_C=1.0e-5,
    fc_kn_m2=25_000,
)
```

#### 0.6 — Section Property Model

```python
# app/solver/kernel/section.py

from dataclasses import dataclass
from enum import Enum

class SectionType(Enum):
    WF       = "WF"          # Wide flange / I-section
    HSS_RECT = "HSS_rect"    # Hollow structural section — rectangular
    HSS_CIR  = "HSS_cir"     # Hollow structural section — circular
    RECT     = "rect"        # Solid rectangular (beton)
    CIRCULAR = "circular"    # Solid circular
    CUSTOM   = "custom"

@dataclass
class SectionProperties:
    """
    Properti penampang dalam satuan SI (m, m², m⁴).
    Ini adalah yang digunakan solver — bukan mm atau cm.
    Konversi dari database (mm/cm) dilakukan di service layer.
    """
    id: str
    name: str
    type: SectionType
    A_m2: float          # Luas penampang [m²]
    Ix_m4: float         # Momen inersia lentur mayor [m⁴]
    Iy_m4: float         # Momen inersia lentur minor [m⁴]
    J_m4: float          # Konstanta torsi [m⁴]
    Zx_m3: float         # Modulus plastis mayor [m³]
    Zy_m3: float         # Modulus plastis minor [m³]
    Sx_m3: float         # Modulus elastis mayor [m³]
    Sy_m3: float         # Modulus elastis minor [m³]
    # Dimensi geometri (untuk design check)
    h_m: float | None = None     # Tinggi total [m]
    bf_m: float | None = None    # Lebar sayap [m]
    tw_m: float | None = None    # Tebal badan [m]
    tf_m: float | None = None    # Tebal sayap [m]
```

#### 0.7 — Load Model

```python
# app/solver/kernel/load_model.py

from dataclasses import dataclass
from enum import Enum

class LoadCaseType(Enum):
    DEAD      = "D"
    LIVE      = "L"
    ROOF_LIVE = "Lr"
    SNOW      = "S"
    WIND      = "W"
    EARTHQUAKE = "E"
    TEMPERATURE = "T"
    CONSTRUCTION = "C"

class LoadDirection(Enum):
    GLOBAL_X = "GX"; GLOBAL_Y = "GY"; GLOBAL_Z = "GZ"
    LOCAL_X  = "LX"; LOCAL_Y  = "LY"; LOCAL_Z  = "LZ"
    GRAVITY  = "GY_NEG"   # Selalu -Y global, shorthand untuk self-weight

@dataclass
class NodalLoad:
    node_id: str
    fx_kn: float = 0.0
    fy_kn: float = 0.0
    fz_kn: float = 0.0
    mx_knm: float = 0.0
    my_knm: float = 0.0
    mz_knm: float = 0.0

@dataclass
class UniformMemberLoad:
    element_id: str
    direction: LoadDirection
    w_kn_m: float       # kN/m

@dataclass
class TrapezoidMemberLoad:
    element_id: str
    direction: LoadDirection
    w_i_kn_m: float     # kN/m di node I
    w_j_kn_m: float     # kN/m di node J

@dataclass
class PointMemberLoad:
    element_id: str
    direction: LoadDirection
    P_kn: float
    a_m: float          # jarak dari node I [m]

@dataclass
class TemperatureLoad:
    element_id: str
    delta_T_C: float    # ΔT [°C]
    alpha: float        # koefisien termal [/°C]

@dataclass
class LoadCase:
    id: str
    name: str
    type: LoadCaseType
    nodal_loads: list[NodalLoad]
    member_uniform: list[UniformMemberLoad]
    member_trapezoid: list[TrapezoidMemberLoad]
    member_point: list[PointMemberLoad]
    temperature_loads: list[TemperatureLoad]
```

#### 0.8 — Result Model

```python
# app/solver/kernel/result_model.py

from dataclasses import dataclass, field

@dataclass
class NodeDisplacement:
    node_id: str
    ux_m: float = 0.0
    uy_m: float = 0.0
    uz_m: float = 0.0
    rx_rad: float = 0.0
    ry_rad: float = 0.0
    rz_rad: float = 0.0

@dataclass
class NodeReaction:
    node_id: str
    rx_kn: float = 0.0
    ry_kn: float = 0.0
    rz_kn: float = 0.0
    rmx_knm: float = 0.0
    rmy_knm: float = 0.0
    rmz_knm: float = 0.0

@dataclass
class ElementEndForces:
    """Gaya dalam di ujung elemen, dalam koordinat LOKAL."""
    element_id: str
    # Ujung I:
    N_i_kn: float = 0.0     # Aksial (positif = tarik)
    Vy_i_kn: float = 0.0    # Geser lokal-y
    Vz_i_kn: float = 0.0    # Geser lokal-z
    Mx_i_knm: float = 0.0   # Torsi
    My_i_knm: float = 0.0   # Momen lentur minor
    Mz_i_knm: float = 0.0   # Momen lentur mayor
    # Ujung J:
    N_j_kn: float = 0.0
    Vy_j_kn: float = 0.0
    Vz_j_kn: float = 0.0
    Mx_j_knm: float = 0.0
    My_j_knm: float = 0.0
    Mz_j_knm: float = 0.0

@dataclass
class AnalysisResult:
    load_case_id: str
    displacements: list[NodeDisplacement]
    reactions: list[NodeReaction]
    element_forces: list[ElementEndForces]
    converged: bool
    message: str
    # Statistik
    max_displacement_m: float = 0.0
    max_moment_knm: float = 0.0
    max_shear_kn: float = 0.0
```

### Modul Backend

```
app/solver/kernel/
├── __init__.py
├── units.py               # ForceUnit, LengthUnit, konversi
├── sign_convention.py     # Dokumentasi konvensi — tidak ada kode yang override ini
├── coordinate_system.py   # CoordinateSystem2D, CoordinateSystem3D
├── transformation.py      # T matrix 2D (3D stub untuk Tahap 16)
├── material.py            # Material dataclass + preset BJ41, fc25
├── section.py             # SectionProperties dataclass
├── load_model.py          # LoadCase, NodalLoad, MemberLoad
├── result_model.py        # AnalysisResult, NodeDisplacement, ElementEndForces
└── traceability.py        # AnalysisTrace, SolverVersion
```

### Unit Test

```python
# tests/solver/kernel/

# Test 1: Unit conversion roundtrip
# 100 kN → N → kN == 100 kN (toleransi floating point)

# Test 2: Rotation matrix — rotasi 90° kemudian 270° = identitas

# Test 3: Transformation matrix T — T @ Tᵀ = I (orthogonal matrix)

# Test 4: Material preset sanity
# STEEL_BJ41.E_kn_m2 == 200_000_000 (200 GPa dalam kN/m²)
# STEEL_BJ41.fy_kn_m2 / 1000 == 250.0 (250 MPa)

# Test 5: Sign convention dokumentasi
# SIGN_CONVENTION_VERSION harus ada dan tidak kosong
# Verifikasi bahwa tidak ada modul solver yang mendefinisikan ulang konvensi
```

---

## Tahap 1 — 2D Frame Analysis (Direct Stiffness Method)

### Tujuan
Membangun solver linear-elastik untuk portal frame 2D menggunakan kernel dari Tahap 0. Ini adalah implementasi pertama yang dapat menghasilkan hasil numerik nyata.

### Fitur
- Elemen balok-kolom Euler-Bernoulli 2D (3 DOF per node: ux, uy, rz)
- Kondisi batas: fixed, pinned, roller-x, roller-y, free
- Beban nodal menggunakan `NodalLoad` dari kernel
- Output: `AnalysisResult` dari kernel (displacement, reaksi, gaya dalam elemen)
- Traceability record otomatis untuk setiap run

### Struktur Data

```python
# app/solver/frame2d/model.py
# Semua tipe dasar diimport dari kernel — tidak ada definisi ulang

from app.solver.kernel.load_model import LoadCase
from app.solver.kernel.material import Material
from app.solver.kernel.section import SectionProperties
from app.solver.kernel.result_model import AnalysisResult
from app.solver.kernel.traceability import AnalysisTrace

@dataclass
class Node2D:
    id: str
    x_m: float
    y_m: float

@dataclass
class Element2D:
    id: str
    node_i: str
    node_j: str
    material_id: str     # referensi ke Material
    section_id: str      # referensi ke SectionProperties
    # Properti yang diekstrak dari material+section saat solve:
    # E = material.E_kn_m2
    # A = section.A_m2
    # I = section.Ix_m4

@dataclass
class Support2D:
    node_id: str
    ux: bool    # True = restrained
    uy: bool
    rz: bool

@dataclass
class Frame2DModel:
    nodes: list[Node2D]
    elements: list[Element2D]
    supports: list[Support2D]
    materials: list[Material]
    sections: list[SectionProperties]

@dataclass
class Frame2DRunInput:
    model: Frame2DModel
    load_cases: list[LoadCase]
    # Combination IDs diambil dari DB di Tahap 6
    combination_ids: list[str]

@dataclass
class Frame2DRunOutput:
    case_results: dict[str, AnalysisResult]   # load_case_id → hasil
    trace: AnalysisTrace
```

### Modul Backend

```
app/solver/frame2d/
├── __init__.py
├── model.py              # Frame2DModel, Node2D, Element2D, Support2D
├── stiffness.py          # Local stiffness 6×6, transform ke global
├── assembly.py           # DOF numbering, global K assembly
├── boundary.py           # Partition method: K_ff, K_fr
├── solver.py             # numpy.linalg.solve → U_f
├── recovery.py           # Hitung reaksi + gaya dalam dari U
└── analyze.py            # Entry point: analyze_frame_2d(input) -> output
```

**`stiffness.py` — local stiffness matrix (6×6):**
```python
def local_stiffness_2d(E: float, A: float, I: float, L: float) -> np.ndarray:
    """
    Matriks kekakuan lokal balok Euler-Bernoulli 2D.
    Satuan: E [kN/m²], A [m²], I [m⁴], L [m] → K [kN/m] atau [kN·m/rad]
    Ref: McGuire et al. "Matrix Structural Analysis" 2nd Ed., §4.2, Eq.4.2-12
    """
    EA_L = E * A / L
    EI_L3 = E * I / L**3
    EI_L2 = E * I / L**2
    EI_L  = E * I / L
    return np.array([
        [ EA_L,      0,        0,     -EA_L,     0,        0     ],
        [ 0,    12*EI_L3,  6*EI_L2,    0,   -12*EI_L3,  6*EI_L2],
        [ 0,     6*EI_L2,  4*EI_L,     0,    -6*EI_L2,  2*EI_L ],
        [-EA_L,     0,        0,      EA_L,     0,        0     ],
        [ 0,   -12*EI_L3, -6*EI_L2,   0,    12*EI_L3, -6*EI_L2],
        [ 0,     6*EI_L2,  2*EI_L,    0,    -6*EI_L2,  4*EI_L ],
    ])
```

**`boundary.py` — partition method:**
```python
# Pisahkan DOF menjadi free (f) dan restrained (r)
# Solve: K_ff · U_f = F_f - K_fr · U_r
# Untuk kondisi batas homogen (U_r = 0): K_ff · U_f = F_f
```

### Modul Frontend

```
modules/solver2d/
├── types.ts              # Mirror Frame2DModel, Frame2DRunOutput
├── ModelBuilder.tsx      # Input: tambah node, element, support, load
├── AnalysisRunner.tsx    # Tombol run, progress, error display
├── ResultsTable.tsx      # Tabel displacement + reaksi
└── TracePanel.tsx        # Tampilkan AnalysisTrace (version, assumptions, warnings)
```

**API endpoint:**
```
POST /api/v1/solver/frame2d/analyze
  Body: Frame2DRunInput (JSON)
  Response: { result: Frame2DRunOutput, trace: AnalysisTrace }
  Status 200: sukses
  Status 422: validasi model gagal (with error detail)
```

### Unit Test

```python
# tests/solver/frame2d/

# Test 1: Simply supported beam — beban terpusat P di tengah bentang L
# Ekspektasi: δ_max = PL³/(48EI) di tengah, M_max = PL/4
# Sumber: Timoshenko "Strength of Materials" Vol.1 §14

# Test 2: Fixed-fixed beam — beban merata w
# Ekspektasi: δ_max = wL⁴/(384EI), M_ujung = wL²/12, M_tengah = wL²/24
# Sumber: Roark's "Formulas for Stress and Strain" 8th Ed. Table 8.1

# Test 3: Cantilever beam — beban terpusat P di ujung bebas
# Ekspektasi: δ_ujung = PL³/(3EI), M_akar = PL (negatif = compressive top fiber)

# Test 4: Portal frame 1 bay, 1 lantai — kolom fixed base, balok kaku
# Bandingkan reaksi horizontal dengan solusi metode Cross
# Sumber: Hibbeler "Structural Analysis" 10th Ed. Example 11.7

# Test 5: Equilibrium global
# Σ(Fx_reaksi) = Σ(Fx_beban), Σ(Fy_reaksi) = Σ(Fy_beban)
# Berlaku untuk SEMUA test case — ini adalah invariant mutlak

# Test 6: Trace record
# Verifikasi bahwa setiap run menghasilkan AnalysisTrace dengan semua field terisi
# Verifikasi kernel_version, timestamp, input_snapshot tidak kosong
```

### Validasi

| Contoh | Sumber | Parameter yang Diverifikasi | Target Akurasi |
|--------|--------|-----------------------------|----------------|
| Simply supported beam, point load | Timoshenko Vol.1 §14 | δ_max, M_max, reaksi | < 0.01% |
| Fixed-fixed beam, UDL | Roark's Table 8.1 | δ_max, M_ujung | < 0.01% |
| Propped cantilever | Hibbeler §12 | Reaksi, moment diagram | < 0.01% |
| Two-span continuous beam | McGuire et al. Ex. 5.2 | Displacement, reaksi | < 0.1% |
| Portal frame 1 bay | Hibbeler Ex. 11.7 | Reaksi, sway | < 0.1% |

---

## Tahap 2 — Verification & Validation Framework untuk 2D Solver

### Tujuan
Sebelum melanjutkan ke tahap berikutnya, bangun framework yang memastikan solver 2D benar secara matematis, fisika, dan numerik. Tahap ini tidak menambah fitur baru — hanya memastikan Tahap 1 dapat dipercaya.

**Prinsip V&V:**
- *Verification* — apakah kode mengimplementasikan matematika dengan benar? (cek internal)
- *Validation* — apakah hasil fisika sesuai dengan dunia nyata? (cek eksternal)
- SAP2000/ETABS digunakan sebagai **pembanding**, bukan sebagai sumber kebenaran tunggal. Jika ada perbedaan, cari dan verifikasi dari sumber primer (textbook, derivasi manual).

### Fitur

#### 2.1 — Benchmark Suite Otomatis

```python
# tests/verification/benchmark_cases.py

# Setiap benchmark case mendefinisikan:
# - model (Frame2DModel)
# - load case
# - expected results (dari sumber primer)
# - tolerance
# - reference citation

@dataclass
class BenchmarkCase:
    id: str
    description: str
    reference: str          # "Timoshenko Vol.1 §14 Eq.14.2"
    model: Frame2DModel
    load_case: LoadCase
    expected: dict[str, float]   # {"delta_max_m": 0.00234, "M_max_knm": 75.0}
    tolerance_pct: float         # e.g. 0.01 untuk 0.01%
```

**Benchmark cases yang wajib lolos:**

| ID | Deskripsi | Referensi | Toleransi |
|----|-----------|-----------|-----------|
| BM-01 | Simply supported beam, point load tengah | Timoshenko §14 | 0.01% |
| BM-02 | Simply supported beam, UDL | Timoshenko §14 | 0.01% |
| BM-03 | Simply supported beam, moment ujung | Roark's Table 8.1c | 0.01% |
| BM-04 | Fixed-fixed beam, UDL | Roark's Table 8.1d | 0.01% |
| BM-05 | Fixed-fixed beam, point load tengah | Roark's Table 8.1e | 0.01% |
| BM-06 | Cantilever, point load ujung | Timoshenko §12 | 0.01% |
| BM-07 | Cantilever, UDL | Timoshenko §12 | 0.01% |
| BM-08 | Propped cantilever, UDL | Hibbeler §12 | 0.01% |
| BM-09 | Two-span beam, midpoint load | McGuire Ex.5.2 | 0.1% |
| BM-10 | Portal frame, horizontal load | Hibbeler Ex.11.7 | 0.1% |
| BM-11 | Grillage 2D | McGuire Ex.5.3 | 0.1% |
| BM-12 | Multi-story frame | McGuire Ex.6.1 | 0.5% |

#### 2.2 — Physical Invariant Checker

```python
# app/solver/verification/invariant_checker.py

def check_global_equilibrium(result: AnalysisResult, load_case: LoadCase) -> list[str]:
    """
    Cek keseimbangan global: ΣF = 0, ΣM = 0.
    Ini adalah check fisika yang wajib lulus untuk SETIAP hasil solver.
    Kegagalan di sini berarti ada bug fundamental di solver.
    """
    errors = []
    sum_Fx = sum(r.rx_kn for r in result.reactions) + sum(l.fx_kn for l in all_nodal_loads)
    sum_Fy = sum(r.ry_kn for r in result.reactions) + sum(l.fy_kn for l in all_nodal_loads)
    if abs(sum_Fx) > 1e-6:
        errors.append(f"Global equilibrium FAIL: ΣFx = {sum_Fx:.6e} kN ≠ 0")
    if abs(sum_Fy) > 1e-6:
        errors.append(f"Global equilibrium FAIL: ΣFy = {sum_Fy:.6e} kN ≠ 0")
    return errors

def check_compatibility(result: AnalysisResult, model: Frame2DModel) -> list[str]:
    """Cek: displacement di node perletakan = 0 (untuk kondisi batas homogen)."""
    ...

def check_symmetry(result: AnalysisResult, axis: str) -> list[str]:
    """Untuk model simetris dengan beban simetris: displacement harus simetris."""
    ...
```

#### 2.3 — Regression Test Runner

```python
# tests/verification/regression_runner.py

# CI pipeline menjalankan semua benchmark case setiap push ke main.
# Jika ada benchmark yang gagal → build gagal, PR tidak bisa di-merge.
# Report: tabel semua benchmark, % error, pass/fail, referensi.

def run_regression_suite() -> RegressionReport:
    cases = load_all_benchmark_cases()
    results = []
    for case in cases:
        solver_result = analyze_frame_2d(case.model, case.load_case)
        for key, expected in case.expected.items():
            actual = extract_value(solver_result, key)
            error_pct = abs(actual - expected) / abs(expected) * 100
            results.append({
                "case": case.id,
                "param": key,
                "expected": expected,
                "actual": actual,
                "error_pct": error_pct,
                "pass": error_pct <= case.tolerance_pct,
                "reference": case.reference,
            })
    return RegressionReport(results)
```

#### 2.4 — Perbandingan dengan SAP2000/ETABS

```
Catatan penting tentang cross-software comparison:

SAP2000 dan ETABS adalah software komersial yang digunakan sebagai pembanding,
BUKAN sebagai sumber kebenaran. Jika hasil AG-SAS berbeda dengan SAP2000:

1. Cek terlebih dahulu apakah AG-SAS benar terhadap solusi manual (textbook).
2. Jika AG-SAS benar terhadap textbook → dokumentasikan perbedaan model
   (apakah ada perbedaan asumsi, shear deformation, dll).
3. Jika AG-SAS salah terhadap textbook → itu adalah bug di AG-SAS.
4. Jangan menganggap SAP2000 selalu benar — cross-check keduanya terhadap
   sumber primer yang dapat diverifikasi.

File perbandingan disimpan di: docs/verification/sap2000-comparison/
Format: model SAP2000 (.sdb) + screenshot + tabel perbandingan + analisis perbedaan
```

### Modul Backend

```
app/solver/verification/
├── __init__.py
├── invariant_checker.py   # Equilibrium, compatibility, symmetry checks
├── benchmark_runner.py    # Jalankan semua BenchmarkCase
└── regression_report.py   # Format laporan regression

tests/verification/
├── benchmark_cases/
│   ├── bm01_ss_beam_point.py
│   ├── bm02_ss_beam_udl.py
│   ├── ... (semua 12 benchmark)
│   └── bm12_multistory_frame.py
├── regression_runner.py
└── sap2000_comparison/
    ├── README.md           # Catatan metodologi perbandingan
    └── results/            # Tabel perbandingan per kasus
```

### Gate: Tahap 3 Tidak Boleh Dimulai Sebelum

- [ ] Semua 12 benchmark cases lulus dengan toleransi yang ditetapkan
- [ ] Global equilibrium check lulus untuk semua benchmark cases
- [ ] Regression runner terintegrasi di CI pipeline
- [ ] Dokumen perbandingan SAP2000 untuk minimal 3 kasus dibuat

---

## Tahap 3 — Matrix Stiffness Infrastructure

### Tujuan
Refactor internal solver menggunakan sparse matrix untuk mendukung model besar, dan membangun validator model yang komprehensif.

### Fitur
- DOF numbering otomatis (bandwidth minimization — Cuthill-McKee)
- Global stiffness menggunakan `scipy.sparse.lil_matrix` → `csr_matrix`
- Solver: `scipy.sparse.linalg.spsolve` (menggantikan `numpy.linalg.solve`)
- Validasi model sebelum solve: konektivitas, kondisi batas minimum, degenerasi
- Prescribed displacement: U_r ≠ 0

### Modul Backend

```
app/solver/core/
├── dof_manager.py        # DOF numbering, free/restrained partition
├── assembler.py          # Sparse assembly — dipakai oleh frame2d dan frame3d
├── preconditioner.py     # Cuthill-McKee reordering untuk bandwidth minimization
├── linear_solver.py      # Abstraksi: dense (n_dof < 500) atau sparse (n_dof ≥ 500)
├── model_validator.py    # Cek kelengkapan model sebelum solve
└── result_recovery.py    # Post-processing umum (dipakai semua solver)
```

**Model validator:**
```python
def validate_model(model) -> list[ValidationError]:
    errors = []
    # 1. Minimum 1 node, 1 element
    # 2. Semua node yang direferensikan element harus ada
    # 3. Semua material dan section yang direferensikan harus ada
    # 4. Rigid body mode check — cukup perletakan untuk mencegah singularity
    # 5. Tidak ada element dengan panjang = 0
    # 6. E, A, I > 0 untuk semua elemen
    # 7. Semua node yang punya beban harus ada di model
    return errors
```

**Threshold sparse:**
```python
# n_dof < 500  → numpy.linalg.solve (lebih cepat untuk model kecil)
# n_dof ≥ 500  → scipy.sparse.linalg.spsolve
```

### Unit Test

```python
# Test 1: Konsistensi dense vs sparse
# Model kecil yang sama → hasil identik dari kedua solver

# Test 2: Performance — 1000-DOF system selesai < 2 detik

# Test 3: Prescribed displacement (settlement 10 mm)
# Verifikasi momen tambahan terhadap solusi manual

# Test 4: Model invalid → validator mengembalikan error yang deskriptif
```

---

## Tahap 4 — Member Load

### Tujuan
Konversi beban pada batang menjadi equivalent nodal loads menggunakan fixed-end forces (FEF).

### Fitur
- Beban merata (uniform): arah global dan lokal
- Beban trapesoid (intensitas berbeda di kedua ujung)
- Beban terpusat di posisi `a` dari node I
- Temperature load (ΔT) → equivalent axial force

**Fixed-end forces untuk uniform load (arah lokal y):**
```python
# FEF = [0, wL/2, wL²/12, 0, wL/2, -wL²/12]  (koordinat lokal)
# Ref: Weaver & Gere "Matrix Analysis of Framed Structures" Appendix A
# Transform ke global → tambahkan ke F_global
```

### Modul Backend

```
app/solver/loads/
├── fixed_end_forces.py   # FEF untuk uniform, trapezoid, point load, temperature
├── load_assembler.py     # Gabungkan nodal loads + FEF menjadi F_global
└── load_validator.py     # Cek: a ≤ L, w tidak NaN, direction valid
```

### Unit Test

```python
# Test 1: Simply supported beam, UDL w
# FEF → nodal loads → solve → δ_max = 5wL⁴/(384EI), M_max = wL²/8

# Test 2: Fixed-fixed beam, UDL
# δ_max = wL⁴/(384EI), M_ujung = wL²/12

# Test 3: Point load di posisi a dari node I
# Verifikasi terhadap formula Roark's Table 8.1i

# Test 4: Temperature load
# Cantilever, ΔT = 30°C → elongasi = α·ΔT·L (verifikasi aksial)
```

---

## Tahap 5 — Boundary Condition Lengkap

### Tujuan
Mendukung semua kondisi batas yang relevan dalam praktik engineering.

### Fitur
- Spring support: kx, ky, krz (kN/m atau kN·m/rad)
- Prescribed displacement / settlement: U_r ≠ 0
- Internal hinge (moment release) di ujung elemen
- Rigid link (master-slave DOF)

**Implementasi moment release:**
```python
# Static condensation — eliminasi DOF rotasi internal
# Ref: McGuire et al. §6.4 "Internal Hinges"
# k_condensed = k_ff - k_fr · k_rr⁻¹ · k_rf
```

### Modul Backend

```
app/solver/boundary/
├── spring_handler.py     # Tambahkan spring ke diagonal K
├── prescribed_disp.py    # Partition method dengan U_r ≠ 0
├── moment_release.py     # Static condensation untuk hinge
└── rigid_link.py         # Constraint equations (Lagrange multiplier)
```

### Unit Test

```python
# Test: Beam dengan spring vertikal di tengah
# Defleksi harus lebih kecil dari tanpa spring

# Test: Settlement pondasi 10 mm
# Verifikasi momen tambahan terhadap formula manual

# Test: Beam dengan internal hinge di tengah
# Momen di titik hinge = 0 (invariant mutlak)
```

---

## Tahap 6 — Load Combination Engine (Rule-Based, Database-Driven)

### Tujuan
Membangun engine kombinasi beban yang fleksibel, transparan, dan dapat dikonfigurasi oleh admin — **bukan hardcode**. Kombinasi SNI disimpan di database, bukan dikodekan langsung di source code.

### Mengapa Rule-Based?

Jika kombinasi di-hardcode:
- Sulit diperbarui ketika SNI direvisi
- Tidak bisa menambahkan kombinasi proyek khusus tanpa mengubah kode
- Tidak ada audit trail — siapa yang mengubah kombinasi kapan?

Dengan database-driven:
- Admin dapat menambah/menonaktifkan kombinasi tanpa deploy ulang
- Setiap kombinasi punya referensi pasal yang jelas
- Riwayat perubahan kombinasi tercatat di database

### Struktur Data Database

```python
# app/models/load_combination_rule.py — SQLModel

class LoadCombinationRule(SQLModel, table=True):
    __tablename__ = "load_combination_rules"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Identitas kombinasi
    code: str = Field(max_length=20)           # e.g. "SNI-1727-2020"
    method: str = Field(max_length=10)         # "LRFD" | "ASD"
    combination_name: str = Field(max_length=100)  # e.g. "U2: 1.2D + 1.6L"
    expression: str = Field(max_length=200)    # e.g. "1.2D + 1.6L"

    # Faktor beban dalam JSON
    # Format: {"D": 1.2, "L": 1.6}
    # Kunci adalah LoadCaseType enum value ("D", "L", "W", "E", dll.)
    load_factors: dict = Field(sa_column=Column(JSON))

    # Referensi pasal standar
    source_reference: str = Field(max_length=200)
    # e.g. "SNI 1727:2020 Pasal 4.2.3 Tabel 4.2-2 Kombinasi U2"

    # Status
    active: bool = Field(default=True)         # False = tidak dipakai dalam analisis
    editable_by_admin: bool = Field(default=True)   # False = system-defined, read-only

    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(max_length=100)    # username
```

**Data seed awal (SNI 1727:2020 LRFD):**

| combination_name | expression | load_factors | source_reference |
|-----------------|------------|--------------|------------------|
| U1: 1.4D | 1.4D | `{"D": 1.4}` | SNI 1727:2020 Ps.4.2.3 Tabel 4.2-2 Komb.1 |
| U2: 1.2D + 1.6L | 1.2D + 1.6L | `{"D": 1.2, "L": 1.6}` | SNI 1727:2020 Ps.4.2.3 Komb.2 |
| U3: 1.2D + 1.6Lr + L | ... | `{"D": 1.2, "Lr": 1.6, "L": 1.0}` | Komb.3 |
| U4a: 1.2D + 1.0W + L | ... | `{"D": 1.2, "W": 1.0, "L": 1.0}` | Komb.4a |
| U4b: 0.9D + 1.0W | ... | `{"D": 0.9, "W": 1.0}` | Komb.4b |
| U5a: 1.2D + 1.0E + L | ... | `{"D": 1.2, "E": 1.0, "L": 1.0}` | Komb.5a |
| U5b: 0.9D + 1.0E | ... | `{"D": 0.9, "E": 1.0}` | Komb.5b |

**Kombinasi dengan `editable_by_admin = false`** adalah kombinasi sistem yang tidak boleh dihapus, hanya bisa dinonaktifkan (`active = false`).

### Struktur Data Runtime

```python
# app/solver/loads/combination_engine.py

@dataclass
class ActiveCombination:
    rule_id: int            # FK ke LoadCombinationRule
    combination_name: str   # disalin dari rule pada saat analisis (snapshot)
    expression: str
    load_factors: dict[str, float]
    source_reference: str

@dataclass
class CombinationResult:
    combination: ActiveCombination
    result: AnalysisResult    # hasil superposisi

@dataclass
class EnvelopeResult:
    max_displacement_per_node: dict[str, NodeDisplacement]
    min_displacement_per_node: dict[str, NodeDisplacement]
    max_moment_per_element: dict[str, float]
    min_moment_per_element: dict[str, float]
    controlling_combination: dict[str, str]   # parameter → nama kombinasi pengontrol
```

**Superposition engine:**
```python
def apply_combination(
    rule: ActiveCombination,
    case_results: dict[str, AnalysisResult]
) -> AnalysisResult:
    """
    Prinsip superposisi linear:
    U_combo = Σ(factor_i × U_case_i)
    PENTING: Solve sekali per load case, scale dan sum results —
    JANGAN solve ulang per kombinasi.
    """
    ...
```

### Modul Backend

```
app/solver/loads/
├── combination_engine.py    # Superposisi linear, apply_combination()
├── envelope.py              # Max/min envelope, controlling combination
└── combination_validator.py # Cek: semua load case yang direferensikan tersedia

app/services/
└── combination_service.py   # CRUD LoadCombinationRule + seed SNI defaults

app/api/v1/endpoints/
└── load_combinations.py     # GET/POST/PATCH/DELETE untuk admin
```

**Admin API:**
```
GET  /api/v1/admin/load-combinations           # List semua rules
POST /api/v1/admin/load-combinations           # Tambah rule baru
GET  /api/v1/admin/load-combinations/{id}      # Detail rule
PATCH /api/v1/admin/load-combinations/{id}     # Edit (hanya jika editable_by_admin=true)
DELETE /api/v1/admin/load-combinations/{id}    # Soft delete (set active=false)
GET  /api/v1/admin/load-combinations/presets   # List kombinasi bawaan SNI
POST /api/v1/admin/load-combinations/seed-sni  # Seed ulang kombinasi SNI default
```

### Traceability untuk Load Combination

Saat analisis dijalankan, `AnalysisTrace.load_combination_ids` berisi ID dari `LoadCombinationRule` yang aktif saat itu. Laporan dapat merekonstruksi faktor beban yang digunakan meskipun admin kemudian mengubah rule.

### Unit Test

```python
# Test 1: Superposisi linear
# Solve DL sendiri, solve LL sendiri
# Kombinasi 1.2DL + 1.6LL via engine == solve langsung 1.2DL + 1.6LL
# Toleransi: < 1e-10 (floating point — harus identik secara matematis)

# Test 2: Envelope
# 3 kombinasi → envelope max displacement per node
# Verifikasi nilai dan controlling combination

# Test 3: Admin CRUD
# Tambah kombinasi baru → aktif di analisis berikutnya
# Nonaktifkan kombinasi → tidak dipakai di analisis berikutnya

# Test 4: Kombinasi system (editable_by_admin=false)
# Upaya PATCH/DELETE → 403 Forbidden

# Test 5: Seed SNI → idempotent
# Panggil seed dua kali → tidak ada duplikasi

# Test 6: Traceability snapshot
# Ubah faktor beban di DB → jalankan analisis lama dari trace → hasilnya sama
# (karena trace menyimpan snapshot faktor, bukan reference ke ID saja)
```

---

## Tahap 7 — Diagram Gaya Dalam: N, V, M, T

### Tujuan
Menghitung dan memvisualisasikan distribusi gaya dalam sepanjang batang.

### Fitur
- Diagram N, V, M (2D) dan tambahan T (torsi, untuk 3D)
- Sampling n titik per elemen (default 20, dapat diubah)
- Rumus eksak untuk: uniform load, trapezoid, point load
- Discontinuity: lompatan V di lokasi point load
- Nilai dan lokasi maksimum/minimum secara otomatis

### Struktur Data

```python
@dataclass
class DiagramPoint:
    x_local_m: float    # posisi dari node I [m]
    N_kn: float
    Vy_kn: float
    Vz_kn: float        # 0 untuk 2D
    Mx_knm: float       # torsi (0 untuk 2D)
    My_knm: float       # 0 untuk 2D
    Mz_knm: float       # momen lentur

@dataclass
class ElementDiagram:
    element_id: str
    points: list[DiagramPoint]
    N_max_kn: float; N_min_kn: float
    V_max_kn: float; V_min_kn: float
    M_max_knm: float; M_min_knm: float
    x_M_max_m: float    # lokasi M_max dari node I

@dataclass
class DiagramResult:
    diagrams: list[ElementDiagram]
    global_M_max_knm: float
    global_V_max_kn: float
    controlling_element_M: str
    controlling_element_V: str
```

**Rumus diagram:**
```
N(x) = N_i + ∫₀ˣ n(ξ) dξ        — n(ξ): distribusi beban aksial
V(x) = V_i + ∫₀ˣ q(ξ) dξ        — q(ξ): distribusi beban transversal
M(x) = M_i + V_i·x - ∫₀ˣ (x-ξ)·q(ξ) dξ

Untuk uniform load w: rumus eksak (closed-form)
Untuk kasus umum: Simpson's rule, n=100 interval
```

### Modul Backend

```
app/solver/postprocess/
├── diagram_calculator.py   # N,V,M sepanjang elemen
├── extremes_finder.py      # Lokasi + nilai max/min
└── interpolator.py         # Smooth curve untuk visualisasi
```

### Modul Frontend

```
modules/diagrams/
├── DiagramViewer2D.tsx     # Canvas 2D: klik elemen → N,V,M diagram
├── DiagramOverlay.tsx      # Overlay N/V/M pada model (offset tegak lurus)
└── DiagramExport.tsx       # Export diagram ke PNG/SVG untuk laporan
```

### Unit Test

```python
# Test: Simply supported beam, UDL w
# V(0) = wL/2, V(L/2) = 0, V(L) = -wL/2
# M(0) = 0, M(L/2) = wL²/8, M(L) = 0

# Test: Kantilever, point load ujung
# V(x) = P (konstan), M(x) = -P·(L-x)

# Test: Keseimbangan per elemen
# V_j + V_i + ∫w dx = 0 (equilibrium check di tiap elemen)
# M_j - M_i - V_i·L + ∫w·x dx = 0

# Test: Continuity check di interior joint
# M dan V dari elemen sebelah kiri = elemen sebelah kanan (di node yang sama)
```

---

## Tahap 8 — Deformed Shape

### Tujuan
Interpolasi bentuk deformasi sepanjang batang dan visualisasi dengan scale factor yang dapat diatur.

### Fitur
- Interpolasi cubic Hermite antara displacement ujung elemen
- Scale factor yang dapat diatur (slider ×1 hingga ×1000)
- Animasi deformasi (cycle 0 → max → 0)
- Tampilkan undeformed shape (wireframe) bersamaan
- Color map berdasarkan besar displacement

**Cubic Hermite interpolation:**
```python
def deformed_y(x, L, v_i, rz_i, v_j, rz_j):
    """
    Interpolasi transversal menggunakan shape functions Hermitian.
    H1 = 1 - 3ξ² + 2ξ³   H2 = L·ξ(1-ξ)²
    H3 = 3ξ² - 2ξ³        H4 = L·ξ²(ξ-1)
    ξ = x/L
    Ref: Cook "FEA" 4th Ed. §12.4
    """
    xi = x / L
    H1 = 1 - 3*xi**2 + 2*xi**3
    H2 = L * xi * (1 - xi)**2
    H3 = 3*xi**2 - 2*xi**3
    H4 = L * xi**2 * (xi - 1)
    return H1*v_i + H2*rz_i + H3*v_j + H4*rz_j
```

### Modul Backend

```
app/solver/postprocess/
└── deformed_shape.py    # Cubic Hermite, sampling 20 titik/elemen
```

### Modul Frontend

```
modules/viewer/
├── DeformedShape.tsx        # Render deformed geometry + scale slider
└── AnimationControls.tsx    # Play/pause, speed, loop
```

---

## Tahap 9 — Modal Analysis

### Tujuan
Menghitung frekuensi natural dan mode shapes untuk keperluan analisis dinamik.

### Fitur
- Consistent mass matrix atau lumped mass matrix per elemen
- Generalized eigenvalue problem: K·φ = ω²·M·φ
- n mode shapes pertama (default: 12, maksimum: 50)
- Modal participation factors dan effective mass ratio
- Warning jika Σ(effective mass ratio) < 90% setelah n mode

### Struktur Data

```python
@dataclass
class ModeShape:
    mode_number: int
    omega_rad_s: float
    frequency_hz: float
    period_s: float
    shape: dict[str, NodeDisplacement]
    participation_x: float
    participation_y: float
    effective_mass_ratio_x: float
    effective_mass_ratio_y: float

@dataclass
class ModalResult:
    modes: list[ModeShape]
    total_mass_kg: float
    cumulative_mass_ratio_x: float   # harus ≥ 0.9 sesuai SNI
    cumulative_mass_ratio_y: float
    converged: bool
    n_modes_requested: int
    n_modes_converged: int
```

**Eigenvalue solver:**
```python
from scipy.sparse.linalg import eigsh

# shift-invert untuk mendapatkan frekuensi TERENDAH
eigenvalues, eigenvectors = eigsh(K_ff, M=M_ff, k=n_modes, sigma=0, which='LM')
```

### Unit Test

```python
# Test: SDOF — k=100 kN/m, m=1000 kg → ω=10 rad/s, T=0.628 s

# Test: Simply supported beam
# T₁ = (π/L)² · √(EI/ρA) — bandingkan dengan solver, toleransi < 1%

# Test: Mass participation check
# Σ(effective_mass_ratio) untuk semua mode ≈ 1.0

# Test: Mode shape orthogonality
# φᵢᵀ · M · φⱼ = 0 untuk i ≠ j (M-orthogonality)
```

---

## Tahap 10 — Response Spectrum Analysis (RSA)

### Tujuan
Analisis seismik menggunakan metode spektrum respons sesuai SNI 1726:2019.

### Fitur
- Input spektrum: parameter SNI (Ss, S1, Fa, Fv) atau custom (T vs Sa)
- CQC (Complete Quadratic Combination) dan SRSS
- Kombinasi arah: 100% X + 30% Y (SNI 1726:2019 §7.5.3.1)
- Story drift check dan base shear minimum check

**CQC correlation coefficient:**
```
ρᵢⱼ = 8ξ²(1+βᵢⱼ)βᵢⱼ^(3/2) / [(1-βᵢⱼ²)² + 4ξ²βᵢⱼ(1+βᵢⱼ)²]
βᵢⱼ = ωⱼ/ωᵢ,  ξ = 0.05 (default)
```

### Modul Backend

```
app/solver/dynamics/
├── spectrum.py          # SNI 1726:2019 spectrum generator + custom interpolasi
├── rsa_solver.py        # Per-mode response, CQC/SRSS combination
├── story_drift.py       # Amplifikasi: δx = Cd·δxe/Ie, cek Δa/h
└── base_shear.py        # Minimum base shear check
```

### Unit Test

```python
# Test: SDOF → spectral acceleration × mass = base shear

# Test: CQC == SRSS ketika βᵢⱼ < 0.1 (mode berjauhan)

# Test: SNI 1726:2019 spectrum — Ss=0.6g, S1=0.2g, Site D
# Verifikasi SDS, SD1, T0, Ts terhadap perhitungan manual
```

---

## Tahap 11 — P-Delta Analysis (Geometric Nonlinearity)

### Tujuan
Memperhitungkan efek P-Δ (second-order geometric stiffness).

### Fitur
- Geometric stiffness matrix per elemen
- Iterative Newton-Raphson hingga konvergensi
- Eigenvalue buckling: K_el·φ = λ·K_geo·φ
- Perbandingan: first-order vs second-order displacement

**Geometric stiffness (2D beam):**
```
K_geo = (N/L) · [matriks 6×6 Ref: McGuire et al. Ch.16]
N = gaya aksial dari first-order solution (tekan = negatif)
```

**Newton-Raphson loop:**
```python
for iter in range(max_iter):
    N_el = recover_axial(U, model)
    K_total = K_elastic + assemble_K_geo(N_el)
    R = F - K_total @ U
    dU = solve(K_total, R)
    U += dU
    if norm(dU) / (norm(U) + 1e-12) < tol: break
```

### Unit Test

```python
# Test: Euler buckling (kolom fixed-free)
# P_cr = π²EI/(4L²) — toleransi < 1%

# Test: P-Delta amplification factor
# 1/(1-θ) dimana θ = P·Δ/(V·h)

# Test: Newton-Raphson konvergen < 5 iterasi untuk θ < 0.1
```

---

## Tahap 12 — Steel Design Check (SNI 1729:2020)

### Tujuan
Pemeriksaan kapasitas elemen baja LRFD menggunakan gaya dalam dari solver.

### Fitur
- Klasifikasi penampang: kompak, non-kompak, langsing (SNI Tabel B4.1)
- Kapasitas lentur Mn: yielding + LTB (SNI F2)
- Kapasitas geser Vn (SNI G2)
- Kapasitas aksial tekan Pn: Euler + inelastic buckling (SNI E3)
- Kapasitas aksial tarik Tn: yielding + fracture (SNI D2)
- Interaksi aksial-momen: H1-1a / H1-1b (SNI H1)
- Defleksi: L/360 (LL), L/240 (total)

### Struktur Data

```python
@dataclass
class SteelDesignInput:
    element_id: str
    section: SectionProperties  # dari kernel
    material: Material          # dari kernel
    Lb_m: float                 # unbraced length untuk LTB
    K: float                    # faktor panjang efektif kolom
    Pu_kn: float; Mux_knm: float; Muy_knm: float
    Vux_kn: float; Vuy_kn: float

@dataclass
class SteelCheckResult:
    element_id: str
    phi_Pn_c_kn: float; phi_Pn_t_kn: float
    phi_Mn_x_knm: float; phi_Vn_kn: float
    axial_ratio: float; moment_ratio: float
    shear_ratio: float; interaction_ratio: float
    status: str   # "AMAN" | "TIDAK AMAN"
    compactness: str
    LTB_mode: str
    Fcr_kn_m2: float
```

### Modul Backend

```
app/calculation/steel/
├── section_classifier.py
├── flexure_check.py
├── shear_check.py
├── compression_check.py
├── tension_check.py
├── interaction_check.py
├── deflection_check.py
└── steel_designer.py
```

### Unit Test

```python
# Referensi: AISC Steel Construction Manual 16th Ed. Design Examples

# Test: WF 400×200, Fy=250 MPa, Lb=0 (fully braced)
# φMn = 0.9 × Fy × Zx

# Test: KL/r = 100 → Fcr = 0.877·Fe (inelastic range)

# Test: H1-1a: Pu/φPn = 0.6, Mu/φMn = 0.3
# ratio = 0.6/2 + 0.3 = 0.6 < 1.0 → AMAN
```

---

## Tahap 13 — Concrete Design Check (SNI 2847:2019)

### Tujuan
Pemeriksaan kapasitas elemen beton bertulang.

### Fitur
- Kapasitas lentur Mn: strain compatibility, blok tekan persegi ekivalen
- Kapasitas geser Vn = Vc + Vs (SNI 22.5)
- Diagram interaksi P-M untuk kolom (strain sweep)
- ρ_min, ρ_max, spasi minimum tulangan

**Diagram interaksi kolom:**
```python
# Sweep strain profile: εc_top dari εcu ke εt_max
# Untuk setiap c: hitung P dan M terhadap centroid
# Hasilnya: kurva P-M yang dapat diplot dan dicek terhadap (Pu, Mu)
```

### Modul Backend

```
app/calculation/concrete/
├── beam_flexure.py
├── beam_shear.py
├── column_interaction.py
├── reinforcement_limits.py
└── concrete_designer.py
```

### Unit Test

```python
# Test: Kolom dengan P=0 → Mn harus sama dengan beam flexure calculator

# Test: Pure compression → P0 = 0.85·fc'·(Ag-Ast) + fy·Ast

# Test: Konsistensi dengan existing beam calculator (Tahap sebelumnya)
```

---

## Tahap 14 — Seismic Design Check (SNI 1726:2019)

### Tujuan
Pemeriksaan desain struktur tahan gempa lengkap.

### Fitur
- Kategori desain seismik (KDS) dari SDS, SD1, Ie
- Base shear: Cs × W, distribusi Fx per lantai
- Story drift: δx = Cd·δxe/Ie, cek Δ/h ≤ Δa
- Irregularity check: mass, stiffness, geometric
- Strong column — weak beam (SRPMK): ΣMpc ≥ 1.2·ΣMpb
- P-Delta stability index: θ ≤ 0.10

### Modul Backend

```
app/calculation/seismic/
├── site_coefficients.py
├── design_spectrum_sni.py
├── seismic_category.py
├── base_shear.py
├── story_drift.py
├── irregularity_checker.py
├── scwb_checker.py
└── seismic_designer.py
```

### Unit Test

```python
# Test: Bandung — Ss=0.60g, S1=0.20g, Site D
# Fa=1.2, Fv=1.8, SDS=0.48g, SD1=0.24g

# Test: Distribusi lateral — verifikasi Cvx dan Fx manual

# Test: Drift amplifikasi: δx = Cd·δxe/Ie
```

---

## Tahap 15 — Full Report Generation

### Tujuan
Mengintegrasikan semua tahap ke dalam laporan engineering lengkap yang dapat diaudit.

### Fitur
- Laporan analisis, desain, dan seismik dalam satu dokumen
- Export HTML (preview) + PDF (distribusi)
- Setiap laporan menyimpan snapshot immutable dengan traceability penuh
- Disclaimer wajib di setiap halaman

### Struktur Laporan (28 halaman)

```
Hal. 1    : Cover + disclaimer
Hal. 2    : Daftar isi + traceability summary (version, timestamp, user)
Hal. 3-4  : Identitas proyek
Hal. 5    : Parameter material
Hal. 6    : Model struktur (screenshot + statistik)
Hal. 7-8  : Load cases + kombinasi yang digunakan (dari DB snapshot)
Hal. 9-12 : Hasil analisis (displacement, reaksi, gaya dalam envelope)
Hal. 13-14: Diagram N, V, M
Hal. 15-16: Deformed shape
Hal. 17-18: Modal analysis (frekuensi, mass participation)
Hal. 19-20: Response spectrum analysis
Hal. 21-24: Steel/concrete design check (tabel utilisasi)
Hal. 25-26: Seismic design check
Hal. 27   : Assumptions & warnings dari AnalysisTrace
Hal. 28   : Disclaimer + kolom tanda tangan engineer struktur
```

**Disclaimer yang wajib muncul di footer setiap halaman:**
```
AG-SAS v{version} — Engineering Calculation Assistant.
Hasil ini wajib diperiksa dan disetujui oleh engineer struktur berwenang
sebelum digunakan dalam dokumen perencanaan resmi.
```

### Modul Backend

```
app/reporting/
├── templates/
│   ├── full_report.html
│   ├── analysis_only.html
│   └── design_only.html
├── html_renderer.py
├── pdf_generator.py
├── screenshot_generator.py    # Playwright headless untuk 3D viewer
└── report_orchestrator.py     # Koordinasi semua bagian
```

---

## Tahap 16 — 3D Frame Analysis

### Tujuan
Ekstensi solver ke ruang 3D setelah seluruh ekosistem 2D stabil dan terverifikasi.

### Mengapa 3D di Tahap 16?

Pada saat Tahap 16 dimulai:
- Kernel sudah stabil (Tahap 0)
- 2D solver sudah terverifikasi secara ketat (Tahap 2)
- Sparse solver, load system, boundary conditions, load combination engine sudah ada (Tahap 3-6)
- Diagram, deformed shape, modal, RSA, P-Delta sudah ada (Tahap 7-11)
- Design check sudah ada (Tahap 12-14)
- Report engine sudah ada (Tahap 15)

Artinya: 3D Frame Analysis hanya perlu menambahkan stiffness matrix 12×12, transformation 3D, dan recovery gaya dalam 3D. Semua infrastruktur lainnya **sudah ada dan bisa langsung dipakai** tanpa modifikasi besar.

### Fitur
- Elemen balok-kolom 3D: 12 DOF per elemen (6 DOF × 2 node)
- Transformation matrix T (12×12): direction cosine matrix 3D
- Output: 6 displacement + 6 reaksi per node, N/Vy/Vz/Mx/My/Mz per elemen
- Penanganan kolom vertikal: local_z default = [1, 0, 0] untuk menghindari singularity

**Direction cosine matrix:**
```python
def direction_cosines_3d(node_i, node_j, local_z=None):
    # x_local = unit vector I→J
    # Untuk kolom vertikal (x_local ≈ [0,1,0]):
    #   gunakan local_z = [1, 0, 0] bukan [0, 0, 1]
    #   karena cross([0,1,0], [0,0,1]) = [1,0,0] → tidak singular
    # y_local = normalize(cross(z_local, x_local))
    # z_local = cross(x_local, y_local)
    # Ref: McGuire et al. §9.2
```

### Validasi 2D-3D Identity

```python
# Test kritis: Model 2D dimasukkan ke solver 3D (z=0, tidak ada Fz/Mx/My)
# Hasil ux, uy, rz harus identik dengan solver 2D
# Ini adalah gate test sebelum Tahap 16 dinyatakan selesai
```

### Validasi Benchmark 3D

| Contoh | Sumber | Target |
|--------|--------|--------|
| Space frame McGuire Ex.9.2 | "Matrix Structural Analysis" 2nd Ed. | < 0.1% |
| Grillage 3D | Bathe "FEM Procedures" Example | < 0.5% |
| 3D building frame | SAP2000 tutorial (sebagai pembanding) | dokumentasi perbedaan |

---

## Verification & Validation — Kerangka Umum

### Hierarki Sumber Kebenaran

```
Tingkat 1 (tertinggi): Derivasi matematika/fisika dari prinsip pertama
Tingkat 2: Textbook dengan solusi analitik (Timoshenko, Roark's, McGuire)
Tingkat 3: Software komersial terverifikasi (SAP2000, ETABS) — sebagai pembanding
Tingkat 4: Software open-source (OpenSEES, FEniCS) — sebagai pembanding tambahan
```

SAP2000 dan ETABS ada di Tingkat 3 — **pembanding, bukan sumber kebenaran tunggal**. Jika ada perbedaan antara AG-SAS dan SAP2000, investigasi dimulai dari Tingkat 1 dan 2.

### Toleransi Error Numerik

| Tipe analisis | Sumber referensi | Toleransi maksimum |
|---------------|------------------|--------------------|
| Linear elastic (closed-form tersedia) | Textbook analitik | 0.01% |
| Linear elastic (multi-element) | Textbook numerik | 0.1% |
| Modal analysis (frekuensi) | Textbook | 1% |
| Response spectrum | Cross-software | 5% |
| P-Delta | Cross-software | 2% |
| Steel design check | AISC Design Examples | 0.5% |
| Concrete design check | Perhitungan manual | 0.5% |

### Regression Test Otomatis

```
CI Pipeline (GitHub Actions / sejenisnya):
  1. Setiap push ke branch → jalankan unit tests
  2. Setiap push ke main → jalankan full benchmark suite
  3. Jika ada benchmark yang gagal → block merge
  4. Weekly: jalankan extended benchmark suite (lebih banyak kasus)
  5. Laporan regression disimpan sebagai artifact CI
```

### Dokumentasi Verifikasi

Setiap benchmark case mendokumentasikan:
- Sumber referensi (judul buku, edisi, nomor contoh, halaman)
- Parameter input
- Hasil yang diharapkan (dari referensi)
- Hasil AG-SAS
- % error
- Tanggal terakhir diverifikasi
- Status: PASS / FAIL / KNOWN-DEVIATION (dengan penjelasan)

File lokasi: `docs/verification/`

---

## Timeline & Milestone (Revisi)

| Tahap | Estimasi Durasi | Dependensi | Output Kunci |
|-------|----------------|------------|--------------|
| 0 — Kernel | 1 minggu | — | Semua tipe dasar, konvensi, traceability |
| 1 — 2D Frame | 2 minggu | Tahap 0 | `analyze_frame_2d()` + API |
| 2 — V&V Framework | 2 minggu | Tahap 1 | 12 benchmark lulus, CI regression |
| 3 — Core Infra | 1 minggu | Tahap 2 | Sparse solver, validator |
| 4 — Member Load | 1 minggu | Tahap 3 | FEF semua tipe |
| 5 — Boundary Conditions | 1 minggu | Tahap 4 | Spring, hinge, settlement |
| 6 — Load Combination | 2 minggu | Tahap 5 | DB-driven engine, admin UI |
| 7 — Diagrams N,V,M | 2 minggu | Tahap 6 | DiagramViewer |
| 8 — Deformed Shape | 1 minggu | Tahap 7 | Animasi deformasi |
| 9 — Modal Analysis | 2 minggu | Tahap 3 | Frekuensi + mode shapes |
| 10 — RSA | 2 minggu | Tahap 9 | CQC + SNI spectrum |
| 11 — P-Delta | 2 minggu | Tahap 6 | Newton-Raphson iterative |
| 12 — Steel Design | 2 minggu | Tahap 6 | Design check per elemen |
| 13 — Concrete Design | 2 minggu | Tahap 6 | P-M diagram + check |
| 14 — Seismic Design | 2 minggu | Tahap 10 | Full seismic check |
| 15 — Full Report | 2 minggu | Tahap 7,8,12,13,14 | Engineering report PDF |
| 16 — 3D Frame | 3 minggu | Tahap 15 | `analyze_frame_3d()` |

**Total estimasi:** ~31 minggu (~8 bulan) untuk implementasi lengkap

---

## MVP Rekomendasi (16 Minggu)

```
Tahap 0 → 1 → 2 → 3 → 4 → 6 → 7 → 8 → 12 → 13 → 15
```

**Konten MVP:**
- 2D frame analysis (nodal load + member load)
- Load combination engine (rule-based, database-driven, SNI 1727:2020 seeded)
- Diagram N, V, M
- Deformed shape dengan animasi
- Steel design check dasar (Mn, Vn, interaction)
- Concrete design check dasar (Mn, Vn)
- PDF report dengan traceability penuh
- Verification test cases — semua 12 benchmark lulus

**Batas penggunaan MVP:**

MVP 16 minggu **cukup untuk validasi internal, pembelajaran, studi awal, dan perhitungan pendamping**. Hasil yang dihasilkan tetap merupakan hasil perangkat lunak dalam pengembangan yang wajib diperiksa dan diverifikasi oleh engineer struktur berwenang sebelum digunakan dalam dokumen perencanaan, perhitungan resmi, atau gambar konstruksi. AG-SAS bukan pengganti penilaian profesional engineer.

---

## Dependency Stack

```
Backend (Python):
├── numpy >= 1.24          # Dense matrix, eigenvalue
├── scipy >= 1.11          # Sparse solver (spsolve, eigsh)
├── jinja2 >= 3.1          # Report template
├── reportlab >= 4.2       # PDF generation
└── playwright >= 1.40     # Screenshot 3D viewer (Tahap 15)

Frontend (TypeScript):
├── @react-three/fiber     # 3D viewer
├── @react-three/drei      # 3D utilities
├── three                  # WebGL
├── recharts               # Diagram N,V,M 2D
└── @tanstack/react-query  # API state management
```

---

## Catatan Validasi Cross-Software

| Software | Status | Digunakan untuk | Posisi dalam hierarki |
|----------|--------|-----------------|-----------------------|
| SAP2000 (trial) | Gratis 14 hari | Linear analysis, modal, RSA | Pembanding (Tingkat 3) |
| ETABS (demo) | Gratis demo | Building, seismik | Pembanding (Tingkat 3) |
| OpenSEES | Open source | Nonlinear, P-Delta | Pembanding (Tingkat 4) |
| Timoshenko "Strength of Materials" | Publik | Closed-form beam solutions | Referensi primer (Tingkat 2) |
| Roark's "Formulas for Stress and Strain" | Tersedia | Beam formulas | Referensi primer (Tingkat 2) |
| McGuire, Gallagher, Ziemian "MSA 2nd Ed." | Tersedia | Frame analysis | Referensi primer (Tingkat 2) |
| AISC Steel Construction Manual 16th Ed. | Tersedia | Steel design examples | Referensi primer (Tingkat 2) |
| Cook "Concepts and Applications of FEA" | Tersedia | Mass matrix, dynamics | Referensi primer (Tingkat 2) |

---

*Dokumen ini adalah panduan teknis hidup. Setiap implementasi harus memperbarui status dan menambahkan catatan verifikasi di sini. Versi dokumen ditingkatkan setiap kali ada perubahan substantif pada roadmap.*
