"""
Unit tests for Frame2D post-processing: diagram data computation.

Tests verify:
  - N(x), V(x), M(x) values at key points
  - Equilibrium: reactions match diagram extremes
  - Deformed shape: zero displacements at fixed supports
  - Global extremes tracking
  - Serialisation to dict
"""
import math
import pytest

from app.postprocessing.frame2d.diagram_data import (
    compute_diagram_data,
    diagram_data_to_dict,
    StructureDiagramData,
)
from app.solver.frame2d.solver import (
    Frame2DSolver,
    Frame2DModel,
    NodeInput,
    ElementInput,
    MaterialInput,
    SectionInput,
    SupportInput,
    NodalLoadInput,
)
from app.api.v1.endpoints.analysis import _result_to_dict

# ── helpers ────────────────────────────────────────────────────────────────────

_SOLVER = Frame2DSolver()

E = 200_000.0   # MPa
A = 100.0       # cm²
I = 10_000.0    # cm⁴


def _run_ssb_udl(L: float = 5.0, q: float = 20.0, n_elem: int = 1):
    """Simply-supported beam with UDL q (kN/m).  Returns (result, nodes, elements)."""
    nodes = [NodeInput(0, 0.0, 0.0), NodeInput(1, L, 0.0)]
    elems = [ElementInput(0, 0, 1, MaterialInput(E), SectionInput(A, I), q)]
    supports = [
        SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=False),
        SupportInput(1, fix_ux=False, fix_uy=True, fix_rz=False),
    ]
    model = Frame2DModel("SSB", nodes, elems, supports, [])
    result = _SOLVER.solve(model)
    return result, nodes, elems


def _build_api_data(result, nodes, elements):
    """Package solver result into API-like dicts."""
    rid = "test"
    resp = _result_to_dict(result, rid, "test")
    node_list = [{"index": n.index, "x_m": n.x_m, "y_m": n.y_m} for n in nodes]
    elem_list = [
        {"index": e.index, "node_i": e.node_i, "node_j": e.node_j,
         "udl_kn_per_m": e.udl_kn_per_m}
        for e in elements
    ]
    return node_list, elem_list, resp["element_forces"], resp["displacements"]


# ── TestSSBDiagram ─────────────────────────────────────────────────────────────

class TestSSBDiagram:
    """SSB with UDL: verify N, V, M at x=0, L/2, L."""

    def setup_method(self):
        L, q = 5.0, 20.0
        result, nodes, elements = _run_ssb_udl(L, q)
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elements)
        self.L = L
        self.q = q
        self.data = compute_diagram_data(
            nodes=node_list,
            elements=elem_list,
            element_forces=ef,
            displacements=disp,
            n_points=21,
            deformation_scale=1.0,
        )
        self.el = self.data.elements[0]

    def test_one_element_produced(self):
        assert len(self.data.elements) == 1

    def test_n_points(self):
        assert len(self.el.points) == 21

    def test_axial_force_zero(self):
        """Horizontal SSB with vertical UDL: N should be ≈ 0 everywhere."""
        for pt in self.el.points:
            assert abs(pt.N_kn) < 1e-6, f"N={pt.N_kn} at x={pt.x_local}"

    def test_shear_at_left(self):
        """V(0) = +qL/2 = +50 kN."""
        pt0 = self.el.points[0]
        assert abs(pt0.V_kn - (self.q * self.L / 2)) < 1e-3

    def test_shear_at_right(self):
        """V(L) = -qL/2 = -50 kN."""
        pt_last = self.el.points[-1]
        assert abs(pt_last.V_kn - (- self.q * self.L / 2)) < 1e-3

    def test_shear_zero_at_midspan(self):
        """V(L/2) = 0."""
        pt_mid = self.el.points[10]   # index 10 of 21 → ξ=0.5
        assert abs(pt_mid.V_kn) < 1e-3

    def test_moment_at_ends_zero(self):
        """M(0) = M(L) = 0 for SSB."""
        assert abs(self.el.points[0].M_knm) < 1e-3
        assert abs(self.el.points[-1].M_knm) < 1e-3

    def test_moment_at_midspan(self):
        """M(L/2) = qL²/8."""
        expected = self.q * self.L ** 2 / 8
        pt_mid = self.el.points[10]
        assert abs(pt_mid.M_knm - expected) < 1e-2

    def test_global_extremes_M(self):
        expected = self.q * self.L ** 2 / 8
        assert abs(self.data.M_max_global - expected) < 1e-2

    def test_global_extremes_V(self):
        expected = self.q * self.L / 2
        assert abs(self.data.V_max_global - expected) < 1e-3
        assert abs(self.data.V_min_global + expected) < 1e-3

    def test_deformed_shape_zero_at_supports(self):
        """Pin & roller: vertical displacement at nodes 0 and 1 = 0."""
        pt0   = self.el.points[0]
        pt_L  = self.el.points[-1]
        # With scale=1, global Y should equal 0 (uy=0 at supports)
        assert abs(pt0.def_gy - pt0.gy) < 1e-6
        assert abs(pt_L.def_gy - pt_L.gy) < 1e-6

    def test_global_xy_start(self):
        """gx, gy at x=0 should equal node-i coordinates."""
        pt0 = self.el.points[0]
        assert abs(pt0.gx - 0.0) < 1e-9
        assert abs(pt0.gy - 0.0) < 1e-9

    def test_global_xy_end(self):
        """gx at x=L should equal L (node-j x)."""
        pt_L = self.el.points[-1]
        assert abs(pt_L.gx - self.L) < 1e-6


