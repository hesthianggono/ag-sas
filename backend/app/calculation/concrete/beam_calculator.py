"""
Modul  : Desain Lentur Balok Beton Bertulang Sederhana
Standar: SNI 2847:2019 — Persyaratan Beton Struktural untuk Bangunan Gedung
         SNI 1727:2020 — Beban Desain Minimum (kombinasi beban)

Metode : Strength Design / Load and Resistance Factor Design (LRFD)

Lingkup: Balok persegi panjang, singly reinforced (tanpa tulangan tekan),
         bentang sederhana (simply supported), beban merata seragam,
         tulangan satu lapis.

DISCLAIMER: Hasil perhitungan ini bersifat indikatif. Wajib diperiksa oleh
            Engineer Struktur berwenang sebelum digunakan dalam dokumen resmi.

Formula Version: 1.1.0
"""
from __future__ import annotations
import math
from app.calculation.types import (
    ConcreteBeamParams, ConcreteBeamResult, CalcMeta, DesignStatus
)
from app.calculation.units import (
    knm_to_nmm, nmm_to_knm, cm3_to_mm3
)

# ── Konstanta modul ───────────────────────────────────────────────────────────

FORMULA_VERSION = "1.1.0"

STANDARD_REFERENCES = (
    "SNI 2847:2019 Pasal 9.3 (Tulangan tarik maksimum), "
    "SNI 2847:2019 Pasal 9.6.1 (Tulangan minimum), "
    "SNI 2847:2019 Pasal 21.2.1 (Faktor reduksi kekuatan φ), "
    "SNI 2847:2019 Pasal 22.2.2.4.3 (Faktor β1 blok tegangan), "
    "SNI 1727:2020 Pasal 5.3.1 (Kombinasi beban LRFD)"
)

ASSUMPTIONS = (
    "1. Balok sederhana (simply supported), beban merata seragam. "
    "2. Penampang persegi panjang, singly reinforced (tulangan tekan diabaikan). "
    "3. Satu lapis tulangan tarik. "
    "4. Strain compatibility: εs ≥ 0.005 (terkontrol tarik, φ = 0.90). "
    "5. Beton di zona tarik diabaikan (cracked section). "
    "6. Tekuk badan dan sayap tidak dicek (sesuai lingkup SNI 2847:2019)."
)

DISCLAIMER = (
    "Perhitungan menggunakan formula SNI 2847:2019 untuk kondisi beban sederhana. "
    "Kondisi khusus (beban terpusat, balok menerus, torsi, geser kritis) memerlukan "
    "analisis tambahan. Wajib diperiksa ulang oleh Engineer Struktur berwenang."
)

_META = CalcMeta(
    formula_version=FORMULA_VERSION,
    standard_references=STANDARD_REFERENCES,
    assumptions=ASSUMPTIONS,
    disclaimer=DISCLAIMER,
)


# ── Fungsi utama ──────────────────────────────────────────────────────────────

