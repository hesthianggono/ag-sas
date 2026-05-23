"""
Enum satuan resmi AG-SAS.
Digunakan untuk menandai satuan pada Quantity dan di struktur data.
"""

from enum import Enum


class LengthUnit(str, Enum):
    """Satuan panjang."""
    MM = "mm"
    CM = "cm"
    M  = "m"


class ForceUnit(str, Enum):
    """Satuan gaya."""
    N  = "N"
    KN = "kN"


class MomentUnit(str, Enum):
    """Satuan momen / torsi."""
    N_MM  = "N·mm"
    N_M   = "N·m"
    KN_M  = "kN·m"


class StressUnit(str, Enum):
    """Satuan tegangan / tekanan."""
    PA    = "Pa"      # N/m²
    KPA   = "kPa"     # kN/m²  (= 1 kN/m²)
    MPA   = "MPa"     # N/mm²  (= 1000 kN/m²)
    KN_M2 = "kN/m²"  # satuan internal solver


class MassUnit(str, Enum):
    """Satuan massa."""
    KG  = "kg"
    TON = "ton"     # metric ton = 1000 kg


class DensityUnit(str, Enum):
    """Satuan kerapatan massa."""
    KG_M3 = "kg/m³"
    KN_M3 = "kN/m³"   # kerapatan berat (γ = ρg)


class AngleUnit(str, Enum):
    """Satuan sudut."""
    DEG = "deg"
    RAD = "rad"


class ForcePerLengthUnit(str, Enum):
    """Satuan beban merata (gaya per panjang)."""
    N_M  = "N/m"
    KN_M = "kN/m"


class AreaUnit(str, Enum):
    """Satuan luas penampang."""
    MM2 = "mm²"
    CM2 = "cm²"
    M2  = "m²"


class SectionModulusUnit(str, Enum):
    """Satuan modulus penampang (elastis / plastis)."""
    MM3 = "mm³"
    CM3 = "cm³"
    M3  = "m³"


class MomentOfInertiaUnit(str, Enum):
    """Satuan momen inersia."""
    MM4 = "mm⁴"
    CM4 = "cm⁴"
    M4  = "m⁴"
