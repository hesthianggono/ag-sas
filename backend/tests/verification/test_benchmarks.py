"""
Unit tests — Verification & Validation Framework AG-SAS.

Tests ini memverifikasi:
1. Formula analitik dalam benchmark cases itu sendiri sudah benar
2. Fungsi compare_result() bekerja dengan benar
3. Runner menghasilkan PASS untuk semua benchmark (analytical vs analytical)
4. Format laporan dapat dibuat tanpa error
"""

import math
import pytest

from app.verification.models import (
    BenchmarkCase,
    BenchmarkResult,
    CheckStatus,
    ExpectedValue,
    StructureType,
    VerificationLevel,
    VerificationSession,
)
from app.verification.compare import compare_quantity, compare_result
from app.verification.benchmarks.simply_supported_beam import (
    BENCHMARK as SSB,
    analytical_solution as ssb_solution,
    L_m as SSB_L,
    w_kNm as SSB_W,
    E_kNm2 as SSB_E,
    I_m4 as SSB_I,
)
from app.verification.benchmarks.cantilever_beam import (
    BENCHMARK as CANT,
    analytical_solution as cant_solution,
    L_m as CANT_L,
    P_kN as CANT_P,
    E_kNm2 as CANT_E,
    I_m4 as CANT_I,
)
from app.verification.benchmarks.portal_2d import (
    BENCHMARK as PORTAL,
    equilibrium_check,
    h_m as PORTAL_H,
    b_m as PORTAL_B,
    H_kN as PORTAL_LOAD,
)
from app.verification.benchmarks.truss_2d import (
    BENCHMARK as TRUSS,
    method_of_joints,
    P_kN as TRUSS_P,
    span_m as TRUSS_SPAN,
    rise_m as TRUSS_RISE,
)
from app.verification.benchmarks.registry import (
    ALL_BENCHMARKS, get_benchmark, list_benchmarks,
)
from app.verification.regression.runner import run_benchmark, run_all
from app.verification.reports.formatter import (
    format_benchmark_result,
    format_session_report,
    result_to_api_dict,
    session_to_api_dict,
)

TOL_REL = 1e-9   # toleransi untuk verifikasi formula Python


# ── Simply Supported Beam — Formula Verification ──────────────────────────────

