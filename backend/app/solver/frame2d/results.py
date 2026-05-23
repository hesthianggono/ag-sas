"""Post-processing: reactions, element end forces, and result containers."""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from .element import ElementGeometry
from .stiffness import local_stiffness_matrix, transformation_matrix, fixed_end_forces_udl


@dataclass
class NodeDisplacement:
    node_index: int
    ux_m: float       # horizontal displacement (m)
    uy_m: float       # vertical displacement (m)
    rz_rad: float     # rotation (rad)


@dataclass
class NodeReaction:
    node_index: int
    rx_kn: float      # horizontal reaction (kN)
    ry_kn: float      # vertical reaction (kN)
    mz_knm: float     # moment reaction (kN·m)


@dataclass
class ElementEndForces:
    element_index: int
    # Node i (start)
    N_i_kn: float     # axial force at i; + = tension
    Vy_i_kn: float    # shear at i; + = upward on left face
    Mz_i_knm: float   # moment at i; + = sagging
    # Node j (end)
    N_j_kn: float
    Vy_j_kn: float
    Mz_j_knm: float


@dataclass
class Frame2DResult:
    """Complete analysis result for a 2D frame model."""
    displacements: list[NodeDisplacement]
    reactions: list[NodeReaction]
    element_forces: list[ElementEndForces]
    max_displacement_m: float
    max_moment_knm: float
    max_shear_kn: float
    solver_notes: list[str] = field(default_factory=list)


def extract_displacements(
    u: np.ndarray,
    n_nodes: int,
) -> list[NodeDisplacement]:
    """Build NodeDisplacement list from global displacement vector."""
    result = []
    for i in range(n_nodes):
        result.append(NodeDisplacement(
            node_index=i,
            ux_m=float(u[3 * i]),
            uy_m=float(u[3 * i + 1]),
            rz_rad=float(u[3 * i + 2]),
        ))
    return result


def extract_reactions(
    K_orig: np.ndarray,
    u: np.ndarray,
    F: np.ndarray,
    constrained_dofs: list[int],
    n_nodes: int,
) -> list[NodeReaction]:
    """Compute support reactions as R = K·u - F for constrained DOFs only.

    For unconstrained DOFs the reaction is zero by equilibrium.
    Groups reaction components by node.
    """
    # Full reaction vector
    R_full = K_orig @ u - F

    # Build per-node map
    node_reactions: dict[int, list[float]] = {i: [0.0, 0.0, 0.0] for i in range(n_nodes)}
    for dof in constrained_dofs:
        node_idx = dof // 3
        local_dof = dof % 3  # 0=UX, 1=UY, 2=RZ
        node_reactions[node_idx][local_dof] = float(R_full[dof])

    result = []
    for node_idx, (rx, ry, mz) in node_reactions.items():
        if any(abs(v) > 1e-10 for v in [rx, ry, mz]):
            result.append(NodeReaction(
                node_index=node_idx,
                rx_kn=rx,
                ry_kn=ry,
                mz_knm=mz,
            ))
    return result


def extract_element_forces(
    elements_data: list[tuple[float, float, float, ElementGeometry, float | None]],
    # each: (E, A, I, geom, udl_q_knm_or_None)
    u: np.ndarray,
) -> list[ElementEndForces]:
    """Compute element end forces in local coordinates.

    For each element:
      u_e = global displacement vector for 6 element DOFs
      u_local = T @ u_e
      Q_local = K_local @ u_local - p_fef_local
      Sign: N_i = Q_local[0] (tension = positive)
            Vy_i = Q_local[1], Mz_i = Q_local[2]
            N_j = -Q_local[3], Vy_j = -Q_local[4], Mz_j = -Q_local[5]
              (equilibrium flip at j end)
    """
    result = []
    for idx, (E, A, I, geom, udl_q) in enumerate(elements_data):
        dofs = geom.dof_indices
        u_e = u[dofs]  # 6-element global displacements

        T = transformation_matrix(geom)
        k_local = local_stiffness_matrix(E, A, I, geom.length)
        u_local = T @ u_e

        Q_local = k_local @ u_local

        # Subtract fixed-end forces if member has UDL
        if udl_q is not None and abs(udl_q) > 1e-12:
            p_fef = fixed_end_forces_udl(udl_q, geom.length, geom)
            Q_local = Q_local - p_fef

        # Extract with sign convention
        N_i  =  float(Q_local[0])
        Vy_i =  float(Q_local[1])
        Mz_i =  float(Q_local[2])
        N_j  = -float(Q_local[3])
        Vy_j = -float(Q_local[4])
        Mz_j = -float(Q_local[5])

        result.append(ElementEndForces(
            element_index=idx,
            N_i_kn=N_i,
            Vy_i_kn=Vy_i,
            Mz_i_knm=Mz_i,
            N_j_kn=N_j,
            Vy_j_kn=Vy_j,
            Mz_j_knm=Mz_j,
        ))
    return result
