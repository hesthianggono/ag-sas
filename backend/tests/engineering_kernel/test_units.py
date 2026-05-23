"""
Unit test untuk sistem satuan dan fungsi konversi AG-SAS.

Prinsip pengujian:
  1. Roundtrip: konversi A→B lalu B→A harus menghasilkan nilai asal.
  2. Nilai diketahui: konversi dengan nilai yang dapat diverifikasi manual.
  3. Sifat matematika: faktor konversi harus konsisten.
"""

import math
import pytest

from app.engineering_kernel.units.converters import (
    # Panjang
    mm_to_m, m_to_mm, cm_to_m, m_to_cm, mm_to_cm, cm_to_mm,
    # Gaya
    n_to_kn, kn_to_n,
    # Momen
    nmm_to_knm, knm_to_nmm, nm_to_knm, knm_to_nm,
    # Tegangan
    mpa_to_kn_m2, kn_m2_to_mpa, kpa_to_kn_m2, kn_m2_to_kpa,
    # Massa
    kg_to_ton, ton_to_kg,
    # Kerapatan
    kg_m3_to_kn_m3, kn_m3_to_kg_m3,
    # Sudut
    deg_to_rad, rad_to_deg,
    # Luas
    mm2_to_m2, m2_to_mm2, cm2_to_m2, m2_to_cm2, mm2_to_cm2, cm2_to_mm2,
    # Inersia
    mm4_to_m4, m4_to_mm4, cm4_to_m4, m4_to_cm4, mm4_to_cm4, cm4_to_mm4,
    # Modulus penampang
    mm3_to_m3, m3_to_mm3, cm3_to_m3, m3_to_cm3, mm3_to_cm3, cm3_to_mm3,
)
from app.engineering_kernel.units.enums import (
    LengthUnit, ForceUnit, MomentUnit, StressUnit,
    MassUnit, DensityUnit, AngleUnit,
)
from app.engineering_kernel.units.quantity import Quantity

TOL = 1e-9   # toleransi floating point untuk roundtrip


# ── Panjang ───────────────────────────────────────────────────────────────────

class TestLengthConversion:
    def test_mm_to_m_known_value(self):
        assert mm_to_m(1000.0) == pytest.approx(1.0, rel=TOL)

    def test_m_to_mm_known_value(self):
        assert m_to_mm(1.0) == pytest.approx(1000.0, rel=TOL)

    def test_mm_to_m_roundtrip(self):
        for v in [0.0, 1.0, 100.0, 500.0, 1234.56]:
            assert m_to_mm(mm_to_m(v)) == pytest.approx(v, rel=TOL)

    def test_cm_to_m_known_value(self):
        assert cm_to_m(100.0) == pytest.approx(1.0, rel=TOL)

    def test_m_to_cm_roundtrip(self):
        for v in [0.0, 1.5, 6.0, 12.345]:
            assert cm_to_m(m_to_cm(v)) == pytest.approx(v, rel=TOL)

    def test_mm_to_cm_known_value(self):
        assert mm_to_cm(10.0) == pytest.approx(1.0, rel=TOL)
        assert cm_to_mm(1.0) == pytest.approx(10.0, rel=TOL)

    def test_mm_cm_m_chain(self):
        """1000 mm = 100 cm = 1 m — tiga arah harus konsisten."""
        val_mm = 1000.0
        assert cm_to_m(mm_to_cm(val_mm)) == pytest.approx(mm_to_m(val_mm), rel=TOL)

    def test_zero(self):
        assert mm_to_m(0.0) == 0.0
        assert m_to_mm(0.0) == 0.0

    def test_negative(self):
        assert mm_to_m(-500.0) == pytest.approx(-0.5, rel=TOL)


# ── Gaya ──────────────────────────────────────────────────────────────────────