# ── TestCantileverDiagram ──────────────────────────────────────────────────────

class TestCantileverDiagram:
    """Cantilever beam with tip point load P."""

    P  = 10.0   # kN
    L  = 3.0    # m

    def setup_method(self):
        nodes = [NodeInput(0, 0.0, 0.0), NodeInput(1, self.L, 0.0)]
        elems = [ElementInput(0, 0, 1, MaterialInput(E), SectionInput(A, I), 0.0)]
        supports = [SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True)]
        nodal_loads = [NodalLoadInput(1, 0.0, -self.P, 0.0)]
        model = Frame2DModel("Cant", nodes, elems, supports, nodal_loads)
        result = _SOLVER.solve(model)
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elems)
        self.data = compute_diagram_data(
            nodes=node_list,
            elements=elem_list,
            element_forces=ef,
            displacements=disp,
            n_points=21,
            deformation_scale=1.0,
        )
        self.el = self.data.elements[0]

    def test_shear_constant(self):
        """V = +P throughout (upward reaction at left face = positive shear)."""
        for pt in self.el.points:
            assert abs(pt.V_kn - self.P) < 1e-3, f"V={pt.V_kn} at x={pt.x_local}"

    def test_moment_at_fixed_end(self):
        """M(0) = -P*L (hogging at fixed end, sagging-positive convention)."""
        expected = -self.P * self.L
        assert abs(self.el.points[0].M_knm - expected) < 1e-2

    def test_moment_at_free_end(self):
        """M(L) = 0."""
        assert abs(self.el.points[-1].M_knm) < 1e-3

    def test_deformed_fixed_end(self):
        """Fixed end: ux=uy=0, no deformation offset."""
        pt0 = self.el.points[0]
        assert abs(pt0.def_gx - pt0.gx) < 1e-9
        assert abs(pt0.def_gy - pt0.gy) < 1e-9


# ── TestVerticalElement ────────────────────────────────────────────────────────

class TestVerticalElement:
    """Vertical column: horizontal point load at top → pure bending + shear."""

    P = 5.0    # kN horizontal
    H = 4.0    # m height

    def setup_method(self):
        nodes = [NodeInput(0, 0.0, 0.0), NodeInput(1, 0.0, self.H)]
        elems = [ElementInput(0, 0, 1, MaterialInput(E), SectionInput(A, I), 0.0)]
        supports = [SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True)]
        nodal_loads = [NodalLoadInput(1, self.P, 0.0, 0.0)]
        model = Frame2DModel("Column", nodes, elems, supports, nodal_loads)
        result = _SOLVER.solve(model)
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elems)
        self.data = compute_diagram_data(
            nodes=node_list,
            elements=elem_list,
            element_forces=ef,
            displacements=disp,
            n_points=21,
            deformation_scale=1.0,
        )
        self.el = self.data.elements[0]

    def test_axial_zero(self):
        """Horizontal load on vertical column: N ≈ 0."""
        for pt in self.el.points:
            assert abs(pt.N_kn) < 1e-4, f"N={pt.N_kn}"

    def test_shear_constant(self):
        """V = P throughout."""
        for pt in self.el.points:
            assert abs(pt.V_kn - self.P) < 1e-3, f"V={pt.V_kn}"

    def test_moment_at_base(self):
        """M(0) = -P*H (hogging at fixed base, sagging-positive convention)."""
        assert abs(self.el.points[0].M_knm - (-self.P * self.H)) < 1e-2

    def test_moment_at_top(self):
        """M(H) = 0 (free end at top of column)."""
        assert abs(self.el.points[-1].M_knm) < 1e-3


