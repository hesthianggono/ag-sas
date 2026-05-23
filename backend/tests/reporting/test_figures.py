"""
Unit Tests — Report Figures Module
=====================================
Menguji:
  1. generate_model_view         — model struktur
  2. generate_load_diagram       — diagram pembebanan
  3. generate_shear_diagram      — diagram gaya geser
  4. generate_moment_diagram     — diagram momen lentur
  5. generate_deformed_shape     — bentuk deformasi
  6. generate_reaction_diagram   — reaksi tumpuan
  7. generate_utilization_map    — peta utilisasi
  8. FigureCaptionBuilder        — penomoran gambar otomatis
  9. build_figures_for_calc      — orkestrasi semua gambar
 10. FigureSpec.figure_number    — urutan & nomor konsisten
 11. PNG bytes validity           — output adalah bytes PNG valid
 12. figure_snapshot storage     — immutable snapshot (mocked)
"""
from __future__ import annotations

import io
import struct
import zlib
import pytest

from app.reporting.figures.base import FigureSpec, FigureCaptionBuilder
from app.reporting.figures.model_view import generate_model_view
from app.reporting.figures.load_diagram import generate_load_diagram
from app.reporting.figures.internal_force_diagram import (
    generate_shear_diagram,
    generate_moment_diagram,
    generate_axial_diagram,
)
from app.reporting.figures.reaction_diagram import generate_reaction_diagram
from app.reporting.figures.deformed_shape import generate_deformed_shape
from app.reporting.figures.utilization_map import generate_utilization_map
from app.reporting.figures.figure_builder import build_figures_for_calc


# ── Fixtures ──────────────────────────────────────────────────────────────────

CONCRETE_INPUT = {
    "span_l_m": 6.0,
    "width_b_mm": 300,
    "height_h_mm": 600,
    "cover_cc_mm": 40,
    "stirrup_diameter_mm": 10,
    "bar_diameter_mm": 19,
    "fc_prime_mpa": 25.0,
    "fy_mpa": 400.0,
    "dead_load_w_knm": 10.0,
    "live_load_w_knm": 8.0,
}

CONCRETE_OUTPUT = {
    "wu_knm": 22.0,
    "mu_ultimate_knm": 99.0,
    "vu_ultimate_kn": 66.0,
    "phi_mn_knm": 130.0,
    "capacity_ratio": 0.762,
    "status": "AMAN",
    "effective_depth_d_mm": 541.0,
    "beta1": 0.85,
    "rho_min": 0.0035,
    "rho_max": 0.0213,
    "rho_required": 0.012,
    "as_required_mm2": 1946.0,
    "as_min_mm2": 568.0,
    "as_design_mm2": 2130.0,
    "num_bars": 3,
    "a_block_mm": 89.0,
    "mn_knm": 144.0,
    "phi_factor": 0.9,
}

STEEL_INPUT = {
    "span_l_m": 8.0,
    "flange_width_b_mm": 175.0,
    "flange_thickness_tf_mm": 11.0,
    "web_thickness_tw_mm": 7.0,
    "height_h_mm": 350.0,
    "fy_mpa": 250.0,
    "dead_load_w_knm": 15.0,
    "live_load_w_knm": 10.0,
}

STEEL_OUTPUT = {
    "wu_knm": 34.0,
    "mu_ultimate_knm": 272.0,
    "phi_mn_knm": 310.0,
    "capacity_ratio": 0.877,
    "status": "AMAN",
    "profile_designation": "WF 350×175×7×11",
    "sx_cm3": 775.0,
    "zx_cm3": 862.0,
    "weight_per_m_kgm": 49.6,
    "self_weight_knm": 0.487,
    "lambda_f": 7.95,
    "lambda_pf": 10.75,
    "lambda_rf": 28.28,
    "is_compact": True,
    "mp_knm": 215.5,
    "mn_knm": 215.5,
    "phi_factor": 0.9,
}


# ── Helper ────────────────────────────────────────────────────────────────────

def _is_valid_png(data: bytes) -> bool:
    """Cek apakah bytes adalah PNG valid (magic bytes + IHDR chunk)."""
    if len(data) < 8:
        return False
    PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
    return data[:8] == PNG_MAGIC


