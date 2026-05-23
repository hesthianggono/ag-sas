"""
Benchmark TRUSS-2D-01: Simple 2D Truss — Warren Truss, Single Point Load

Struktur: Warren truss 3-panel, 4-node, 5-batang, satu beban vertikal di tengah.

Geometri:
         2
        /|
       / |
      /  |
     1---3---4
     P       P/2+P/2
     (jepit) (rol)

Lebih tepatnya:

    Node 1: (0, 0) — sendi (pin)
    Node 2: (2, 2) — bebas
    Node 3: (4, 0) — bebas
    Node 4: (4, 0) ...

Gunakan truss Warren standar yang lebih representatif:

    Node layout (in m):
      N1 (0,0) pin
      N2 (2,2) free
      N3 (4,0) free
      N4 (4,0) roller → harus beda titik

Truss yang digunakan: Howe Truss 2-panel sederhana

    N1 (0,0) pin --- N3 (4,0) roller
    |              |
    N2 (0,2)       N4 (4,2)
    diagonal dari N1-N4 atau N2-N3

Truss SEDERHANA yang deterministik:

    N3 (2, 2)
    /         \\
   /           \\
  N1 (0, 0) - N2 (4, 0)
  (pin)        (roller)
  P↓ at N3

Ini adalah SIMPLE TRUSS 3-MEMBER:
  Member 1: N1-N3  (kiri atas)
  Member 2: N3-N2  (kanan atas)
  Member 3: N1-N2  (bawah / tie rod)

  Dimensi: span = 4 m, rise = 2 m → L_diag = √(4+4) = 2√2 m
  Beban: P = 40 kN ke bawah di N3

Solusi metode joint (statics):

  Reaksi: R1_y = R2_y = P/2 = 20 kN (simetris)
          R1_x = 0  (sendi tidak ada gaya horizontal jika struktur simetris)

  Di joint N3 (beban P↓):
    θ = arctan(2/2) = 45°
    F1 sin45 + F2 sin45 = P  → (F1+F2) = P/sin45 = P√2
    F1 cos45 = F2 cos45      → F1 = F2  (simetris)
    F1 = F2 = P/(2 sin45) = P√2/2

  Di joint N1 (sendi):
    R1_y = 20 kN ↑
    F_diag(N1-N3) vertikal component = 20 kN → F_diag = 20/sin45 = 20√2
    F_tie horizontal component = F_diag cos45 = 20 → F_tie = 20 kN (tarik)

  Jadi:
    F_left  = P√2/2  = 40×√2/2 = 20√2 ≈ 28.284 kN  TEKAN (compression)
    F_right = P√2/2  = 20√2     ≈ 28.284 kN  TEKAN (compression)
    F_tie   = P/2    = 20 kN    TARIK (tension)

Referensi:
  Hibbeler, R.C. — "Structural Analysis", 10th Ed., Chapter 6.
  Method of Joints.
"""

import math
from app.verification.models import (
    BenchmarkCase, ExpectedValue, StructureType, VerificationLevel,
)

# ── Parameter ─────────────────────────────────────────────────────────────────

P_kN   = 40.0     # beban vertikal di puncak truss [kN]
span_m = 4.0      # jarak horisontal N1-N2 [m]
rise_m = 2.0      # tinggi truss N3 [m]

# ── Solusi analitik (method of joints, statics eksak) ─────────────────────────

theta_rad = math.atan2(rise_m, span_m / 2)   # sudut batang diagonal
sin_t     = math.sin(theta_rad)
cos_t     = math.cos(theta_rad)

_R_y_kN          = P_kN / 2                  # reaksi vertikal tiap tumpuan
_F_diagonal_kN   = P_kN / (2 * sin_t)        # gaya batang diagonal (tekan)
_F_tie_kN        = _F_diagonal_kN * cos_t    # gaya batang bawah (tarik)

# Panjang batang diagonal
_L_diag_m = math.sqrt((span_m/2)**2 + rise_m**2)

# ── Benchmark Definition ──────────────────────────────────────────────────────

