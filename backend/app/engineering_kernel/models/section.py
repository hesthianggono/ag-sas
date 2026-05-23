"""
Model properti penampang AG-SAS.

Semua properti penampang dalam satuan meter (m, m², m³, m⁴) — satuan internal solver.
Konversi dari mm/cm dilakukan di lapisan input (service layer / API schema).
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.engineering_kernel.units.converters import (
    mm2_to_m2, cm2_to_m2,
    mm4_to_m4, cm4_to_m4,
    mm3_to_m3, cm3_to_m3,
    mm_to_m, cm_to_m,
)


class SectionType(str, Enum):
    """Tipe profil penampang."""
    WF        = "WF"          # Wide Flange / I-section (baja)
    HSS_RECT  = "HSS_rect"   # Hollow Structural Section — persegi panjang
    HSS_CIR   = "HSS_cir"    # Hollow Structural Section — lingkaran
    RECT      = "rect"        # Persegi padat (beton)
    CIRCULAR  = "circular"   # Lingkaran padat
    T_SECTION = "T"           # T-section
    L_SECTION = "L"           # L-section / angle
    CUSTOM    = "custom"      # Penampang custom


@dataclass
class SectionProperties:
    """
    Properti penampang elemen struktur.

    Semua nilai dalam satuan SI/m (satuan internal solver):
      Panjang   : m
      Luas      : m²
      Inersia   : m⁴
      Modulus   : m³

    Catatan: Database dan antarmuka pengguna menggunakan mm/cm.
    Konversi dilakukan di service layer sebelum diteruskan ke solver.

    Attributes:
        id:        Identifikasi unik
        name:      Nama profil (e.g. "WF 400x200x8x13")
        type:      Tipe penampang
        A_m2:      Luas penampang [m²]
        Ix_m4:     Momen inersia lentur mayor (sumbu kuat) [m⁴]
        Iy_m4:     Momen inersia lentur minor (sumbu lemah) [m⁴]
        J_m4:      Konstanta torsi [m⁴]
        Zx_m3:     Modulus plastis mayor [m³]
        Zy_m3:     Modulus plastis minor [m³]
        Sx_m3:     Modulus elastis mayor [m³]
        Sy_m3:     Modulus elastis minor [m³]
        rx_m:      Jari-jari girasi mayor [m]
        ry_m:      Jari-jari girasi minor [m]
        -- Dimensi geometri (untuk design check) --
        h_m:       Tinggi total [m]
        bf_m:      Lebar sayap [m]
        tw_m:      Tebal badan [m]
        tf_m:      Tebal sayap [m]
        description: Referensi / catatan
    """
    id: str
    name: str
    type: SectionType
    A_m2: float
    Ix_m4: float
    Iy_m4: float
    J_m4: float
    Zx_m3: float
    Zy_m3: float
    Sx_m3: float
    Sy_m3: float
    rx_m: float = 0.0
    ry_m: float = 0.0
    # Dimensi geometri (opsional, diisi untuk design check)
    h_m: Optional[float] = None
    bf_m: Optional[float] = None
    tw_m: Optional[float] = None
    tf_m: Optional[float] = None
    description: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("SectionProperties.id tidak boleh kosong.")
        for attr, label in [
            ("A_m2", "Luas A"), ("Ix_m4", "Inersia Ix"),
            ("Iy_m4", "Inersia Iy"), ("J_m4", "Konstanta torsi J"),
            ("Zx_m3", "Modulus plastis Zx"), ("Sx_m3", "Modulus elastis Sx"),
        ]:
            val = getattr(self, attr)
            if val <= 0:
                errors.append(
                    f"SectionProperties '{self.id}': {label} = {val} harus > 0."
                )
        return errors

    # ── Konversi display (untuk laporan dan UI) ───────────────────────────────

    @property
    def A_cm2(self) -> float:
        return self.A_m2 * 1e4

    @property
    def A_mm2(self) -> float:
        return self.A_m2 * 1e6

    @property
    def Ix_cm4(self) -> float:
        return self.Ix_m4 * 1e8

    @property
    def Iy_cm4(self) -> float:
        return self.Iy_m4 * 1e8

    @property
    def Zx_cm3(self) -> float:
        return self.Zx_m3 * 1e6

    @property
    def Sx_cm3(self) -> float:
        return self.Sx_m3 * 1e6

    @property
    def ry_cm(self) -> float:
        return self.ry_m * 100.0

    @property
    def rx_cm(self) -> float:
        return self.rx_m * 100.0

    # ── Factory methods dari satuan pengguna ──────────────────────────────────

    @classmethod
    def from_mm_units(
        cls,
        id: str,
        name: str,
        type: SectionType,
        A_mm2: float,
        Ix_mm4: float,
        Iy_mm4: float,
        J_mm4: float,
        Zx_mm3: float,
        Zy_mm3: float,
        Sx_mm3: float,
        Sy_mm3: float,
        rx_mm: float = 0.0,
        ry_mm: float = 0.0,
        h_mm: Optional[float] = None,
        bf_mm: Optional[float] = None,
        tw_mm: Optional[float] = None,
        tf_mm: Optional[float] = None,
        description: str = "",
    ) -> "SectionProperties":
        """Buat SectionProperties dari nilai dalam satuan mm/mm²/mm⁴."""
        return cls(
            id=id, name=name, type=type,
            A_m2=mm2_to_m2(A_mm2),
            Ix_m4=mm4_to_m4(Ix_mm4),
            Iy_m4=mm4_to_m4(Iy_mm4),
            J_m4=mm4_to_m4(J_mm4),
            Zx_m3=mm3_to_m3(Zx_mm3),
            Zy_m3=mm3_to_m3(Zy_mm3),
            Sx_m3=mm3_to_m3(Sx_mm3),
            Sy_m3=mm3_to_m3(Sy_mm3),
            rx_m=mm_to_m(rx_mm),
            ry_m=mm_to_m(ry_mm),
            h_m=mm_to_m(h_mm) if h_mm is not None else None,
            bf_m=mm_to_m(bf_mm) if bf_mm is not None else None,
            tw_m=mm_to_m(tw_mm) if tw_mm is not None else None,
            tf_m=mm_to_m(tf_mm) if tf_mm is not None else None,
            description=description,
        )

    @classmethod
    def from_cm_units(
        cls,
        id: str,
        name: str,
        type: SectionType,
        A_cm2: float,
        Ix_cm4: float,
        Iy_cm4: float,
        J_cm4: float,
        Zx_cm3: float,
        Zy_cm3: float,
        Sx_cm3: float,
        Sy_cm3: float,
        rx_cm: float = 0.0,
        ry_cm: float = 0.0,
        h_mm: Optional[float] = None,
        bf_mm: Optional[float] = None,
        tw_mm: Optional[float] = None,
        tf_mm: Optional[float] = None,
        description: str = "",
    ) -> "SectionProperties":
        """Buat SectionProperties dari nilai dalam satuan cm²/cm⁴ (umum di tabel baja Indonesia)."""
        return cls(
            id=id, name=name, type=type,
            A_m2=cm2_to_m2(A_cm2),
            Ix_m4=cm4_to_m4(Ix_cm4),
            Iy_m4=cm4_to_m4(Iy_cm4),
            J_m4=cm4_to_m4(J_cm4),
            Zx_m3=cm3_to_m3(Zx_cm3),
            Zy_m3=cm3_to_m3(Zy_cm3),
            Sx_m3=cm3_to_m3(Sx_cm3),
            Sy_m3=cm3_to_m3(Sy_cm3),
            rx_m=cm_to_m(rx_cm),
            ry_m=cm_to_m(ry_cm),
            h_m=mm_to_m(h_mm) if h_mm is not None else None,
            bf_m=mm_to_m(bf_mm) if bf_mm is not None else None,
            tw_m=mm_to_m(tw_mm) if tw_mm is not None else None,
            tf_m=mm_to_m(tf_mm) if tf_mm is not None else None,
            description=description,
        )