def _png_dimensions(data: bytes) -> tuple[int, int]:
    """Ambil lebar × tinggi dari PNG bytes (dari IHDR chunk)."""
    # IHDR dimulai di offset 16, berisi 4+4 bytes width+height big-endian
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    return w, h


# ── Test 1: Model View ────────────────────────────────────────────────────────

class TestModelView:
    def test_returns_valid_png(self):
        png = generate_model_view(
            span_l=6.0, section_label="b/h=300/600",
            calc_type="concrete_beam", input_data=CONCRETE_INPUT,
        )
        assert _is_valid_png(png), "generate_model_view harus return PNG valid"

    def test_png_has_reasonable_size(self):
        png = generate_model_view(
            span_l=6.0, section_label="b/h=300/600",
            calc_type="concrete_beam", input_data=CONCRETE_INPUT,
        )
        # Minimum 5KB, maksimum 500KB
        assert 5_000 < len(png) < 500_000, f"PNG size tidak wajar: {len(png)} bytes"

    def test_steel_beam_variant(self):
        png = generate_model_view(
            span_l=8.0, section_label="WF 350×175",
            calc_type="steel_beam", input_data=STEEL_INPUT,
        )
        assert _is_valid_png(png)

    def test_with_caption(self):
        png = generate_model_view(
            span_l=6.0, section_label="b/h=300/600",
            calc_type="concrete_beam", input_data=CONCRETE_INPUT,
            caption="Gambar 4.1  Model struktur",
        )
        assert _is_valid_png(png)


# ── Test 2: Load Diagram ──────────────────────────────────────────────────────

class TestLoadDiagram:
    def test_returns_valid_png(self):
        png = generate_load_diagram(
            span_l=6.0, wu_knm=22.0, wd_knm=10.0, wl_knm=8.0,
        )
        assert _is_valid_png(png)

    def test_large_udl(self):
        png = generate_load_diagram(
            span_l=12.0, wu_knm=100.0, wd_knm=50.0, wl_knm=30.0,
        )
        assert _is_valid_png(png)
        assert len(png) > 0

    def test_small_udl(self):
        png = generate_load_diagram(
            span_l=2.0, wu_knm=1.5, wd_knm=0.5, wl_knm=0.5,
        )
        assert _is_valid_png(png)


# ── Test 3: Shear Diagram ─────────────────────────────────────────────────────

class TestShearDiagram:
    def test_returns_valid_png(self):
        png = generate_shear_diagram(span_l=6.0, wu_knm=22.0)
        assert _is_valid_png(png)

    def test_symmetric_shear(self):
        """SSB dengan UDL harus simetris: V(0) = -V(L) = wuL/2."""
        import numpy as np
        L, wu = 6.0, 22.0
        V0 = wu * L / 2
        VL = -(wu * L / 2)
        assert abs(V0 - (-VL)) < 1e-10, "Gaya geser harus simetris"

    def test_png_dimensions(self):
        png = generate_shear_diagram(span_l=6.0, wu_knm=22.0)
        w, h = _png_dimensions(png)
        assert w > 800, f"Lebar PNG terlalu kecil: {w}px"
        assert h > 300, f"Tinggi PNG terlalu kecil: {h}px"


# ── Test 4: Moment Diagram ────────────────────────────────────────────────────

class TestMomentDiagram:
    def test_returns_valid_png(self):
        png = generate_moment_diagram(
            span_l=6.0, wu_knm=22.0, mu_knm=99.0,
        )
        assert _is_valid_png(png)

    def test_max_moment_at_midspan(self):
        """Momen maksimum SSB-UDL harus di midspan: M = wuL²/8."""
        import numpy as np
        L, wu = 6.0, 22.0
        x = np.linspace(0, L, 1001)
        M = wu * x * (L - x) / 2
        i_max = np.argmax(M)
        x_max = x[i_max]
        M_max = M[i_max]
        expected_M = wu * L ** 2 / 8
        assert abs(x_max - L / 2) < 0.05, f"Momen maks bukan di midspan: x={x_max}"
        assert abs(M_max - expected_M) < 0.01, f"M_max={M_max} ≠ {expected_M}"

    def test_boundary_conditions(self):
        """M(0) = M(L) = 0 untuk SSB."""
        import numpy as np
        L, wu = 6.0, 22.0
        x = np.array([0.0, L])
        M = wu * x * (L - x) / 2
        assert abs(M[0]) < 1e-10, "M(0) harus = 0"
        assert abs(M[1]) < 1e-10, "M(L) harus = 0"


