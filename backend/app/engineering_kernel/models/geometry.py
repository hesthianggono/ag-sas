"""
Model geometri struktur: Node, Element, Support.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    """
    Node (titik simpul) dalam model struktur.

    Koordinat dalam satuan meter (m) — satuan internal solver AG-SAS.
    Koordinat z = 0.0 untuk model 2D.

    Attributes:
        id:          Identifikasi unik (string, e.g. "N1", "N-base-left")
        x_m:         Koordinat X global [m]
        y_m:         Koordinat Y global [m]
        z_m:         Koordinat Z global [m] — 0.0 untuk model 2D
        name:        Nama deskriptif opsional (e.g. "Tumpuan kiri")
        description: Catatan tambahan
    """
    id: str
    x_m: float
    y_m: float
    z_m: float = 0.0
    name: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Node.id tidak boleh kosong.")

    def validate(self) -> list[str]:
        """Validasi teknis node. Returns daftar pesan error."""
        errors: list[str] = []
        if not self.id.strip():
            errors.append("Node.id tidak boleh kosong.")
        return errors

    @property
    def coords_2d(self) -> tuple[float, float]:
        """Koordinat (x, y) dalam meter."""
        return self.x_m, self.y_m

    @property
    def coords_3d(self) -> tuple[float, float, float]:
        """Koordinat (x, y, z) dalam meter."""
        return self.x_m, self.y_m, self.z_m


@dataclass
class Element:
    """
    Elemen batang (beam-column) dalam model struktur.

    Elemen menghubungkan dua node (I dan J) dan membawa properti
    material dan penampang.

    Attributes:
        id:           Identifikasi unik (e.g. "E1", "COL-1")
        node_i_id:    ID node awal (start node I)
        node_j_id:    ID node akhir (end node J)
        material_id:  Referensi ke Material.id
        section_id:   Referensi ke SectionProperties.id
        element_type: Tipe elemen: "beam", "column", "brace", "general"
        name:         Nama deskriptif opsional
        description:  Catatan tambahan
        local_z:      Vektor z lokal opsional untuk elemen 3D (tuple 3 float)
                      Jika None, dihitung otomatis dari geometri.
    """
    id: str
    node_i_id: str
    node_j_id: str
    material_id: str
    section_id: str
    element_type: str = "general"      # "beam" | "column" | "brace" | "general"
    name: str = ""
    description: str = ""
    local_z: Optional[tuple[float, float, float]] = None

    _VALID_TYPES = frozenset({"beam", "column", "brace", "general"})

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Element.id tidak boleh kosong.")
        if self.node_i_id == self.node_j_id:
            raise ValueError(
                f"Element '{self.id}': node_i_id dan node_j_id tidak boleh sama "
                f"(keduanya = '{self.node_i_id}'). Elemen harus menghubungkan dua node berbeda."
            )

    def validate(self) -> list[str]:
        """Validasi teknis elemen. Returns daftar pesan error."""
        errors: list[str] = []
        if not self.id.strip():
            errors.append("Element.id tidak boleh kosong.")
        if self.node_i_id == self.node_j_id:
            errors.append(
                f"Element '{self.id}': node_i dan node_j tidak boleh sama."
            )
        if self.element_type not in self._VALID_TYPES:
            errors.append(
                f"Element '{self.id}': element_type '{self.element_type}' tidak valid. "
                f"Pilihan: {sorted(self._VALID_TYPES)}"
            )
        if not self.material_id.strip():
            errors.append(f"Element '{self.id}': material_id tidak boleh kosong.")
        if not self.section_id.strip():
            errors.append(f"Element '{self.id}': section_id tidak boleh kosong.")
        if self.local_z is not None:
            if len(self.local_z) != 3:
                errors.append(f"Element '{self.id}': local_z harus tuple 3 float.")
            mag = sum(v**2 for v in self.local_z) ** 0.5
            if mag < 1e-10:
                errors.append(f"Element '{self.id}': local_z tidak boleh vektor nol.")
        return errors


@dataclass
class Support:
    """
    Kondisi batas perletakan pada node.

    DOF (Degree of Freedom):
      2D: [ux, uy, rz]
      3D: [ux, uy, uz, rx, ry, rz]
      True = tertahan (restrained), False = bebas (free)

    Tipe perletakan umum:
      fixed  : semua DOF tertahan
      pinned : translasi tertahan, rotasi bebas
      roller : satu arah translasi tertahan, sisanya bebas
    """
    node_id: str
    ux: bool = False    # translasi X tertahan?
    uy: bool = False    # translasi Y tertahan?
    uz: bool = False    # translasi Z tertahan? (3D)
    rx: bool = False    # rotasi X tertahan? (3D — torsi)
    ry: bool = False    # rotasi Y tertahan? (3D)
    rz: bool = False    # rotasi Z tertahan? (2D + 3D)
    name: str = ""
    description: str = ""

    # ── Factory methods untuk tipe perletakan umum ────────────────────────────

    @classmethod
    def fixed_2d(cls, node_id: str) -> "Support":
        """Perletakan jepit 2D: ux, uy, rz tertahan."""
        return cls(node_id=node_id, ux=True, uy=True, rz=True,
                   name="Jepit", description="Fixed support 2D")

    @classmethod
    def pinned_2d(cls, node_id: str) -> "Support":
        """Perletakan sendi 2D: ux, uy tertahan, rz bebas."""
        return cls(node_id=node_id, ux=True, uy=True, rz=False,
                   name="Sendi", description="Pinned support 2D")

    @classmethod
    def roller_x_2d(cls, node_id: str) -> "Support":
        """Perletakan rol 2D: hanya uy tertahan (rol bergerak arah X)."""
        return cls(node_id=node_id, ux=False, uy=True, rz=False,
                   name="Rol-X", description="Roller support (Y restrained) 2D")

    @classmethod
    def roller_y_2d(cls, node_id: str) -> "Support":
        """Perletakan rol 2D: hanya ux tertahan (rol bergerak arah Y)."""
        return cls(node_id=node_id, ux=True, uy=False, rz=False,
                   name="Rol-Y", description="Roller support (X restrained) 2D")

    @classmethod
    def fixed_3d(cls, node_id: str) -> "Support":
        """Perletakan jepit 3D: semua 6 DOF tertahan."""
        return cls(node_id=node_id, ux=True, uy=True, uz=True,
                   rx=True, ry=True, rz=True,
                   name="Jepit-3D", description="Fixed support 3D")

    @classmethod
    def pinned_3d(cls, node_id: str) -> "Support":
        """Perletakan sendi 3D: translasi tertahan, rotasi bebas."""
        return cls(node_id=node_id, ux=True, uy=True, uz=True,
                   rx=False, ry=False, rz=False,
                   name="Sendi-3D", description="Pinned support 3D")

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.node_id.strip():
            errors.append("Support.node_id tidak boleh kosong.")
        dofs = [self.ux, self.uy, self.uz, self.rx, self.ry, self.rz]
        if not any(dofs):
            errors.append(
                f"Support pada node '{self.node_id}': tidak ada DOF yang tertahan — "
                "perletakan ini tidak berguna."
            )
        return errors

    def dof_list_2d(self) -> list[bool]:
        """DOF list untuk model 2D: [ux, uy, rz]."""
        return [self.ux, self.uy, self.rz]

    def dof_list_3d(self) -> list[bool]:
        """DOF list untuk model 3D: [ux, uy, uz, rx, ry, rz]."""
        return [self.ux, self.uy, self.uz, self.rx, self.ry, self.rz]

    @property
    def support_type_label(self) -> str:
        """Label deskriptif tipe perletakan untuk laporan."""
        dof_2d = self.dof_list_2d()
        dof_3d = self.dof_list_3d()
        if all(dof_3d):
            return "Jepit (Fixed)"
        if dof_2d == [True, True, False]:
            return "Sendi (Pinned)"
        if dof_2d == [False, True, False]:
            return "Rol-X (Roller Y)"
        if dof_2d == [True, False, False]:
            return "Rol-Y (Roller X)"
        restrained = [
            name for name, val in zip(["ux","uy","uz","rx","ry","rz"], dof_3d) if val
        ]
        return f"Custom ({', '.join(restrained)})"

