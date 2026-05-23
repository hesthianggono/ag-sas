"""
Kombinasi Pembebanan
Referensi: SNI 1727:2020 Pasal 5.3 — Kombinasi beban LRFD

Formula Version: 1.0.0
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class LoadCombinationResult:
    uls_governing: float    # Kombinasi terfaktor paling kritis (kN/m atau kN/m²)
    uls_combo_id: str       # e.g. "1.2D + 1.6L"
    all_combinations: dict  # Semua nilai kombinasi


def compute_load_combinations(
    dead: float = 0.0,     # D — beban mati
    live: float = 0.0,     # L — beban hidup
    roof_live: float = 0.0, # Lr — beban hidup atap
    snow: float = 0.0,      # S — beban salju
    wind: float = 0.0,      # W — beban angin (positif)
    seismic: float = 0.0,   # E — beban gempa
) -> LoadCombinationResult:
    """
    Hitung kombinasi beban LRFD sesuai SNI 1727:2020 Tabel 5.3-1.
    Input dalam satuan yang sama (kN/m, kN/m², atau kN).
    """
    combos = {
        "1.4D":                      1.4 * dead,
        "1.2D + 1.6L + 0.5Lr":      1.2 * dead + 1.6 * live + 0.5 * roof_live,
        "1.2D + 1.6Lr + L":         1.2 * dead + 1.6 * roof_live + live,
        "1.2D + 1.6Lr + 0.5W":      1.2 * dead + 1.6 * roof_live + 0.5 * wind,
        "1.2D + 1.0W + L + 0.5Lr":  1.2 * dead + 1.0 * wind + live + 0.5 * roof_live,
        "0.9D + 1.0W":               0.9 * dead + 1.0 * wind,
        "1.2D + 1.0E + L":          1.2 * dead + 1.0 * seismic + live,
        "0.9D + 1.0E":              0.9 * dead + 1.0 * seismic,
    }
    governing_combo = max(combos, key=lambda k: combos[k])
    return LoadCombinationResult(
        uls_governing=combos[governing_combo],
        uls_combo_id=governing_combo,
        all_combinations=combos,
    )
