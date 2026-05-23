"""
Model material struktur AG-SAS.

Semua properti material disimpan dalam satuan internal solver:
  E, G  : kN/m²
  fy, fc: kN/m²
  rho   : kg/m³
  alpha : /°C

Konversi ke MPa dilakukan di boundary modul (concrete/steel calculator).
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.engineering_kernel.units.converters import mpa_to_kn_m2, kg_m3_to_kn_m3


class MaterialType(str, Enum):
    """Tipe material."""
    STEEL    = "steel"
    CONCRETE = "concrete"
    TIMBER   = "timber"
    CUSTOM   = "custom"


@dataclass
class Material:
    """
    Properti material untuk analisis dan desain struktur.

    Semua nilai dalam satuan internal solver (kN, m) kecuali rho (kg/m³).

    Attributes:
        id:           Identifikasi unik (e.g. "BJ41", "fc25")
        name:         Nama deskriptif
        type:         Tipe material (MaterialType)
        E_kn_m2:      Modulus elastisitas [kN/m²]
        G_kn_m2:      Modulus geser [kN/m²]
        nu:           Rasio Poisson [-]
        rho_kg_m3:    Kerapatan massa [kg/m³]
        alpha_per_C:  Koefisien ekspansi termal [1/°C]
        fy_kn_m2:     Tegangan leleh [kN/m²] — baja, None untuk beton
        fu_kn_m2:     Tegangan ultimate [kN/m²] — baja, None untuk beton
        fc_kn_m2:     Kuat tekan [kN/m²] — beton, None untuk baja
        description:  Referensi standar / catatan
    """
    id: str
    name: str
    type: MaterialType
    E_kn_m2: float          # [kN/m²]
    G_kn_m2: float          # [kN/m²]
    nu: float               # [-]
    rho_kg_m3: float        # [kg/m³]
    alpha_per_C: float      # [1/°C]
    fy_kn_m2: Optional[float] = None   # [kN/m²] — baja
    fu_kn_m2: Optional[float] = None   # [kN/m²] — baja
    fc_kn_m2: Optional[float] = None   # [kN/m²] — beton
    description: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("Material.id tidak boleh kosong.")
        if self.E_kn_m2 <= 0:
            errors.append(f"Material '{self.id}': E_kn_m2 harus > 0.")
        if self.G_kn_m2 <= 0:
            errors.append(f"Material '{self.id}': G_kn_m2 harus > 0.")
        if not (0.0 <= self.nu < 0.5):
            errors.append(
                f"Material '{self.id}': rasio Poisson nu={self.nu} tidak valid "
                "(harus 0.0 ≤ nu < 0.5)."
            )
        if self.rho_kg_m3 <= 0:
            errors.append(f"Material '{self.id}': rho_kg_m3 harus > 0.")
        if self.alpha_per_C < 0:
            errors.append(f"Material '{self.id}': alpha_per_C harus ≥ 0.")
        if self.type == MaterialType.STEEL:
            if self.fy_kn_m2 is None:
                errors.append(f"Material baja '{self.id}': fy_kn_m2 wajib diisi.")
            elif self.fy_kn_m2 <= 0:
                errors.append(f"Material '{self.id}': fy_kn_m2 harus > 0.")
        if self.type == MaterialType.CONCRETE:
            if self.fc_kn_m2 is None:
                errors.append(f"Material beton '{self.id}': fc_kn_m2 wajib diisi.")
            elif self.fc_kn_m2 <= 0:
                errors.append(f"Material '{self.id}': fc_kn_m2 harus > 0.")
        return errors

    # ── Konversi praktis ──────────────────────────────────────────────────────

    @property
    def E_gpa(self) -> float:
        """Modulus elastisitas dalam GPa (untuk display)."""
        return self.E_kn_m2 / 1_000_000.0

    @property
    def fy_mpa(self) -> Optional[float]:
        """Tegangan leleh dalam MPa (untuk display dan design check)."""
        if self.fy_kn_m2 is None:
            return None
        return self.fy_kn_m2 / 1_000.0

    @property
    def fu_mpa(self) -> Optional[float]:
        """Tegangan ultimate dalam MPa."""
        if self.fu_kn_m2 is None:
            return None
        return self.fu_kn_m2 / 1_000.0

    @property
    def fc_mpa(self) -> Optional[float]:
        """Kuat tekan beton dalam MPa."""
        if self.fc_kn_m2 is None:
            return None
        return self.fc_kn_m2 / 1_000.0

    @property
    def gamma_kn_m3(self) -> float:
        """Berat jenis (weight density) γ = ρg [kN/m³]."""
        return kg_m3_to_kn_m3(self.rho_kg_m3)


# ── Preset material standar ───────────────────────────────────────────────────
# Nilai berdasarkan SNI 1729:2020 (baja) dan SNI 2847:2019 (beton)

STEEL_BJ37 = Material(
    id="BJ37",
    name="Baja BJ-37 (SNI 1729:2020)",
    type=MaterialType.STEEL,
    E_kn_m2=mpa_to_kn_m2(200_000.0),   # 200 GPa
    G_kn_m2=mpa_to_kn_m2(77_000.0),    # 77 GPa
    nu=0.30,
    rho_kg_m3=7_850.0,
    alpha_per_C=1.2e-5,
    fy_kn_m2=mpa_to_kn_m2(240.0),      # 240 MPa
    fu_kn_m2=mpa_to_kn_m2(370.0),      # 370 MPa
    description="SNI 1729:2020 — Baja BJ-37, Fy=240 MPa, Fu=370 MPa",
)

STEEL_BJ41 = Material(
    id="BJ41",
    name="Baja BJ-41 (SNI 1729:2020)",
    type=MaterialType.STEEL,
    E_kn_m2=mpa_to_kn_m2(200_000.0),
    G_kn_m2=mpa_to_kn_m2(77_000.0),
    nu=0.30,
    rho_kg_m3=7_850.0,
    alpha_per_C=1.2e-5,
    fy_kn_m2=mpa_to_kn_m2(250.0),      # 250 MPa
    fu_kn_m2=mpa_to_kn_m2(410.0),      # 410 MPa
    description="SNI 1729:2020 — Baja BJ-41, Fy=250 MPa, Fu=410 MPa",
)

CONCRETE_FC21 = Material(
    id="fc21",
    name="Beton fc'=21 MPa (SNI 2847:2019)",
    type=MaterialType.CONCRETE,
    E_kn_m2=mpa_to_kn_m2(4700.0 * (21.0 ** 0.5)),   # Ec = 4700√fc' MPa
    G_kn_m2=mpa_to_kn_m2(4700.0 * (21.0 ** 0.5) / (2 * (1 + 0.2))),
    nu=0.20,
    rho_kg_m3=2_400.0,
    alpha_per_C=1.0e-5,
    fc_kn_m2=mpa_to_kn_m2(21.0),
    description="SNI 2847:2019 — fc'=21 MPa, Ec=4700√fc' MPa",
)

CONCRETE_FC25 = Material(
    id="fc25",
    name="Beton fc'=25 MPa (SNI 2847:2019)",
    type=MaterialType.CONCRETE,
    E_kn_m2=mpa_to_kn_m2(4700.0 * (25.0 ** 0.5)),   # ≈ 23,500 MPa
    G_kn_m2=mpa_to_kn_m2(4700.0 * (25.0 ** 0.5) / (2 * (1 + 0.2))),
    nu=0.20,
    rho_kg_m3=2_400.0,
    alpha_per_C=1.0e-5,
    fc_kn_m2=mpa_to_kn_m2(25.0),
    description="SNI 2847:2019 — fc'=25 MPa, Ec≈23,500 MPa",
)

CONCRETE_FC30 = Material(
    id="fc30",
    name="Beton fc'=30 MPa (SNI 2847:2019)",
    type=MaterialType.CONCRETE,
    E_kn_m2=mpa_to_kn_m2(4700.0 * (30.0 ** 0.5)),   # ≈ 25,743 MPa
    G_kn_m2=mpa_to_kn_m2(4700.0 * (30.0 ** 0.5) / (2 * (1 + 0.2))),
    nu=0.20,
    rho_kg_m3=2_400.0,
    alpha_per_C=1.0e-5,
    fc_kn_m2=mpa_to_kn_m2(30.0),
    description="SNI 2847:2019 — fc'=30 MPa, Ec≈25,743 MPa",
)

# Dict lookup untuk kemudahan akses
MATERIAL_PRESETS: dict[str, Material] = {
    m.id: m for m in [STEEL_BJ37, STEEL_BJ41, CONCRETE_FC21, CONCRETE_FC25, CONCRETE_FC30]
}
