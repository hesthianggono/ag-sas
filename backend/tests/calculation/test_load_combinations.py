"""Unit tests untuk kombinasi beban SNI 1727:2020."""
import pytest
from app.calculation.loads.combinations import compute_load_combinations


class TestLoadCombinations:
    def test_dead_only(self):
        r = compute_load_combinations(dead=10.0)
        assert r.uls_governing == pytest.approx(14.0)  # 1.4D
        assert r.uls_combo_id == "1.4D"

    def test_dead_and_live(self):
        r = compute_load_combinations(dead=20.0, live=15.0)
        # 1.2D + 1.6L = 24 + 24 = 48
        assert r.all_combinations["1.2D + 1.6L + 0.5Lr"] == pytest.approx(48.0)

    def test_governing_combination(self):
        r = compute_load_combinations(dead=10.0, live=5.0)
        assert r.uls_governing >= 1.4 * 10.0

    def test_all_combinations_present(self):
        r = compute_load_combinations(dead=10.0, live=5.0, wind=3.0, seismic=4.0)
        assert "1.2D + 1.0E + L" in r.all_combinations
        assert "0.9D + 1.0W" in r.all_combinations
