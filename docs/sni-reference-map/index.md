# SNI Reference Map — AG-SAS

Dokumen ini adalah indeks referensi pasal SNI yang digunakan dalam calculation engine.
Teks lengkap SNI adalah hak cipta BSN dan tidak disalin di sini.

## Standar yang Digunakan

| Standar | Judul | Dokumen Detail |
|---------|-------|---------------|
| SNI 1727:2020 | Beban Desain Minimum | [sni_1727_2020.md](sni_1727_2020.md) |
| SNI 2847:2019 | Beton Struktural | [sni_2847_2019.md](sni_2847_2019.md) |
| SNI 1729:2020 | Baja Struktural | [sni_1729_2020.md](sni_1729_2020.md) |
| SNI 1726:2019 | Ketahanan Gempa | Belum (Phase 4) |
| SNI 7860:2020 | Seismik Baja | Belum (Phase 4) |

## Peta Modul ↔ Standar

| Modul Aplikasi | Standar | Pasal Utama |
|---------------|---------|------------|
| `loads/combinations.py` | SNI 1727:2020 | Pasal 5.3.1 |
| `concrete/beam_calculator.py` | SNI 2847:2019, SNI 1727:2020 | 9.6.1.2, 22.2.2, 22.3.2 |
| `steel/beam_calculator.py` | SNI 1729:2020, SNI 1727:2020 | B3.4a, B4.1b, F2.1, F3-1 |

## SNI 2847:2019 — Beton Struktural

| Pasal | Topik | Digunakan Di |
|-------|-------|--------------|
| 9.6.1.2 | Tulangan minimum | `concrete/beam_calculator.py` |
| 21.2.2 (Tabel) | Faktor reduksi kekuatan φ | `concrete/beam_calculator.py` |
| 22.2.2.1 | Regangan beton maksimum εcu = 0.003 | `concrete/beam_calculator.py` |
| 22.2.2.4.1 | Blok tegangan ekivalen 0.85fc' | `concrete/beam_calculator.py` |
| 22.2.2.4.3 | Faktor blok tegangan β1 | `concrete/beam_calculator.py` |
| 22.3.2 | Momen nominal Mn | `concrete/beam_calculator.py` |

## SNI 1729:2020 — Baja Struktural

| Pasal | Topik | Digunakan Di |
|-------|-------|--------------|
| A3.2 | Modulus elastisitas E = 200,000 MPa | `units.py` |
| B3.4a | Faktor reduksi φ = 0.90 untuk lentur | `steel/beam_calculator.py` |
| B4.1b (Tabel) | Batas kelangsingan sayap λ_pf, λ_rf | `steel/beam_calculator.py` |
| F2.1 | Mn = Mp untuk penampang kompak, Lb ≤ Lp | `steel/beam_calculator.py` |
| F3-1 (Persamaan) | Mn tereduksi, flange local buckling | `steel/beam_calculator.py` |

## SNI 1727:2020 — Beban Desain Minimum

| Pasal | Topik | Digunakan Di |
|-------|-------|--------------|
| 5.3.1c | Kombinasi 1.2D + 1.6L | `loads/combinations.py`, semua beam_calculator |
| 5.3.1 | Semua kombinasi LRFD | `loads/combinations.py` |

---

*Referensi pasal diketik manual oleh developer. Selalu verifikasi dengan dokumen SNI resmi.*
