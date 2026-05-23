# Sistem Satuan AG-SAS

> **Disclaimer:** AG-SAS adalah engineering calculation assistant.
> Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.

---

## Prinsip Umum

AG-SAS menggunakan **satu set satuan internal yang konsisten** di seluruh
solver. Konversi terjadi **di batas sistem** — saat input dari pengguna
masuk dan saat output ditampilkan. Solver tidak pernah menerima satuan
campuran.

---

## Satuan Internal Solver

| Kuantitas                | Satuan Internal | Simbol   |
|--------------------------|-----------------|----------|
| Panjang                  | meter           | m        |
| Gaya                     | kilonewton      | kN       |
| Momen / Torsi            | kilonewton-meter| kN·m     |
| Tegangan / Modulus Elastis | kilonewton per meter persegi | kN/m² |
| Massa jenis              | kilogram per meter kubik | kg/m³ |
| Luas penampang           | meter persegi   | m²       |
| Momen inersia luas       | meter pangkat empat | m⁴   |
| Modulus penampang        | meter kubik     | m³       |
| Massa                    | kilogram        | kg       |
| Sudut                    | radian          | rad      |

---

## Satuan Antarmuka (Interface Units)

Satuan yang umum digunakan pengguna dan yang ditampilkan di UI:

| Kuantitas              | Satuan Antarmuka | Konversi ke Internal         |
|------------------------|------------------|------------------------------|
| Dimensi penampang      | mm               | ÷ 1 000 → m                  |
| Luas penampang         | cm² atau mm²     | cm² ÷ 10 000 → m²            |
| Momen inersia          | cm⁴ atau mm⁴     | cm⁴ ÷ 100 000 000 → m⁴       |
| Modulus penampang      | cm³ atau mm³     | cm³ ÷ 1 000 000 → m³         |
| Tegangan / kuat        | MPa              | × 1 000 → kN/m²              |
| Displacement output    | mm               | × 1 000 ← m                  |

---

## Modul Konversi

Semua fungsi konversi tersedia di:

```python
from app.engineering_kernel.units.converters import (
    mm_to_m, m_to_mm,
    cm_to_m, m_to_cm,
    n_to_kn, kn_to_n,
    mpa_to_kn_m2, kn_m2_to_mpa,
    mm2_to_m2, cm2_to_m2,
    mm4_to_m4, cm4_to_m4,
    mm3_to_m3, cm3_to_m3,
    deg_to_rad, rad_to_deg,
)
```

---

## Contoh Konversi

### Dimensi Profil WF 400×200×8×13

```
H  = 400 mm → 0.400 m
bf = 200 mm → 0.200 m
tw =   8 mm → 0.008 m
tf =  13 mm → 0.013 m
```

### Properti Penampang

```
A  = 8 412 mm²     → 8.412 × 10⁻³ m²
Ix = 237 000 000 mm⁴ → 2.370 × 10⁻⁴ m⁴
Zx = 1 190 000 mm³  → 1.190 × 10⁻³ m³
```

### Material BJ41

```
fy = 250 MPa   → 250 000 kN/m²
E  = 200 000 MPa → 200 000 000 kN/m²  (= 2 × 10⁸ kN/m²)
```

---

## Enum Satuan

```python
from app.engineering_kernel.units.enums import (
    LengthUnit,      # MM, CM, M
    ForceUnit,       # N, KN
    MomentUnit,      # N_MM, N_M, KN_M
    StressUnit,      # PA, KPA, MPA, KN_M2
    MassUnit,        # KG, TON
    DensityUnit,     # KG_M3, KN_M3
    AngleUnit,       # DEG, RAD
)
```

---

## Kelas Quantity

Untuk nilai yang perlu membawa informasi satuannya:

```python
from app.engineering_kernel.units.quantity import Quantity
from app.engineering_kernel.units.enums import ForceUnit

gaya = Quantity(value=50.0, unit=ForceUnit.KN)
assert gaya.is_positive()
assert not gaya.is_zero()
```

`Quantity` adalah frozen dataclass — immutable setelah dibuat.

---

## Aturan Implementasi

1. **Jangan memasukkan nilai bersatuan MPa ke variabel yang mengharapkan kN/m².**
   Selalu konversi eksplisit di titik masuk.

2. **Jangan menyimpan satuan di dalam struct solver.**
   Semua field numerik di `Node`, `Element`, `Material`, `SectionProperties`
   diasumsikan dalam satuan internal. Satuannya tersirat dari nama field
   (misalnya `x_m`, `E_kn_m2`, `A_m2`).

3. **Gunakan nama field yang mengandung satuan** untuk menghindari ambiguitas:
   - `x_m` bukan `x`
   - `E_kn_m2` bukan `E`
   - `A_m2` bukan `A`
   - `Ix_m4` bukan `Ix`

4. **Konversi untuk output UI** dilakukan di layer API/serializer,
   bukan di solver.