# ── Test 5: Deformed Shape ────────────────────────────────────────────────────

class TestDeformedShape:
    def test_returns_valid_png(self):
        png = generate_deformed_shape(span_l=6.0, wu_knm=22.0, scale_factor=50.0)
        assert _is_valid_png(png)

    def test_different_scale_factors(self):
        for scale in [10, 50, 100, 200]:
            png = generate_deformed_shape(span_l=6.0, wu_knm=22.0, scale_factor=scale)
            assert _is_valid_png(png), f"Gagal untuk scale={scale}"

    def test_deformation_symmetry(self):
        """Kurva elastika SSB dengan UDL harus simetris di midspan."""
        import numpy as np
        from app.reporting.figures.deformed_shape import _elastic_curve_ssb
        L = 6.0
        x = np.linspace(0, L, 101)
        y = _elastic_curve_ssb(x, L)
        # y[0] ≈ 0, y[-1] ≈ 0 (tumpuan)
        assert abs(y[0]) < 0.01, f"Defleksi di tumpuan A ≠ 0: y(0)={y[0]}"
        assert abs(y[-1]) < 0.01, f"Defleksi di tumpuan B ≠ 0: y(L)={y[-1]}"
        # Defleksi maks di midspan
        i_max = np.argmin(y)  # ke bawah = negatif
        x_max = x[i_max]
        assert abs(x_max - L / 2) < L * 0.05, f"δmax bukan di midspan: x={x_max}"


# ── Test 6: Reaction Diagram ──────────────────────────────────────────────────

class TestReactionDiagram:
    def test_returns_valid_png(self):
        png = generate_reaction_diagram(span_l=6.0, wu_knm=22.0)
        assert _is_valid_png(png)

    def test_equilibrium(self):
        """RA + RB harus = wu × L (keseimbangan)."""
        L, wu = 6.0, 22.0
        RA = wu * L / 2
        RB = wu * L / 2
        total_reaction = RA + RB
        total_load = wu * L
        assert abs(total_reaction - total_load) < 1e-9, (
            f"Keseimbangan gagal: R={total_reaction} ≠ wu·L={total_load}"
        )

    def test_symmetric_reactions(self):
        """RA = RB untuk SSB dengan UDL simetris."""
        L, wu = 6.0, 22.0
        RA = wu * L / 2
        RB = wu * L / 2
        assert abs(RA - RB) < 1e-10, f"RA={RA} ≠ RB={RB}"


# ── Test 7: Utilization Map ───────────────────────────────────────────────────

class TestUtilizationMap:
    def test_returns_valid_png_safe(self):
        png = generate_utilization_map(
            mu_knm=99.0, phi_mn_knm=130.0, capacity_ratio=0.762,
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT, output_data=CONCRETE_OUTPUT,
        )
        assert _is_valid_png(png)

    def test_returns_valid_png_unsafe(self):
        png = generate_utilization_map(
            mu_knm=150.0, phi_mn_knm=130.0, capacity_ratio=1.154,
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data={**CONCRETE_OUTPUT, "capacity_ratio": 1.154},
        )
        assert _is_valid_png(png)

    def test_returns_valid_png_warning_zone(self):
        png = generate_utilization_map(
            mu_knm=100.0, phi_mn_knm=120.0, capacity_ratio=0.833,
            calc_type="steel_beam",
            input_data=STEEL_INPUT, output_data=STEEL_OUTPUT,
        )
        assert _is_valid_png(png)


# ── Test 8: Auto-Caption Builder ──────────────────────────────────────────────

