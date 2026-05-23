"""Boundary condition application for 2D frame analysis.

Uses the elimination (zero row/col + diagonal=1) method for
prescribed zero displacements. Non-zero prescribed displacements
are not supported in this version.
"""
from __future__ import annotations
import numpy as np


def get_constrained_dofs(
    supports: list[tuple[int, bool, bool, bool]],
    # each tuple: (node_index, fix_ux, fix_uy, fix_rz)
) -> list[int]:
    """Return list of globally-constrained DOF indices from support conditions."""
    constrained = []
    for node_idx, fix_ux, fix_uy, fix_rz in supports:
        if fix_ux:
            constrained.append(3 * node_idx)
        if fix_uy:
            constrained.append(3 * node_idx + 1)
        if fix_rz:
            constrained.append(3 * node_idx + 2)
    return constrained


def apply_boundary_conditions(
    K: np.ndarray,
    F: np.ndarray,
    constrained_dofs: list[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Apply zero-displacement boundary conditions in-place.

    Modifies copies of K and F:
    - Zeros row and column for each constrained DOF
    - Sets diagonal = 1.0 (so K is non-singular)
    - Sets F[dof] = 0.0 (enforces zero displacement)

    Returns modified (K_bc, F_bc) — originals unchanged.
    """
    K_bc = K.copy()
    F_bc = F.copy()

    for dof in constrained_dofs:
        K_bc[dof, :] = 0.0
        K_bc[:, dof] = 0.0
        K_bc[dof, dof] = 1.0
        F_bc[dof] = 0.0

    return K_bc, F_bc
