"""
Tipe Data Umum Calculation Engine AG-SAS
=========================================
Semua schema input/output untuk calculation engine didefinisikan di sini.
Modul ini TIDAK mengimpor FastAPI, SQLModel, atau dependensi web/DB apapun.
Dapat dipanggil langsung dari unit test.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Status Kapasitas ──────────────────────────────────────────────────────────

class DesignStatus(str, Enum):
    AMAN = "AMAN"
    TIDAK_AMAN = "TIDAK AMAN"
    ERROR = "ERROR"


# ── Meta Perhitungan ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CalcMeta:
    """Metadata yang menyertai setiap hasil perhitungan."""
    formula_version: str        # SemVer formula, e.g. "1.0.0"
    standard_references: str    # Pasal-pasal SNI yang digunakan
    disclaimer: str             # Peringatan wajib engineering review
    assumptions: str            # Asumsi-asumsi yang digunakan


# ── Input Schemas (pure, no DB/API fields) ────────────────────────────────────

@dataclass(frozen=True)
class ConcreteBeamParams:
    """
    Parameter input untuk desain lentur balok beton bertulang.
    Semua dimensi dalam satuan konsisten: mm untuk penampang, m untuk bentang,
    MPa untuk tegangan, kN/m untuk beban.
    """
    # Dimensi penampang
    width_b_mm: float           # Lebar balok b [mm]
    height_h_mm: float          # Tinggi total balok h [mm]
    cover_cc_mm: float          # Selimut beton bersih cc [mm]
    bar_diameter_mm: float      # Diameter tulangan utama Ø [mm]
    stirrup_diameter_mm: float  # Diameter sengkang Øs [mm]

    # Properti material
    fc_prime_mpa: float         # Kuat tekan beton fc' [MPa]
    fy_mpa: float               # Kuat leleh baja tulangan fy [MPa]

    # Beban dan geometri global
    span_l_m: float             # Panjang bentang bersih L [m]
    dead_load_w_knm: float      # Beban mati merata wD [kN/m]
    live_load_w_knm: float      # Beban hidup merata wL [kN/m]

    def validate(self) -> list[str]:
        """Validasi nilai-nilai input secara teknis. Returns daftar pesan error."""
        errors = []
        if self.width_b_mm < 100:
            errors.append(f"Lebar balok b={self.width_b_mm} mm terlalu kecil (min 100 mm)")
        if self.height_h_mm < 2 * self.width_b_mm:
            errors.append("Tinggi balok h < 2b — tidak lazim untuk balok")
        if self.fc_prime_mpa < 17:
            errors.append(f"fc'={self.fc_prime_mpa} MPa di bawah minimum SNI 2847:2019 (17 MPa)")
        if self.fc_prime_mpa > 70:
            errors.append(f"fc'={self.fc_prime_mpa} MPa — rumus β1 berlaku s/d 70 MPa")
        if self.fy_mpa > 550:
            errors.append(f"fy={self.fy_mpa} MPa melebihi batas SNI 2847:2019 (550 MPa)")
        if self.span_l_m <= 0:
            errors.append("Panjang bentang L harus > 0")
        if self.dead_load_w_knm < 0 or self.live_load_w_knm < 0:
            errors.append("Beban tidak boleh negatif")
        eff_d = self.height_h_mm - self.cover_cc_mm - self.stirrup_diameter_mm - 0.5 * self.bar_diameter_mm
        if eff_d <= 0:
            errors.append(f"Tinggi efektif d={eff_d:.1f} mm tidak valid — periksa cover dan diameter tulangan")
        return errors


@dataclass(frozen=True)
class SteelBeamParams:
    """
    Parameter input untuk desain lentur balok baja WF.
    Dimensi penampang dalam mm, properti penampang dalam cm³/cm⁴, beban dalam kN/m.
    """
    # Identifikasi profil
    profile_designation: str    # Nama profil, e.g. "WF 400x200x8x13"

    # Dimensi penampang [mm]
    height_h_mm: float          # Tinggi total profil H [mm]
    flange_width_b_mm: float    # Lebar sayap B [mm]
    web_thickness_tw_mm: float  # Tebal badan tw [mm]
    flange_thickness_tf_mm: float  # Tebal sayap tf [mm]

    # Properti penampang (dari tabel baja)
    sx_cm3: float               # Modulus penampang elastis Sx [cm³]
    zx_cm3: float               # Modulus penampang plastis Zx [cm³]
    weight_per_m_kgm: float     # Berat per meter [kg/m]

    # Material
    fy_mpa: float               # Kuat leleh baja Fy [MPa]

    # Beban dan geometri global
    span_l_m: float             # Panjang bentang L [m]
    dead_load_w_knm: float      # Beban mati merata wD (tidak termasuk SW) [kN/m]
    live_load_w_knm: float      # Beban hidup merata wL [kN/m]

    def validate(self) -> list[str]:
        """Validasi parameter input secara teknis."""
        errors = []
        valid_fy = {210, 240, 250, 290, 360, 410, 500}
        if self.fy_mpa not in valid_fy and not (200 <= self.fy_mpa <= 550):
            errors.append(f"fy={self.fy_mpa} MPa tidak dalam rentang tipikal (200–550 MPa)")
        if self.span_l_m <= 0:
            errors.append("Panjang bentang L harus > 0")
        if self.zx_cm3 <= 0 or self.sx_cm3 <= 0:
            errors.append("Modulus penampang Zx dan Sx harus > 0")
        if self.flange_thickness_tf_mm <= 0:
            errors.append("Tebal sayap tf harus > 0")
        if self.dead_load_w_knm < 0 or self.live_load_w_knm < 0:
            errors.append("Beban tidak boleh negatif")
        return errors


# ── Output Schemas ────────────────────────────────────────────────────────────

@dataclass
class ConcreteBeamResult:
    """
    Hasil perhitungan desain lentur balok beton bertulang.
    Semua field diberi satuan di nama dan di komentar.
    """
    # ── Beban terfaktor ──────────────────────────────────────────────────────
    wu_knm: float = 0.0         # Beban terfaktor merata wu [kN/m]
    mu_ultimate_knm: float = 0.0  # Momen ultimit Mu [kN·m]
    vu_ultimate_kn: float = 0.0   # Geser ultimit Vu [kN]

    # ── Geometri efektif ─────────────────────────────────────────────────────
    effective_depth_d_mm: float = 0.0  # Tinggi efektif d [mm]

    # ── Rasio tulangan ───────────────────────────────────────────────────────
    rho_min: float = 0.0        # Rasio tulangan minimum ρ_min [-]
    rho_max: float = 0.0        # Rasio tulangan maksimum ρ_max (0.75ρb) [-]
    rho_required: float = 0.0   # Rasio tulangan perlu ρ_req [-]
    beta1: float = 0.0          # Faktor blok tegangan β1 [-]

    # ── Luas tulangan ────────────────────────────────────────────────────────
    as_required_mm2: float = 0.0  # Luas tulangan perlu As_req [mm²]
    as_min_mm2: float = 0.0       # Luas tulangan minimum As_min [mm²]
    as_design_mm2: float = 0.0    # Luas tulangan desain As_design [mm²]
    bar_area_mm2: float = 0.0     # Luas satu batang tulangan [mm²]
    num_bars: int = 0             # Jumlah batang tulangan

    # ── Kapasitas lentur ─────────────────────────────────────────────────────
    a_block_mm: float = 0.0     # Tinggi blok tegangan ekivalen a [mm]
    mn_knm: float = 0.0         # Momen nominal Mn [kN·m]
    phi_factor: float = 0.90    # Faktor reduksi kekuatan φ [-]
    phi_mn_knm: float = 0.0     # Kapasitas momen tereduksi φMn [kN·m]
    capacity_ratio: float = 0.0  # Rasio Mu/φMn — harus ≤ 1.0 untuk AMAN [-]

    # ── Hasil ─────────────────────────────────────────────────────────────────
    status: DesignStatus = DesignStatus.TIDAK_AMAN

    # ── Meta ──────────────────────────────────────────────────────────────────
    meta: CalcMeta = field(default_factory=lambda: CalcMeta(
        formula_version="", standard_references="", disclaimer="", assumptions=""
    ))


@dataclass
class SteelBeamResult:
    """
    Hasil perhitungan desain lentur balok baja WF (LRFD).
    Semua field diberi satuan di nama dan di komentar.
    """
    # ── Profil yang digunakan ────────────────────────────────────────────────
    profile_designation: str = ""
    sx_cm3: float = 0.0         # Modulus penampang elastis Sx [cm³]
    zx_cm3: float = 0.0         # Modulus penampang plastis Zx [cm³]
    weight_per_m_kgm: float = 0.0  # Berat per meter [kg/m]

    # ── Beban terfaktor ──────────────────────────────────────────────────────
    self_weight_knm: float = 0.0  # Berat sendiri profil [kN/m]
    wu_knm: float = 0.0           # Beban terfaktor merata wu [kN/m]
    mu_ultimate_knm: float = 0.0  # Momen ultimit Mu [kN·m]

    # ── Cek kelangsingan sayap ───────────────────────────────────────────────
    lambda_f: float = 0.0       # Rasio kelangsingan sayap λ_f = (b/2)/tf [-]
    lambda_pf: float = 0.0      # Batas kompak λ_pf = 0.38√(E/Fy) [-]
    lambda_rf: float = 0.0      # Batas tidak kompak λ_rf = 1.0√(E/Fy) [-]
    is_compact: bool = True      # Apakah penampang kompak?

    # ── Kapasitas lentur ─────────────────────────────────────────────────────
    mp_knm: float = 0.0         # Momen plastis Mp = Fy·Zx [kN·m]
    mn_knm: float = 0.0         # Momen nominal Mn [kN·m] (= Mp jika kompak)
    phi_factor: float = 0.90    # Faktor reduksi kekuatan φ [-]
    phi_mn_knm: float = 0.0     # Kapasitas lentur tereduksi φMn [kN·m]
    capacity_ratio: float = 0.0  # Rasio Mu/φMn — harus ≤ 1.0 untuk AMAN [-]

    # ── Hasil ─────────────────────────────────────────────────────────────────
    status: DesignStatus = DesignStatus.TIDAK_AMAN

    # ── Meta ──────────────────────────────────────────────────────────────────
    meta: CalcMeta = field(default_factory=lambda: CalcMeta(
        formula_version="", standard_references="", disclaimer="", assumptions=""
    ))