class TestSSBFormula:
    """Verifikasi formula analitik SSB UDL."""

    def test_midspan_deflection_formula(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        EI = SSB_E * SSB_I
        expected_mm = 5 * SSB_W * SSB_L**4 / (384 * EI) * 1000
        assert sol["midspan_deflection_mm"] == pytest.approx(expected_mm, rel=TOL_REL)

    def test_max_moment_formula(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        expected = SSB_W * SSB_L**2 / 8
        assert sol["max_moment_kNm"] == pytest.approx(expected, rel=TOL_REL)

    def test_reactions_symmetric(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        assert sol["reaction_A_kN"] == pytest.approx(sol["reaction_B_kN"], rel=TOL_REL)

    def test_reaction_equals_half_total_load(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        total_load = SSB_W * SSB_L
        assert sol["reaction_A_kN"] == pytest.approx(total_load / 2, rel=TOL_REL)

    def test_max_shear_equals_reaction(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        assert sol["max_shear_kN"] == pytest.approx(sol["reaction_A_kN"], rel=TOL_REL)

    def test_known_values(self):
        # L=6m, w=20kN/m, E=200GPa, I=237e6mm⁴ — nilai referensi
        sol = ssb_solution(L=6.0, w=20.0, E=200_000_000, I=237e-6)
        # M_max = 20×36/8 = 90 kN·m
        assert sol["max_moment_kNm"] == pytest.approx(90.0, rel=TOL_REL)
        # R = 20×6/2 = 60 kN
        assert sol["reaction_A_kN"] == pytest.approx(60.0, rel=TOL_REL)

    def test_deflection_increases_with_load(self):
        sol1 = ssb_solution(L=SSB_L, w=10.0,  E=SSB_E, I=SSB_I)
        sol2 = ssb_solution(L=SSB_L, w=20.0,  E=SSB_E, I=SSB_I)
        assert sol2["midspan_deflection_mm"] == pytest.approx(2 * sol1["midspan_deflection_mm"], rel=TOL_REL)

    def test_deflection_decreases_with_stiffer_I(self):
        sol1 = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        sol2 = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I * 2)
        assert sol2["midspan_deflection_mm"] == pytest.approx(sol1["midspan_deflection_mm"] / 2, rel=TOL_REL)


# ── Cantilever Beam — Formula Verification ────────────────────────────────────

class TestCantileverFormula:
    def test_tip_deflection_formula(self):
        sol = cant_solution(L=CANT_L, P=CANT_P, E=CANT_E, I=CANT_I)
        EI = CANT_E * CANT_I
        expected_mm = CANT_P * CANT_L**3 / (3 * EI) * 1000
        assert sol["tip_deflection_mm"] == pytest.approx(expected_mm, rel=TOL_REL)

    def test_tip_rotation_formula(self):
        sol = cant_solution(L=CANT_L, P=CANT_P, E=CANT_E, I=CANT_I)
        EI = CANT_E * CANT_I
        expected_rad = CANT_P * CANT_L**2 / (2 * EI)
        assert sol["tip_rotation_rad"] == pytest.approx(expected_rad, rel=TOL_REL)

    def test_fixed_end_moment(self):
        sol = cant_solution(L=CANT_L, P=CANT_P, E=CANT_E, I=CANT_I)
        assert sol["fixed_end_moment_kNm"] == pytest.approx(CANT_P * CANT_L, rel=TOL_REL)

    def test_shear_equals_point_load(self):
        sol = cant_solution(L=CANT_L, P=CANT_P, E=CANT_E, I=CANT_I)
        assert sol["max_shear_kN"] == pytest.approx(CANT_P, rel=TOL_REL)

    def test_reaction_equals_point_load(self):
        sol = cant_solution(L=CANT_L, P=CANT_P, E=CANT_E, I=CANT_I)
        assert sol["reaction_vertical_kN"] == pytest.approx(CANT_P, rel=TOL_REL)

    def test_deflection_scales_with_L_cubed(self):
        sol1 = cant_solution(L=2.0, P=CANT_P, E=CANT_E, I=CANT_I)
        sol2 = cant_solution(L=4.0, P=CANT_P, E=CANT_E, I=CANT_I)
        ratio = sol2["tip_deflection_mm"] / sol1["tip_deflection_mm"]
        assert ratio == pytest.approx(8.0, rel=TOL_REL)

    def test_known_values_L4_P50(self):
        sol = cant_solution(L=4.0, P=50.0, E=200_000_000, I=237e-6)
        # M_fix = 50 × 4 = 200 kN·m
        assert sol["fixed_end_moment_kNm"] == pytest.approx(200.0, rel=TOL_REL)


# ── Portal 2D — Equilibrium Verification ─────────────────────────────────────

class TestPortalEquilibrium:
    def test_horizontal_reactions_sum_to_H(self):
        sol = equilibrium_check(H=PORTAL_LOAD, h=PORTAL_H, b=PORTAL_B)
        total_h = sol["horizontal_reaction_left_kN"] + sol["horizontal_reaction_right_kN"]
        assert total_h == pytest.approx(PORTAL_LOAD, rel=TOL_REL)

    def test_each_column_carries_half_shear(self):
        sol = equilibrium_check(H=PORTAL_LOAD, h=PORTAL_H, b=PORTAL_B)
        assert sol["shear_per_column_kN"] == pytest.approx(PORTAL_LOAD / 2, rel=TOL_REL)

    def test_vertical_reactions_overturning(self):
        sol = equilibrium_check(H=30.0, h=4.0, b=6.0)
        # ΣM_A = 0: R_v_B × 6 = 30 × 4 → R_v_B = 20 kN
        assert sol["vertical_reaction_left_kN"] == pytest.approx(20.0, rel=TOL_REL)
        assert sol["vertical_reaction_right_kN"] == pytest.approx(20.0, rel=TOL_REL)

    def test_moment_equilibrium_about_base(self):
        H, h, b = 30.0, 4.0, 6.0
        sol = equilibrium_check(H=H, h=h, b=b)
        # ΣM_A = H×h - R_v × b = 0
        residual = H * h - sol["vertical_reaction_right_kN"] * b
        assert abs(residual) < 1e-9

    def test_global_horizontal_equilibrium(self):
        H = 30.0
        sol = equilibrium_check(H=H, h=PORTAL_H, b=PORTAL_B)
        # ΣFx: H - R_left - R_right = 0
        residual = H - sol["horizontal_reaction_left_kN"] - sol["horizontal_reaction_right_kN"]
        assert abs(residual) < 1e-9


# ── Truss 2D — Method of Joints Verification ─────────────────────────────────

class TestTrussMethodOfJoints:
    def test_vertical_reactions_sum_to_P(self):
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        total_v = sol["reaction_N1_y_kN"] + sol["reaction_N2_y_kN"]
        assert total_v == pytest.approx(TRUSS_P, rel=TOL_REL)

    def test_reactions_symmetric(self):
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        assert sol["reaction_N1_y_kN"] == pytest.approx(sol["reaction_N2_y_kN"], rel=TOL_REL)

    def test_no_horizontal_reaction(self):
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        assert abs(sol["reaction_N1_x_kN"]) < 1e-9

    def test_diagonal_members_equal(self):
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        assert sol["force_M1_kN"] == pytest.approx(sol["force_M2_kN"], rel=TOL_REL)

    def test_diagonal_in_compression(self):
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        assert sol["force_M1_kN"] < 0  # negatif = tekan

    def test_tie_rod_in_tension(self):
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        assert sol["force_M3_kN"] > 0  # positif = tarik

    def test_joint_equilibrium_N3_vertical(self):
        # Di joint N3: ΣFy = 0: F_M1_y + F_M2_y + (-P) = 0
        theta = math.atan2(TRUSS_RISE, TRUSS_SPAN / 2)
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        # F_M1 dan F_M2 bertanda negatif (tekan), komponen Y positif saat menuju N3
        Fy_M1 = -sol["force_M1_kN"] * math.sin(theta)  # gaya ke N3 dari M1
        Fy_M2 = -sol["force_M2_kN"] * math.sin(theta)  # gaya ke N3 dari M2
        residual = Fy_M1 + Fy_M2 - TRUSS_P
        assert abs(residual) < 1e-9

    def test_tie_rod_horizontal_equilibrium(self):
        # Di joint N1: ΣFx = 0: F_tie - F_M1 cos θ = 0
        theta = math.atan2(TRUSS_RISE, TRUSS_SPAN / 2)
        sol = method_of_joints(P=TRUSS_P, span=TRUSS_SPAN, rise=TRUSS_RISE)
        F_diag = -sol["force_M1_kN"]          # besar gaya diagonal
        F_tie_expected = F_diag * math.cos(theta)
        assert sol["force_M3_kN"] == pytest.approx(F_tie_expected, rel=TOL_REL)

    def test_known_values_P40(self):
        sol = method_of_joints(P=40.0, span=4.0, rise=2.0)
        # θ = arctan(2/2) = 45°
        # F_diag = P/(2sin45) = 40/√2 = 20√2 ≈ 28.284
        # F_tie  = F_diag × cos45 = 20
        assert sol["force_M3_kN"] == pytest.approx(20.0, rel=TOL_REL)
        assert abs(sol["force_M1_kN"]) == pytest.approx(20 * math.sqrt(2), rel=TOL_REL)


# ── compare_quantity ──────────────────────────────────────────────────────────

class TestCompareQuantity:
    def test_exact_match_passes(self):
        check = compare_quantity("x", expected=100.0, actual=100.0,
                                 unit="mm", tolerance_rel=0.001, tolerance_abs=1e-9)
        assert check.status == CheckStatus.PASS
        assert check.abs_error == pytest.approx(0.0)

    def test_within_tolerance_passes(self):
        check = compare_quantity("x", expected=100.0, actual=100.05,
                                 unit="mm", tolerance_rel=0.001, tolerance_abs=1e-9)
        # rel_error = 0.05/100 = 5e-4 < 1e-3 → PASS
        assert check.status == CheckStatus.PASS

    def test_outside_tolerance_fails(self):
        check = compare_quantity("x", expected=100.0, actual=105.0,
                                 unit="mm", tolerance_rel=0.001, tolerance_abs=1e-9)
        # rel_error = 5/100 = 0.05 > 0.001 → FAIL
        assert check.status == CheckStatus.FAIL

    def test_none_actual_skips(self):
        check = compare_quantity("x", expected=100.0, actual=None,
                                 unit="mm", tolerance_rel=0.001, tolerance_abs=1e-9)
        assert check.status == CheckStatus.SKIP

    def test_near_zero_expected_uses_abs_tol(self):
        check = compare_quantity("x", expected=0.0, actual=1e-10,
                                 unit="mm", tolerance_rel=0.001, tolerance_abs=1e-9)
        assert check.status == CheckStatus.PASS

    def test_error_fields_populated(self):
        check = compare_quantity("x", expected=50.0, actual=51.0,
                                 unit="kN", tolerance_rel=0.1, tolerance_abs=1e-9)
        assert check.abs_error == pytest.approx(1.0)
        assert check.rel_error == pytest.approx(1.0 / 50.0)

    def test_negative_values(self):
        check = compare_quantity("N", expected=-28.28, actual=-28.29,
                                 unit="kN", tolerance_rel=0.01, tolerance_abs=1e-9)
        assert check.status == CheckStatus.PASS


# ── compare_result ────────────────────────────────────────────────────────────

class TestCompareResult:
    def test_all_pass(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        result = compare_result(SSB, actual_values=sol, solver_name="test")
        assert result.overall_status == CheckStatus.PASS
        assert result.failed == 0

    def test_partial_skip(self):
        result = compare_result(SSB, actual_values={}, solver_name="empty")
        assert result.overall_status == CheckStatus.SKIP
        assert result.skipped == len(SSB.expected_values)

    def test_one_fail_makes_overall_fail(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        sol["midspan_deflection_mm"] = 999.0   # nilai salah
        result = compare_result(SSB, actual_values=sol)
        assert result.overall_status == CheckStatus.FAIL
        assert result.failed >= 1

    def test_result_id_is_uuid(self):
        import uuid
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        result = compare_result(SSB, actual_values=sol)
        uuid.UUID(result.result_id)  # raises ValueError if not valid

    def test_result_has_correct_benchmark_id(self):
        sol = ssb_solution(L=SSB_L, w=SSB_W, E=SSB_E, I=SSB_I)
        result = compare_result(SSB, actual_values=sol)
        assert result.benchmark_id == SSB.benchmark_id


# ── Registry ──────────────────────────────────────────────────────────────────

class TestRegistry:
    def test_all_benchmarks_not_empty(self):
        assert len(ALL_BENCHMARKS) >= 4

    def test_get_benchmark_by_id(self):
        b = get_benchmark("ssb_udl_01")
        assert b is not None
        assert b.benchmark_id == "ssb_udl_01"

    def test_get_benchmark_missing(self):
        assert get_benchmark("nonexistent_xyz") is None

    def test_list_filter_by_type(self):
        beams = list_benchmarks(structure_type="beam_2d")
        assert all(b.structure_type.value == "beam_2d" for b in beams)
        assert len(beams) >= 2

    def test_list_filter_by_tag(self):
        analytical = list_benchmarks(tag="analytical")
        assert len(analytical) >= 2

    def test_all_benchmarks_have_expected_values(self):
        for b in ALL_BENCHMARKS:
            assert len(b.expected_values) > 0, f"{b.benchmark_id} has no expected values"

    def test_all_benchmark_ids_unique(self):
        ids = [b.benchmark_id for b in ALL_BENCHMARKS]
        assert len(ids) == len(set(ids))


# ── Regression Runner ─────────────────────────────────────────────────────────

class TestRegressionRunner:
    def test_run_single_benchmark_passes(self):
        result = run_benchmark("ssb_udl_01")
        assert result.overall_status == CheckStatus.PASS

    def test_run_cantilever_passes(self):
        result = run_benchmark("cant_pl_01")
        assert result.overall_status == CheckStatus.PASS

    def test_run_portal_passes(self):
        result = run_benchmark("portal_2d_01")
        assert result.overall_status == CheckStatus.PASS

    def test_run_truss_passes(self):
        result = run_benchmark("truss_2d_01")
        assert result.overall_status == CheckStatus.PASS

    def test_run_all_returns_session(self):
        session = run_all()
        assert isinstance(session, VerificationSession)
        assert len(session.results) >= 4

    def test_run_all_no_failures(self):
        session = run_all()
        assert session.total_failed == 0

    def test_run_all_session_id_unique(self):
        import uuid
        s1 = run_all()
        s2 = run_all()
        assert s1.session_id != s2.session_id
        uuid.UUID(s1.session_id)

    def test_run_invalid_benchmark_raises(self):
        with pytest.raises(ValueError):
            run_benchmark("nonexistent_benchmark")


# ── Report Formatter ──────────────────────────────────────────────────────────

class TestReportFormatter:
    def test_format_benchmark_result_no_error(self):
        result = run_benchmark("ssb_udl_01")
        report = format_benchmark_result(result)
        assert isinstance(report, str)
        assert len(report) > 0

    def test_format_session_report_no_error(self):
        session = run_all()
        report = format_session_report(session)
        assert "VERIFICATION REPORT" in report
        assert "DISCLAIMER" in report

    def test_format_contains_benchmark_id(self):
        result = run_benchmark("ssb_udl_01")
        report = format_benchmark_result(result)
        assert "ssb_udl_01" in report

    def test_format_contains_pass_status(self):
        result = run_benchmark("ssb_udl_01")
        report = format_benchmark_result(result)
        assert "PASS" in report or "✓" in report

    def test_result_to_api_dict_keys(self):
        result = run_benchmark("ssb_udl_01")
        d = result_to_api_dict(result)
        assert "result_id" in d
        assert "benchmark_id" in d
        assert "overall_status" in d
        assert "checks" in d
        assert "summary" in d

    def test_session_to_api_dict_keys(self):
        session = run_all()
        d = session_to_api_dict(session)
        assert "session_id" in d
        assert "summary" in d
        assert "results" in d
        assert d["summary"]["total"] >= 4