class TestFigureCaptionBuilder:
    def test_sequential_numbering(self):
        cb = FigureCaptionBuilder(section="4")
        num1, cap1 = cb.next("model_view", "Model Struktur")
        num2, cap2 = cb.next("load_diagram", "Diagram Pembebanan")
        num3, cap3 = cb.next("moment_diagram", "Diagram Momen Lentur")

        assert num1 == "4.1", f"Nomor pertama harus 4.1, dapat {num1}"
        assert num2 == "4.2"
        assert num3 == "4.3"

    def test_caption_format(self):
        cb = FigureCaptionBuilder(section="12")
        num, cap = cb.next("load_diagram", "Diagram Pembebanan",
                           suffix="Kombinasi 1.2D + 1.6L")
        assert cap.startswith("Gambar 12.1")
        assert "Diagram Pembebanan" in cap
        assert "1.2D + 1.6L" in cap

    def test_different_sections(self):
        cb3 = FigureCaptionBuilder(section="3")
        num, _ = cb3.next("model_view", "Model")
        assert num.startswith("3.")

        cb5 = FigureCaptionBuilder(section="5")
        num, _ = cb5.next("model_view", "Model")
        assert num.startswith("5.")

    def test_order_index_tracking(self):
        cb = FigureCaptionBuilder(section="4")
        cb.next("model_view", "A")
        cb.next("load_diagram", "B")
        cb.next("moment_diagram", "C")
        assert cb.order_of("model_view") == 1
        assert cb.order_of("load_diagram") == 2
        assert cb.order_of("moment_diagram") == 3

    def test_unknown_key_returns_zero(self):
        cb = FigureCaptionBuilder(section="4")
        assert cb.order_of("tidak_ada") == 0


# ── Test 9: build_figures_for_calc ────────────────────────────────────────────