class TestForceConversion:
    def test_kn_to_n_known_value(self):
        assert kn_to_n(1.0) == pytest.approx(1000.0, rel=TOL)

    def test_n_to_kn_known_value(self):
        assert n_to_kn(1000.0) == pytest.approx(1.0, rel=TOL)

    def test_roundtrip(self):
        for v in [0.0, 1.0, 50.0, 250.0, 1234.56]:
            assert n_to_kn(kn_to_n(v)) == pytest.approx(v, rel=TOL)
            assert kn_to_n(n_to_kn(v)) == pytest.approx(v, rel=TOL)

    def test_typical_structural_force(self):
        """100 kN = 100,000 N — nilai tipikal beban struktur."""
        assert kn_to_n(100.0) == pytest.approx(100_000.0, rel=TOL)

    def test_negative_force(self):
        assert kn_to_n(-50.0) == pytest.approx(-50_000.0, rel=TOL)


# ── Momen ─────────────────────────────────────────────────────────────────────

class TestMomentConversion:
    def test_knm_to_nmm_known_value(self):
        """1 kN·m = 1,000,000 N·mm."""
        assert knm_to_nmm(1.0) == pytest.approx(1_000_000.0, rel=TOL)

    def test_nmm_to_knm_known_value(self):
        assert nmm_to_knm(1_000_000.0) == pytest.approx(1.0, rel=TOL)

    def test_knm_nmm_roundtrip(self):
        for v in [0.0, 1.0, 50.0, 150.25]:
            assert nmm_to_knm(knm_to_nmm(v)) == pytest.approx(v, rel=TOL)

    def test_knm_to_nm_known_value(self):
        """1 kN·m = 1000 N·m."""
        assert knm_to_nm(1.0) == pytest.approx(1000.0, rel=TOL)

    def test_nm_to_knm_roundtrip(self):
        for v in [0.0, 10.0, 500.0]:
            assert nm_to_knm(knm_to_nm(v)) == pytest.approx(v, rel=TOL)

    def test_consistency_knm_nmm_nm(self):
        """150 kN·m = 150,000 N·m = 150,000,000 N·mm."""
        val_knm = 150.0
        assert knm_to_nm(val_knm) == pytest.approx(150_000.0, rel=TOL)
        assert knm_to_nmm(val_knm) == pytest.approx(150_000_000.0, rel=TOL)


# ── Tegangan ──────────────────────────────────────────────────────────────────

class TestStressConversion:
    def test_mpa_to_kn_m2_known_value(self):
        """1 MPa = 1000 kN/m²."""
        assert mpa_to_kn_m2(1.0) == pytest.approx(1000.0, rel=TOL)

    def test_kn_m2_to_mpa_known_value(self):
        assert kn_m2_to_mpa(1000.0) == pytest.approx(1.0, rel=TOL)

    def test_mpa_kn_m2_roundtrip(self):
        for v in [0.0, 1.0, 25.0, 200_000.0, 250.0]:
            assert kn_m2_to_mpa(mpa_to_kn_m2(v)) == pytest.approx(v, rel=TOL)

    def test_typical_steel_E(self):
        """E baja = 200,000 MPa = 200,000,000 kN/m²."""
        assert mpa_to_kn_m2(200_000.0) == pytest.approx(200_000_000.0, rel=TOL)

    def test_typical_fy_bj41(self):
        """fy BJ-41 = 250 MPa = 250,000 kN/m²."""
        assert mpa_to_kn_m2(250.0) == pytest.approx(250_000.0, rel=TOL)

    def test_kpa_equals_kn_m2(self):
        """kPa ≡ kN/m² — konversi harus sama dengan 1:1."""
        for v in [0.0, 1.0, 50.0, 100.0]:
            assert kpa_to_kn_m2(v) == pytest.approx(v, rel=TOL)
            assert kn_m2_to_kpa(v) == pytest.approx(v, rel=TOL)


# ── Massa ─────────────────────────────────────────────────────────────────────

class TestMassConversion:
    def test_ton_to_kg_known_value(self):
        assert ton_to_kg(1.0) == pytest.approx(1000.0, rel=TOL)

    def test_kg_to_ton_known_value(self):
        assert kg_to_ton(1000.0) == pytest.approx(1.0, rel=TOL)

    def test_roundtrip(self):
        for v in [0.0, 1.0, 10.5, 100.0]:
            assert kg_to_ton(ton_to_kg(v)) == pytest.approx(v, rel=TOL)


