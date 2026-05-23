# Panduan Pengguna — Manajer Gambar Teknik

## Apa itu Manajer Gambar Teknik?

Manajer Gambar Teknik (Report Figure Manager) adalah fitur AG-SAS untuk
menghasilkan, mengelola, dan menyesuaikan **gambar teknik otomatis** yang
akan dimasukkan ke dalam laporan PDF perhitungan struktur.

Gambar dihasilkan secara otomatis dari data perhitungan Anda — tidak perlu
membuat gambar manual.

---

## Cara Mengakses

1. Buka menu **Laporan** di sidebar
2. Klik laporan yang ingin dikelola
3. Di halaman detail laporan, klik tab **Gambar Teknik**

Atau langsung akses: `/report/{report_id}` → tab **Gambar Teknik**

---

## Gambar yang Dihasilkan Otomatis

Untuk setiap laporan perhitungan (balok beton atau balok baja), sistem akan
menghasilkan **7 gambar teknik**:

| No. | Gambar                       | Keterangan                                      |
|-----|------------------------------|-------------------------------------------------|
| 1   | **Model Struktur**           | Balok sederhana dengan simbol tumpuan sendi/rol |
| 2   | **Diagram Pembebanan**       | UDL terfaktor wu dengan panah dan nilai         |
| 3   | **Diagram Reaksi Tumpuan**   | RA = RB = wu·L/2 dengan kontrol keseimbangan   |
| 4   | **Diagram Gaya Geser V(x)**  | Diagram V dengan zona positif/negatif           |
| 5   | **Diagram Momen Lentur M(x)**| Diagram M parabolik, max di midspan             |
| 6   | **Bentuk Deformasi**         | Kurva elastika dengan faktor skala visual       |
| 7   | **Peta Rasio Utilisasi**     | Gauge Mu/φMn dengan zona aman/peringatan/bahaya |

---

## Cara Generate Gambar

### Generate Pertama Kali

1. Klik tombol **Generate Gambar** (biru)
2. Tunggu proses selesai (~3–10 detik)
3. Semua 7 gambar akan muncul dalam grid

### Pengaturan Sebelum Generate

Klik **Opsi** untuk mengatur:

- **Faktor Skala Deformasi** — Berapa kali deformasi diperbesar secara visual.
  Default: 50×. Nilai lebih besar = deformasi lebih terlihat jelas.
  *Catatan: Ini hanya faktor visual, bukan nilai deformasi nyata.*

### Generate Ulang

Klik **Generate Ulang** untuk mengganti semua gambar lama dengan yang baru.
Berguna jika Anda mengubah parameter seperti faktor skala.

---

## Mengelola Gambar

### Preview Gambar

Klik gambar untuk membuka lightbox tampilan penuh.

### Sembunyikan / Tampilkan

Klik ikon **mata** (👁) di setiap gambar untuk menyembunyikan atau
menampilkan gambar di laporan PDF.

- Gambar tersembunyi tetap tersimpan, hanya tidak muncul di PDF
- Gunakan **Tampilkan Semua** / **Sembunyikan Semua** untuk semua gambar sekaligus

### Edit Caption

1. Klik ikon **edit** (✏) di gambar yang ingin diubah
2. Edit judul dan/atau caption lengkap
3. Klik **Simpan**

**Format caption yang disarankan:**
```
Gambar 12.5  Diagram momen lentur M(x) — Kombinasi 1.2D + 1.6L
```

### Download Gambar

Klik ikon **download** (⬇) untuk menyimpan gambar sebagai file PNG.
Klik **Unduh Semua** untuk mengunduh semua gambar yang terlihat sekaligus.

### Hapus Gambar

Klik ikon **sampah** (🗑) untuk menghapus gambar dari laporan.
Gambar yang dihapus tidak dapat dipulihkan — generate ulang jika diperlukan.

---

## Upload Gambar dari Three.js / Canvas

Jika Anda memiliki tampilan 3D atau visualisasi kustom di aplikasi:

1. Ambil screenshot dengan tombol **Capture Snapshot** (jika tersedia di modul tersebut)
2. Gambar akan otomatis dikirim ke server dan muncul di Manajer Gambar
3. Edit caption sesuai kebutuhan

---

## Urutan Gambar di Laporan PDF

Gambar ditampilkan di laporan PDF sesuai **order_index** (urutan generate).
Saat ini urutan sesuai urutan default:
1. Model Struktur
2. Pembebanan
3. Reaksi
4. Gaya Geser
5. Momen Lentur
6. Deformasi
7. Utilisasi

---

## Snapshot Immutable

> **Penting:** Setiap gambar disimpan sebagai **snapshot immutable** bersama laporan.

Artinya:
- Jika Anda mengubah data model **setelah laporan dibuat**, gambar lama tetap tidak berubah
- Laporan lama Anda selalu memiliki gambar yang sesuai dengan data saat itu
- Untuk memperbarui, gunakan **Generate Ulang** secara eksplisit

---

## Gambar di Laporan PDF

Saat Anda mengunduh PDF dari halaman laporan, Seksi 12 (Gambar Teknik) akan berisi:

1. **Daftar Gambar** — tabel berisi nomor, judul, dan satuan semua gambar
2. **Gambar satu per satu** — setiap gambar dengan caption di bawahnya

Hanya gambar yang **terlihat** (is_visible = true) yang masuk ke PDF.

---

## Informasi Teknis

| Aspek            | Detail                                       |
|------------------|----------------------------------------------|
| Format output    | PNG (DPI 150) + JSON data mentah             |
| Library          | Matplotlib 3.x (backend Agg, headless)       |
| Penyimpanan      | Database PostgreSQL (kolom `BYTEA`)          |
| Sumber gambar    | `backend` (otomatis) atau `frontend` (upload) |
| Kapasitas        | Tidak dibatasi jumlah gambar per laporan     |

---

## Troubleshooting

### Gambar tidak muncul di PDF

- Pastikan gambar memiliki status **terlihat** (ikon mata terbuka)
- Coba **Generate Ulang** gambar

### Tombol Generate tidak aktif

- Pastikan laporan sudah terbuat terlebih dahulu dari halaman Laporan

### Gambar terlalu kecil / tidak jelas

- Gambar digenerate dengan DPI 150 — cukup untuk PDF A4
- Ukuran tampilan di layar mungkin terlihat kecil karena disesuaikan

### Caption tidak tampil di PDF

- Pastikan field caption tidak kosong
- Format: `Gambar X.Y  Judul gambar`
