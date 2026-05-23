"""
Unit Tests: Desain Lentur Balok Beton Bertulang
================================================
Semua test memanggil calculation engine secara langsung (tanpa FastAPI, tanpa DB).
Input menggunakan ConcreteBeamParams agar satuan selalu eksplisit.

Referensi: SNI 2847:2019, SNI 1727:2020
"""
import math
import pytest
from app.calculation.types import ConcreteBeamParams, DesignStatus
from app.calculation.concrete.beam_calculator import design_concrete_beam, _beta1
from app.calculation.units import knm_to_nmm, NMM_PER_KNM


def _params(**overrides) -> ConcreteBeamParams:
    """Buat params standar dengan kemungkinan override."""
    defaults = dict(
        width_b_mm=300.0, height_h_mm=600.0, cover_cc_mm=40.0,
        bar_diameter_mm=19.0, stirrup_diameter_mm=10.0,
        fc_prime_mpa=25.0, fy_mpa=400.0,
        span_l_m=6.0, dead_load_w_knm=20.0, live_load_w_knm=15.0,
    )
    defaults.update(overrides)
    return ConcreteBeamParams(**defaults)


# ── Validasi Input ────────────────────────────────────────────────────────────

class TestInputValidation:
    def test_no_errors_for_valid_params(self):
        assert _params().validate() == []

    def test_fc_below_minimum_returns_error(self):
        errors = _params(fc_prime_mpa=15.0).validate()
        assert any("17 MPa" in e for e in errors)

    def test_negative_span_returns_error(self):
        errors = _params(span_l_m=-1.0).validate()
        assert any("L harus > 0" in e for e in errors)

    def test_invalid_effective_depth_returns_error(self):
        # cover > h → d negatif
        errors = _params(height_h_mm=100.0, cover_cc_mm=90.0,
                         bar_diameter_mm=25.0, stirrup_diameter_mm=10.0).validate()
        assert any("efektif" in e.lower() for e in errors)


# ── Faktor β1 ─────────────────────────────────────────────────────────────────

class TestBeta1:
    def test_fc_le_28_gives_085(self):
        assert _beta1(25.0) == pytest.approx(0.85)

    def test_fc_exactly_28_gives_085(self):
        assert _beta1(28.0) == pytest.approx(0.85)

    def test_fc_35_gives_080(self):
        # β1 = 0.85 − 0.05×(35−28)/7 = 0.85 − 0.05 = 0.80
        assert _beta1(35.0) == pytest.approx(0.80, abs=1e-6)

    def test_fc_56_gives_065(self):
        # β1 = 0.85 − 0.05×(56−28)/7 = 0.85 − 0.20 = 0.65
        assert _beta1(56.0) == pytest.approx(0.65, abs=1e-6)

    def test_fc_very_high_capped_at_065(self):
        assert _beta1(100.0) == pytest.approx(0.65)


# ── Beban Terfaktor ───────────────────────────────────────────────────────────

class TestFactoredLoads:
    def test_wu_lrfd_combination_1_2D_plus_1_6L(self):
        r = design_concrete_beam(_params(dead_load_w_knm=20.0, live_load_w_knm=15.0))
        # U = 1.2×20 + 1.6×15 = 24 + 24 = 48 kN/m
        assert r.wu_knm == pytest.approx(48.0)

    def test_mu_simply_supported(self):
        r = design_concrete_beam(_params(span_l_m=6.0, dead_load_w_knm=20.0, live_load_w_knm=15.0))
        # Mu = 48×6²/8 = 216 kN·m
        assert r.mu_ultimate_knm == pytest.approx(216.0)

    def test_vu_simply_supported(self):
        r = design_concrete_beam(_params(span_l_m=6.0, dead_load_w_knm=20.0, live_load_w_knm=15.0))
        # Vu = 48×6/2 = 144 kN
        assert r.vu_ultimate_kn == pytest.approx(144.0)

    def test_dead_only_load(self):
        r = design_concrete_beam(_params(dead_load_w_knm=10.0, live_load_w_knm=0.0))
        assert r.wu_knm == pytest.approx(12.0)  # 1.2×10


# ── Geometri Efektif ──────────────────────────────────────────────────────────

class TestEffectiveDepth:
    def test_d_calculation(self):
        r = design_concrete_beam(_params(
            height_h_mm=500, cover_cc_mm=40,
            bar_diameter_mm=16, stirrup_diameter_mm=10,
        ))
        # d = 500 − 40 − 10 − 0.5×16 = 442 mm
        assert r.effective_depth_d_mm == pytest.approx(442.0)


# ── Rasio Tulangan ────────────────────────────────────────────────────────────

