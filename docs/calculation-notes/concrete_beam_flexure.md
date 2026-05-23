# Catatan Formula: Desain Lentur Balok Beton Bertulang

**Standar:** SNI 2847:2019 — Persyaratan Beton Struktural untuk Bangunan Gedung  
**Modul:** `backend/app/calculation/concrete/beam_calculator.py`  
**Formula Version:** 1.1.0  
**Metode:** Kuat Batas (Strength Design / LRFD)  
**Lingkup:** Singly reinforced rectangular beam, simply supported, beban merata seragam

---

## 1. Kombinasi Beban Terfaktor

```
U = 1.2 × wD + 1.6 × wL                         [SNI 1727:2020 §5.3.1c]
```

| Simbol | Keterangan | Satuan |
|--------|-----------|--------|
| `U` → `wu` | Beban terfaktor | kN/m |
| `wD` | Beban mati merata | kN/m |
| `wL` | Beban hidup merata | kN/m |

---

## 2. Gaya Dalam Balok Sederhana

```
Mu = wu × L² / 8                                 [Statika dasar]
Vu = wu × L / 2
```

| Simbol | Keterangan | Satuan |
|--------|-----------|--------|
| `Mu` | Momen lentur terfaktor | kN·m |
| `Vu` | Gaya geser terfaktor | kN |
| `L` | Panjang bentang | m |

---

## 3. Kedalaman Efektif

```
d = h - cc - Øs - Ø/2
```

| Simbol | Keterangan | Satuan |
|--------|-----------|--------|
| `d` | Kedalaman efektif | mm |
| `h` | Tinggi total penampang | mm |
| `cc` | Selimut beton bersih | mm |
| `Øs` | Diameter sengkang | mm |
| `Ø` | Diameter tulangan utama | mm |

---

## 4. Faktor Blok Tegangan Ekivalen β1

```
β1 = 0.85                          untuk fc' ≤ 28 MPa
β1 = 0.85 - 0.05 × (fc' - 28) / 7  untuk 28 < fc' < 56 MPa
β1 = 0.65                          untuk fc' ≥ 56 MPa
```

Referensi pasal: SNI 2847:2019 Pasal 22.2.2.4.3  
Kode: `_beta1(fc_prime)` di `beam_calculator.py`

---

## 5. Rasio Tulangan Minimum dan Maksimum

### ρ_min (tulangan minimum)

```
ρ_min = max( 0.25 × √fc' / fy ,  1.4 / fy )    [SNI 2847:2019 Pasal 9.6.1.2]
```

### ρ_balanced (tulangan berimbang)

```
ρ_balanced = (0.85 × β1 × fc' / fy) × (600 / (600 + fy))
```

Derivasi: Keseimbangan regangan—baja mencapai leleh (εs = fy/Es) tepat saat beton mencapai εcu = 0.003

### ρ_max (tulangan maksimum — zone terkontrol tarik)

```
ρ_max = 0.75 × ρ_balanced
```

Batas ini menjamin kondisi "tension-controlled" sehingga φ = 0.90 berlaku (SNI 2847:2019 Tabel 21.2.2)

---

## 6. Luas Tulangan yang Diperlukan

Dari kesetimbangan momen nominal:

```
Rn = Mu / (φ × b × d²)                           [kN/m²]
```

Diselesaikan dari persamaan parabola tulangan:

```
ρ_required = (0.85 × fc' / fy) × (1 - √(1 - 2×Rn / (0.85×fc')))
As_required = ρ_required × b × d
As_min      = ρ_min × b × d
As_design   = max(As_required, As_min)
```

Catatan: Formula `ρ_required` merupakan solusi analitik eksak dari persamaan `Mn = As×fy×(d - a/2)` dengan `a = As×fy/(0.85×fc'×b)`. Tidak menggunakan iterasi.

---

## 7. Jumlah Batang Tulangan

```
bar_area = π × Ø² / 4
num_bars = ceil(As_design / bar_area)
As_design (final) = num_bars × bar_area
```

Minimal 2 batang sesuai praktik standar.

---

## 8. Tinggi Blok Tekan (Whitney Stress Block)

```
a = As_design × fy / (0.85 × fc' × b)           [SNI 2847:2019 Pasal 22.2.2.4.1]
```

---

## 9. Kapasitas Momen Nominal dan Tereduksi

```
Mn   = As_design × fy × (d - a/2)               [SNI 2847:2019 Pasal 22.3.2]
φMn  = φ × Mn    dengan φ = 0.90
```

φ = 0.90 berlaku untuk zone terkontrol tarik (εt ≥ 0.005), yang dijamin oleh ρ_max = 0.75 × ρ_balanced.

---

## 10. Cek Kapasitas

```
capacity_ratio = Mu / φMn

status = AMAN      jika Mu ≤ φMn  (capacity_ratio ≤ 1.0)
status = TIDAK_AMAN jika Mu > φMn  (capacity_ratio > 1.0)
```

---

## Batasan Penggunaan Modul

- Hanya untuk penampang segi empat, tulangan tunggal (singly reinforced)
- Balok sederhana (simply supported) dengan beban merata seragam
- Geser dan torsi tidak dicek di modul ini
- Lendutan tidak dicek di modul ini
- Hasil harus diverifikasi oleh Engineer Struktur berwenang

---

## Referensi Pasal

| Topik | Pasal SNI |
|-------|-----------|
| Kombinasi beban LRFD | SNI 1727:2020 Pasal 5.3.1c |
| Regangan beton maksimum εcu = 0.003 | SNI 2847:2019 Pasal 22.2.2.1 |
| Faktor β1 | SNI 2847:2019 Pasal 22.2.2.4.3 |
| Blok tegangan ekivalen | SNI 2847:2019 Pasal 22.2.2.4.1 |
| Tulangan minimum | SNI 2847:2019 Pasal 9.6.1.2 |
| Faktor reduksi kekuatan φ | SNI 2847:2019 Tabel 21.2.2 |
| Momen nominal | SNI 2847:2019 Pasal 22.3.2 |
