# Benchmark Cases AG-SAS

> **Disclaimer:** AG-SAS adalah engineering calculation assistant.
> Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.

---

## Daftar Benchmark

| ID | Judul | Tipe | Level | Solver Tersedia |
|----|-------|------|-------|-----------------|
| `ssb_udl_01` | Simply Supported Beam — UDL | Balok 2D | L1 Analitik | Ya (formula) |
| `cant_pl_01` | Cantilever — Point Load at Tip | Balok 2D | L1 Analitik | Ya (formula) |
| `portal_2d_01` | Portal 2D — Lateral Load, Fixed Base | Portal 2D | L2 Textbook | Sebagian (statics) |
| `truss_2d_01` | Truss Segitiga — Point Load at Apex | Truss 2D | L1 Analitik | Ya (method of joints) |

---

## SSB-UDL-01: Simply Supported Beam, Uniformly Distributed Load

### Deskripsi Problem

```
    w = 20 kN/m (merata sepanjang bentang)
    ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
    ●══════════════════════●
    △                      ○
    (pin)                (roller)
    ←──────── L = 6 m ────────→
```

**Material/Profil:** Baja, WF 400×200×8×13  
**E** = 200 000 MPa = 2 × 10⁸ kN/m²  
**I** = 237 × 10⁶ mm⁴ = 2.370 × 10⁻⁴ m⁴  
**EI** = 200 000 000 × 2.370 × 10⁻⁴ = 47 400 kN·m²

### Solusi Analitik (Euler-Bernoulli)

| Besaran | Formula | Hasil |
|---------|---------|-------|
| Defleksi tengah bentang | δ = 5wL⁴ / (384EI) | 11.392 mm |
| Momen maksimum | M_max = wL² / 8 | 90.0 kN·m |
| Reaksi tiap tumpuan | R = wL / 2 | 60.0 kN |
| Geser maksimum | V_max = wL / 2 | 60.0 kN |

### Derivasi

```
Defleksi maksimum (tengah bentang):
  δ = 5 × 20 × 6⁴ / (384 × 47 400)
  δ = 5 × 20 × 1296 / 18 201 600
  δ = 129 600 / 18 201 600
  δ = 0.007121 m = 11.39 mm  ✓

Momen maksimum (tengah bentang):
  M = w × L² / 8 = 20 × 36 / 8 = 90 kN·m  ✓
```

**Referensi:** Hibbeler, R.C. — Structural Analysis 10th Ed., App. C, Case 2.

---

## CANT-PL-01: Cantilever Beam, Point Load at Free End

### Deskripsi Problem

```
    (jepit)                  (bebas)
    ▓─────────────────────── ●
    ▓  L = 4 m               ↓ P = 50 kN
```

**Profil:** WF 400×200×8×13, E = 200 GPa, I = 237 × 10⁶ mm⁴  
**EI** = 200 000 000 × 2.370 × 10⁻⁴ = 47 400 kN·m²

### Solusi Analitik (Euler-Bernoulli)

| Besaran | Formula | Hasil |
|---------|---------|-------|
| Defleksi ujung bebas | δ = PL³ / (3EI) | 22.532 mm |
| Rotasi ujung bebas | θ = PL² / (2EI) | 8.449 × 10⁻³ rad |
| Momen di jepit | M_fix = P × L | 200.0 kN·m |
| Geser (konstan) | V = P | 50.0 kN |

### Derivasi

```
Defleksi ujung bebas:
  δ = 50 × 4³ / (3 × 47 400)
  δ = 50 × 64 / 142 200
  δ = 3200 / 142 200
  δ = 0.022504 m = 22.50 mm  ✓

Rotasi ujung bebas:
  θ = 50 × 4² / (2 × 47 400)
  θ = 50 × 16 / 94 800
  θ = 800 / 94 800
  θ = 0.008439 rad  ✓
```

**Referensi:** Hibbeler — Structural Analysis 10th Ed., App. C, Case 6.

---

## PORTAL-2D-01: Simple Portal Frame, Lateral Load

### Deskripsi Problem

```
         H = 30 kN →
         ┌──────────────────────┐  ← balok (EIb = 2×EIc)
         │                      │
    h=4m │                      │ h=4m
         │                      │
        ▓▓                     ▓▓
      (jepit)               (jepit)
         ←──── b = 6 m ────→
```

