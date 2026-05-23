# Panduan Pengguna: Hasil Analisis Portal 2D

**Versi:** 1.0  
**Halaman:** `/frame2d`

---

## 1. Menjalankan Analisis

1. Buka menu **Portal 2D** di sidebar.
2. Isi data masukan:
   - **Titik Simpul (Node)**: koordinat X, Y dalam meter.
   - **Elemen (Batang)**: pilih node-i dan node-j, properti material (E dalam MPa), penampang (A dalam cm², I dalam cm⁴), dan beban merata UDL (kN/m, positif = ke bawah).
   - **Tumpuan**: pilih node dan derajat kebebasan yang dikekang (UX, UY, RZ).
   - **Beban Titik**: gaya nodal FX, FY (kN) dan momen MZ (kN·m).
3. Klik tombol **Jalankan Analisis**.

---

## 2. Kartu Ringkasan Hasil

Setelah analisis berhasil, tiga kartu ringkasan ditampilkan:

| Kartu | Keterangan |
|-------|------------|
| Lendutan Maks | Perpindahan maksimum di semua node (mm) |
| Momen Maks | Nilai absolut momen terbesar (kN·m) |
| Geser Maks | Nilai absolut geser terbesar (kN) |

---

## 3. Tabel Detail Hasil

Klik header untuk membuka/menutup tabel:

### 3.1 Perpindahan Node
- **UX (mm)**: perpindahan horizontal
- **UY (mm)**: perpindahan vertikal (negatif = ke bawah)
- **RZ (mrad)**: rotasi (miliradian, positif = berlawanan jarum jam)

### 3.2 Reaksi Tumpuan
- **RX, RY (kN)**: gaya reaksi horizontal dan vertikal
- **MZ (kN·m)**: momen reaksi (hanya untuk tumpuan jepit)

### 3.3 Gaya Dalam Elemen
Gaya di ujung-i dan ujung-j setiap elemen:
- **N (kN)**: gaya aksial. Negatif = tekan.
- **Vy (kN)**: gaya geser transversal
- **Mz (kN·m)**: momen lentur

---

## 4. Visualisasi Diagram

Setelah analisis selesai, panel **Visualisasi Diagram Gaya Dalam & Deformasi** muncul di bawah hasil.

### 4.1 Tombol Mode Diagram

| Tombol | Tampilan |
|--------|----------|
| Struktur | Hanya rangka tidak terdeformasi |
| Deformasi | Bentuk deformasi (diperbesar, garis ungu putus-putus) |
| Gaya N | Diagram gaya aksial (biru) |
| Gaya V | Diagram gaya geser (hijau) |
| Gaya M | Diagram momen lentur (kuning/amber) |

### 4.2 Kontrol

- **Skala**: mengatur lebar maksimum diagram (piksel). Geser ke kiri untuk memperkecil, ke kanan untuk memperbesar.
- **Label**: tampilkan/sembunyikan nomor node dan elemen.
- **Beban**: tampilkan/sembunyikan tanda panah beban nodal dan UDL.

### 4.3 Ekspor SVG

Klik tombol **⬇ SVG** untuk mengunduh gambar diagram saat ini dalam format SVG (dapat dibuka di Inkscape, browser, atau dimasukkan ke laporan Word/PDF).

### 4.4 Tabel Nilai Ekstrem

Di bawah diagram, tabel menampilkan nilai maksimum dan minimum setiap elemen untuk mode yang aktif.

---

## 5. Interpretasi Diagram

### Diagram Momen (M)
- Nilai positif (area di atas garis elemen): **sagging** (tarik sisi bawah untuk balok horizontal).
- Nilai negatif: **hogging** (tarik sisi atas).
- Untuk balok sederhana dengan UDL, momen maksimum terjadi di tengah bentang = qL²/8.

### Diagram Geser (V)
- V > 0: gaya geser ke atas pada muka kiri elemen.
- V berubah tanda di titik momen maksimum.

### Diagram Aksial (N)
- N < 0: elemen tertekan (compression).
- Untuk struktur kolom-balok, kolom umumnya tertekan.

### Bentuk Deformasi
- Faktor amplifikasi default = 100× (visual saja, bukan skala fisik).
- Titik sendi menunjukkan tidak ada momen → tidak ada tekukan.
- Tumpuan jepit tidak bergerak maupun berotasi.

---

## 6. Catatan Penting

> **Solver linear elastik** — tidak memperhitungkan:
> - Non-linearitas geometri (efek P-delta)
> - Non-linearitas material (plastisitas, leleh)
> - Tekuk lokal atau lateral-torsional buckling
>
> Hasil ini hanya untuk **preliminary design** dan **harus diverifikasi** oleh insinyur struktural berpengalaman sesuai SNI yang berlaku.

---

## 7. Contoh Default

Halaman dimuat dengan contoh **balok sederhana** (3 node, 2 elemen, UDL 20 kN/m):

- Node: 0 (0,0), 1 (3,0), 2 (6,0)
- Elemen: profil W dengan E=200000 MPa, A=84.12 cm², I=23700 cm⁴
- Tumpuan: sendi di node 0, rol di node 2
- Hasil teoritis: M_maks = qL²/8 = 20×6²/8 = 90 kN·m