# ── TestAxialElement ───────────────────────────────────────────────────────────

class TestAxialElement:
    """Pure axial bar: tension force only."""

    P = 100.0  # kN
    L = 2.0    # m

    def setup_method(self):
        nodes = [NodeInput(0, 0.0, 0.0), NodeInput(1, self.L, 0.0)]
        elems = [ElementInput(0, 0, 1, MaterialInput(E), SectionInput(A, I), 0.0)]
        supports = [
            SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True),
            SupportInput(1, fix_ux=False, fix_uy=True, fix_rz=False),
        ]
        nodal_loads = [NodalLoadInput(1, self.P, 0.0, 0.0)]
        model = Frame2DModel("Axial", nodes, elems, supports, nodal_loads)
        result = _SOLVER.solve(model)
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elems)
        self.data = compute_diagram_data(
            nodes=node_list,
            elements=elem_list,
            element_forces=ef,
            displacements=disp,
            n_points=21,
            deformation_scale=1.0,
        )
        self.el = self.data.elements[0]

    def test_N_constant_tension(self):
        """Axial bar in tension: N = -P throughout.

        Convention: Q_local[0] at node-i is the element resisting force.
        For a bar elongating (tension), the element pulls node-i in +X,
        giving Q_local[0] = -EA/L * delta < 0. Hence N_i = -P (negative).
        This is consistent with the solver sign convention used throughout.
        """
        for pt in self.el.points:
            assert abs(pt.N_kn - (-self.P)) < 1e-3, f"N={pt.N_kn} at x={pt.x_local}"

    def test_shear_zero(self):
        for pt in self.el.points:
            assert abs(pt.V_kn) < 1e-6

    def test_moment_zero(self):
        for pt in self.el.points:
            assert abs(pt.M_knm) < 1e-6


# ── TestDiagramSerialisation ───────────────────────────────────────────────────

class TestDiagramSerialisation:
    def setup_method(self):
        result, nodes, elements = _run_ssb_udl()
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elements)
        data = compute_diagram_data(
            nodes=node_list, elements=elem_list,
            element_forces=ef, displacements=disp,
        )
        self.d = diagram_data_to_dict(data)

    def test_top_level_keys(self):
        assert "global_extremes" in self.d
        assert "elements" in self.d

    def test_element_keys(self):
        el = self.d["elements"][0]
        for k in ["element_index", "node_i", "node_j", "length_m",
                  "angle_deg", "M_max_knm", "points"]:
            assert k in el, f"Missing key: {k}"

    def test_point_keys(self):
        pt = self.d["elements"][0]["points"][0]
        for k in ["x", "N", "V", "M", "gx", "gy",
                  "N_gx", "N_gy", "V_gx", "V_gy", "M_gx", "M_gy",
                  "def_gx", "def_gy"]:
            assert k in pt, f"Missing key: {k}"

    def test_global_extremes_positive_M(self):
        ge = self.d["global_extremes"]
        assert ge["M_max_knm"] > 0

    def test_n_points_default(self):
        assert len(self.d["elements"][0]["points"]) == 21


# ── TestNPointsParameter ───────────────────────────────────────────────────────

class TestNPointsParameter:
    def test_custom_n_points(self):
        result, nodes, elements = _run_ssb_udl()
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elements)
        data = compute_diagram_data(
            nodes=node_list, elements=elem_list,
            element_forces=ef, displacements=disp,
            n_points=51,
        )
        assert len(data.elements[0].points) == 51

    def test_min_two_points(self):
        result, nodes, elements = _run_ssb_udl()
        node_list, elem_list, ef, disp = _build_api_data(result, nodes, elements)
        data = compute_diagram_data(
            nodes=node_list, elements=elem_list,
            element_forces=ef, displacements=disp,
            n_points=1,  # should clamp to 2
        )
        assert len(data.elements[0].points) == 2