class TestReinforcementRatios:
    def test_rho_min_formula(self):
        r = design_concrete_beam(_params(fc_prime_mpa=25.0, fy_mpa=400.0))
        expected = max(0.25 * math.sqrt(25.0) / 400.0, 1.4 / 400.0)
        assert r.rho_min == pytest.approx(expected, rel=1e-5)

    def test_rho_max_is_075_rho_balanced(self):
        r = design_concrete_beam(_params(fc_prime_mpa=25.0, fy_mpa=400.0))
        beta1 = 0.85  # fc'=25 ≤ 28
        rho_bal = (0.85 * beta1 * 25.0 / 400.0) * (600.0 / (600.0 + 400.0))
        expected_rho_max = 0.75 * rho_bal
        assert r.rho_max == pytest.approx(expected_rho_max, rel=1e-5)

    def test_rho_max_lt_rho_balanced(self):
        r = design_concrete_beam(_params())
        beta1 = 0.85
        rho_bal = (0.85 * beta1 * 25.0 / 400.0) * (600.0 / 1000.0)
        assert r.rho_max < rho_bal


# ── Luas Tulangan ─────────────────────────────────────────────────────────────

class TestReinforcement:
    def test_as_design_geq_as_required(self):
        r = design_concrete_beam(_params())
        assert r.as_design_mm2 >= r.as_required_mm2

    def test_as_design_geq_as_min(self):
        r = design_concrete_beam(_params())
        assert r.as_design_mm2 >= r.as_min_mm2

    def test_num_bars_at_least_two(self):
        # Beban sangat kecil → tulangan minimum → minimal 2 batang
        r = design_concrete_beam(_params(span_l_m=2.0, dead_load_w_knm=1.0, live_load_w_knm=1.0))
        assert r.num_bars >= 2

    def test_as_design_equals_num_bars_times_bar_area(self):
        r = design_concrete_beam(_params())
        expected_area = math.pi * 19.0**2 / 4.0
        assert r.bar_area_mm2 == pytest.approx(expected_area, rel=1e-6)
        assert r.as_design_mm2 == pytest.approx(r.num_bars * r.bar_area_mm2, rel=1e-6)


# ── Kapasitas Penampang ───────────────────────────────────────────────────────

class TestCapacity:
    def test_phi_factor_is_090(self):
        r = design_concrete_beam(_params())
        assert r.phi_factor == pytest.approx(0.90)

    def test_phi_mn_positive(self):
        r = design_concrete_beam(_params())
        assert r.phi_mn_knm > 0

    def test_a_block_positive(self):
        r = design_concrete_beam(_params())
        assert r.a_block_mm > 0

    def test_phi_mn_equals_phi_times_mn(self):
        r = design_concrete_beam(_params())
        assert r.phi_mn_knm == pytest.approx(r.phi_factor * r.mn_knm, rel=1e-6)

    def test_capacity_ratio_equals_mu_over_phi_mn(self):
        r = design_concrete_beam(_params())
        assert r.capacity_ratio == pytest.approx(r.mu_ultimate_knm / r.phi_mn_knm, rel=1e-6)


# ── Status AMAN / TIDAK AMAN ─────────────────────────────────────────────────

class TestDesignStatus:
    def test_large_beam_small_load_is_aman(self):
        r = design_concrete_beam(_params(
            width_b_mm=400, height_h_mm=700,
            span_l_m=4.0, dead_load_w_knm=10.0, live_load_w_knm=8.0,
        ))
        assert r.status == DesignStatus.AMAN
        assert r.capacity_ratio <= 1.0

    def test_small_beam_heavy_load_is_tidak_aman(self):
        r = design_concrete_beam(_params(
            width_b_mm=150, height_h_mm=250,
            fc_prime_mpa=20.0,
            span_l_m=8.0, dead_load_w_knm=30.0, live_load_w_knm=25.0,
        ))
        assert r.status == DesignStatus.TIDAK_AMAN
        assert r.capacity_ratio > 1.0

    def test_status_aman_iff_capacity_ratio_le_1(self):
        r = design_concrete_beam(_params())
        if r.status == DesignStatus.AMAN:
            assert r.capacity_ratio <= 1.0
        else:
            assert r.capacity_ratio > 1.0


# ── Metadata ──────────────────────────────────────────────────────────────────

class TestMetadata:
    def test_sni_references_present(self):
        r = design_concrete_beam(_params())
        assert "SNI 2847:2019" in r.meta.standard_references
        assert "SNI 1727:2020" in r.meta.standard_references

    def test_formula_version(self):
        r = design_concrete_beam(_params())
        assert r.meta.formula_version == "1.1.0"

    def test_disclaimer_present(self):
        r = design_concrete_beam(_params())
        assert len(r.meta.disclaimer) > 20

    def test_assumptions_present(self):
        r = design_concrete_beam(_params())
        assert "simply supported" in r.meta.assumptions.lower()