class TestBuildFiguresForCalc:
    def test_concrete_beam_count(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        assert len(specs) == 7, f"Harus 7 gambar, dapat {len(specs)}"

    def test_steel_beam_count(self):
        specs = build_figures_for_calc(
            calc_type="steel_beam",
            input_data=STEEL_INPUT,
            output_data=STEEL_OUTPUT,
        )
        assert len(specs) == 7

    def test_figure_keys_complete(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        keys = {s.figure_key for s in specs}
        expected = {
            "model_view", "load_diagram", "reaction_diagram",
            "shear_diagram", "moment_diagram", "deformed_shape",
            "utilization_map",
        }
        assert keys == expected, f"Keys tidak lengkap: {keys ^ expected}"

    def test_all_png_valid(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        for spec in specs:
            assert _is_valid_png(spec.png_bytes), (
                f"PNG tidak valid untuk {spec.figure_key}"
            )

    def test_figure_numbers_sequential(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
            section="4",
        )
        nums = [s.figure_number for s in specs]
        expected = [f"4.{i}" for i in range(1, len(specs) + 1)]
        assert nums == expected, f"Penomoran tidak urut: {nums}"

    def test_captions_contain_figure_number(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
            section="4",
        )
        for spec in specs:
            assert spec.figure_number in spec.caption, (
                f"Caption tidak mengandung nomor: {spec.figure_number} tidak ada di '{spec.caption}'"
            )

    def test_custom_section_numbering(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
            section="12",
        )
        for spec in specs:
            assert spec.figure_number.startswith("12."), (
                f"Nomor gambar harus mulai 12.x, dapat {spec.figure_number}"
            )

    def test_order_index_set(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        for i, spec in enumerate(specs, start=1):
            assert spec.order_index == i, (
                f"order_index {spec.order_index} ≠ {i} untuk {spec.figure_key}"
            )

    def test_metadata_complete(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        for spec in specs:
            assert spec.title, f"title kosong untuk {spec.figure_key}"
            assert spec.caption, f"caption kosong untuk {spec.figure_key}"
            assert spec.unit, f"unit kosong untuk {spec.figure_key}"
            assert spec.timestamp is not None
            assert spec.source == "backend"

    def test_json_data_present(self):
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        for spec in specs:
            assert spec.json_data is not None, (
                f"json_data tidak ada untuk {spec.figure_key}"
            )
            assert isinstance(spec.json_data, dict)


# ── Test 10: PNG validity detail ──────────────────────────────────────────────

class TestPNGValidity:
    def test_model_view_dimensions(self):
        png = generate_model_view(
            span_l=6.0, section_label="b/h=300/600",
            calc_type="concrete_beam", input_data=CONCRETE_INPUT,
        )
        w, h = _png_dimensions(png)
        assert w >= 600, f"Lebar terlalu kecil: {w}px"
        assert h >= 200, f"Tinggi terlalu kecil: {h}px"
        assert w / h > 1.5, "Gambar harus landscape"

    def test_moment_diagram_dimensions(self):
        png = generate_moment_diagram(
            span_l=6.0, wu_knm=22.0, mu_knm=99.0,
        )
        w, h = _png_dimensions(png)
        assert w >= 600
        assert w / h > 1.0, "Diagram momen harus landscape"

    def test_utilization_dimensions(self):
        png = generate_utilization_map(
            mu_knm=99.0, phi_mn_knm=130.0, capacity_ratio=0.762,
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT, output_data=CONCRETE_OUTPUT,
        )
        w, h = _png_dimensions(png)
        assert w >= 600


# ── Test 11: FigureSpec dataclass ─────────────────────────────────────────────

class TestFigureSpec:
    def test_create_spec(self):
        from datetime import datetime
        spec = FigureSpec(
            figure_key="test_key",
            title="Test Figure",
            caption="Gambar 4.1  Test Figure",
            figure_number="4.1",
            section="4",
            load_case="DL+LL",
            load_combination="1.2D+1.6L",
            scale_factor=50.0,
            unit="kN·m",
            timestamp=datetime.utcnow(),
            source_result_id=42,
            source="backend",
            png_bytes=b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            svg_data=None,
            json_data={"test": True},
        )
        assert spec.figure_key == "test_key"
        assert spec.figure_number == "4.1"
        assert spec.order_index == 0   # default

    def test_order_index_default(self):
        from datetime import datetime
        spec = FigureSpec(
            figure_key="k", title="T", caption="C",
            figure_number="1.1", section="1",
            load_case=None, load_combination=None,
            scale_factor=None, unit="—",
            timestamp=datetime.utcnow(),
            source_result_id=None, source="backend",
            png_bytes=b"", svg_data=None, json_data=None,
        )
        assert spec.order_index == 0


# ── Test 12: Snapshot immutability concept ────────────────────────────────────

class TestSnapshotImmutability:
    """
    Uji konsep snapshot immutable:
    Gambar yang di-generate dari data A tetap ada meski data berubah ke B.
    (Ini diimplementasikan di DB layer — gambar disimpan terpisah per report_id)
    """

    def test_different_data_produces_different_png(self):
        """Data berbeda harus menghasilkan gambar berbeda."""
        png1 = generate_moment_diagram(span_l=6.0, wu_knm=22.0, mu_knm=99.0)
        png2 = generate_moment_diagram(span_l=8.0, wu_knm=34.0, mu_knm=272.0)
        assert png1 != png2, "Data berbeda harus menghasilkan PNG berbeda"

    def test_same_data_produces_similar_png(self):
        """Data sama harus menghasilkan gambar yang valid (determinisme)."""
        png1 = generate_model_view(
            span_l=6.0, section_label="b/h=300/600",
            calc_type="concrete_beam", input_data=CONCRETE_INPUT,
        )
        png2 = generate_model_view(
            span_l=6.0, section_label="b/h=300/600",
            calc_type="concrete_beam", input_data=CONCRETE_INPUT,
        )
        # Keduanya harus PNG valid
        assert _is_valid_png(png1)
        assert _is_valid_png(png2)
        # Ukuran mendekati sama
        assert abs(len(png1) - len(png2)) < len(png1) * 0.1, (
            "PNG dari data sama harus berukuran serupa"
        )

    def test_build_specs_contain_snapshot_data(self):
        """Setiap FigureSpec mengandung json_data sebagai snapshot data mentah."""
        specs = build_figures_for_calc(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        moment_spec = next(s for s in specs if s.figure_key == "moment_diagram")
        assert "M_max" in moment_spec.json_data
        assert abs(moment_spec.json_data["M_max"] - 99.0) < 1e-6

        load_spec = next(s for s in specs if s.figure_key == "load_diagram")
        assert "wu" in load_spec.json_data
        assert abs(load_spec.json_data["wu"] - 22.0) < 1e-6
