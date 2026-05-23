# Catatan Perhitungan: Diagram Gaya Dalam 2D Frame

**Versi:** 1.0  
**Tanggal:** 2026-05-23  
**Referensi:** McGuire, Gallagher & Ziemian — *Matrix Structural Analysis*, 2nd Ed.

---

## 1. Konvensi Tanda (Sign Convention)

Mengikuti konvensi McGuire MSA §3.2:

| Gaya | Positif |
|------|---------|
| N (Aksial) | Tarik (tension) |
| Vy (Geser) | Ke atas pada muka kiri (left face upward) |
| Mz (Momen) | Sagging (tarik sisi bawah) |

**Catatan implementasi:** Gaya ujung elemen `Q_local` dari matriks kekakuan merupakan gaya yang **elemen berikan pada node**. Momen lentur internal pada penampang menggunakan tanda `-Mz_i` pada posisi x=0 (lihat Bagian 4).

---

## 2. Komponen Beban Terbagi Merata (UDL) dalam Koordinat Lokal

Untuk elemen dengan sudut θ (diukur dari sumbu X global), dan UDL q (kN/m, positif = ke bawah dalam Y global):

Vektor UDL global: **q_global** = (0, −q)

Komponen lokal:
- Aksial: `q_axial = q_global · (cos θ, sin θ) = −q·sin θ`
- Transversal: `q_trans = q_global · (−sin θ, cos θ) = −q·cos θ`

Untuk balok horizontal (θ = 0°): q_axial = 0, q_trans = −q (ke bawah dalam koordinat lokal).

---

## 3. Rumus Gaya Dalam Sepanjang Elemen

Pada posisi x dari node-i (0 ≤ x ≤ L):

```
N(x)  =  N_i  + q_axial · x
V(x)  =  Vy_i + q_trans · x
M(x)  = −Mz_i + Vy_i · x  +  ½ · q_trans · x²
```

**Catatan tanda M:** Tanda negatif pada Mz_i muncul karena Q_local[2] merupakan momen yang elemen berikan kepada node-i (searah jarum jam jika M_internal positif/sagging), sedangkan konvensi gaya internal menggunakan tanda berlawanan pada muka kiri.

Verifikasi untuk balok sederhana (SSB) dengan UDL q, L = 5 m, q = 20 kN/m:
- Vy_i = +50 kN (reaksi), Mz_i = 0 (sendi)
- M(2.5) = 0 + 50×2.5 + ½(−20)(2.5²) = 125 − 62.5 = **62.5 kN·m** = qL²/8 ✓
- V(0) = 50 kN ✓, V(5) = 50 − 100 = −50 kN ✓

---

## 4. Bentuk Deformasi (Hermite Shape Functions)

Untuk interpolasi perpindahan transversal sepanjang elemen (ξ = x/L):

| Fungsi | Formula |
|--------|---------|
| H₁(ξ) | 1 − 3ξ² + 2ξ³ |
| H₂(ξ) | L·ξ·(1−ξ)² |
| H₃(ξ) | 3ξ² − 2ξ³ |
| H₄(ξ) | L·ξ²·(ξ−1) |

```
v(x) = H₁·v_i + H₂·θ_i + H₃·v_j + H₄·θ_j   (transversal lokal)
u(x) = (1−ξ)·u_i + ξ·u_j                       (aksial lokal, linear)
```

Konversi ke koordinat global (θ = sudut elemen):
```
Δx_global = cos θ · u(x) − sin θ · v(x)
Δy_global = sin θ · u(x) + cos θ · v(x)
```

Posisi deformasi (dengan faktor skala `s`):
```
x_def = x_undef + s · Δx_global
y_def = y_undef + s · Δy_global
```

---

## 5. Offset Diagram pada Bidang SVG

Diagram N, V, M digambarkan tegak lurus terhadap sumbu elemen. Arah normal elemen (dari i ke j):

**n** = (−sin θ, cos θ)   *(ke "kiri" saat berjalan dari i ke j)*

Titik diagram pada posisi x dengan nilai F:

```
gx_diagram = gx_elemen(x) + F · scale_px · (−sin θ)
gy_diagram = gy_elemen(x) + F · scale_px · (cos θ)
```

Di mana `scale_px` adalah faktor piksel per satuan gaya (disesuaikan dengan nilai maksimum global agar diagram proporsional).

---

## 6. Implementasi

File: `backend/app/postprocessing/frame2d/diagram_data.py`

Fungsi utama:
- `compute_diagram_data(nodes, elements, element_forces, displacements, n_points=21, deformation_scale=100.0)`
- `diagram_data_to_dict(data: StructureDiagramData) → dict`

Unit test: `backend/tests/postprocessing/test_frame2d_diagrams.py` — 31 tes, semua lulus.

---

## 7. Batasan

- Hanya berlaku untuk analisis **linear elastik** (small displacement).
- Faktor deformasi (`deformation_scale`) bersifat visual saja — bukan nilai fisik sebenarnya.
- Tidak mempertimbangkan efek P-delta atau non-linearitas.
