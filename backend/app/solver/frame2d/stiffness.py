"""Local and global stiffness matrices for 2D frame elements.

Sign convention (McGuire MSA §3.2):
  N+  = tension (axial force, positive away from element)
  Vy+ = upward on left face (shear)
  Mz+ = sagging (counter-clockwise rotation on left face)

DOF order in local frame: [u1, v1, θ1, u2, v2, θ2]
  u = axial, v = transverse, θ = rotation
"""
from __future__ import annotations
import numpy as np
from .element import ElementGeometry


def local_stiffness_matrix(
    E: float,   # kN/m²
    A: float,   # m²
    I: float,   # m⁴
    L: float,   # m
) -> np.ndarray:
    """6×6 local stiffness matrix for 2D Euler-Bernoulli beam-column element.

    All values in kN and m units.
    """
    EA_L = E * A / L
    EI_L3 = E * I / L**3
    EI_L2 = E * I / L**2
    EI_L  = E * I / L

    k = np.zeros((6, 6))

    # Axial terms (rows/cols 0, 3)
    k[0, 0] =  EA_L;  k[0, 3] = -EA_L
    k[3, 0] = -EA_L;  k[3, 3] =  EA_L

    # Bending terms (rows/cols 1, 2, 4, 5)
    k[1, 1] =  12 * EI_L3;  k[1, 2] =  6 * EI_L2
    k[1, 4] = -12 * EI_L3;  k[1, 5] =  6 * EI_L2

    k[2, 1] =  6 * EI_L2;   k[2, 2] =  4 * EI_L
    k[2, 4] = -6 * EI_L2;   k[2, 5] =  2 * EI_L

    k[4, 1] = -12 * EI_L3;  k[4, 2] = -6 * EI_L2
    k[4, 4] =  12 * EI_L3;  k[4, 5] = -6 * EI_L2

    k[5, 1] =  6 * EI_L2;   k[5, 2] =  2 * EI_L
    k[5, 4] = -6 * EI_L2;   k[5, 5] =  4 * EI_L

    return k


def transformation_matrix(geom: ElementGeometry) -> np.ndarray:
    """6×6 transformation matrix T mapping local → global DOFs.

    Global DOF order: [UX, UY, RZ] per node.
    u_local = T @ u_global_element
    """
    c = geom.cos_theta
    s = geom.sin_theta

    T = np.zeros((6, 6))
    # Node i block (rows/cols 0-2)
    T[0, 0] =  c;  T[0, 1] = s
    T[1, 0] = -s;  T[1, 1] = c
    T[2, 2] =  1.0
    # Node j block (rows/cols 3-5)
    T[3, 3] =  c;  T[3, 4] = s
    T[4, 3] = -s;  T[4, 4] = c
    T[5, 5] =  1.0

    return T


def global_element_stiffness(
    E: float, A: float, I: float,
    geom: ElementGeometry,
) -> np.ndarray:
    """6×6 element stiffness matrix in global coordinates.

    K_global = Tᵀ · K_local · T
    """
    k_local = local_stiffness_matrix(E, A, I, geom.length)
    T = transformation_matrix(geom)
    return T.T @ k_local @ T


def fixed_end_forces_udl(
    q: float,   # kN/m, positive = downward (gravity) in global Y
    L: float,   # m
    geom: ElementGeometry,
) -> np.ndarray:
    """Fixed-end force vector in LOCAL coordinates for uniform distributed load.

    q is the distributed load intensity in global Y direction (positive = downward).
    Transforms to local transverse direction using sin_theta/cos_theta.

    Local FEF for transverse UDL q_local:
      p_local = [0, qL/2, qL²/12, 0, qL/2, -qL²/12]

    Returns 6-element array in local DOF order [u1, v1, θ1, u2, v2, θ2].
    """
    # Project global load onto local transverse (v) and axial (u) directions
    # local axial: q_axial = q_global_Y * (-sin_theta)  [no contribution for gravity beam]
    # local transverse: q_trans = q_global_Y * (-cos_theta) for y-load on inclined element
    # For horizontal beam: theta=0, c=1, s=0 → q_trans = q_global_Y * 1 (downward = negative v)
    # We use the standard sign: q > 0 means downward global Y → local transverse load
    c = geom.cos_theta
    s = geom.sin_theta

    # Decompose global (0, -q) load vector (downward = -Y) into local axes
    # local_u direction = (c, s), local_v direction = (-s, c)
    q_global_vec = np.array([0.0, -q])  # downward Y
    q_axial = q_global_vec @ np.array([c, s])
    q_trans = q_global_vec @ np.array([-s, c])

    qL = q_trans * L
    qL2 = q_trans * L * L

    # Standard FEF for uniform transverse load (positive v direction)
    p = np.array([
        -q_axial * L / 2,   # u1 (axial reaction at node i)
         qL / 2,             # v1
         qL2 / 12,           # θ1
        -q_axial * L / 2,   # u2
         qL / 2,             # v2
        -qL2 / 12,           # θ2
    ])
    return p
