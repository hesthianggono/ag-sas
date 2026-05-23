"""
Modul  : Desain Lentur Balok Baja WF Sederhana
Standar: SNI 1729:2020 — Spesifikasi untuk Bangunan Gedung Baja Struktural
         SNI 1727:2020 — Beban Desain Minimum (kombinasi beban)

Metode : Load and Resistance Factor Design (LRFD)

Lingkup: Profil WF / H-Beam, bentang sederhana, beban merata seragam.
         Tekuk lateral-torsi (LTB) diasumsikan tidak mengontrol (Lb ≤ Lp).
         Cek kelangsingan sayap: kompak vs tidak kompak.
         Badan diasumsikan kompak (dicek terpisah jika diperlukan).

DISCLAIMER: Hasil perhitungan ini bersifat indikatif. Wajib diperiksa oleh
            Engineer Struktur berwenang sebelum digunakan dalam dokumen resmi.

Formula Version: 1.1.0
"""
from __future__ import annotations
import math
from app.calculation.types import (
    SteelBeamParams, SteelBeamResult, CalcMeta, DesignStatus
)
from app.calculation.units import (
    kgm_to_knm, knm_to_nmm, nmm_to_knm, cm3_to_mm3, E_STEEL_MPA
)

# ── Konstanta modul ───────────────────────────────────────────────────────────

FORMULA_VERSION = "1.1.0"

STANDARD_REFERENCES = (
    "SNI 1729:2020 Tabel B4.1b (Batas kelangsingan elemen tekan), "
    "SNI 1729:2020 Pasal B3.4a (Faktor reduksi φ = 0.90 untuk lentur), "
    "SNI 1729:2020 Pasal F2.1 (Mn = Mp untuk penampang kompak, Lb ≤ Lp), "
    "SNI 1729:2020 Pasal F3.1 (Mn tereduksi untuk penampang tidak kompak), "
    "SNI 1727:2020 Pasal 5.3.1 (Kombinasi beban LRFD)"
)

ASSUMPTIONS = (
    "1. Balok sederhana (simply supported), beban merata seragam. "
    "2. Tekuk lateral-torsi (LTB) tidak mengontrol — pengekang lateral memadai "
    "   (Lb ≤ Lp); kondisi ini harus diverifikasi di lapangan. "
    "3. Hanya kelangsingan sayap yang dicek; badan diasumsikan kompak. "
    "4. Defleksi dan lendutan tidak dicek dalam modul ini. "
    "5. Berat sendiri profil diperhitungkan dalam beban mati."
)

DISCLAIMER = (
    "Perhitungan ini menggunakan metode LRFD SNI 1729:2020. "
    "Asumsi Lb ≤ Lp (LTB tidak mengontrol) HARUS diverifikasi untuk setiap kasus. "
    "Cek lendutan, geser, dan sambungan harus dilakukan terpisah. "
    "Wajib diperiksa ulang oleh Engineer Struktur berwenang."
)

_META = CalcMeta(
    formula_version=FORMULA_VERSION,
    standard_references=STANDARD_REFERENCES,
    assumptions=ASSUMPTIONS,
    disclaimer=DISCLAIMER,
)


# ── Fungsi utama ──────────────────────────────────────────────────────────────

