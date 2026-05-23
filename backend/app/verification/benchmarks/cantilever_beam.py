"""
Benchmark CANT-PL-01: Cantilever Beam — Point Load at Free End

Solusi analitik eksak (Euler-Bernoulli, linear elastic):

  Defleksi ujung bebas:   δ_tip = PL³ / (3EI)
  Rotasi ujung bebas:     θ_tip = PL² / (2EI)   [rad]
  Momen maksimum:         M_max = P·L  (di perletakan jepit)
  Geser maksimum:         V_max = P    (konstan sepanjang batang)
  Reaksi vertikal:        R_y   = P    (ke atas)
  Reaksi momen:           M_fix = P·L  (berlawanan dengan beban)

Referensi:
  Hibbeler, R.C. — "Structural Analysis", 10th Ed.
  Table of Beam Deflections, Appendix C, Case 6.

Parameter yang digunakan:
  L = 4.0 m
  P = 50.0 kN (beban titik ke bawah di ujung bebas)
  E = 200 000 MPa = 200 000 000 kN/m²  (baja)
  I = 237 000 000 mm⁴ = 2.370 × 10⁻⁴ m⁴  (WF 400×200×8×13)
"""

from app.verification.models import (
    BenchmarkCase, ExpectedValue, StructureType, VerificationLevel,
)

# ── Parameter ─────────────────────────────────────────────────────────────────

L_m    = 4.0
P_kN   = 50.0
E_kNm2 = 200_000.0 * 1_000.0
I_m4   = 237_000_000e-12

EI = E_kNm2 * I_m4

# ── Solusi analitik ───────────────────────────────────────────────────────────

_delta_tip_m   = P_kN * L_m**3 / (3 * EI)
_delta_tip_mm  = _delta_tip_m * 1000
_theta_tip_rad = P_kN * L_m**2 / (2 * EI)
_M_fix_kNm     = P_kN * L_m                   # momen jepit (positif hogging)
_V_max_kN      = P_kN

# ── Benchmark Definition ──────────────────────────────────────────────────────

BENCHMARK = BenchmarkCase(
    benchmark_id="cant_pl_01",
    title="Cantilever Beam — Point Load at Free End",
    description=(
        f"Balok kantilever panjang L={L_m} m dengan beban titik P={P_kN} kN "
        f"di ujung bebas. WF 400×200×8×13, baja E=200 GPa. "
        "Solusi analitik Euler-Bernoulli."
    ),
    structure_type=StructureType.BEAM_2D,
    level=VerificationLevel.L1_ANALYTICAL,
    source_reference=(
        "Hibbeler R.C. — Structural Analysis 10th Ed., App. C Case 6. "
        "δ_tip = PL³/3EI, θ_tip = PL²/2EI"
    ),
    input_data={
        "L_m": L_m,
        "P_kN": P_kN,
        "E_kN_m2": E_kNm2,
        "I_m4": I_m4,
        "support_A": "fixed",   # ujung kiri = jepit
        "load_position": "free_end",
    },
    expected_values=[
        ExpectedValue(
            quantity="tip_deflection_mm",
            value=_delta_tip_mm,
            unit="mm",
            tolerance_rel=0.001,
            notes="δ_tip = PL³/3EI (ke bawah, positif untuk display)",
        ),
        ExpectedValue(
            quantity="tip_rotation_rad",
            value=_theta_tip_rad,
            unit="rad",
            tolerance_rel=0.001,
            notes="θ_tip = PL²/2EI (rotasi ujung bebas)",
        ),
        ExpectedValue(
            quantity="fixed_end_moment_kNm",
            value=_M_fix_kNm,
            unit="kN·m",
            tolerance_rel=0.001,
            notes="M_fix = PL (momen reaksi di perletakan jepit)",
        ),
        ExpectedValue(
            quantity="max_shear_kN",
            value=_V_max_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="V = P konstan sepanjang batang",
        ),
        ExpectedValue(
            quantity="reaction_vertical_kN",
            value=_V_max_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="R_y = P (ke atas)",
        ),
    ],
    tags=["beam", "cantilever", "point_load", "deflection", "analytical"],
)


def analytical_solution(L: float, P: float, E: float, I: float) -> dict:
    """
    Hitung solusi analitik untuk kantilever dengan beban titik di ujung bebas.

    Args:
        L: Panjang [m]
        P: Beban titik [kN]
        E: Modulus elastis [kN/m²]
        I: Momen inersia [m⁴]

    Returns:
        Dict berisi semua nilai yang relevan.
    """
    EI = E * I
    delta_tip_m   = P * L**3 / (3 * EI)
    theta_tip_rad = P * L**2 / (2 * EI)
    M_fix         = P * L

    return {
        "tip_deflection_mm":      delta_tip_m * 1000,
        "tip_rotation_rad":       theta_tip_rad,
        "fixed_end_moment_kNm":   M_fix,
        "max_shear_kN":           P,
        "reaction_vertical_kN":   P,
    }
