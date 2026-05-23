"""
Model hasil analisis dan pemeriksaan desain AG-SAS.

Semua nilai dalam satuan internal solver (kN, m, kN·m).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DesignCheckStatus(str, Enum):
    """Status hasil pemeriksaan kapasitas elemen."""
    AMAN       = "AMAN"
    TIDAK_AMAN = "TIDAK AMAN"
    ERROR      = "ERROR"
    NOT_CHECKED = "BELUM DIPERIKSA"


# ── Displacement nodal ────────────────────────────────────────────────────────

@dataclass
class NodeDisplacement:
    """
    Perpindahan node hasil analisis.

    Satuan: translasi [m], rotasi [rad].
    Konvensi: positif searah sumbu global positif (lihat sign_convention.py).
    """
    node_id: str
    ux_m:   float = 0.0    # translasi X [m]
    uy_m:   float = 0.0    # translasi Y [m]
    uz_m:   float = 0.0    # translasi Z [m] — 0 untuk model 2D
    rx_rad: float = 0.0    # rotasi X [rad] — 0 untuk model 2D
    ry_rad: float = 0.0    # rotasi Y [rad] — 0 untuk model 2D
    rz_rad: float = 0.0    # rotasi Z [rad]

    @property
    def resultant_translation_m(self) -> float:
        """Besar resultante perpindahan translasi [m]."""
        return (self.ux_m**2 + self.uy_m**2 + self.uz_m**2) ** 0.5

    def to_mm(self) -> dict[str, float]:
        """Perpindahan dalam mm untuk display."""
        return {
            "ux_mm": self.ux_m * 1000,
            "uy_mm": self.uy_m * 1000,
            "uz_mm": self.uz_m * 1000,
        }


# ── Reaksi perletakan ─────────────────────────────────────────────────────────

@dataclass
class NodeReaction:
    """
    Gaya reaksi pada node perletakan.

    Satuan: gaya [kN], momen [kN·m].
    Konvensi: reaksi positif = perletakan mendorong node dalam arah positif.
    """
    node_id: str
    rx_kn:   float = 0.0
    ry_kn:   float = 0.0
    rz_kn:   float = 0.0
    rmx_knm: float = 0.0
    rmy_knm: float = 0.0
    rmz_knm: float = 0.0


# ── Gaya dalam elemen ─────────────────────────────────────────────────────────

@dataclass
class ElementEndForces:
    """
    Gaya dalam di ujung elemen dalam koordinat LOKAL elemen.

    Notasi: _i = ujung node I (start), _j = ujung node J (end).

    Konvensi gaya:
      N   > 0 = tarik (tension)
      V   > 0 = geser naik pada muka kiri (lihat sign_convention.py)
      Mz  > 0 = sagging (serat bawah tarik)
      Mx  > 0 = torsi positif (right-hand rule terhadap x_lokal)

    Satuan: N [kN], V [kN], M [kN·m].
    """
    element_id: str
    # Ujung I
    N_i_kn:   float = 0.0
    Vy_i_kn:  float = 0.0
    Vz_i_kn:  float = 0.0    # 0 untuk model 2D
    Mx_i_knm: float = 0.0    # torsi, 0 untuk model 2D
    My_i_knm: float = 0.0    # 0 untuk model 2D
    Mz_i_knm: float = 0.0
    # Ujung J
    N_j_kn:   float = 0.0
    Vy_j_kn:  float = 0.0
    Vz_j_kn:  float = 0.0
    Mx_j_knm: float = 0.0
    My_j_knm: float = 0.0
    Mz_j_knm: float = 0.0

    @property
    def N_max_kn(self) -> float:
        return max(self.N_i_kn, self.N_j_kn)

    @property
    def N_min_kn(self) -> float:
        return min(self.N_i_kn, self.N_j_kn)

    @property
    def M_max_knm(self) -> float:
        return max(abs(self.Mz_i_knm), abs(self.Mz_j_knm))

    @property
    def V_max_kn(self) -> float:
        return max(abs(self.Vy_i_kn), abs(self.Vy_j_kn))


# ── Hasil analisis ────────────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    """
    Hasil lengkap satu run analisis untuk satu load case atau kombinasi.

    Attributes:
        load_case_id:       ID load case atau kombinasi yang menghasilkan ini
        displacements:      Perpindahan nodal
        reactions:          Reaksi perletakan
        element_forces:     Gaya dalam ujung elemen
        converged:          Apakah solver konvergen?
        message:            Pesan dari solver (warning, info konvergensi)
        max_disp_m:         Perpindahan maksimum [m]
        max_moment_knm:     Momen maksimum [kN·m]
        max_shear_kn:       Geser maksimum [kN]
        max_axial_kn:       Gaya aksial maksimum [kN]
        controlling_node:   ID node dengan displacement maksimum
        controlling_element: ID elemen dengan gaya dalam maksimum
    """
    load_case_id: str
    displacements: list[NodeDisplacement] = field(default_factory=list)
    reactions: list[NodeReaction] = field(default_factory=list)
    element_forces: list[ElementEndForces] = field(default_factory=list)
    converged: bool = False
    message: str = ""
    # Statistik (diisi setelah post-processing)
    max_disp_m: float = 0.0
    max_moment_knm: float = 0.0
    max_shear_kn: float = 0.0
    max_axial_kn: float = 0.0
    controlling_node: str = ""
    controlling_element: str = ""

    def get_displacement(self, node_id: str) -> Optional[NodeDisplacement]:
        """Cari displacement untuk node tertentu."""
        for d in self.displacements:
            if d.node_id == node_id:
                return d
        return None

    def get_reaction(self, node_id: str) -> Optional[NodeReaction]:
        """Cari reaksi untuk node tertentu."""
        for r in self.reactions:
            if r.node_id == node_id:
                return r
        return None

    def get_element_forces(self, element_id: str) -> Optional[ElementEndForces]:
        """Cari gaya dalam untuk elemen tertentu."""
        for f in self.element_forces:
            if f.element_id == element_id:
                return f
        return None


# ── Hasil pemeriksaan desain ──────────────────────────────────────────────────

@dataclass
class DesignCheckResult:
    """
    Hasil pemeriksaan kapasitas elemen (steel atau concrete design check).

    Semua rasio utilisasi harus ≤ 1.0 untuk status AMAN.

    Attributes:
        element_id:          ID elemen yang diperiksa
        check_type:          Tipe check: "steel_lrfd", "concrete_sni", dll.
        status:              Status akhir (DesignCheckStatus)
        controlling_combo:   Nama kombinasi beban yang mengontrol
        -- Rasio utilisasi --
        moment_ratio:        Mu/φMn
        shear_ratio:         Vu/φVn
        axial_ratio:         Pu/φPn
        interaction_ratio:   Nilai interaksi aksial-momen (H1-1 untuk baja)
        -- Kapasitas --
        phi_Mn_knm:          Kapasitas lentur tereduksi [kN·m]
        phi_Vn_kn:           Kapasitas geser tereduksi [kN]
        phi_Pn_kn:           Kapasitas aksial tereduksi [kN]
        -- Gaya design --
        Mu_knm:              Momen design [kN·m]
        Vu_kn:               Geser design [kN]
        Pu_kn:               Aksial design [kN]
        -- Metadata --
        notes:               Catatan hasil (kompak/non-kompak, LTB mode, dll.)
        warnings:            Peringatan yang dihasilkan saat check
    """
    element_id: str
    check_type: str
    status: DesignCheckStatus = DesignCheckStatus.NOT_CHECKED
    controlling_combo: str = ""
    # Rasio utilisasi
    moment_ratio: float = 0.0
    shear_ratio: float = 0.0
    axial_ratio: float = 0.0
    interaction_ratio: float = 0.0
    # Kapasitas
    phi_Mn_knm: float = 0.0
    phi_Vn_kn: float = 0.0
    phi_Pn_kn: float = 0.0
    # Gaya design
    Mu_knm: float = 0.0
    Vu_kn: float = 0.0
    Pu_kn: float = 0.0
    # Metadata
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        return self.status == DesignCheckStatus.AMAN

    @property
    def critical_ratio(self) -> float:
        """Rasio utilisasi paling kritis (tertinggi)."""
        return max(
            self.moment_ratio,
            self.shear_ratio,
            self.axial_ratio,
            self.interaction_ratio,
        )