def design_steel_beam(params: SteelBeamParams) -> SteelBeamResult:
    """
    Desain lentur balok baja WF menggunakan metode LRFD.

    Parameter
    ---------
    params : SteelBeamParams
        Input tervalidasi.

    Returns
    -------
    SteelBeamResult
        Semua hasil dengan satuan jelas (embedded dalam nama field).

    Referensi formula utama
    -----------------------
    1. Berat sendiri   : SW = weight_per_m × g / 1000          [kN/m]
    2. Kombinasi beban : U = 1.2(D + SW) + 1.6L               [SNI 1727:2020 §5.3.1c]
    3. Momen ultimit   : Mu = wu·L²/8                          [Statika]
    4. λ_f             : (b/2) / tf                            [SNI 1729:2020 Tabel B4.1b]
    5. λ_pf            : 0.38·√(E/Fy)                         [Batas kompak sayap]
    6. λ_rf            : 1.0·√(E/Fy)                          [Batas tidak kompak]
    7. Mp              : Fy · Zx                               [SNI 1729:2020 F2-1]
    8. Mn (kompak)     : Mp                                    [F2-1, Lb ≤ Lp]
    9. Mn (tak kompak) : Mp − (Mp − 0.7FySx)·(λ−λpf)/(λrf−λpf)  [F3-1]
    10. φMn            : 0.90 · Mn                             [B3.4a]
    """
    r = SteelBeamResult(meta=_META)

    # Ekstrak parameter
    Fy  = params.fy_mpa               # Kuat leleh Fy [MPa]
    L   = params.span_l_m             # Panjang bentang [m]
    wD  = params.dead_load_w_knm      # Beban mati (tanpa SW) [kN/m]
    wL  = params.live_load_w_knm      # Beban hidup [kN/m]
    b   = params.flange_width_b_mm    # Lebar sayap [mm]
    tf  = params.flange_thickness_tf_mm  # Tebal sayap [mm]
    Sx  = params.sx_cm3               # Sx [cm³]
    Zx  = params.zx_cm3               # Zx [cm³]
    W   = params.weight_per_m_kgm     # Berat per meter [kg/m]

    r.profile_designation  = params.profile_designation
    r.sx_cm3               = Sx
    r.zx_cm3               = Zx
    r.weight_per_m_kgm     = W
    r.phi_factor           = 0.90  # SNI 1729:2020 Pasal B3.4a

    # ── 1. Berat Sendiri Profil ────────────────────────────────────────────────
    # SW = W [kg/m] × g [m/s²] / 1000 [N/kN]
    r.self_weight_knm = kgm_to_knm(W)   # [kN/m]

    # ── 2. Kombinasi Beban ────────────────────────────────────────────────────
    # SNI 1727:2020 Pasal 5.3.1c: U = 1.2D + 1.6L
    # Beban mati total = beban mati eksternal + berat sendiri profil
    w_dead_total  = wD + r.self_weight_knm
    r.wu_knm = 1.2 * w_dead_total + 1.6 * wL   # [kN/m]

    # ── 3. Momen Ultimit ──────────────────────────────────────────────────────
    # Balok sederhana, beban merata: Mu = wu·L²/8
    r.mu_ultimate_knm = r.wu_knm * L**2 / 8.0  # [kN·m]

    # ── 4. Cek Kelangsingan Sayap (SNI 1729:2020 Tabel B4.1b) ──────────────
    # Untuk sayap profil I yang mengalami tekan dalam lentur:
    # λ_f  = (b/2) / tf           (setengah lebar sayap dibagi tebal sayap)
    # λ_pf = 0.38·√(E/Fy)         (batas kompak)
    # λ_rf = 1.0·√(E/Fy)          (batas tidak kompak / slender)
    E = E_STEEL_MPA                              # E = 200,000 MPa
    r.lambda_f   = (b / 2.0) / tf               # [-]
    r.lambda_pf  = 0.38 * math.sqrt(E / Fy)     # [-]
    r.lambda_rf  = 1.0  * math.sqrt(E / Fy)     # [-]
    r.is_compact = r.lambda_f <= r.lambda_pf

    # ── 5. Momen Plastis Mp ───────────────────────────────────────────────────
    # Mp = Fy · Zx     [SNI 1729:2020 Pasal F2.1]
    # Zx dalam cm³ dikonversi ke mm³: × 1000
    zx_mm3   = cm3_to_mm3(Zx)                       # [mm³]
    r.mp_knm = nmm_to_knm(Fy * zx_mm3)              # [kN·m]

    # ── 6. Momen Nominal Mn ───────────────────────────────────────────────────
    if r.is_compact:
        # Penampang kompak + Lb ≤ Lp → tidak ada reduksi LTB atau kelangsingan
        # Mn = Mp     [SNI 1729:2020 Pasal F2.1]
        mn_knm = r.mp_knm

    else:
        # Penampang tidak kompak (inelastic local buckling pada sayap)
        # Mn = Mp − (Mp − 0.7·Fy·Sx) · (λ_f − λ_pf) / (λ_rf − λ_pf)
        # [SNI 1729:2020 Persamaan F3-1]
        sx_mm3  = cm3_to_mm3(Sx)                    # [mm³]
        mr_knm  = nmm_to_knm(0.7 * Fy * sx_mm3)    # 0.7·Fy·Sx [kN·m]
        ratio   = (r.lambda_f - r.lambda_pf) / (r.lambda_rf - r.lambda_pf)
        mn_knm  = r.mp_knm - (r.mp_knm - mr_knm) * ratio

    r.mn_knm     = mn_knm                   # Mn [kN·m]
    r.phi_mn_knm = r.phi_factor * mn_knm   # φMn [kN·m]

    # ── 7. Cek Kapasitas ──────────────────────────────────────────────────────
    # Syarat: Mu ≤ φMn  →  capacity_ratio = Mu/φMn ≤ 1.0
    r.capacity_ratio = (
        r.mu_ultimate_knm / r.phi_mn_knm if r.phi_mn_knm > 0 else float("inf")
    )
    r.status = (
        DesignStatus.AMAN if r.mu_ultimate_knm <= r.phi_mn_knm
        else DesignStatus.TIDAK_AMAN
    )

    return r
