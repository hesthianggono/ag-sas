"""
Unit Tests: Desain Lentur Balok Baja WF
========================================
Semua test memanggil calculation engine secara langsung (tanpa FastAPI, tanpa DB).
Input menggunakan SteelBeamParams agar satuan selalu eksplisit.

Referensi: SNI 1729:2020, SNI 1727:2020
"""
import math
import pytest
from app.calculation.types import SteelBeamParams, DesignStatus
from app.calculation.steel.beam_calculator import design_steel_beam
from app.calculation.units import E_STEEL_MPA


def _params_wf400(**overrides) -> SteelBeamParams:
    """Params standar WF 400x200x8x13."""
    defaults = dict(
        profile_designation="WF 400x200x8x13",
        height_h_mm=400.0,
        flange_width_b_mm=200.0,
        web_thickness_tw_mm=8.0,
        flange_thickness_tf_mm=13.0,
        sx_cm3=1160.0,
        zx_cm3=1310.0,
        weight_per_m_kgm=66.0,
        fy_mpa=250.0,
        span_l_m=6.0,
        dead_load_w_knm=10.0,
        live_load_w_knm=8.0,
    )
    defaults.update(overrides)
    return SteelBeamParams(**defaults)


def _params_wf200(**overrides) -> SteelBeamParams:
    """Params standar WF 200x100x5.5x8."""
    defaults = dict(
        profile_designation="WF 200x100x5.5x8",
        height_h_mm=200.0,
        flange_width_b_mm=100.0,
        web_thickness_tw_mm=5.5,
        flange_thickness_tf_mm=8.0,
        sx_cm3=180.0,
        zx_cm3=200.0,
        weight_per_m_kgm=21.3,
        fy_mpa=250.0,
        span_l_m=6.0,
        dead_load_w_knm=5.0,
        live_load_w_knm=5.0,
    )
    defaults.update(overrides)
    return SteelBeamParams(**defaults)


# ── Beban Terfaktor ───────────────────────────────────────────────────────────

class TestFactoredLoads:
    def test_wu_includes_self_weight(self):
        r = design_steel_beam(_params_wf200(dead_load_w_knm=10.0, live_load_w_knm=8.0))
        self_weight_knm = 21.3 * 9.81 / 1000.0
        expected_wu = 1.2 * (10.0 + self_weight_knm) + 1.6 * 8.0
        assert r.wu_knm == pytest.approx(expected_wu, rel=1e-4)

    def test_wu_dead_only(self):
        r = design_steel_beam(_params_wf400(dead_load_w_knm=10.0, live_load_w_knm=0.0))
        self_weight_knm = 66.0 * 9.81 / 1000.0
        expected_wu = 1.2 * (10.0 + self_weight_knm)
        assert r.wu_knm == pytest.approx(expected_wu, rel=1e-4)

    def test_mu_simply_supported(self):
        r = design_steel_beam(_params_wf400(span_l_m=8.0, dead_load_w_knm=15.0, live_load_w_knm=20.0))
        expected_mu = r.wu_knm * 8.0**2 / 8.0
        assert r.mu_ultimate_knm == pytest.approx(expected_mu, rel=1e-6)


# ── Cek Kelangsingan Sayap ────────────────────────────────────────────────────

class TestCompactness:
    def test_compact_flange_wf400(self):
        # λ_f = (200/2)/13 = 7.69; λ_pf = 0.38×√(200000/250) = 10.75 → compact
        r = design_steel_beam(_params_wf400())
        assert r.lambda_f == pytest.approx((200.0 / 2.0) / 13.0, rel=1e-4)
        assert r.is_compact is True

    def test_lambda_pf_formula(self):
        r = design_steel_beam(_params_wf400())
        expected = 0.38 * math.sqrt(E_STEEL_MPA / 250.0)
        assert r.lambda_pf == pytest.approx(expected, rel=1e-4)

    def test_lambda_rf_formula(self):
        r = design_steel_beam(_params_wf400())
        expected = 1.0 * math.sqrt(E_STEEL_MPA / 250.0)
        assert r.lambda_rf == pytest.approx(expected, rel=1e-4)

    def test_lambda_rf_greater_than_lambda_pf(self):
        r = design_steel_beam(_params_wf400())
        assert r.lambda_rf > r.lambda_pf

    def test_wf200_compact_check(self):
        # λ_f = (100/2)/8 = 6.25; λ_pf ≈ 10.75 → compact
        r = design_steel_beam(_params_wf200())
        assert r.lambda_f == pytest.approx((100.0 / 2.0) / 8.0, rel=1e-4)
        assert r.is_compact is True


# ── Kapasitas Penampang ───────────────────────────────────────────────────────

class TestCapacity:
    def test_phi_factor_is_090(self):
        r = design_steel_beam(_params_wf400())
        assert r.phi_factor == pytest.approx(0.90)

    def test_mp_compact_formula(self):
        # Mp = Fy × Zx; Zx = 1310 cm³ → 1310000 mm³
        r = design_steel_beam(_params_wf400())
        expected_mp = 250.0 * (1310.0 * 1000.0) / 1_000_000.0  # kN·m
        assert r.mp_knm == pytest.approx(expected_mp, rel=1e-4)

    def test_phi_mn_compact_equals_090_mp(self):
        r = design_steel_beam(_params_wf400())
        assert r.is_compact is True
        assert r.phi_mn_knm == pytest.approx(0.90 * r.mp_knm, rel=1e-6)

    def test_capacity_ratio_formula(self):
        r = design_steel_beam(_params_wf400())
        assert r.capacity_ratio == pytest.approx(r.mu_ultimate_knm / r.phi_mn_knm, rel=1e-6)

    def test_phi_mn_positive(self):
        r = design_steel_beam(_params_wf400())
        assert r.phi_mn_knm > 0


# ── Status AMAN / TIDAK AMAN ─────────────────────────────────────────────────

class TestDesignStatus:
    def test_safe_beam_wf400_light_load(self):
        r = design_steel_beam(_params_wf400(span_l_m=6.0, dead_load_w_knm=10.0, live_load_w_knm=10.0))
        assert r.status == DesignStatus.AMAN
        assert r.capacity_ratio <= 1.0

    def test_unsafe_beam_wf200_heavy_load(self):
        r = design_steel_beam(_params_wf200(span_l_m=8.0, dead_load_w_knm=20.0, live_load_w_knm=25.0))
        assert r.status == DesignStatus.TIDAK_AMAN
        assert r.capacity_ratio > 1.0

    def test_status_aman_iff_capacity_ratio_le_1(self):
        r = design_steel_beam(_params_wf400())
        if r.status == DesignStatus.AMAN:
            assert r.capacity_ratio <= 1.0
        else:
            assert r.capacity_ratio > 1.0


# ── Metadata ──────────────────────────────────────────────────────────────────

class TestMetadata:
    def test_sni_references_present(self):
        r = design_steel_beam(_params_wf400())
        assert "SNI 1729:2020" in r.meta.standard_references
        assert "SNI 1727:2020" in r.meta.standard_references

    def test_formula_version(self):
        r = design_steel_beam(_params_wf400())
        assert r.meta.formula_version == "1.1.0"

    def test_disclaimer_present(self):
        r = design_steel_beam(_params_wf400())
        assert len(r.meta.disclaimer) > 20

    def test_assumptions_present(self):
        r = design_steel_beam(_params_wf400())
        assert "simply supported" in r.meta.assumptions.lower()