### Nilai dari Keseimbangan Statis (Eksak)

| Besaran | Formula | Hasil |
|---------|---------|-------|
| Geser tiap kolom | V_col = H/2 | 15.0 kN |
| Reaksi horizontal kiri | R_Hx = H/2 | 15.0 kN |
| Reaksi horizontal kanan | R_Hx = H/2 | 15.0 kN |
| Reaksi vertikal | R_v = H×h/b | 20.0 kN |
| Defleksi lateral (batas atas, balok kaku) | δ = Hh³/(12EIc) | ~3.37 mm |

### Catatan

- Reaksi horizontal dan vertikal diperoleh dari keseimbangan statis — tidak memerlukan solver FEM.
- Defleksi lateral adalah **batas atas** (asumsi balok infinitely stiff).
  Nilai aktual dengan balok finite stiffness akan lebih besar.
- Momen di kaki kolom dan pertemuan kolom-balok memerlukan solver FEM atau slope-deflection method.

**Referensi:** Kassimali, A. — Structural Analysis 5th Ed., Ch. 12.

---

## TRUSS-2D-01: Simple 2D Truss, Symmetric Triangle

### Deskripsi Problem

```
            N3 (2, 2)
           /  ↓P=40kN
          /          \
         /             \
        N1 (0,0) ----- N2 (4,0)
        (sendi)         (rol)
        ←── span = 4m ──→
              rise = 2m
```

**Batang:**
- M1: N1–N3 (diagonal kiri)
- M2: N3–N2 (diagonal kanan)
- M3: N1–N2 (batang bawah / tie rod)

### Solusi Method of Joints

```
θ = arctan(rise/(span/2)) = arctan(2/2) = 45°

Di joint N3 (beban P↓):
  ΣFy = 0: F_M1×sin45 + F_M2×sin45 = P
  ΣFx = 0: F_M1×cos45 = F_M2×cos45  → F_M1 = F_M2
  → F_M1 = F_M2 = P/(2×sin45) = 40/(2×0.7071) = 28.284 kN TEKAN

Di joint N1 (sendi):
  ΣFy = 0: R_N1 - F_M1×sin45 = 0 → R_N1 = 20 kN  ✓
  ΣFx = 0: F_tie - F_M1×cos45 = 0 → F_tie = 20 kN TARIK
```

| Besaran | Nilai | Tipe |
|---------|-------|------|
| Reaksi N1 vertikal | 20.0 kN | — |
| Reaksi N2 vertikal | 20.0 kN | — |
| Reaksi N1 horizontal | 0.0 kN | — |
| Gaya batang M1 | −28.284 kN | Tekan |
| Gaya batang M2 | −28.284 kN | Tekan |
| Gaya batang M3 | +20.0 kN | Tarik |

**Konvensi:** N+ = tarik (tension), N− = tekan (compression)

**Referensi:** Hibbeler — Structural Analysis 10th Ed., Ch. 6, Method of Joints.

---

## Rencana Benchmark Berikutnya

| ID | Deskripsi | Level | Prasyarat |
|----|-----------|-------|-----------|
| `ssb_pl_01` | Simply supported beam, point load mid-span | L1 | — |
| `ssb_fixed_01` | Fixed-fixed beam, UDL | L1 | — |
| `portal_2d_02` | Portal 2D + gravitasi, balok finite stiffness | L2 | FEM solver |
| `truss_2d_02` | Pratt truss 4-panel | L1 | — |
| `frame_3d_01` | Portal 3D sederhana, beban gravitasi | L2 | 3D FEM solver |
| `ssb_dynamic_01` | Frekuensi natural balok sederhana | L1 | Eigenvalue solver |

---

## Catatan Umum

1. Semua defleksi dalam benchmark menggunakan teori **Euler-Bernoulli**
   (shear deformation diabaikan). Untuk profil tinggi atau bentang pendek,
   perbedaan dengan teori Timoshenko bisa signifikan.

2. Material diasumsikan **linear elastis** — tidak ada plastisitas.

3. Semua analisis bersifat **first-order** — efek P-Delta tidak diperhitungkan.

4. Benchmark ini valid untuk **unit sistem internal AG-SAS**:
   kN, m, kN·m, kN/m².