# ── Kerapatan / Berat jenis ───────────────────────────────────────────────────

class TestDensityConversion:
    def test_steel_density(self):
        """Baja: 7850 kg/m³ → ≈ 76.99 kN/m³ (γ = ρg)."""
        gamma = kg_m3_to_kn_m3(7850.0)
        assert gamma == pytest.approx(7850.0 * 9.81 / 1000.0, rel=1e-6)

    def test_concrete_density(self):
        """Beton: 2400 kg/m³ → ≈ 23.544 kN/m³."""
        gamma = kg_m3_to_kn_m3(2400.0)
        assert gamma == pytest.approx(2400.0 * 9.81 / 1000.0, rel=1e-6)

    def test_roundtrip(self):
        for v in [1.0, 1000.0, 7850.0, 2400.0]:
            assert kn_m3_to_kg_m3(kg_m3_to_kn_m3(v)) == pytest.approx(v, rel=TOL)


# ── Sudut ─────────────────────────────────────────────────────────────────────

class TestAngleConversion:
    def test_deg_to_rad_known_values(self):
        assert deg_to_rad(0.0)   == pytest.approx(0.0, abs=TOL)
        assert deg_to_rad(90.0)  == pytest.approx(math.pi / 2, rel=TOL)
        assert deg_to_rad(180.0) == pytest.approx(math.pi, rel=TOL)
        assert deg_to_rad(360.0) == pytest.approx(2 * math.pi, rel=TOL)

    def test_rad_to_deg_known_values(self):
        assert rad_to_deg(0.0)           == pytest.approx(0.0, abs=TOL)
        assert rad_to_deg(math.pi / 2)   == pytest.approx(90.0, rel=TOL)
        assert rad_to_deg(math.pi)       == pytest.approx(180.0, rel=TOL)
        assert rad_to_deg(2 * math.pi)   == pytest.approx(360.0, rel=TOL)

    def test_roundtrip(self):
        for deg in [0, 30, 45, 60, 90, 120, 180, 270, 360]:
            assert rad_to_deg(deg_to_rad(float(deg))) == pytest.approx(float(deg), rel=TOL)

    def test_negative_angle(self):
        assert deg_to_rad(-90.0) == pytest.approx(-math.pi / 2, rel=TOL)


# ── Luas ──────────────────────────────────────────────────────────────────────

class TestAreaConversion:
    def test_mm2_to_m2_known(self):
        """1 m² = 1,000,000 mm²."""
        assert mm2_to_m2(1_000_000.0) == pytest.approx(1.0, rel=TOL)

    def test_cm2_to_m2_known(self):
        """1 m² = 10,000 cm²."""
        assert cm2_to_m2(10_000.0) == pytest.approx(1.0, rel=TOL)

    def test_chain_consistency(self):
        """10,000 mm² = 100 cm² = 0.001 m²."""
        val_mm2 = 10_000.0
        val_cm2 = mm2_to_cm2(val_mm2)
        val_m2  = mm2_to_m2(val_mm2)
        assert cm2_to_m2(val_cm2) == pytest.approx(val_m2, rel=TOL)

    def test_typical_section_area(self):
        """WF 400x200: A ≈ 8412 mm² = 84.12 cm²."""
        A_mm2 = 8412.0
        assert mm2_to_cm2(A_mm2) == pytest.approx(84.12, rel=TOL)


# ── Momen inersia ─────────────────────────────────────────────────────────────

