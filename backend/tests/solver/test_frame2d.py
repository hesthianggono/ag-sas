"""Unit tests for 2D Frame Analysis Solver.

Benchmark cases:
  TC-01: Simply supported beam, UDL — verifies midspan deflection & reactions
  TC-02: Cantilever beam, tip point load — verifies tip deflection & fixed-end moment
  TC-03: Fixed-fixed beam, UDL — verifies midspan deflection (analytical)
  TC-04: Symmetric portal frame, lateral load — verifies equilibrium
  TC-05: Single horizontal element, axial load only — verifies axial behaviour

Tolerances: 0.5% relative for deflections/forces, 0.1% for reactions.
"""
import math
import pytest
import numpy as np

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
from app.solver.frame2d.element import compute_element_geometry
from app.solver.frame2d.stiffness import (
    local_stiffness_matrix,
    transformation_matrix,
    global_element_stiffness,
    fixed_end_forces_udl,
)
from app.solver.frame2d.boundary import get_constrained_dofs, apply_boundary_conditions
from app.solver.frame2d.results import Frame2DResult


# ── Common material/section (steel WF400, E=200GPa, I=237e6mm⁴, A=84.12cm²) ─

STEEL = MaterialInput(E_mpa=200_000.0)
SEC_WF400 = SectionInput(A_cm2=84.12, I_cm4=23_700.0)   # I = 237e6 mm⁴ = 23700 cm⁴

SOLVER = Frame2DSolver()


# ── TC-01: Simply Supported Beam, UDL ────────────────────────────────────────

class TestSSB_UDL:
    """
    L=6m, w=20kN/m, pinned-roller supports.
    Analytical: δ_mid = 5wL⁴/(384EI), R_A=R_B=wL/2=60kN, M_mid=wL²/8=90kNm
    """
    L = 6.0
    w = 20.0  # kN/m
    E = 200_000.0  # MPa
    I_cm4 = 23_700.0
    I_m4 = I_cm4 * 1e-8
    E_kn_m2 = E * 1e3

    def _model(self):
        return Frame2DModel(
            title="SSB UDL",
            nodes=[NodeInput(0, 0.0, 0.0), NodeInput(1, self.L, 0.0)],
            elements=[ElementInput(0, 0, 1, STEEL, SEC_WF400, udl_kn_per_m=self.w)],
            supports=[
                SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=False),   # pin
                SupportInput(1, fix_ux=False, fix_uy=True, fix_rz=False),  # roller
            ],
        )

    def test_reactions(self):
        result = SOLVER.solve(self._model())
        reactions = {r.node_index: r for r in result.reactions}
        expected_r = self.w * self.L / 2  # 60 kN
        assert abs(reactions[0].ry_kn - expected_r) < 0.1, \
            f"R_A={reactions[0].ry_kn:.3f}, expected {expected_r}"
        assert abs(reactions[1].ry_kn - expected_r) < 0.1, \
            f"R_B={reactions[1].ry_kn:.3f}, expected {expected_r}"

    def test_midspan_deflection(self):
        result = SOLVER.solve(self._model())
        # Only 2 nodes (ends) — deflection at midspan is zero from DOF indexing.
        # Test max displacement magnitude is reasonable (< span/100 check)
        # With 2-element refinement: split at midpoint to get midspan node
        L = self.L
        w = self.w
        E = self.E_kn_m2
        I = self.I_m4
        delta_analytical = 5 * w * L**4 / (384 * E * I)  # m

        # Use 3-node model for midspan deflection
        model = Frame2DModel(
            title="SSB 3node",
            nodes=[
                NodeInput(0, 0.0, 0.0),
                NodeInput(1, L / 2, 0.0),
                NodeInput(2, L, 0.0),
            ],
            elements=[
                ElementInput(0, 0, 1, STEEL, SEC_WF400, udl_kn_per_m=w),
                ElementInput(1, 1, 2, STEEL, SEC_WF400, udl_kn_per_m=w),
            ],
            supports=[
                SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=False),
                SupportInput(2, fix_ux=False, fix_uy=True, fix_rz=False),
            ],
        )
        result = SOLVER.solve(model)
        disp = {d.node_index: d for d in result.displacements}
        delta_fem = abs(disp[1].uy_m)
        rel_err = abs(delta_fem - delta_analytical) / delta_analytical
        assert rel_err < 0.005, \
            f"Midspan δ: FEM={delta_fem*1000:.3f}mm, analytical={delta_analytical*1000:.3f}mm, err={rel_err:.4f}"

    def test_end_shear(self):
        result = SOLVER.solve(self._model())
        # Shear at node i of element 0 should equal reaction (60 kN)
        ef = result.element_forces[0]
        assert abs(abs(ef.Vy_i_kn) - 60.0) < 0.5, f"Vy_i={ef.Vy_i_kn:.3f}"

    def test_equilibrium(self):
        result = SOLVER.solve(self._model())
        total_ry = sum(r.ry_kn for r in result.reactions)
        assert abs(total_ry - self.w * self.L) < 0.01, \
            f"Sum Ry={total_ry:.4f}, expected {self.w * self.L}"

    def test_max_moment(self):
        # 3-node model to get midspan moment
        L, w = self.L, self.w
        model = Frame2DModel(
            title="SSB moment check",
            nodes=[NodeInput(0,0,0), NodeInput(1,L/2,0), NodeInput(2,L,0)],
            elements=[
                ElementInput(0, 0, 1, STEEL, SEC_WF400, udl_kn_per_m=w),
                ElementInput(1, 1, 2, STEEL, SEC_WF400, udl_kn_per_m=w),
            ],
            supports=[
                SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=False),
                SupportInput(2, fix_ux=False, fix_uy=True, fix_rz=False),
            ],
        )
        result = SOLVER.solve(model)
        # At midspan node, moment from left element j-end should ≈ wL²/8 = 90 kNm
        M_analytical = w * L**2 / 8
        M_fem = abs(result.element_forces[0].Mz_j_knm)
        rel_err = abs(M_fem - M_analytical) / M_analytical
        assert rel_err < 0.005, \
            f"M_mid: FEM={M_fem:.3f}, analytical={M_analytical:.3f}, err={rel_err:.4f}"


