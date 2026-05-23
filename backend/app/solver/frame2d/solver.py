"""Main 2D Frame Analysis Solver using Direct Stiffness Method.

Units:
  Length  : m
  Force   : kN
  Moment  : kN·m
  Stress  : kN/m² (= kPa)
  Area    : m²
  Inertia : m⁴

Input interface uses mm/cm²/cm⁴/MPa and converts internally.
"""
from __future__ import annotations
import math
import uuid
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from .element import compute_element_geometry, ElementGeometry
from .stiffness import fixed_end_forces_udl, transformation_matrix
from .assembly import assemble_global_stiffness, assemble_load_vector
from .boundary import get_constrained_dofs, apply_boundary_conditions
from .results import (
    Frame2DResult,
    extract_displacements,
    extract_reactions,
    extract_element_forces,
)


# ── Input Data Structures ─────────────────────────────────────────────────────

@dataclass
class NodeInput:
    """A structural node."""
    index: int          # 0-based, must be unique
    x_m: float          # X coordinate (m)
    y_m: float          # Y coordinate (m)


@dataclass
class MaterialInput:
    """Elastic material."""
    E_mpa: float        # Young's modulus (MPa = kN/mm²)
    # Internally converted to kN/m²


@dataclass
class SectionInput:
    """Cross-section properties."""
    A_cm2: float        # area (cm²)
    I_cm4: float        # moment of inertia (cm⁴)
    # Internally converted to m² and m⁴


@dataclass
class ElementInput:
    """A 2D frame element (beam-column)."""
    index: int          # 0-based, must be unique
    node_i: int         # start node index
    node_j: int         # end node index
    material: MaterialInput
    section: SectionInput
    udl_kn_per_m: float = 0.0   # uniform distributed load (kN/m, positive = downward)


@dataclass
class SupportInput:
    """Nodal support condition."""
    node_index: int
    fix_ux: bool = False
    fix_uy: bool = False
    fix_rz: bool = False


@dataclass
class NodalLoadInput:
    """Concentrated nodal load."""
    node_index: int
    fx_kn: float = 0.0      # horizontal force (kN, + = rightward)
    fy_kn: float = 0.0      # vertical force (kN, + = upward)
    mz_knm: float = 0.0     # moment (kN·m, + = counter-clockwise)


@dataclass
class Frame2DModel:
    """Complete input model for 2D frame analysis."""
    title: str
    nodes: list[NodeInput]
    elements: list[ElementInput]
    supports: list[SupportInput]
    nodal_loads: list[NodalLoadInput] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> list[str]:
        """Return list of validation errors (empty = OK)."""
        errors = []
        node_indices = {n.index for n in self.nodes}
        if len(node_indices) != len(self.nodes):
            errors.append("Duplicate node indices found")
        for elem in self.elements:
            if elem.node_i not in node_indices:
                errors.append(f"Element {elem.index}: node_i={elem.node_i} not found")
            if elem.node_j not in node_indices:
                errors.append(f"Element {elem.index}: node_j={elem.node_j} not found")
            if elem.node_i == elem.node_j:
                errors.append(f"Element {elem.index}: node_i == node_j")
            if elem.material.E_mpa <= 0:
                errors.append(f"Element {elem.index}: E_mpa must be positive")
            if elem.section.A_cm2 <= 0:
                errors.append(f"Element {elem.index}: A_cm2 must be positive")
            if elem.section.I_cm4 <= 0:
                errors.append(f"Element {elem.index}: I_cm4 must be positive")
        for sup in self.supports:
            if sup.node_index not in node_indices:
                errors.append(f"Support at node {sup.node_index} not found")
            if not (sup.fix_ux or sup.fix_uy or sup.fix_rz):
                errors.append(f"Support at node {sup.node_index} has no constraints")
        for load in self.nodal_loads:
            if load.node_index not in node_indices:
                errors.append(f"Nodal load at node {load.node_index} not found")
        return errors


# ── Solver ────────────────────────────────────────────────────────────────────

