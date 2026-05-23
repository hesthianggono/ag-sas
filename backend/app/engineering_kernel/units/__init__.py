"""
AG-SAS Unit System
==================
Sistem satuan, enum, dan fungsi konversi resmi AG-SAS.

Satuan internal solver (digunakan di dalam semua modul solver):
  Gaya      : kN
  Panjang   : m
  Momen     : kN·m
  Tegangan  : kN/m²  (bukan MPa — konversi di boundary modul)
  Massa     : kg
  Sudut     : radian

Satuan antarmuka (input/output ke user dan DB):
  Dimensi penampang  : mm
  Tegangan           : MPa (= N/mm² = 1000 kN/m²)
  Modulus penampang  : cm³
  Momen inersia      : cm⁴
  Berat profil       : kg/m
"""

from app.engineering_kernel.units.enums import (
    LengthUnit,
    ForceUnit,
    MomentUnit,
    StressUnit,
    MassUnit,
    DensityUnit,
    AngleUnit,
)
from app.engineering_kernel.units.converters import (
    # Panjang
    mm_to_m,
    m_to_mm,
    cm_to_m,
    m_to_cm,
    mm_to_cm,
    cm_to_mm,
    # Gaya
    n_to_kn,
    kn_to_n,
    # Momen
    nmm_to_knm,
    knm_to_nmm,
    nm_to_knm,
    knm_to_nm,
    # Tegangan
    mpa_to_kn_m2,
    kn_m2_to_mpa,
    kpa_to_kn_m2,
    kn_m2_to_kpa,
    # Massa
    ton_to_kg,
    kg_to_ton,
    # Sudut
    deg_to_rad,
    rad_to_deg,
    # Luas dan inersia
    mm2_to_m2,
    m2_to_mm2,
    cm2_to_m2,
    m2_to_cm2,
    mm4_to_m4,
    m4_to_mm4,
    cm4_to_m4,
    m4_to_cm4,
    mm3_to_m3,
    m3_to_mm3,
    cm3_to_m3,
    m3_to_cm3,
    # Kerapatan
    kg_m3_to_kn_m3,
)
from app.engineering_kernel.units.quantity import Quantity

__all__ = [
    "LengthUnit", "ForceUnit", "MomentUnit", "StressUnit",
    "MassUnit", "DensityUnit", "AngleUnit",
    "mm_to_m", "m_to_mm", "cm_to_m", "m_to_cm", "mm_to_cm", "cm_to_mm",
    "n_to_kn", "kn_to_n",
    "nmm_to_knm", "knm_to_nmm", "nm_to_knm", "knm_to_nm",
    "mpa_to_kn_m2", "kn_m2_to_mpa", "kpa_to_kn_m2", "kn_m2_to_kpa",
    "ton_to_kg", "kg_to_ton",
    "deg_to_rad", "rad_to_deg",
    "mm2_to_m2", "m2_to_mm2", "cm2_to_m2", "m2_to_cm2",
    "mm4_to_m4", "m4_to_mm4", "cm4_to_m4", "m4_to_cm4",
    "mm3_to_m3", "m3_to_mm3", "cm3_to_m3", "m3_to_cm3",
    "kg_m3_to_kn_m3",
    "Quantity",
]
