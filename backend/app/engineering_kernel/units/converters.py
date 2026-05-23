"""
Fungsi konversi satuan AG-SAS.
==============================
Semua fungsi bersifat pure (no side effects), deterministik, dan diuji unit.

Konvensi penamaan:
  <dari>_to_<ke>(value) -> float

Faktor konversi didefinisikan sebagai konstanta MODULE-LEVEL agar dapat
diinspeksi dan digunakan langsung tanpa memanggil fungsi.

PENTING: Jangan menambahkan konversi implisit di tempat lain.
         Seluruh konversi satuan harus melalui modul ini.
"""

import math

# ── Faktor konversi (konstanta) ───────────────────────────────────────────────

# Panjang
_MM_PER_M:  float = 1_000.0
_CM_PER_M:  float = 100.0
_MM_PER_CM: float = 10.0

# Gaya
_N_PER_KN:  float = 1_000.0

# Momen
_NMM_PER_KNM: float = 1_000_000.0   # 1 kN·m = 1e6 N·mm
_NM_PER_KNM:  float = 1_000.0        # 1 kN·m = 1e3 N·m

# Tegangan
# 1 MPa = 1 N/mm² = 1e6 N/m² = 1e6 Pa = 1000 kN/m²
_KN_M2_PER_MPA:  float = 1_000.0
_KN_M2_PER_KPA:  float = 1.0         # 1 kPa = 1 kN/m²

# Massa
_KG_PER_TON: float = 1_000.0

# Gravitasi
_G_M_S2: float = 9.81                # m/s² — percepatan gravitasi standar (ISO 80000-3)

# Luas
_MM2_PER_M2:  float = 1_000_000.0   # 1 m² = 1e6 mm²
_CM2_PER_M2:  float = 10_000.0      # 1 m² = 1e4 cm²
_MM2_PER_CM2: float = 100.0          # 1 cm² = 100 mm²

# Momen inersia
_MM4_PER_M4:  float = 1e12           # 1 m⁴ = 1e12 mm⁴
_CM4_PER_M4:  float = 1e8            # 1 m⁴ = 1e8 cm⁴
_MM4_PER_CM4: float = 1e4            # 1 cm⁴ = 1e4 mm⁴

# Modulus penampang (m³)
_MM3_PER_M3:  float = 1e9            # 1 m³ = 1e9 mm³
_CM3_PER_M3:  float = 1e6            # 1 m³ = 1e6 cm³
_MM3_PER_CM3: float = 1e3            # 1 cm³ = 1e3 mm³


# ── Panjang ───────────────────────────────────────────────────────────────────

def mm_to_m(value: float) -> float:
    """Konversi panjang: mm → m."""
    return value / _MM_PER_M


def m_to_mm(value: float) -> float:
    """Konversi panjang: m → mm."""
    return value * _MM_PER_M


def cm_to_m(value: float) -> float:
    """Konversi panjang: cm → m."""
    return value / _CM_PER_M


def m_to_cm(value: float) -> float:
    """Konversi panjang: m → cm."""
    return value * _CM_PER_M


def mm_to_cm(value: float) -> float:
    """Konversi panjang: mm → cm."""
    return value / _MM_PER_CM


def cm_to_mm(value: float) -> float:
    """Konversi panjang: cm → mm."""
    return value * _MM_PER_CM


# ── Gaya ──────────────────────────────────────────────────────────────────────

def n_to_kn(value: float) -> float:
    """Konversi gaya: N → kN."""
    return value / _N_PER_KN


def kn_to_n(value: float) -> float:
    """Konversi gaya: kN → N."""
    return value * _N_PER_KN


# ── Momen ────────────────────────────────────────────────────────────────────

def nmm_to_knm(value: float) -> float:
    """Konversi momen: N·mm → kN·m."""
    return value / _NMM_PER_KNM


def knm_to_nmm(value: float) -> float:
    """Konversi momen: kN·m → N·mm."""
    return value * _NMM_PER_KNM


def nm_to_knm(value: float) -> float:
    """Konversi momen: N·m → kN·m."""
    return value / _NM_PER_KNM


def knm_to_nm(value: float) -> float:
    """Konversi momen: kN·m → N·m."""
    return value * _NM_PER_KNM


# ── Tegangan ──────────────────────────────────────────────────────────────────

def mpa_to_kn_m2(value: float) -> float:
    """Konversi tegangan: MPa → kN/m²  (satuan internal solver)."""
    return value * _KN_M2_PER_MPA