class Frame2DSolver:
    """Direct Stiffness Method solver for linear elastic 2D frames."""

    SOLVER_VERSION = "frame2d-dsm-v1.0"

    def solve(self, model: Frame2DModel) -> Frame2DResult:
        """Run analysis and return Frame2DResult.

        Raises:
            ValueError: if model has validation errors
            np.linalg.LinAlgError: if stiffness matrix is singular
                (under-constrained structure)
        """
        # 1. Validate
        errors = model.validate()
        if errors:
            raise ValueError("Model validation failed:\n" + "\n".join(errors))

        # 2. Build node coordinate map
        nodes = sorted(model.nodes, key=lambda n: n.index)
        n_nodes = len(nodes)
        node_map = {n.index: n for n in nodes}

        # 3. Compute element geometries (unit conversion inline)
        geom_list: list[ElementGeometry] = []
        elem_data: list[tuple[float, float, float, ElementGeometry, float]] = []

        for elem in model.elements:
            ni = node_map[elem.node_i]
            nj = node_map[elem.node_j]

            # Find 0-based positions in sorted node list
            ni_pos = next(i for i, n in enumerate(nodes) if n.index == elem.node_i)
            nj_pos = next(i for i, n in enumerate(nodes) if n.index == elem.node_j)

            geom = compute_element_geometry(
                ni.x_m, ni.y_m, nj.x_m, nj.y_m, ni_pos, nj_pos
            )

            # Unit conversion
            E = elem.material.E_mpa * 1e3   # MPa → kN/m²  (1 MPa = 1000 kN/m²)
            A = elem.section.A_cm2 * 1e-4   # cm² → m²
            I = elem.section.I_cm4 * 1e-8   # cm⁴ → m⁴

            geom_list.append(geom)
            elem_data.append((E, A, I, geom, elem.udl_kn_per_m))

        # 4. Assemble global stiffness matrix
        K = assemble_global_stiffness(
            n_nodes,
            [(E, A, I, geom) for E, A, I, geom, _ in elem_data],
        )
        K_orig = K.copy()

        # 5. Assemble load vector (nodal loads)
        nodal = [(load.node_index, load.fx_kn, load.fy_kn, load.mz_knm)
                 for load in model.nodal_loads]

        # Equivalent nodal loads from member UDL (negated FEF in global coords)
        enl: dict[int, float] = {}
        for E, A, I, geom, udl_q in elem_data:
            if abs(udl_q) < 1e-12:
                continue
            p_fef_local = fixed_end_forces_udl(udl_q, geom.length, geom)
            T = transformation_matrix(geom)
            # FEF in global DOFs
            p_fef_global = T.T @ p_fef_local
            # Equivalent nodal loads: add p_fef directly (downward load → negative v-terms)
            for r, dof in enumerate(geom.dof_indices):
                enl[dof] = enl.get(dof, 0.0) + p_fef_global[r]

        F = assemble_load_vector(n_nodes, nodal, enl)
        F_orig = F.copy()

        # 6. Boundary conditions
        supports_list = [
            (sup.node_index, sup.fix_ux, sup.fix_uy, sup.fix_rz)
            for sup in model.supports
        ]
        constrained_dofs = get_constrained_dofs(supports_list)
        K_bc, F_bc = apply_boundary_conditions(K, F, constrained_dofs)

        # 7. Solve: K_bc · u = F_bc
        u = np.linalg.solve(K_bc, F_bc)

        # 8. Post-process
        displacements = extract_displacements(u, n_nodes)
        reactions = extract_reactions(K_orig, u, F_orig, constrained_dofs, n_nodes)
        element_forces = extract_element_forces(elem_data, u)

        # 9. Summary metrics
        max_disp = float(np.max(np.abs(u)))
        max_moment = max(
            (abs(f.Mz_i_knm) for f in element_forces), default=0.0
        )
        max_moment = max(
            max_moment,
            max((abs(f.Mz_j_knm) for f in element_forces), default=0.0)
        )
        max_shear = max(
            (abs(f.Vy_i_kn) for f in element_forces), default=0.0
        )
        max_shear = max(
            max_shear,
            max((abs(f.Vy_j_kn) for f in element_forces), default=0.0)
        )

        return Frame2DResult(
            displacements=displacements,
            reactions=reactions,
            element_forces=element_forces,
            max_displacement_m=max_disp,
            max_moment_knm=max_moment,
            max_shear_kn=max_shear,
        )