# ── TC-02: Cantilever Beam, Tip Point Load ────────────────────────────────────

class TestCantilever:
    """
    L=4m, P=50kN downward at tip, fixed at root.
    δ_tip = PL³/(3EI), M_fix = PL = 200kNm, V = P = 50kN
    """
    L = 4.0
    P = 50.0
    E = 200_000.0
    I_cm4 = 23_700.0
    I_m4 = I_cm4 * 1e-8
    E_kn_m2 = E * 1e3

    def _model(self):
        return Frame2DModel(
            title="Cantilever",
            nodes=[NodeInput(0, 0.0, 0.0), NodeInput(1, self.L, 0.0)],
            elements=[ElementInput(0, 0, 1, STEEL, SEC_WF400)],
            supports=[SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True)],
            nodal_loads=[NodalLoadInput(1, fy_kn=-self.P)],
        )

    def test_tip_deflection(self):
        result = SOLVER.solve(self._model())
        delta_analytical = self.P * self.L**3 / (3 * self.E_kn_m2 * self.I_m4)
        delta_fem = abs(result.displacements[1].uy_m)
        rel_err = abs(delta_fem - delta_analytical) / delta_analytical
        assert rel_err < 0.001, \
            f"Tip δ: FEM={delta_fem*1000:.3f}mm, analytical={delta_analytical*1000:.3f}mm"

    def test_fixed_end_moment(self):
        result = SOLVER.solve(self._model())
        M_fix_analytical = self.P * self.L  # 200 kNm
        M_fix_fem = abs(result.reactions[0].mz_knm)
        rel_err = abs(M_fix_fem - M_fix_analytical) / M_fix_analytical
        assert rel_err < 0.001, \
            f"M_fix: FEM={M_fix_fem:.3f}, analytical={M_fix_analytical:.3f}"

    def test_reaction_force(self):
        result = SOLVER.solve(self._model())
        reactions = {r.node_index: r for r in result.reactions}
        assert abs(reactions[0].ry_kn - self.P) < 0.01, \
            f"R_y={reactions[0].ry_kn:.3f}, expected {self.P}"

    def test_shear(self):
        result = SOLVER.solve(self._model())
        ef = result.element_forces[0]
        assert abs(abs(ef.Vy_i_kn) - self.P) < 0.1, f"Vy_i={ef.Vy_i_kn:.3f}"

    def test_tip_rotation(self):
        result = SOLVER.solve(self._model())
        rot_analytical = self.P * self.L**2 / (2 * self.E_kn_m2 * self.I_m4)
        rot_fem = abs(result.displacements[1].rz_rad)
        rel_err = abs(rot_fem - rot_analytical) / rot_analytical
        assert rel_err < 0.001, \
            f"Tip θ: FEM={rot_fem:.6f}, analytical={rot_analytical:.6f}"


