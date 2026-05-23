# Catatan Formula: Desain Lentur Balok Baja WF

**Standar:** SNI 1729:2020 — Spesifikasi untuk Bangunan Gedung Baja Struktural  
**Modul:** `backend/app/calculation/steel/beam_calculator.py`  
**Formula Version:** 1.1.0  
**Metode:** Load and Resistance Factor Design (LRFD)  
**Lingkup:** Profil WF/H-Beam, bentang sederhana, beban merata seragam, Lb ≤ Lp (LTB tidak mengontrol)

---

## 1. Berat Sendiri Profil

```
SW = W × g / 1000                               [konversi kg/m → kN/m]
   = W × 9.81 / 1000
```

| Simbol | Keterangan | Satuan |
|--------|-----------|--------|
| `W` | Berat profil per meter | kg/m |
| `SW` → `self_weight_knm` | Berat sendiri | kN/m |

---

## 2. Kombinasi Beban Terfaktor

```
U = 1.2 × (wD + SW) + 1.6 × wL                [SNI 1727:2020 Pasal 5.3.1c]
```

Beban mati total mencakup beban mati eksternal ditambah berat sendiri profil.

---

## 3. Momen Ultimit

```
Mu = wu × L² / 8                               [Statika dasar, balok sederhana]
```

---

## 4. Cek Kelangsingan Sayap (SNI 1729:2020 Tabel B4.1b)

Untuk sayap profil I simetris ganda dalam lentur:

```
λ_f  = (b/2) / tf                              [rasio kelangsingan sayap]
λ_pf = 0.38 × √(E / Fy)                       [batas kompak]
λ_rf = 1.0  × √(E / Fy)                       [batas tidak kompak / slender]
```

| Kondisi | Klasifikasi |
|---------|------------|
| λ_f ≤ λ_pf | Kompak (compact) |
| λ_pf < λ_f ≤ λ_rf | Tidak kompak (noncompact) |
| λ_f > λ_rf | Langsing (slender) |

**Nilai E:** 200,000 MPa (Modulus elastisitas baja)  
**Catatan:** Modul ini tidak menangani penampang slender (λ_f > λ_rf).

---

## 5. Momen Plastis Mp

```
Mp = Fy × Zx                                   [SNI 1729:2020 Persamaan F2-1]
```

Zx (modulus plastis) dalam cm³ dikonversi ke mm³: × 1000

---

## 6. Momen Nominal Mn

### Penampang Kompak (λ_f ≤ λ_pf) + Lb ≤ Lp

```
Mn = Mp                                         [SNI 1729:2020 Pasal F2.1]
```

Tidak ada reduksi karena LTB maupun local buckling sayap.

### Penampang Tidak Kompak (λ_pf < λ_f ≤ λ_rf)

```
Mn = Mp − (Mp − 0.7 × Fy × Sx) × (λ_f − λ_pf) / (λ_rf − λ_pf)
                                               [SNI 1729:2020 Persamaan F3-1]
```

Interpolasi linier antara Mp (saat kompak) dan 0.7FySx (saat batas tidak kompak).

---

## 7. Momen Desain Tereduksi

```
φMn = φ × Mn    dengan φ = 0.90               [SNI 1729:2020 Pasal B3.4a]
```

---

## 8. Cek Kapasitas

```
capacity_ratio = Mu / φMn

status = AMAN       jika Mu ≤ φMn
status = TIDAK_AMAN  jika Mu > φMn
```

---

## Asumsi Penting

1. **Lb ≤ Lp** — Tekuk lateral-torsi (Lateral-Torsional Buckling) diasumsikan tidak mengontrol. Harus diverifikasi berdasarkan jarak pengekang lateral aktual di lapangan.
2. **Badan kompak** — Hanya kelangsingan sayap yang dicek. Verifikasi kelangsingan badan dilakukan terpisah jika diperlukan.
3. **Penampang tidak slender** — Modul tidak menangani λ_f > λ_rf.
4. **Geser dan lendutan** tidak dicek di modul ini.

---

## Referensi Pasal

| Topik | Pasal SNI |
|-------|-----------|
| Kombinasi beban LRFD | SNI 1727:2020 Pasal 5.3.1c |
| Faktor reduksi φ = 0.90 untuk lentur | SNI 1729:2020 Pasal B3.4a |
| Batas kelangsingan elemen tekan | SNI 1729:2020 Tabel B4.1b |
| Mn kompak (Lb ≤ Lp) | SNI 1729:2020 Pasal F2.1 |
| Mn tidak kompak (local buckling sayap) | SNI 1729:2020 Persamaan F3-1 |
| Modulus elastisitas E = 200,000 MPa | SNI 1729:2020 Pasal A3.2 |