class TestMomentOfInertiaConversion:
    def test_cm4_to_m4_known(self):
        """1 m⁴ = 1e8 cm⁴."""
        assert cm4_to_m4(1e8) == pytest.approx(1.0, rel=TOL)

    def test_mm4_to_m4_known(self):
        """1 m⁴ = 1e12 mm⁴."""
        assert mm4_to_m4(1e12) == pytest.approx(1.0, rel=TOL)

    def test_roundtrip_cm4_m4(self):
        for v in [1.0, 23_700.0, 7_210.0, 100_000.0]:
            assert m4_to_cm4(cm4_to_m4(v)) == pytest.approx(v, rel=TOL)

    def test_roundtrip_mm4_cm4(self):
        for v in [1.0, 237_000_000.0, 72_100_000.0]:
            assert cm4_to_mm4(mm4_to_cm4(v)) == pytest.approx(v, rel=TOL)

    def test_typical_wf400_Ix(self):
        """WF 400x200: Ix ≈ 23,700 cm⁴ = 2.37e-4 m⁴."""
        Ix_cm4 = 23_700.0
        Ix_m4 = cm4_to_m4(Ix_cm4)
        assert Ix_m4 == pytest.approx(2.37e-4, rel=1e-4)


# ── Modulus penampang ─────────────────────────────────────────────────────────

class TestSectionModulusConversion:
    def test_cm3_to_m3_known(self):
        """1 m³ = 1e6 cm³."""
        assert cm3_to_m3(1e6) == pytest.approx(1.0, rel=TOL)

    def test_mm3_to_m3_known(self):
        """1 m³ = 1e9 mm³."""
        assert mm3_to_m3(1e9) == pytest.approx(1.0, rel=TOL)

    def test_roundtrip_cm3_m3(self):
        for v in [1.0, 1_350.0, 538.0]:
            assert m3_to_cm3(cm3_to_m3(v)) == pytest.approx(v, rel=TOL)

    def test_typical_wf400_Zx(self):
        """WF 400x200: Zx ≈ 1,350 cm³ = 1.35e-3 m³."""
        Zx_cm3 = 1_350.0
        Zx_m3 = cm3_to_m3(Zx_cm3)
        assert Zx_m3 == pytest.approx(1.35e-3, rel=1e-4)


# ── Quantity ──────────────────────────────────────────────────────────────────

class TestQuantity:
    def test_create_length_quantity(self):
        q = Quantity(6.0, LengthUnit.M)
        assert q.value == 6.0
        assert q.unit == LengthUnit.M

    def test_create_force_quantity(self):
        q = Quantity(100.0, ForceUnit.KN)
        assert q.value == 100.0
        assert q.unit == ForceUnit.KN

    def test_create_stress_quantity(self):
        q = Quantity(250.0, StressUnit.MPA)
        assert q.value == 250.0

    def test_str_representation(self):
        q = Quantity(6.0, LengthUnit.M)
        assert "6.0" in str(q)
        assert "m" in str(q)

    def test_repr(self):
        q = Quantity(100.0, ForceUnit.KN)
        assert "100.0" in repr(q)
        assert "kN" in repr(q)

    def test_is_positive(self):
        assert Quantity(10.0, ForceUnit.KN).is_positive() is True
        assert Quantity(-10.0, ForceUnit.KN).is_positive() is False

    def test_is_zero(self):
        assert Quantity(0.0, ForceUnit.KN).is_zero() is True
        assert Quantity(1e-15, ForceUnit.KN).is_zero() is True
        assert Quantity(0.1, ForceUnit.KN).is_zero() is False

    def test_is_negative(self):
        assert Quantity(-5.0, MomentUnit.KN_M).is_negative() is True
        assert Quantity(5.0, MomentUnit.KN_M).is_negative() is False

    def test_frozen(self):
        """Quantity harus immutable (frozen dataclass)."""
        q = Quantity(6.0, LengthUnit.M)
        with pytest.raises(Exception):
            q.value = 7.0  # type: ignore

    def test_string_unit_fallback(self):
        """Quantity harus dapat menerima string sebagai unit."""
        q = Quantity(100.0, "kN/m²")
        assert q.unit == "kN/m²"

    def test_zero_value(self):
        q = Quantity(0.0, LengthUnit.M)
        assert q.value == 0.0
        assert q.is_zero() is True

    def test_equality(self):
        q1 = Quantity(6.0, LengthUnit.M)
        q2 = Quantity(6.0, LengthUnit.M)
        assert q1 == q2

    def test_inequality_different_unit(self):
        q1 = Quantity(6.0, LengthUnit.M)
        q2 = Quantity(6.0, LengthUnit.MM)
        assert q1 != q2