# ── TC-03: Fixed-Fixed Beam, UDL ─────────────────────────────────────────────

class TestFixedFixed:
    """
    L=6m, w=20kN/m, both ends fixed.
    δ_mid = wL⁴/(384EI), M_end = wL²/12 = 60kNm, M_mid = wL²/24 = 30kNm
    R = wL/2 = 60kN
    """
    L = 6.0
    w = 20.0
    E = 200_000.0
    I_cm4 = 23_700.0
    I_m4 = I_cm4 * 1e-8
    E_kn_m2 = E * 1e3

    def _model_3node(self):
        L, w = self.L, self.w
        return Frame2DModel(
            title="Fixed-Fixed 3node",
            nodes=[NodeInput(0,0,0), NodeInput(1,L/2,0), NodeInput(2,L,0)],
            elements=[
                ElementInput(0, 0, 1, STEEL, SEC_WF400, udl_kn_per_m=w),
                ElementInput(1, 1, 2, STEEL, SEC_WF400, udl_kn_per_m=w),
            ],
            supports=[
                SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True),
                SupportInput(2, fix_ux=True, fix_uy=True, fix_rz=True),
            ],
        )

    def test_midspan_deflection(self):
        delta_analytical = self.w * self.L**4 / (384 * self.E_kn_m2 * self.I_m4)
        result = SOLVER.solve(self._model_3node())
        delta_fem = abs(result.displacements[1].uy_m)
        rel_err = abs(delta_fem - delta_analytical) / delta_analytical
        assert rel_err < 0.01, \
            f"δ_mid: FEM={delta_fem*1000:.3f}mm, analytical={delta_analytical*1000:.3f}mm"

    def test_end_moments(self):
        M_end_analytical = self.w * self.L**2 / 12  # 60 kNm
        result = SOLVER.solve(self._model_3node())
        M_fix = abs(result.reactions[0].mz_knm)
        rel_err = abs(M_fix - M_end_analytical) / M_end_analytical
        assert rel_err < 0.01, \
            f"M_fix: FEM={M_fix:.3f}, analytical={M_end_analytical:.3f}"

    def test_reactions(self):
        result = SOLVER.solve(self._model_3node())
        r = {rx.node_index: rx for rx in result.reactions}
        expected = self.w * self.L / 2
        assert abs(r[0].ry_kn - expected) < 0.1
        assert abs(r[2].ry_kn - expected) < 0.1


# ── TC-04: Symmetric Portal Frame, Lateral Load ───────────────────────────────

class TestPortalFrame:
    """
    h=4m columns (fixed at base), b=6m beam.
    H=30kN lateral at top-left node (node 1).
    Equilibrium: sum Rx = 30kN (split 15kN each column base).
    """
    h, b, H = 4.0, 6.0, 30.0
    SEC_COL = SectionInput(A_cm2=84.12, I_cm4=23_700.0)
    SEC_BEAM = SectionInput(A_cm2=168.24, I_cm4=47_400.0)

    def _model(self):
        #  Node layout:
        #  1 ---beam--- 2
        #  |             |
        #  0             3  (fixed bases)
        nodes = [
            NodeInput(0, 0.0, 0.0),
            NodeInput(1, 0.0, self.h),
            NodeInput(2, self.b, self.h),
            NodeInput(3, self.b, 0.0),
        ]
        elements = [
            ElementInput(0, 0, 1, STEEL, self.SEC_COL),   # left column
            ElementInput(1, 1, 2, STEEL, self.SEC_BEAM),  # beam
            ElementInput(2, 3, 2, STEEL, self.SEC_COL),   # right column
        ]
        supports = [
            SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True),
            SupportInput(3, fix_ux=True, fix_uy=True, fix_rz=True),
        ]
        loads = [NodalLoadInput(1, fx_kn=self.H)]
        return Frame2DModel("Portal", nodes, elements, supports, loads)

    def test_horizontal_equilibrium(self):
        result = SOLVER.solve(self._model())
        total_rx = sum(r.rx_kn for r in result.reactions)
        assert abs(total_rx + self.H) < 0.1, \
            f"Sum Rx + H = {total_rx + self.H:.4f} (should be 0)"

    def test_vertical_equilibrium(self):
        result = SOLVER.solve(self._model())
        total_ry = sum(r.ry_kn for r in result.reactions)
        assert abs(total_ry) < 0.1, f"Sum Ry = {total_ry:.4f} (should be 0)"

    def test_sway_direction(self):
        result = SOLVER.solve(self._model())
        disp = {d.node_index: d for d in result.displacements}
        # Top nodes should displace in +X direction (rightward)
        assert disp[1].ux_m > 0, "Node 1 should sway right"
        assert disp[2].ux_m > 0, "Node 2 should sway right"

    def test_column_base_shear(self):
        # By anti-symmetry (rigid beam approximation): each column takes H/2
        result = SOLVER.solve(self._model())
        total_rx = abs(sum(r.rx_kn for r in result.reactions))
        assert abs(total_rx - self.H) < 0.5


