"""
Sistem Satuan AG-SAS
====================
Modul ini mendefinisikan konstanta konversi dan tipe satuan yang digunakan
di seluruh calculation engine.

Aturan satuan internal AG-SAS:
  Gaya    : kN
  Momen   : kN·m
  Panjang : mm  (dimensi penampang)
  Panjang : m   (panjang bentang, dimensi global)
  Tegangan: MPa (= N/mm²)
  Luas    : mm²
  Momen inersia: cm⁴
  Modulus penampang: cm³
  Berat per meter: kg/m
"""

# ── Konversi gaya ─────────────────────────────────────────────────────────────
N_PER_KN: float = 1_000.0          # 1 kN = 1000 N
KN_PER_N: float = 1.0 / N_PER_KN

# ── Konversi panjang ──────────────────────────────────────────────────────────
MM_PER_M: float = 1_000.0          # 1 m = 1000 mm
M_PER_MM: float = 1.0 / MM_PER_M
CM_PER_MM: float = 0.1             # 1 mm = 0.1 cm
MM_PER_CM: float = 10.0

# ── Konversi momen dan tegangan ───────────────────────────────────────────────
NMM_PER_KNM: float = 1_000_000.0  # 1 kN·m = 1e6 N·mm
KNM_PER_NMM: float = 1.0 / NMM_PER_KNM

# ── Konversi luas penampang ───────────────────────────────────────────────────
MM2_PER_CM2: float = 100.0         # 1 cm² = 100 mm²
MM3_PER_CM3: float = 1_000.0       # 1 cm³ = 1000 mm³
MM4_PER_CM4: float = 10_000.0      # 1 cm⁴ = 10000 mm⁴

# ── Gravitasi ─────────────────────────────────────────────────────────────────
G_MS2: float = 9.81                # percepatan gravitasi (m/s²)
KN_PER_KGM: float = G_MS2 / N_PER_KN  # kg/m → kN/m : × (9.81/1000)

# ── Konstanta material ────────────────────────────────────────────────────────
E_STEEL_MPA: float = 200_000.0    # Modulus elastisitas baja (MPa)
G_STEEL_MPA: float = 77_200.0     # Modulus geser baja (MPa)


def kgm_to_knm(kg_per_m: float) -> float:
    """Konversi berat profil (kg/m) ke beban merata (kN/m)."""
    return kg_per_m * KN_PER_KGM


def knm_to_nmm(knm: float) -> float:
    """Konversi momen kN·m ke N·mm."""
    return knm * NMM_PER_KNM


def nmm_to_knm(nmm: float) -> float:
    """Konversi momen N·mm ke kN·m."""
    return nmm * KNM_PER_NMM


def cm3_to_mm3(cm3: float) -> float:
    """Konversi modulus penampang cm³ ke mm³."""
    return cm3 * MM3_PER_CM3


def cm4_to_mm4(cm4: float) -> float:
    """Konversi momen inersia cm⁴ ke mm⁴."""
    return cm4 * MM4_PER_CM4