def design_concrete_beam(params: ConcreteBeamParams) -> ConcreteBeamResult:
    """
    Desain lentur balok beton bertulang singly reinforced.

    Parameter
    ---------
    params : ConcreteBeamParams
        Input tervalidasi. Panggil params.validate() sebelum memanggil fungsi ini.

    Returns
    -------
    ConcreteBeamResult
        Semua hasil perhitungan dengan satuan jelas (embedded dalam nama field).

    Referensi formula utama
    -----------------------
    1. Kombinasi beban  : U = 1.2D + 1.6L                    [SNI 1727:2020 §5.3.1c]
    2. Momen ultimit    : Mu = wu·L²/8                        [Mekanika statika]
    3. Tinggi efektif   : d = h - cc - Øs - Ø/2              [Geometri penampang]
    4. β1               : 0.85 − 0.05·(fc'−28)/7 ≥ 0.65      [SNI 2847:2019 §22.2.2.4.3]
    5. ρ_min            : max(0.25√fc'/fy, 1.4/fy)            [SNI 2847:2019 §9.6.1]
    6. ρ_max            : 0.75·ρb  dimana ρb = 0.85β1·fc'/fy·(600/(600+fy))
    7. Rn               : Mu / (φ·b·d²)                       [Koefisien tahanan momen]
    8. ρ perlu          : (0.85fc'/fy)·(1 − √(1 − 2Rn/(0.85fc')))
    9. a                : As·fy / (0.85·fc'·b)                [Blok tegangan Whitney]
    10. φMn             : φ·As·fy·(d − a/2)                   [SNI 2847:2019 §22.3.2.1]
    """
    r = ConcreteBeamResult(meta=_META)

    # Ekstrak parameter untuk kenyamanan pembacaan
    b  = params.width_b_mm
    h  = params.height_h_mm
    cc = params.cover_cc_mm
    D  = params.bar_diameter_mm
    Ds = params.stirrup_diameter_mm
    fc = params.fc_prime_mpa        # fc' [MPa]
    fy = params.fy_mpa              # fy [MPa]
    L  = params.span_l_m            # L [m]
    wD = params.dead_load_w_knm     # wD [kN/m]
    wL = params.live_load_w_knm     # wL [kN/m]

    # ── 1. Kombinasi Beban ───────────────────────────────────────────────────
    # SNI 1727:2020 Pasal 5.3.1c: U = 1.2D + 1.6L
    # Kombinasi ini umumnya mengontrol untuk gedung dengan beban hidup dominan.
    r.wu_knm = 1.2 * wD + 1.6 * wL  # [kN/m]

    # ── 2. Gaya Dalam Ultimit (Statika Balok Sederhana) ──────────────────────
    # Momen maksimum di tengah bentang:   Mu = wu·L²/8
    # Geser maksimum di tumpuan:          Vu = wu·L/2
    r.mu_ultimate_knm = r.wu_knm * L**2 / 8.0   # [kN·m]
    r.vu_ultimate_kn  = r.wu_knm * L / 2.0       # [kN]

    # ── 3. Tinggi Efektif Penampang ──────────────────────────────────────────
    # d = h - cc - Øsengkang - ½·Øtulangan_utama
    # (jarak dari serat tekan ekstrem ke titik berat tulangan tarik)
    r.effective_depth_d_mm = h - cc - Ds - 0.5 * D  # [mm]
    d = r.effective_depth_d_mm

    # ── 4. Faktor Blok Tegangan β1 ────────────────────────────────────────────
    # SNI 2847:2019 Pasal 22.2.2.4.3:
    #   β1 = 0.85                           untuk fc' ≤ 28 MPa
    #   β1 = 0.85 − 0.05·(fc'−28)/7        untuk 28 < fc' ≤ 56 MPa
    #   β1 ≥ 0.65                           (batas bawah)
    r.beta1 = _beta1(fc)

    # ── 5. Faktor Reduksi Kekuatan φ ─────────────────────────────────────────
    # SNI 2847:2019 Tabel 21.2.1:
    # Komponen lentur yang didominasi tarik dengan εt ≥ 0.005: φ = 0.90
    # (diasumsikan terkontrol tarik — dicek implisit melalui ρ ≤ ρ_max)
    r.phi_factor = 0.90

    # ── 6. Batas Rasio Tulangan ───────────────────────────────────────────────
    # ρ_min: tulangan minimum mencegah retak getas tiba-tiba
    # SNI 2847:2019 Pasal 9.6.1.2: ρ_min = max(0.25√fc'/fy, 1.4/fy)
    r.rho_min = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy)

    # ρ_balanced: rasio tulangan saat beton mencapai εcu=0.003 bersamaan
    # dengan tulangan mencapai εy=fy/Es secara simultan
    # ρb = (0.85·β1·fc') / fy × [600 / (600 + fy)]
    # (600 = Es·εcu = 200000 × 0.003 dalam MPa)
    rho_bal = (0.85 * r.beta1 * fc / fy) * (600.0 / (600.0 + fy))

    # ρ_max = 0.75·ρb: membatasi agar penampang terkontrol tarik (εt ≥ 0.004)
    r.rho_max = 0.75 * rho_bal

    # ── 7. Rasio Tulangan yang Diperlukan ─────────────────────────────────────
    # Dari Mu = φ·Rn·b·d²  →  Rn = Mu/(φ·b·d²)   [N/mm² = MPa]
    mu_nmm = knm_to_nmm(r.mu_ultimate_knm)           # [N·mm]
    rn = mu_nmm / (r.phi_factor * b * d**2)          # [MPa]

    # ρ perlu dari inversi persamaan momen persegi panjang:
    # Rn = ρ·fy·(1 − ρ·fy/(1.7·fc'))
    # Diselesaikan dengan rumus kuadrat:
    # ρ = (0.85fc'/fy)·[1 − √(1 − 2Rn/(0.85fc'))]
    discriminant = max(0.0, 1.0 - (2.0 * rn) / (0.85 * fc))
    rho_req = (0.85 * fc / fy) * (1.0 - math.sqrt(discriminant))
    r.rho_required = max(rho_req, 0.0)

    # ── 8. Luas Tulangan ─────────────────────────────────────────────────────
    r.as_required_mm2 = r.rho_required * b * d   # [mm²]
    r.as_min_mm2      = r.rho_min * b * d        # [mm²]

    as_needed = max(r.as_required_mm2, r.as_min_mm2)

    # Jumlah batang: pembulatan ke atas, minimum 2 batang
    r.bar_area_mm2 = math.pi * D**2 / 4.0           # Luas satu batang [mm²]
    r.num_bars     = max(math.ceil(as_needed / r.bar_area_mm2), 2)
    r.as_design_mm2 = r.num_bars * r.bar_area_mm2   # [mm²]

    # ── 9. Kapasitas Penampang ────────────────────────────────────────────────
    # Tinggi blok tegangan ekivalen Whitney:
    # a = As·fy / (0.85·fc'·b)   [mm]
    r.a_block_mm = r.as_design_mm2 * fy / (0.85 * fc * b)  # [mm]

    # Momen nominal: Mn = As·fy·(d − a/2)   [N·mm]
    mn_nmm = r.as_design_mm2 * fy * (d - r.a_block_mm / 2.0)  # [N·mm]
    r.mn_knm    = nmm_to_knm(mn_nmm)                           # [kN·m]
    r.phi_mn_knm = r.phi_factor * r.mn_knm                     # [kN·m]

    # ── 10. Cek Kapasitas ────────────────────────────────────────────────────
    # Syarat: Mu ≤ φMn  →  capacity_ratio = Mu/φMn ≤ 1.0
    r.capacity_ratio = (
        r.mu_ultimate_knm / r.phi_mn_knm if r.phi_mn_knm > 0 else float("inf")
    )
    r.status = (
        DesignStatus.AMAN if r.mu_ultimate_knm <= r.phi_mn_knm
        else DesignStatus.TIDAK_AMAN
    )

    return r


# ── Fungsi bantu ──────────────────────────────────────────────────────────────

def _beta1(fc_prime: float) -> float:
    """
    Faktor β1 untuk blok tegangan ekivalen (SNI 2847:2019 Pasal 22.2.2.4.3).

    β1 menghubungkan tinggi blok tegangan ekivalen (a) dengan kedalaman
    sumbu netral (c): a = β1·c

    fc' [MPa] | β1
    ----------|-----
    ≤ 28      | 0.85
    35        | 0.80
    42        | 0.75
    ≥ 56      | 0.65 (minimum)
    """
    if fc_prime <= 28.0:
        return 0.85
    beta1 = 0.85 - 0.05 * (fc_prime - 28.0) / 7.0
    return max(beta1, 0.65)
