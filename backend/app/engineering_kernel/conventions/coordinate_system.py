"""
Sistem Koordinat AG-SAS
========================
Definisi formal sistem koordinat global 2D dan 3D.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Tuple


Vec2 = Tuple[float, float]
Vec3 = Tuple[float, float, float]


@dataclass(frozen=True)
class CoordinateSystem2D:
    """
    Sistem koordinat global 2D AG-SAS.

      X → horizontal (positif ke kanan)
      Y ↑ vertikal   (positif ke atas)
      Z = 0          (bidang 2D adalah XY)

    Right-hand rule berlaku: putaran positif rz berlawanan jarum jam
    dilihat dari arah +Z (keluar layar).
    """
    name: str = "Global-2D"
    x_axis: Vec2 = (1.0, 0.0)
    y_axis: Vec2 = (0.0, 1.0)
    gravity: Vec2 = (0.0, -1.0)   # arah gravitasi = -Y


@dataclass(frozen=True)
class CoordinateSystem3D:
    """
    Sistem koordinat global 3D AG-SAS.

      X → horizontal (positif ke kanan)
      Y ↑ vertikal   (positif ke atas, berlawanan gravitasi)
      Z ○ keluar bidang (positif keluar layar, right-hand rule)

    Gravitasi bekerja dalam arah -Y global.
    Konsisten dengan mayoritas software struktur (SAP2000, ETABS, STAAD.Pro).
    """
    name: str = "Global-3D"
    x_axis: Vec3 = (1.0, 0.0, 0.0)
    y_axis: Vec3 = (0.0, 1.0, 0.0)
    z_axis: Vec3 = (0.0, 0.0, 1.0)
    gravity: Vec3 = (0.0, -1.0, 0.0)   # arah gravitasi = -Y


# Singleton — digunakan di seluruh modul solver
GLOBAL_2D = CoordinateSystem2D()
GLOBAL_3D = CoordinateSystem3D()


def element_angle_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Hitung sudut elemen 2D dalam radian.

    Sudut θ diukur dari sumbu +X global ke arah I→J,
    berlawanan jarum jam adalah positif.

    Returns:
        theta: sudut dalam radian, rentang (-π, π].
    """
    dx = x2 - x1
    dy = y2 - y1
    return math.atan2(dy, dx)


def element_length_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """Hitung panjang elemen 2D dari koordinat node I dan J."""
    return math.hypot(x2 - x1, y2 - y1)


def element_length_3d(
    x1: float, y1: float, z1: float,
    x2: float, y2: float, z2: float,
) -> float:
    """Hitung panjang elemen 3D dari koordinat node I dan J."""
    return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)


def direction_cosines_2d(
    x1: float, y1: float, x2: float, y2: float
) -> Tuple[float, float]:
    """
    Hitung direction cosines (cx, cy) elemen 2D.

    cx = cos θ = (x2-x1)/L
    cy = sin θ = (y2-y1)/L

    Returns:
        (cx, cy) — direction cosines terhadap sumbu X dan Y global.

    Raises:
        ValueError: jika panjang elemen = 0 (elemen degenerasi).
    """
    L = element_length_2d(x1, y1, x2, y2)
    if L < 1e-12:
        raise ValueError(
            f"Panjang elemen = 0: node I=({x1},{y1}) identik dengan node J=({x2},{y2}). "
            "Elemen degenerasi tidak diperbolehkan."
        )
    return (x2 - x1) / L, (y2 - y1) / L
