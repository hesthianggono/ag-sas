"""
Tests — Full Engineering Report PDF
=====================================
python -m pytest backend/tests/reporting/test_full_report.py -v
"""
import io
import pytest

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import (
    FullReportConfig, FullReportData, EngineerInfo,
)
from app.reporting.full_report.pdf_exporter import export_full_report_pdf


# ── Fixtures ──────────────────────────────────────────────────────────────────

CONCRETE_INPUT = {
    "span_m":            6.0,
    "dead_load_kn_m":    8.0,
    "live_load_kn_m":    6.0,
    "super_dead_kn_m":   2.0,
    "fc_mpa":            25.0,
    "fy_mpa":            420.0,
    "fyt_mpa":           240.0,
    "b_mm":              300.0,
    "h_mm":              500.0,
    "cover_mm":          40.0,
    "main_bar_dia_mm":   19.0,
    "main_bars":         "3D19",
}

CONCRETE_OUTPUT = {
    "wu_kn_m":     21.6,
    "Mu_kNm":      97.2,
    "Vu_kN":       64.8,
    "phi_Mn_kNm":  110.5,
    "phi_Vn_kN":   84.0,
    "As_req_mm2":  1350.0,
    "As_prov_mm2": 849.0,
    "deflection_mm": 12.5,
}

STEEL_INPUT = {
    "span_m":          8.0,
    "dead_load_kn_m":  10.0,
    "live_load_kn_m":   8.0,
    "fy_mpa":          250.0,
    "fu_mpa":          410.0,
    "profile_name":    "WF 300x150x6.5x9",
    "profile": {
        "A_mm2":   4680.0,
        "Ix_mm4":  7210e4,
        "Sx_mm3":  481e3,
        "Zx_mm3":  544e3,
        "d_mm":    300.0,
        "bf_mm":   150.0,
        "tf_mm":     9.0,
        "tw_mm":     6.5,
    },
}

STEEL_OUTPUT = {
    "wu_kn_m":     24.8,
    "Mu_kNm":      198.4,
    "Vu_kN":        99.2,
    "phi_Mn_kNm":  216.9,
    "phi_Vn_kN":   153.0,
    "deflection_mm": 22.1,
}

@pytest.fixture
def concrete_config():
    return FullReportConfig(
        project_name="Gedung Kantor A",
        project_location="Jakarta",
        report_title="Laporan Perhitungan Balok B-1",
        status="DRAFT",
        engineers=[EngineerInfo(name="Ir. Budi", position="Ahli Struktur", skk="1234")],
        show_watermark=True,
        include_figures=False,  # skip figures in tests for speed
    )

@pytest.fixture
def steel_config():
    return FullReportConfig(
        project_name="Gudang Baja",
        report_title="Laporan Balok Baja WF",
        status="FINAL",
        show_watermark=False,
        include_figures=False,
    )


# ── NumberingContext tests ─────────────────────────────────────────────────────

class TestNumberingContext:
    def test_chapter_increments_toc(self):
        ctx = NumberingContext()
        label = ctx.chapter(1, "Pendahuluan")
        assert label == "1  Pendahuluan"
        assert len(ctx.toc) == 1
        assert ctx.toc[0].number == "1"

    def test_subchapter_format(self):
        ctx = NumberingContext()
        ctx.chapter(2, "Data")
        label = ctx.subchapter("Identitas")
        assert label == "2.1  Identitas"
        assert len(ctx.toc) == 2

    def test_table_registers_to_lot(self):
        ctx = NumberingContext()
        ctx.chapter(3, "Analisis")
        label = ctx.table("Data Beban")
        assert label == "Tabel 3.1  Data Beban"
        assert len(ctx.lot) == 1
        assert ctx.lot[0].number == "Tabel 3.1"

    def test_figure_registers_to_lof(self):
        ctx = NumberingContext()
        ctx.chapter(4, "Gambar")
        label = ctx.figure("Model Struktur")
        assert label == "Gambar 4.1  Model Struktur"
        assert len(ctx.lof) == 1

    def test_equation_numbering(self):
        ctx = NumberingContext()
        ctx.chapter(5, "X")
        e1 = ctx.equation()
        e2 = ctx.equation()
        assert e1 == "(5.1)"
        assert e2 == "(5.2)"

    def test_table_resets_on_new_chapter(self):
        ctx = NumberingContext()
        ctx.chapter(1, "A")
        ctx.table("T1")
        ctx.chapter(2, "B")
        label = ctx.table("T2")
        assert label == "Tabel 2.1  T2"

    def test_appendix_letter(self):
        ctx = NumberingContext()
        a1 = ctx.appendix("Lampiran Pertama")
        a2 = ctx.appendix("Lampiran Kedua")
        assert "Lampiran A" in a1
        assert "Lampiran B" in a2

    def test_appendix_table(self):
        ctx = NumberingContext()
        ctx.appendix("X")
        label = ctx.appendix_table("Tabel Lampiran")
        assert label == "Tabel A.1  Tabel Lampiran"
        assert len(ctx.lot) == 1


# ── PDF Generation tests ──────────────────────────────────────────────────────

class TestConcreteReport:
    def test_generates_non_empty_pdf(self, concrete_config):
        data = FullReportData(
            calc_type="concrete_beam",
            calc_title="Balok B-1",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        pdf = export_full_report_pdf(config=concrete_config, data=data)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 10_000
        assert pdf[:4] == b"%PDF"

    def test_pdf_is_valid_pdf(self, concrete_config):
        data = FullReportData(
            calc_type="concrete_beam",
            calc_title="Balok B-1",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
        )
        pdf = export_full_report_pdf(config=concrete_config, data=data)
        # Valid PDF ends with %%EOF
        assert b"%%EOF" in pdf[-20:]

    def test_shortcut_params(self):
        pdf = export_full_report_pdf(
            calc_type="concrete_beam",
            input_data=CONCRETE_INPUT,
            output_data=CONCRETE_OUTPUT,
            calc_title="Test Balok",
            project_name="Test Project",
            status="DRAFT",
            include_figures=False,
        )
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 5_000


class TestSteelReport:
    def test_generates_non_empty_pdf(self, steel_config):
        data = FullReportData(
            calc_type="steel_beam",
            calc_title="Balok WF",
            input_data=STEEL_INPUT,
            output_data=STEEL_OUTPUT,
        )
        pdf = export_full_report_pdf(config=steel_config, data=data)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 10_000


class TestReportConfig:
    def test_draft_watermark_flag(self, concrete_config):
        assert concrete_config.show_watermark is True
        assert concrete_config.status == "DRAFT"

    def test_final_no_watermark(self, steel_config):
        assert steel_config.show_watermark is False
        assert steel_config.status == "FINAL"

    def test_engineers_list(self, concrete_config):
        assert len(concrete_config.engineers) == 1
        eng = concrete_config.engineers[0]
        assert eng.name == "Ir. Budi"
        assert eng.skk == "1234"


class TestEmptyData:
    def test_empty_output_does_not_crash(self):
        """Laporan harus tetap terbuat meski output kosong."""
        pdf = export_full_report_pdf(
            calc_type="concrete_beam",
            input_data={"span_m": 5.0, "b_mm": 250.0, "h_mm": 450.0,
                        "fc_mpa": 25.0, "fy_mpa": 420.0},
            output_data={},
            include_figures=False,
        )
        assert pdf[:4] == b"%PDF"
