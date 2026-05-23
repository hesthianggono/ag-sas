"""
Post-processing module for 2D Frame Analysis.

Computes:
  - Internal force diagrams: N(x), V(x), M(x) at n_points per element
  - Deformed shape using Hermite cubic interpolation
  - Global XY coordinates for diagram plotting (perpendicular offsets)

Sign convention (McGuire MSA):
  N  > 0  tension
  Vy > 0  upward at left face
  Mz > 0  sagging (tension at bottom)

Diagram offsets are perpendicular to the element axis, drawn on the
*compression side* for moment (positive M extends below a horizontal beam).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────── data structures ──────────────────────────────────

@dataclass
class DiagramPoint:
    """A single sample point along an element."""
    x_local: float          # distance from node-i along element axis (m)
    N_kn: float             # axial force (kN)
    V_kn: float             # shear force (kN)
    M_knm: float            # bending moment (kN·m)
    # Global XY of the point on the *element axis* (undeformed)
    gx: float = 0.0
    gy: float = 0.0
    # Global XY for N diagram (offset perpendicular to element)
    N_gx: float = 0.0
    N_gy: float = 0.0
    # Global XY for V diagram
    V_gx: float = 0.0
    V_gy: float = 0.0
    # Global XY for M diagram
    M_gx: float = 0.0
    M_gy: float = 0.0
    # Deformed position (global XY, scaled)
    def_gx: float = 0.0
    def_gy: float = 0.0


@dataclass
class ElementDiagram:
    """Diagram data for one element."""
    element_index: int
    node_i: int
    node_j: int
    length: float           # m
    angle_deg: float        # degrees
    points: list[DiagramPoint] = field(default_factory=list)
    # Extreme values (for scaling)
    N_max: float = 0.0
    N_min: float = 0.0
    V_max: float = 0.0
    V_min: float = 0.0
    M_max: float = 0.0
    M_min: float = 0.0


@dataclass
class StructureDiagramData:
    """Complete post-processing output."""
    elements: list[ElementDiagram]
    # Global extremes for auto-scaling
    N_max_global: float = 0.0
    N_min_global: float = 0.0
    V_max_global: float = 0.0
    V_min_global: float = 0.0
    M_max_global: float = 0.0
    M_min_global: float = 0.0
    max_defl_global: float = 0.0   # m


# ─────────────────────────── main function ────────────────────────────────────

def compute_diagram_data(
    *,
    nodes: list[dict],          # [{"index": i, "x_m": x, "y_m": y}, ...]
    elements: list[dict],       # [{"index": e, "node_i": ni, "node_j": nj, "udl_kn_per_m": q}, ...]
    element_forces: list[dict], # [{"element": e, "N_i_kn", "Vy_i_kn", "Mz_i_knm", ...}, ...]
    displacements: list[dict],  # [{"node": n, "ux_mm", "uy_mm", "rz_mrad"}, ...]
    n_points: int = 21,
    deformation_scale: float = 100.0,
) -> StructureDiagramData:
    """
    Compute diagram data for all elements.

    Parameters
    ----------
    nodes, elements, element_forces, displacements:
        Data as returned by the Frame2D solver API response.
    n_points:
        Number of sample points per element (≥ 2, odd recommended).
    deformation_scale:
        Amplification factor applied to displacements for visualisation.
    """
    if n_points < 2:
        n_points = 2

    # Build lookup dicts
    node_coords: dict[int, tuple[float, float]] = {
        n["index"]: (n["x_m"], n["y_m"]) for n in nodes
    }
    node_disp: dict[int, tuple[float, float, float]] = {
        d["node"]: (d["ux_mm"] * 1e-3, d["uy_mm"] * 1e-3, d["rz_mrad"] * 1e-3)
        for d in displacements
    }
    ef_map: dict[int, dict] = {ef["element"]: ef for ef in element_forces}

    result_elements: list[ElementDiagram] = []

    for elem in elements:
        eidx = elem["index"]
        ni   = elem["node_i"]
        nj   = elem["node_j"]
        q    = elem.get("udl_kn_per_m", 0.0)  # positive = downward

        xi, yi = node_coords[ni]
        xj, yj = node_coords[nj]
        dx = xj - xi
        dy = yj - yi
        L  = math.hypot(dx, dy)
        if L < 1e-12:
            continue

        c = dx / L   # cos θ
        s = dy / L   # sin θ
        angle_deg = math.degrees(math.atan2(dy, dx))

        ef = ef_map.get(eidx, {})
        N_i  = ef.get("N_i_kn",  0.0)
        Vy_i = ef.get("Vy_i_kn", 0.0)
        Mz_i = ef.get("Mz_i_knm", 0.0)

        # UDL components in local coords
        # global UDL direction: (0, -q)  (positive q = downward)
        q_axial = (0.0 * c + (-q) * s)   # q_axial = -q·sin(θ)
        q_trans = (0.0 *(-s) + (-q) * c) # q_trans = -q·cos(θ)
        # For horizontal beam (s=0, c=1): q_trans = -q (downward = negative local Y)

        # Displacements at node i and j (global → local)
        ux_i, uy_i, rz_i = node_disp.get(ni, (0.0, 0.0, 0.0))
        ux_j, uy_j, rz_j = node_disp.get(nj, (0.0, 0.0, 0.0))

        # Local displacements
        u_i =  c * ux_i + s * uy_i   # axial at i
        v_i = -s * ux_i + c * uy_i   # transverse at i
        u_j =  c * ux_j + s * uy_j
        v_j = -s * ux_j + c * uy_j
        theta_i = rz_i
        theta_j = rz_j

        elem_diag = ElementDiagram(
            element_index=eidx,
            node_i=ni,
            node_j=nj,
            length=L,
            angle_deg=angle_deg,
        )

        N_vals, V_vals, M_vals = [], [], []

        for k in range(n_points):
            xi_local = k / (n_points - 1)   # ξ ∈ [0, 1]
            x = xi_local * L                 # distance along element (m)

            # ── Internal forces ──────────────────────────────────────────────
            # Note: Mz_i from the solver is the force the element exerts on node i.
            # The internal bending moment on the cross-section uses -Mz_i at x=0
            # (moment the right portion exerts on the left portion in the standard
            # beam sign convention: Mz positive = sagging).
            N_x  =  N_i  + q_axial * x
            V_x  =  Vy_i + q_trans * x
            M_x  = -Mz_i + Vy_i * x + 0.5 * q_trans * x * x

            # ── Undeformed global position ───────────────────────────────────
            gx = xi + c * x
            gy = yi + s * x

            # ── Perpendicular direction (normal to element axis) ─────────────
            # normal = (-s, c)   → points to the "left" when walking i→j
            nx = -s
            ny =  c

            # ── Deformed shape (Hermite interpolation) ───────────────────────
            xi2 = xi_local * xi_local
            xi3 = xi2 * xi_local

            # Hermite shape functions (transverse)
            H1 =  1 - 3*xi2 + 2*xi3
            H2 =  L * xi_local * (1 - xi_local)**2
            H3 =  3*xi2 - 2*xi3
            H4 =  L * xi2 * (xi_local - 1)

            # Linear shape function (axial)
            N1_ax = 1 - xi_local
            N2_ax = xi_local

            u_local  = N1_ax * u_i + N2_ax * u_j
            v_local  = H1 * v_i + H2 * theta_i + H3 * v_j + H4 * theta_j

            # Transform local deformation to global
            def_gx = gx + deformation_scale * (c * u_local - s * v_local)
            def_gy = gy + deformation_scale * (s * u_local + c * v_local)

            pt = DiagramPoint(
                x_local=x,
                N_kn=N_x,
                V_kn=V_x,
                M_knm=M_x,
                gx=gx,
                gy=gy,
                N_gx=gx + N_x * nx,
                N_gy=gy + N_x * ny,
                V_gx=gx + V_x * nx,
                V_gy=gy + V_x * ny,
                M_gx=gx + M_x * nx,
                M_gy=gy + M_x * ny,
                def_gx=def_gx,
                def_gy=def_gy,
            )
            elem_diag.points.append(pt)
            N_vals.append(N_x)
            V_vals.append(V_x)
            M_vals.append(M_x)

        elem_diag.N_max = max(N_vals)
        elem_diag.N_min = min(N_vals)
        elem_diag.V_max = max(V_vals)
        elem_diag.V_min = min(V_vals)
        elem_diag.M_max = max(M_vals)
        elem_diag.M_min = min(M_vals)

        result_elements.append(elem_diag)

    # ── Global extremes ──────────────────────────────────────────────────────
    data = StructureDiagramData(elements=result_elements)
    if result_elements:
        data.N_max_global = max(e.N_max for e in result_elements)
        data.N_min_global = min(e.N_min for e in result_elements)
        data.V_max_global = max(e.V_max for e in result_elements)
        data.V_min_global = min(e.V_min for e in result_elements)
        data.M_max_global = max(e.M_max for e in result_elements)
        data.M_min_global = min(e.M_min for e in result_elements)

        # Max deflection across all nodes (in metres, before scaling)
        all_def = []
        for n_d in node_disp.values():
            all_def.append(math.hypot(n_d[0], n_d[1]))
        data.max_defl_global = max(all_def) if all_def else 0.0

    return data


# ─────────────────────────── serialization ────────────────────────────────────

def diagram_data_to_dict(data: StructureDiagramData) -> dict:
    """Convert StructureDiagramData to a JSON-serialisable dict."""
    return {
        "global_extremes": {
            "N_max_kn": round(data.N_max_global, 4),
            "N_min_kn": round(data.N_min_global, 4),
            "V_max_kn": round(data.V_max_global, 4),
            "V_min_kn": round(data.V_min_global, 4),
            "M_max_knm": round(data.M_max_global, 4),
            "M_min_knm": round(data.M_min_global, 4),
            "max_deflection_m": round(data.max_defl_global, 6),
        },
        "elements": [
            {
                "element_index": e.element_index,
                "node_i": e.node_i,
                "node_j": e.node_j,
                "length_m": round(e.length, 4),
                "angle_deg": round(e.angle_deg, 4),
                "N_max_kn": round(e.N_max, 4),
                "N_min_kn": round(e.N_min, 4),
                "V_max_kn": round(e.V_max, 4),
                "V_min_kn": round(e.V_min, 4),
                "M_max_knm": round(e.M_max, 4),
                "M_min_knm": round(e.M_min, 4),
                "points": [
                    {
                        "x": round(p.x_local, 4),
                        "N": round(p.N_kn, 4),
                        "V": round(p.V_kn, 4),
                        "M": round(p.M_knm, 4),
                        "gx": round(p.gx, 5),
                        "gy": round(p.gy, 5),
                        "N_gx": round(p.N_gx, 5),
                        "N_gy": round(p.N_gy, 5),
                        "V_gx": round(p.V_gx, 5),
                        "V_gy": round(p.V_gy, 5),
                        "M_gx": round(p.M_gx, 5),
                        "M_gy": round(p.M_gy, 5),
                        "def_gx": round(p.def_gx, 5),
                        "def_gy": round(p.def_gy, 5),
                    }
                    for p in e.points
                ],
            }
            for e in data.elements
        ],
    }
