"""Global stiffness matrix assembly for 2D frame structures."""
from __future__ import annotations
import numpy as np
from .element import ElementGeometry
from .stiffness import global_element_stiffness


def assemble_global_stiffness(
    n_nodes: int,
    elements: list[tuple[float, float, float, ElementGeometry]],
    # each tuple: (E, A, I, geom)
) -> np.ndarray:
    """Assemble global stiffness matrix K (n_dof × n_dof).

    Args:
        n_nodes: total number of nodes in the model
        elements: list of (E, A, I, ElementGeometry) for each element

    Returns:
        K: (3*n_nodes × 3*n_nodes) global stiffness matrix in kN/m units
    """
    n_dof = 3 * n_nodes
    K = np.zeros((n_dof, n_dof))

    for E, A, I, geom in elements:
        k_e = global_element_stiffness(E, A, I, geom)
        dofs = geom.dof_indices  # list of 6 global DOF indices
        for r, i in enumerate(dofs):
            for c, j in enumerate(dofs):
                K[i, j] += k_e[r, c]

    return K


def assemble_load_vector(
    n_nodes: int,
    nodal_loads: list[tuple[int, float, float, float]],
    # each tuple: (node_index, FX_kN, FY_kN, MZ_kNm)
    equivalent_nodal_loads: dict[int, np.ndarray] | None = None,
    # DOF_index → additional force from FEF (in global coords)
) -> np.ndarray:
    """Assemble global load vector F (n_dof).

    Args:
        n_nodes: total number of nodes
        nodal_loads: list of (node_index, FX, FY, MZ) concentrated loads
        equivalent_nodal_loads: dict mapping DOF index to equivalent nodal
            force from member distributed loads (negated FEF in global coords)

    Returns:
        F: (3*n_nodes,) load vector in kN/kN·m units
    """
    n_dof = 3 * n_nodes
    F = np.zeros(n_dof)

    for node_idx, fx, fy, mz in nodal_loads:
        F[3 * node_idx]     += fx
        F[3 * node_idx + 1] += fy
        F[3 * node_idx + 2] += mz

    if equivalent_nodal_loads:
        for dof_idx, force in equivalent_nodal_loads.items():
            F[dof_idx] += force

    return F
