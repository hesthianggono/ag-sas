"""Element geometry utilities for 2D frame elements.

Each element has 2 nodes, 3 DOF per node: [UX, UY, RZ].
DOF index for node i: [3i, 3i+1, 3i+2].
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ElementGeometry:
    """Pre-computed geometry for a single 2D frame element."""
    length: float       # m
    angle_rad: float    # radians, measured from +X axis
    cos_theta: float
    sin_theta: float
    dof_i: tuple[int, int, int]  # DOF indices for start node
    dof_j: tuple[int, int, int]  # DOF indices for end node

    @property
    def dof_indices(self) -> list[int]:
        """All 6 DOF indices: [ui_x, ui_y, ri_z, uj_x, uj_y, rj_z]."""
        return list(self.dof_i) + list(self.dof_j)


def compute_element_geometry(
    xi: float, yi: float,
    xj: float, yj: float,
    node_i_index: int,
    node_j_index: int,
) -> ElementGeometry:
    """Compute element geometry from node coordinates and indices.

    Args:
        xi, yi: coordinates of start node (m)
        xj, yj: coordinates of end node (m)
        node_i_index: 0-based index of start node in global node list
        node_j_index: 0-based index of end node in global node list

    Raises:
        ValueError: if element has zero length
    """
    dx = xj - xi
    dy = yj - yi
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-12:
        raise ValueError(
            f"Element between nodes {node_i_index} and {node_j_index} "
            f"has zero length"
        )
    c = dx / length
    s = dy / length
    angle = math.atan2(dy, dx)

    dof_i = (3 * node_i_index, 3 * node_i_index + 1, 3 * node_i_index + 2)
    dof_j = (3 * node_j_index, 3 * node_j_index + 1, 3 * node_j_index + 2)

    return ElementGeometry(
        length=length,
        angle_rad=angle,
        cos_theta=c,
        sin_theta=s,
        dof_i=dof_i,
        dof_j=dof_j,
    )