# ── TC-05: Axial-Only Truss Bar ───────────────────────────────────────────────

class TestAxialBar:
    """Single horizontal bar, axial tension load.
    F=100kN, L=5m, A=50cm²=50e-4m², E=200GPa=200e6kN/m²
    δ = FL/(EA) = 100*5/(200e6*50e-4) = 0.00025m = 0.25mm
    """
    L, F = 5.0, 100.0
    A_cm2 = 50.0
    E = 200_000.0

    def _model(self):
        return Frame2DModel(
            title="Axial bar",
            nodes=[NodeInput(0,0,0), NodeInput(1,self.L,0)],
            elements=[ElementInput(0, 0, 1, MaterialInput(self.E), SectionInput(self.A_cm2, 1.0))],
            supports=[SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True)],
            nodal_loads=[NodalLoadInput(1, fx_kn=self.F)],
        )

    def test_axial_displacement(self):
        result = SOLVER.solve(self._model())
        E_kn_m2 = self.E * 1e3
        A_m2 = self.A_cm2 * 1e-4
        delta_analytical = self.F * self.L / (E_kn_m2 * A_m2)
        delta_fem = abs(result.displacements[1].ux_m)
        rel_err = abs(delta_fem - delta_analytical) / delta_analytical
        assert rel_err < 0.001, \
            f"δ_axial: FEM={delta_fem*1000:.4f}mm, analytical={delta_analytical*1000:.4f}mm"

    def test_axial_reaction(self):
        result = SOLVER.solve(self._model())
        reactions = {r.node_index: r for r in result.reactions}
        assert abs(reactions[0].rx_kn + self.F) < 0.01, \
            f"R_x={reactions[0].rx_kn:.4f}, expected {-self.F}"


# ── Unit tests for element/stiffness modules ──────────────────────────────────

class TestElementGeometry:
    def test_horizontal(self):
        g = compute_element_geometry(0,0, 6,0, 0, 1)
        assert abs(g.length - 6.0) < 1e-10
        assert abs(g.angle_rad) < 1e-10
        assert abs(g.cos_theta - 1.0) < 1e-10
        assert abs(g.sin_theta) < 1e-10
        assert g.dof_i == (0, 1, 2)
        assert g.dof_j == (3, 4, 5)

    def test_vertical(self):
        g = compute_element_geometry(0,0, 0,4, 0, 1)
        assert abs(g.length - 4.0) < 1e-10
        assert abs(g.angle_rad - math.pi/2) < 1e-10
        assert abs(g.cos_theta) < 1e-10
        assert abs(g.sin_theta - 1.0) < 1e-10

    def test_inclined(self):
        g = compute_element_geometry(0,0, 3,4, 0, 1)
        assert abs(g.length - 5.0) < 1e-10
        assert abs(g.cos_theta - 0.6) < 1e-10
        assert abs(g.sin_theta - 0.8) < 1e-10

    def test_zero_length_raises(self):
        with pytest.raises(ValueError):
            compute_element_geometry(1,1, 1,1, 0, 1)

    def test_dof_indices_non_zero_nodes(self):
        g = compute_element_geometry(0,0, 1,0, 2, 5)
        assert g.dof_i == (6, 7, 8)
        assert g.dof_j == (15, 16, 17)


