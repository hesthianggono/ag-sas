"""
Benchmark SSB-UDL-01: Simply Supported Beam — Uniformly Distributed Load

Solusi analitik eksak (Euler-Bernoulli, linear elastic):

  Defleksi tengah bentang:  δ_max = 5wL⁴ / (384 EI)
  Momen maksimum (tengah):  M_max = wL² / 8
  Reaksi perletakan:        R_A = R_B = wL / 2
  Geser maksimum:           V_max = wL / 2

Referensi:
  Hibbeler, R.C. — "Structural Analysis", 10th Ed.
  Table of Beam Deflections, Appendix C, Case 2.

Parameter yang digunakan:
  L = 6.0 m
  w = 20.0 kN/m (beban merata)
  E = 200 000 MPa = 200 000 000 kN/m²  (baja)
  I = 237 000 000 mm⁴ = 2.370 × 10⁻⁴ m⁴  (WF 400×200×8×13)
"""

import math
from app.verification.models import (
    BenchmarkCase, ExpectedValue, StructureType, VerificationLevel,
)

# ── Parameter ─────────────────────────────────────────────────────────────────

L_m   = 6.0                       # bentang [m]
w_kNm = 20.0                      # beban merata [kN/m]
E_kNm2 = 200_000.0 * 1_000.0     # 200 000 MPa → kN/m²
I_m4  = 237_000_000e-12           # mm⁴ → m⁴

EI = E_kNm2 * I_m4               # kN·m²

# ── Solusi analitik ───────────────────────────────────────────────────────────

_delta_max_m   = 5 * w_kNm * L_m**4 / (384 * EI)    # [m]
_delta_max_mm  = _delta_max_m * 1000                  # [mm]
_M_max_kNm     = w_kNm * L_m**2 / 8                  # [kN·m]
_R_A_kN        = w_kNm * L_m / 2                     # [kN]
_V_max_kN      = w_kNm * L_m / 2                     # [kN]

# ── Benchmark Definition ──────────────────────────────────────────────────────

BENCHMARK = BenchmarkCase(
    benchmark_id="ssb_udl_01",
    title="Simply Supported Beam — Uniformly Distributed Load",
    description=(
        f"Balok sederhana bentang L={L_m} m dengan beban merata w={w_kNm} kN/m. "
        f"Profil WF 400×200×8×13 (I={I_m4*1e12:.0f}×10⁻¹² m⁴), material baja E=200 GPa. "
        "Solusi analitik Euler-Bernoulli."
    ),
    structure_type=StructureType.BEAM_2D,
    level=VerificationLevel.L1_ANALYTICAL,
    source_reference=(
        "Hibbeler R.C. — Structural Analysis 10th Ed., App. C Case 2. "
        "δ_max = 5wL⁴/384EI, M_max = wL²/8"
    ),
    input_data={
        "L_m": L_m,
        "w_kN_m": w_kNm,
        "E_kN_m2": E_kNm2,
        "I_m4": I_m4,
        "support_A": "pinned",
        "support_B": "roller",
    },
    expected_values=[
        ExpectedValue(
            quantity="midspan_deflection_mm",
            value=_delta_max_mm,
            unit="mm",
            tolerance_rel=0.001,
            notes="δ = 5wL⁴/384EI",
        ),
        ExpectedValue(
            quantity="max_moment_kNm",
            value=_M_max_kNm,
            unit="kN·m",
            tolerance_rel=0.001,
            notes="M_max = wL²/8 di tengah bentang",
        ),
        ExpectedValue(
            quantity="reaction_A_kN",
            value=_R_A_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="R_A = wL/2 (simetris)",
        ),
        ExpectedValue(
            quantity="reaction_B_kN",
            value=_R_A_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="R_B = wL/2 (simetris)",
        ),
        ExpectedValue(
            quantity="max_shear_kN",
            value=_V_max_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="V_max = wL/2 di perletakan",
        ),
    ],
    tags=["beam", "simply_supported", "udl", "deflection", "analytical"],
)


def analytical_solution(L: float, w: float, E: float, I: float) -> dict:
    """
    Hitung solusi analitik untuk balok sederhana dengan UDL.

    Args:
        L: Bentang [m]
        w: Beban merata [kN/m]
        E: Modulus elastis [kN/m²]
        I: Momen inersia [m⁴]

    Returns:
        Dict berisi semua nilai yang relevan.
    """
    EI = E * I
    delta_m  = 5 * w * L**4 / (384 * EI)
    M_max    = w * L**2 / 8
    R        = w * L / 2

    return {
        "midspan_deflection_mm": delta_m * 1000,
        "max_moment_kNm":        M_max,
        "reaction_A_kN":         R,
        "reaction_B_kN":         R,
        "max_shear_kN":          R,
    }
