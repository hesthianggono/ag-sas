"""
Quantity — nilai bertanda satuan.
==================================
Membungkus nilai numerik bersama satuannya agar tidak ada nilai "telanjang"
yang melayang tanpa konteks satuan di antarmuka publik.

Penggunaan:
    span = Quantity(6.0, LengthUnit.M)
    load = Quantity(25.0, ForceUnit.KN)
    moment = Quantity(150.0, MomentUnit.KN_M)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union

from app.engineering_kernel.units.enums import (
    LengthUnit, ForceUnit, MomentUnit, StressUnit,
    MassUnit, DensityUnit, AngleUnit,
    ForcePerLengthUnit, AreaUnit, SectionModulusUnit, MomentOfInertiaUnit,
)

# Semua enum satuan yang valid
_AnyUnit = Union[
    LengthUnit, ForceUnit, MomentUnit, StressUnit,
    MassUnit, DensityUnit, AngleUnit,
    ForcePerLengthUnit, AreaUnit, SectionModulusUnit, MomentOfInertiaUnit,
    str,  # fallback untuk satuan custom/composite
]


@dataclass(frozen=True)
class Quantity:
    """
    Nilai fisika dengan satuan eksplisit.

    Attributes:
        value: Nilai numerik.
        unit:  Satuan dari enum AG-SAS atau string custom.

    Contoh:
        >>> q = Quantity(200_000.0, StressUnit.MPA)
        >>> q.value
        200000.0
        >>> q.unit
        <StressUnit.MPA: 'MPa'>
    """
    value: float
    unit: _AnyUnit

    def __repr__(self) -> str:
        unit_str = self.unit.value if hasattr(self.unit, "value") else str(self.unit)
        return f"Quantity({self.value} {unit_str})"

    def __str__(self) -> str:
        unit_str = self.unit.value if hasattr(self.unit, "value") else str(self.unit)
        return f"{self.value} {unit_str}"

    def is_positive(self) -> bool:
        return self.value > 0

    def is_zero(self, tol: float = 1e-12) -> bool:
        return abs(self.value) < tol

    def is_negative(self) -> bool:
        return self.value < 0