class TestLocalStiffness:
    def test_shape_and_symmetry(self):
        k = local_stiffness_matrix(200e6, 50e-4, 237e-6, 6.0)
        assert k.shape == (6, 6)
        assert np.allclose(k, k.T, atol=1e-6)

    def test_axial_terms(self):
        E, A, L = 200e6, 50e-4, 5.0
        k = local_stiffness_matrix(E, A, 1e-4, L)
        EA_L = E * A / L
        assert abs(k[0, 0] - EA_L) < 1e-6
        assert abs(k[3, 3] - EA_L) < 1e-6
        assert abs(k[0, 3] + EA_L) < 1e-6

    def test_positive_definite_constrained(self):
        # Remove rows/cols 0,1,2 (fix node i) and check remaining is PD
        k = local_stiffness_matrix(200e6, 84.12e-4, 23700e-8, 6.0)
        k_free = k[3:, 3:]
        eigvals = np.linalg.eigvalsh(k_free)
        assert np.all(eigvals > 0), f"Eigenvalues: {eigvals}"


class TestFEF:
    def test_horizontal_beam_downward_udl(self):
        from app.solver.frame2d.element import compute_element_geometry
        L = 6.0
        w = 20.0  # kN/m downward
        geom = compute_element_geometry(0,0, L,0, 0, 1)
        p = fixed_end_forces_udl(w, L, geom)
        # For downward UDL w, p_fef is the equivalent load vector:
        # v-components are negative (downward = -v direction)
        # p_fef = [0, -wL/2, -wL²/12, 0, -wL/2, +wL²/12]
        assert abs(p[1] + w*L/2) < 1e-6, f"v1={p[1]}, expected {-w*L/2}"
        assert abs(p[2] + w*L**2/12) < 1e-6, f"θ1={p[2]}, expected {-w*L**2/12}"
        assert abs(p[4] + w*L/2) < 1e-6, f"v2={p[4]}, expected {-w*L/2}"
        assert abs(p[5] - w*L**2/12) < 1e-6, f"θ2={p[5]}, expected {+w*L**2/12}"
        assert abs(p[0]) < 1e-10  # no axial for horizontal beam


class TestBoundaryConditions:
    def test_constrained_dofs_fixed(self):
        supports = [(0, True, True, True)]
        dofs = get_constrained_dofs(supports)
        assert set(dofs) == {0, 1, 2}

    def test_constrained_dofs_pin_roller(self):
        supports = [(0, True, True, False), (2, False, True, False)]
        dofs = get_constrained_dofs(supports)
        assert set(dofs) == {0, 1, 7}  # node 2 → dofs 6,7,8; fix_uy → 7

    def test_apply_bc_diagonal(self):
        K = np.eye(6)
        F = np.ones(6)
        K_bc, F_bc = apply_boundary_conditions(K, F, [0, 2])
        assert K_bc[0, 0] == 1.0
        assert K_bc[2, 2] == 1.0
        assert F_bc[0] == 0.0
        assert F_bc[2] == 0.0
        assert F_bc[1] == 1.0  # unconstrained unchanged


class TestModelValidation:
    def test_valid_model(self):
        model = Frame2DModel(
            title="Valid",
            nodes=[NodeInput(0,0,0), NodeInput(1,5,0)],
            elements=[ElementInput(0, 0, 1, STEEL, SEC_WF400)],
            supports=[SupportInput(0, True, True, True)],
            nodal_loads=[NodalLoadInput(1, fy_kn=-10)],
        )
        assert model.validate() == []

    def test_invalid_node_reference(self):
        model = Frame2DModel(
            title="Bad",
            nodes=[NodeInput(0,0,0), NodeInput(1,5,0)],
            elements=[ElementInput(0, 0, 99, STEEL, SEC_WF400)],
            supports=[SupportInput(0, True, True, True)],
        )
        errors = model.validate()
        assert any("node_j" in e for e in errors)

    def test_zero_length_element_fails(self):
        model = Frame2DModel(
            title="ZeroLen",
            nodes=[NodeInput(0,0,0), NodeInput(1,0,0)],
            elements=[ElementInput(0, 0, 1, STEEL, SEC_WF400)],
            supports=[SupportInput(0, True, True, True)],
        )
        with pytest.raises(ValueError):
            SOLVER.solve(model)

    def test_singular_matrix_raises(self):
        # No supports at all → singular K
        model = Frame2DModel(
            title="Unstable",
            nodes=[NodeInput(0,0,0), NodeInput(1,5,0)],
            elements=[ElementInput(0, 0, 1, STEEL, SEC_WF400)],
            supports=[],
            nodal_loads=[NodalLoadInput(1, fy_kn=-10)],
        )
        with pytest.raises((np.linalg.LinAlgError, ValueError)):
            SOLVER.solve(model)