def kn_m2_to_mpa(value: float) -> float:
    """Konversi tegangan: kN/m² → MPa."""
    return value / _KN_M2_PER_MPA


def kpa_to_kn_m2(value: float) -> float:
    """Konversi tekanan: kPa → kN/m²  (ekivalen: kPa ≡ kN/m²)."""
    return value * _KN_M2_PER_KPA


def kn_m2_to_kpa(value: float) -> float:
    """Konversi tekanan: kN/m² → kPa."""
    return value / _KN_M2_PER_KPA


# ── Massa ────────────────────────────────────────────────────────────────────

def kg_to_ton(value: float) -> float:
    """Konversi massa: kg → ton (metric)."""
    return value / _KG_PER_TON


def ton_to_kg(value: float) -> float:
    """Konversi massa: ton → kg."""
    return value * _KG_PER_TON


# ── Kerapatan / Berat jenis ───────────────────────────────────────────────────

def kg_m3_to_kn_m3(value: float) -> float:
    """
    Konversi kerapatan: kg/m³ → kN/m³ (berat jenis γ = ρg).
    Contoh: baja 7850 kg/m³ → 76.99 kN/m³
    """
    return value * _G_M_S2 / _N_PER_KN


def kn_m3_to_kg_m3(value: float) -> float:
    """Konversi berat jenis: kN/m³ → kerapatan kg/m³."""
    return value * _N_PER_KN / _G_M_S2


# ── Sudut ─────────────────────────────────────────────────────────────────────

def deg_to_rad(value: float) -> float:
    """Konversi sudut: derajat → radian."""
    return math.radians(value)


def rad_to_deg(value: float) -> float:
    """Konversi sudut: radian → derajat."""
    return math.degrees(value)


# ── Luas penampang ────────────────────────────────────────────────────────────

def mm2_to_m2(value: float) -> float:
    """Konversi luas: mm² → m²."""
    return value / _MM2_PER_M2


def m2_to_mm2(value: float) -> float:
    """Konversi luas: m² → mm²."""
    return value * _MM2_PER_M2


def cm2_to_m2(value: float) -> float:
    """Konversi luas: cm² → m²."""
    return value / _CM2_PER_M2


def m2_to_cm2(value: float) -> float:
    """Konversi luas: m² → cm²."""
    return value * _CM2_PER_M2


def mm2_to_cm2(value: float) -> float:
    """Konversi luas: mm² → cm²."""
    return value / _MM2_PER_CM2


def cm2_to_mm2(value: float) -> float:
    """Konversi luas: cm² → mm²."""
    return value * _MM2_PER_CM2


# ── Momen inersia ─────────────────────────────────────────────────────────────

def mm4_to_m4(value: float) -> float:
    """Konversi momen inersia: mm⁴ → m⁴."""
    return value / _MM4_PER_M4


def m4_to_mm4(value: float) -> float:
    """Konversi momen inersia: m⁴ → mm⁴."""
    return value * _MM4_PER_M4


def cm4_to_m4(value: float) -> float:
    """Konversi momen inersia: cm⁴ → m⁴."""
    return value / _CM4_PER_M4


def m4_to_cm4(value: float) -> float:
    """Konversi momen inersia: m⁴ → cm⁴."""
    return value * _CM4_PER_M4


def mm4_to_cm4(value: float) -> float:
    """Konversi momen inersia: mm⁴ → cm⁴."""
    return value / _MM4_PER_CM4


def cm4_to_mm4(value: float) -> float:
    """Konversi momen inersia: cm⁴ → mm⁴."""
    return value * _MM4_PER_CM4


# ── Modulus penampang ─────────────────────────────────────────────────────────

def mm3_to_m3(value: float) -> float:
    """Konversi modulus penampang: mm³ → m³."""
    return value / _MM3_PER_M3


def m3_to_mm3(value: float) -> float:
    """Konversi modulus penampang: m³ → mm³."""
    return value * _MM3_PER_M3


def cm3_to_m3(value: float) -> float:
    """Konversi modulus penampang: cm³ → m³."""
    return value / _CM3_PER_M3


def m3_to_cm3(value: float) -> float:
    """Konversi modulus penampang: m³ → cm³."""
    return value * _CM3_PER_M3


def mm3_to_cm3(value: float) -> float:
    """Konversi modulus penampang: mm³ → cm³."""
    return value / _MM3_PER_CM3


def cm3_to_mm3(value: float) -> float:
    """Konversi modulus penampang: cm³ → mm³."""
    return value * _MM3_PER_CM3