BENCHMARK = BenchmarkCase(
    benchmark_id="truss_2d_01",
    title="Simple 2D Truss — Symmetric Triangle, Point Load at Apex",
    description=(
        f"Truss segitiga simetris 3 batang. N1(0,0) sendi, N2({span_m},0) rol, "
        f"N3({span_m/2},{rise_m}) bebas. Beban P={P_kN} kN ke bawah di N3. "
        "Solusi method of joints (statics eksak)."
    ),
    structure_type=StructureType.TRUSS_2D,
    level=VerificationLevel.L1_ANALYTICAL,
    source_reference=(
        "Hibbeler R.C. — Structural Analysis 10th Ed., Ch. 6. "
        "Method of Joints — truss segitiga simetris."
    ),
    input_data={
        "nodes": {
            "N1": {"x_m": 0.0,        "y_m": 0.0},
            "N2": {"x_m": span_m,     "y_m": 0.0},
            "N3": {"x_m": span_m/2,   "y_m": rise_m},
        },
        "members": {
            "M1": {"i": "N1", "j": "N3"},   # diagonal kiri
            "M2": {"i": "N3", "j": "N2"},   # diagonal kanan
            "M3": {"i": "N1", "j": "N2"},   # batang bawah (tie rod)
        },
        "supports": {"N1": "pin", "N2": "roller"},
        "loads": {"N3": {"Fy_kN": -P_kN}},   # negatif = ke bawah
        "span_m": span_m,
        "rise_m": rise_m,
        "P_kN": P_kN,
    },
    expected_values=[
        ExpectedValue(
            quantity="reaction_N1_y_kN",
            value=_R_y_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="R_N1_y = P/2 (simetris)",
        ),
        ExpectedValue(
            quantity="reaction_N2_y_kN",
            value=_R_y_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="R_N2_y = P/2 (simetris)",
        ),
        ExpectedValue(
            quantity="reaction_N1_x_kN",
            value=0.0,
            unit="kN",
            tolerance_abs=1e-6,
            notes="Reaksi horisontal = 0 (beban simetris, tidak ada gaya horisontal)",
        ),
        ExpectedValue(
            quantity="force_M1_kN",
            value=-_F_diagonal_kN,   # negatif = tekan (compression)
            unit="kN",
            tolerance_rel=0.001,
            notes=f"Batang diagonal kiri: tekan = -{_F_diagonal_kN:.4f} kN (F = P/2sinθ)",
        ),
        ExpectedValue(
            quantity="force_M2_kN",
            value=-_F_diagonal_kN,
            unit="kN",
            tolerance_rel=0.001,
            notes="Batang diagonal kanan: tekan (simetris dengan M1)",
        ),
        ExpectedValue(
            quantity="force_M3_kN",
            value=_F_tie_kN,          # positif = tarik (tension)
            unit="kN",
            tolerance_rel=0.001,
            notes=f"Batang bawah: tarik = {_F_tie_kN:.4f} kN (F_tie = F_diag × cosθ)",
        ),
    ],
    tags=["truss", "2d", "method_of_joints", "symmetric", "analytical"],
)


def method_of_joints(P: float, span: float, rise: float) -> dict:
    """
    Hitung gaya batang dan reaksi truss segitiga simetris.

    Args:
        P:    Beban vertikal di puncak [kN]
        span: Lebar truss [m]
        rise: Tinggi truss [m]

    Returns:
        Dict berisi reaksi dan gaya batang. Positif = tarik, negatif = tekan.
    """
    theta = math.atan2(rise, span / 2)
    sin_t = math.sin(theta)
    cos_t = math.cos(theta)

    R_y       = P / 2
    F_diag    = P / (2 * sin_t)          # tekan → negatif dalam konvensi AG-SAS
    F_tie     = F_diag * cos_t           # tarik → positif

    return {
        "reaction_N1_y_kN":   R_y,
        "reaction_N2_y_kN":   R_y,
        "reaction_N1_x_kN":   0.0,
        "force_M1_kN":        -F_diag,   # compression
        "force_M2_kN":        -F_diag,
        "force_M3_kN":         F_tie,    # tension
    }
