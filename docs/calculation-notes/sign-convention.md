# Konvensi Tanda AG-SAS

> **Disclaimer:** AG-SAS adalah engineering calculation assistant.
> Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.

---

## Referensi

**McGuire, W., Gallagher, R.H., Ziemian, R.D.**
*Matrix Structural Analysis*, 2nd Edition.
John Wiley & Sons, 2000. **§3.2**

Semua konvensi tanda AG-SAS mengikuti buku referensi di atas
kecuali disebutkan secara eksplisit.

---

## Sistem Koordinat Global

```
         Y (↑ vertikal, anti-gravitasi)
         |
         |
         +--------→  X (horizontal)
        /
       /
      Z  (○ keluar bidang, right-hand rule)
```

| Sumbu | Arah positif              |
|-------|---------------------------|
| X     | Horizontal ke kanan       |
| Y     | Vertikal ke atas          |
| Z     | Keluar bidang (dari layar)|
| Gravitasi | Arah −Y             |

**Right-hand rule berlaku** untuk semua rotasi dan torsi.

---

## Koordinat Lokal Elemen

Untuk elemen 2D frame:

```
         y_lokal (↑ tegak lurus elemen)
         |
         |
  Node I ●----------→ Node J   (x_lokal, arah elemen)
```

- `x_lokal`: dari Node I ke Node J
- `y_lokal`: tegak lurus `x_lokal`, 90° berlawanan jarum jam
- `z_lokal`: keluar bidang (sama dengan Z global untuk model 2D)

---

## Gaya Aksial (N)

```
  ←  N−  ●========●  N−  →    (tekan / compression)
  →  N+  ●========●  N+  ←    (tarik / tension)
```

| Tanda | Kondisi             |
|-------|---------------------|
| N > 0 | Tarik (tension)     |
| N < 0 | Tekan (compression) |

---

## Gaya Geser (V)

Untuk penampang 2D (bidang XY):

```
         ↑ Vy+
  -------●-------
         ↓ Vy−
```

| Tanda  | Kondisi pada muka kiri elemen |
|--------|-------------------------------|
| Vy > 0 | Naik (upward on left face)    |
| Vy < 0 | Turun (downward on left face) |

Konvensi: **gaya geser positif = naik pada muka kiri**.

---

## Momen Lentur (Mz)

```
        ___
       /   \     ← serat atas tertekan
  ----/     \----
       \   /     ← serat bawah tarik
        ---

  Mz > 0 = Sagging (serat bawah tarik, kurva cekung ke atas)
  Mz < 0 = Hogging (serat atas tarik, kurva cekung ke bawah)
```

| Tanda  | Kondisi                        |
|--------|--------------------------------|
| Mz > 0 | Sagging (serat bawah tarik)    |
| Mz < 0 | Hogging (serat atas tarik)     |

---

## Torsi (Mx)

| Tanda  | Kondisi                              |
|--------|--------------------------------------|
| Mx > 0 | Torsi positif (right-hand rule terhadap x_lokal) |
| Mx < 0 | Torsi negatif                        |

Untuk model 2D: Mx = 0 selalu.

---

## Perpindahan Nodal

| Simbol  | Arah                          | Satuan |
|---------|-------------------------------|--------|
| ux      | Translasi searah X global     | m      |
| uy      | Translasi searah Y global     | m      |
| uz      | Translasi searah Z global     | m      |
| rx      | Rotasi terhadap X global      | rad    |
| ry      | Rotasi terhadap Y global      | rad    |
| rz      | Rotasi terhadap Z global      | rad    |

Positif: searah sumbu positif (right-hand rule untuk rotasi).

---

## Reaksi Perletakan

Reaksi positif = searah dengan gaya eksternal positif.

```
Node jepit dengan beban ke bawah (−Y):
  Reaksi ry = +P (mendorong node ke atas, positif Y)
```

---

## Gaya Dalam di Ujung Elemen

Suffix `_i` = ujung Node I (start), suffix `_j` = ujung Node J (end).

Contoh untuk elemen horizontal (I di kiri, J di kanan):

```
  N_i ←  ●===========●  → N_j
     Vy_i ↑           ↑ Vy_j
       Mz_i ↺         ↻ Mz_j
```

Nilai `N_i` dan `N_j` umumnya berlawanan tanda (aksi-reaksi internal),
kecuali ada beban terdistribusi sepanjang elemen.

---

## Transformasi Koordinat

Transformasi dari lokal ke global:

```
K_global = Tᵀ · K_lokal · T
F_global = Tᵀ · F_lokal
```

di mana `T` adalah matriks transformasi berdasarkan sudut orientasi elemen
terhadap sumbu global X.

Untuk elemen 2D:
```
cos θ = (xJ − xI) / L
sin θ = (yJ − yI) / L
L = panjang elemen
```

---

## Versi Konvensi

| Field                        | Nilai  |
|------------------------------|--------|
| `SIGN_CONVENTION_VERSION`    | 1.0    |
| Referensi                    | McGuire MSA 2nd Ed. §3.2 |

Versi dinaikkan hanya jika ada perubahan konvensi yang mempengaruhi
tanda hasil perhitungan yang tersimpan di database.
