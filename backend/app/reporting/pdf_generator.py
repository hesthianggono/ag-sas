"""
PDF Report Generator — AG-SAS
================================
Generate laporan perhitungan 12 seksi dalam format PDF menggunakan ReportLab.
Laporan diformat sesuai konvensi laporan konsultan struktur Indonesia.

Format Version: 2.0.0
"""
from __future__ import annotations
import io
import os
import math
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image as RLImage,
)

# ── Unicode Font Registration ──────────────────────────────────────────────────
# Arial (Windows built-in) mendukung Unicode penuh: Greek (β ρ φ λ), math (√ → ≤ ≥ ×)
# Consolas = monospace Unicode untuk blok formula

def _setup_unicode_fonts() -> tuple[str, str, str, str, str]:
    """Daftarkan font TTF Unicode. Return (regular, bold, italic, mono, mono_bold)."""
    _DIR = r"C:\Windows\Fonts"
    _SPECS = [
        ("_ArialU",     "arial.ttf"),
        ("_ArialU-B",   "arialbd.ttf"),
        ("_ArialU-I",   "ariali.ttf"),
        ("_ArialU-BI",  "arialbi.ttf"),
        ("_ConsolasU",  "consola.ttf"),
        ("_ConsolasU-B","consolab.ttf"),
    ]
    loaded: set[str] = set()
    for name, fname in _SPECS:
        path = os.path.join(_DIR, fname)
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                loaded.add(name)
            except Exception:
                pass

    if "_ArialU" in loaded and "_ArialU-B" in loaded:
        addMapping("_ArialU", 0, 0, "_ArialU")
        addMapping("_ArialU", 1, 0, "_ArialU-B")
        if "_ArialU-I"  in loaded: addMapping("_ArialU", 0, 1, "_ArialU-I")
        if "_ArialU-BI" in loaded: addMapping("_ArialU", 1, 1, "_ArialU-BI")
        reg   = "_ArialU"
        bold  = "_ArialU-B"
        italic= "_ArialU-I"  if "_ArialU-I"   in loaded else "_ArialU"
        mono  = "_ConsolasU" if "_ConsolasU"  in loaded else "_ArialU"
        mono_b= "_ConsolasU-B" if "_ConsolasU-B" in loaded else "_ArialU-B"
        return reg, bold, italic, mono, mono_b
    else:
        # Fallback ke Helvetica (tanpa Unicode — kotak hitam untuk simbol Yunani)
        return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Courier", "Courier-Bold"

_FREG, _FBOLD, _FITAL, _FMONO, _FMONO_B = _setup_unicode_fonts()

# ── Color Palette ─────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#1e3a5f")
BLUE       = colors.HexColor("#2563eb")
STEEL_GRAY = colors.HexColor("#475569")
LIGHT      = colors.HexColor("#f1f5f9")
MID_GRAY   = colors.HexColor("#94a3b8")
BORDER     = colors.HexColor("#cbd5e1")
GREEN      = colors.HexColor("#16a34a")
GREEN_BG   = colors.HexColor("#f0fdf4")
RED        = colors.HexColor("#dc2626")
RED_BG     = colors.HexColor("#fef2f2")
ORANGE     = colors.HexColor("#ea580c")
AMBER_BG   = colors.HexColor("#fff7ed")
AMBER      = colors.HexColor("#9a3412")
WHITE      = colors.white
BLACK      = colors.black


def _styles():
    base = getSampleStyleSheet()
    s = {}
    s["cover_title"]    = ParagraphStyle("cover_title",    parent=base["Title"],
        fontSize=20, textColor=WHITE, alignment=TA_CENTER, spaceAfter=6, fontName=_FBOLD)
    s["cover_subtitle"] = ParagraphStyle("cover_subtitle", parent=base["Normal"],
        fontSize=10, textColor=WHITE, alignment=TA_CENTER, fontName=_FREG)
    s["cover_meta"]     = ParagraphStyle("cover_meta",     parent=base["Normal"],
        fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER, fontName=_FREG)
    s["section_num"]    = ParagraphStyle("section_num",    parent=base["Normal"],
        fontSize=8, textColor=WHITE, fontName=_FBOLD)
    s["section_title"]  = ParagraphStyle("section_title",  parent=base["Heading1"],
        fontSize=11, textColor=NAVY, fontName=_FBOLD, spaceBefore=2, spaceAfter=6)
    s["subsection"]     = ParagraphStyle("subsection",     parent=base["Heading2"],
        fontSize=9, textColor=NAVY, fontName=_FBOLD, spaceBefore=6, spaceAfter=4)
    s["body"]           = ParagraphStyle("body",           parent=base["Normal"],
        fontSize=8.5, fontName=_FREG, spaceAfter=3, leading=13)
    s["body_bold"]      = ParagraphStyle("body_bold",      parent=base["Normal"],
        fontSize=8.5, fontName=_FBOLD, spaceAfter=3)
    s["formula"]        = ParagraphStyle("formula",        parent=base["Code"],
        fontSize=8, fontName=_FMONO, textColor=NAVY,
        backColor=LIGHT, borderPad=5, spaceBefore=2, spaceAfter=2, leading=13)
    s["formula_result"] = ParagraphStyle("formula_result", parent=base["Code"],
        fontSize=8.5, fontName=_FMONO_B, textColor=NAVY,
        backColor=LIGHT, borderPad=5, spaceAfter=4)
    s["status_safe"]    = ParagraphStyle("status_safe",    parent=base["Normal"],
        fontSize=13, fontName=_FBOLD, textColor=GREEN, alignment=TA_CENTER)
    s["status_unsafe"]  = ParagraphStyle("status_unsafe",  parent=base["Normal"],
        fontSize=13, fontName=_FBOLD, textColor=RED, alignment=TA_CENTER)
    s["disclaimer"]     = ParagraphStyle("disclaimer",     parent=base["Normal"],
        fontSize=8, fontName=_FITAL, textColor=AMBER,
        borderColor=ORANGE, borderWidth=0.5, borderPad=6, spaceAfter=4, leading=13)
    s["small"]          = ParagraphStyle("small",          parent=base["Normal"],
        fontSize=7.5, fontName=_FREG, textColor=MID_GRAY)
    s["table_header"]   = ParagraphStyle("table_header",   parent=base["Normal"],
        fontSize=8, fontName=_FBOLD, textColor=WHITE)
    s["cell"]           = ParagraphStyle("cell",           parent=base["Normal"],
        fontSize=8, fontName=_FREG, leading=11)
    s["cell_bold"]      = ParagraphStyle("cell_bold",      parent=base["Normal"],
        fontSize=8, fontName=_FBOLD, leading=11)
    s["cell_mono"]      = ParagraphStyle("cell_mono",      parent=base["Normal"],
        fontSize=7.5, fontName=_FMONO, textColor=NAVY, leading=11)
    return s


# ── Page template ─────────────────────────────────────────────────────────────

_report_meta: dict = {}   # populated before build

def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Header
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 1.4*cm, w, 1.4*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(_FBOLD, 8)
    canvas.drawString(2.5*cm, h - 0.9*cm, "AG Structural Analysis Suite")
    canvas.setFont(_FREG, 7.5)
    title = _report_meta.get("title", "")
    canvas.drawCentredString(w/2, h - 0.9*cm, title[:80])
    canvas.drawRightString(w - 2*cm, h - 0.9*cm,
                           f"Dicetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    # Footer
    canvas.setFillColor(LIGHT)
    canvas.rect(0, 0, w, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(MID_GRAY)
    canvas.setFont(_FITAL, 6.5)
    canvas.drawString(2.5*cm, 0.4*cm,
                      "DISCLAIMER: Hasil ini bersifat indikatif. Wajib diperiksa Engineer Struktur berwenang.")
    canvas.setFont(_FREG, 7.5)
    canvas.drawRightString(w - 2*cm, 0.4*cm, f"Halaman {doc.page}")
    canvas.restoreState()


# ── Table helpers ─────────────────────────────────────────────────────────────

_TS_BASE = [
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ("GRID",          (0,0), (-1,-1), 0.4, BORDER),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
]

def _tbl_data_style(header_color=NAVY):
    return TableStyle(_TS_BASE + [
        ("BACKGROUND",   (0,0), (-1,0), header_color),
        ("TEXTCOLOR",    (0,0), (-1,0), WHITE),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
    ])

def _two_col_table(rows: list[tuple], s, col_widths=None):
    """Tabel 2 kolom: label | nilai."""
    cw = col_widths or [5.5*cm, 10*cm]
    data = [[Paragraph(str(r[0]), s["cell_bold"]), Paragraph(str(r[1]), s["cell"])] for r in rows]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle(_TS_BASE + [("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, LIGHT])]))
    return t

def _data_table(headers: list[str], rows: list[list], s, col_widths=None, header_color=NAVY):
    """Tabel dengan header row dan data rows."""
    hdr = [Paragraph(h, s["table_header"]) for h in headers]
    data = [hdr]
    for row in rows:
        data.append([Paragraph(str(c), s["cell"]) for c in row])
    t = Table(data, colWidths=col_widths)
    t.setStyle(_tbl_data_style(header_color))
    return t

def _fmt(val, decimals=2):
    if isinstance(val, float):
        return f"{val:.{decimals}f}"
    return str(val) if val is not None else "—"


# ── Section header builder ─────────────────────────────────────────────────────

def _section(num: str, title: str, s) -> list:
    num_tbl = Table([[Paragraph(num, s["section_num"])]], colWidths=[1*cm])
    num_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
    ]))
    hdr_row = Table([[num_tbl, Paragraph(title, s["section_title"])]], colWidths=[1.2*cm, 14.8*cm])
    hdr_row.setStyle(TableStyle([
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",    (0,0), (-1,-1), 0),
        ("RIGHTPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 4),
        ("LINEBELOW",      (0,0), (-1,0),  1.5, NAVY),
    ]))
    return [hdr_row]


# ── Report assembly ────────────────────────────────────────────────────────────

def generate_calculation_report(
    project_data: dict,
    calc_type: str,
    input_data: dict,
    output_data: dict,
    calc_title: str,
    standard_references: str,
    generated_by: str = "AG-SAS",
    engineer_data: dict | None = None,
    figure_snapshots: list | None = None,
) -> bytes:
    """
    Generate PDF laporan perhitungan 12-seksi + Seksi 12 Gambar Teknik.

    Parameters
    ----------
    figure_snapshots : list[FigureSnapshot] opsional — gambar yang sudah tersimpan di DB.
                       Jika None, gambar di-generate on-the-fly dari data input/output.

    Returns: bytes (PDF content)
    """
    global _report_meta
    _report_meta = {"title": calc_title}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=1.8*cm, bottomMargin=1.8*cm,
                            leftMargin=2.5*cm, rightMargin=2*cm)
    s = _styles()
    story = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    story += _build_cover(project_data, calc_title, calc_type, generated_by, s)
    story.append(PageBreak())

    # ── SECTION 1: IDENTITAS PROYEK ───────────────────────────────────────────
    story += _section("1", "IDENTITAS PROYEK", s)
    story.append(_build_project_table(project_data, calc_title, generated_by, s))
    story.append(Spacer(1, 10))

    # ── SECTION 2: STANDAR DAN PERATURAN DESAIN ───────────────────────────────
    story += _section("2", "STANDAR DAN PERATURAN DESAIN", s)
    story += _build_standards_section(standard_references, s)
    story.append(Spacer(1, 10))

    # ── SECTION 3: DATA MATERIAL ──────────────────────────────────────────────
    story += _section("3", "DATA MATERIAL", s)
    story += _build_material_section(input_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 4: DATA GEOMETRI ELEMEN ──────────────────────────────────────
    story += _section("4", "DATA GEOMETRI ELEMEN", s)
    story += _build_geometry_section(input_data, output_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 5: DATA PEMBEBANAN ────────────────────────────────────────────
    story += _section("5", "DATA PEMBEBANAN", s)
    story += _build_loading_section(input_data, output_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 6: KOMBINASI PEMBEBANAN ──────────────────────────────────────
    story += _section("6", "KOMBINASI PEMBEBANAN", s)
    story += _build_combination_section(input_data, output_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 7: GAYA DALAM SEDERHANA ──────────────────────────────────────
    story += _section("7", "PERHITUNGAN GAYA DALAM SEDERHANA", s)
    story += _build_forces_section(input_data, output_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 8: KAPASITAS ELEMEN ───────────────────────────────────────────
    story += _section("8", "PERHITUNGAN KAPASITAS ELEMEN", s)
    story += _build_capacity_section(input_data, output_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 9: RINGKASAN HASIL ────────────────────────────────────────────
    story += _section("9", "TABEL RINGKASAN HASIL", s)
    story += _build_summary_section(input_data, output_data, calc_type, s)
    story.append(Spacer(1, 10))

    # ── SECTION 10: KESIMPULAN ────────────────────────────────────────────────
    story += _section("10", "KESIMPULAN", s)
    story += _build_conclusion_section(output_data, s)
    story.append(Spacer(1, 10))

    # ── SECTION 11: CATATAN & DISCLAIMER ─────────────────────────────────────
    story += _section("11", "CATATAN DAN DISCLAIMER ENGINEER REVIEW", s)
    story += _build_disclaimer_section(calc_type, generated_by,
                                        output_data.get("meta", {}), s,
                                        engineer_data=engineer_data or {})
    story.append(PageBreak())

    # ── SECTION 12: GAMBAR TEKNIK ────────────────────────────────────────────
    story += _section("12", "GAMBAR TEKNIK", s)
    story += _build_figures_section(
        calc_type=calc_type,
        input_data=input_data,
        output_data=output_data,
        figure_snapshots=figure_snapshots,
        s=s,
    )

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


# ── Section builders ──────────────────────────────────────────────────────────

def _build_cover(project_data, calc_title, calc_type, generated_by, s):
    calc_type_label = ("Desain Lentur Balok Beton Bertulang — SNI 2847:2019"
                       if calc_type == "concrete_beam"
                       else "Desain Lentur Balok Baja WF — SNI 1729:2020")

    cover_data = [
        [Paragraph("AG STRUCTURAL ANALYSIS SUITE", s["cover_title"])],
        [Paragraph("AG-SAS v1.0  ·  Platform Perhitungan Struktur", s["cover_subtitle"])],
        [Spacer(1, 18)],
        [Paragraph(calc_type_label.upper(), s["cover_meta"])],
        [Spacer(1, 8)],
        [Paragraph(calc_title.upper(), s["cover_title"])],
        [Spacer(1, 24)],
        [Paragraph(f"Proyek: {project_data.get('name', '—')}", s["cover_subtitle"])],
        [Paragraph(f"Lokasi: {project_data.get('location', '—')}", s["cover_subtitle"])],
        [Paragraph(f"Pemberi Tugas: {project_data.get('client_name', '—')}", s["cover_subtitle"])],
    ]
    if project_data.get("consultant_name"):
        cover_data.append([Paragraph(f"Konsultan: {project_data['consultant_name']}", s["cover_subtitle"])])

    cover_tbl = Table(cover_data, colWidths=[16*cm])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 20),
        ("RIGHTPADDING",  (0,0), (-1,-1), 20),
    ]))

    meta_rows = [
        ["Tanggal Cetak:",  datetime.now().strftime("%d %B %Y")],
        ["Dibuat Oleh:",    generated_by],
        ["Formula Version:", project_data.get("formula_version", "1.1.0")],
    ]
    meta_tbl = Table([[Paragraph(r[0], s["cell_bold"]), Paragraph(r[1], s["cell"])]
                      for r in meta_rows], colWidths=[5*cm, 11*cm])
    meta_tbl.setStyle(TableStyle([
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
    ]))

    return [Spacer(1, 40), cover_tbl, Spacer(1, 30), meta_tbl]


def _build_project_table(project_data, calc_title, generated_by, s):
    rows = [
        ("Nama Proyek",         project_data.get("name", "—")),
        ("Lokasi",              project_data.get("location", "—")),
        ("Pemberi Tugas",       project_data.get("client_name", "—")),
        ("Konsultan Perencana", project_data.get("consultant_name") or "—"),
        ("Jenis Bangunan",      project_data.get("building_type", "—")),
        ("Jumlah Lantai",       str(project_data.get("num_floors", "—"))),
        ("Sistem Struktur",     project_data.get("structural_system", "—")),
        ("Material Utama",      project_data.get("primary_material", "—")),
        ("Judul Perhitungan",   calc_title),
        ("Tanggal Generate",    datetime.now().strftime("%d %B %Y, %H:%M")),
        ("Dibuat Oleh",         generated_by),
    ]
    return _two_col_table(rows, s)


def _build_standards_section(standard_references: str, s) -> list:
    _SNI_DESC = {
        "SNI 1727:2020": "Beban Desain Minimum dan Kriteria Terkait -- Kombinasi beban LRFD Pasal 5.3.1",
        "SNI 2847:2019": "Persyaratan Beton Struktural untuk Bangunan Gedung -- Desain lentur singly reinforced, faktor β₁, ρ_min, ρ_max, φMn",
        "SNI 1729:2020": "Bangunan Gedung Baja Struktural -- Kelangsingan sayap B4.1b, desain lentur F2/F3",
        "SNI 1726:2019": "Perencanaan Ketahanan Gempa untuk Bangunan Gedung dan Non-Gedung",
        "SNI 7860:2020": "Ketentuan Seismik untuk Struktur Baja Struktural",
    }
    rows = []
    for code, desc in _SNI_DESC.items():
        if code in standard_references:
            rows.append([code, desc])
    if not rows:
        rows = [[r.strip(), "—"] for r in standard_references.split(",") if r.strip()]

    t = _data_table(
        ["Kode Standar", "Judul / Lingkup Penggunaan"],
        rows, s,
        col_widths=[4.5*cm, 11.5*cm],
    )
    return [t]


def _build_material_section(input_data: dict, calc_type: str, s) -> list:
    if calc_type == "concrete_beam":
        fc = input_data.get("fc_prime_mpa", 0)
        fy = input_data.get("fy_mpa", 0)
        ec = 4700 * math.sqrt(fc)
        rows = [
            ["Kuat tekan beton fc'",       "fc'",  _fmt(fc, 1), "MPa",   "Min. 17 MPa (SNI 2847:2019)"],
            ["Kuat leleh tulangan fy",      "fy",   _fmt(fy, 1), "MPa",   "Maks. 550 MPa"],
            ["Modulus elastisitas beton",   "Ec",   _fmt(ec, 0), "MPa",   "Ec = 4700√fc' (SNI 2847:2019 Ps. 19.2.2)"],
            ["Modulus elastisitas baja",    "Es",   "200,000",   "MPa",   "Nilai standar SNI 2847:2019"],
        ]
        hdr_color = BLUE
    else:
        fy = input_data.get("fy_mpa", 0)
        rows = [
            ["Kuat leleh baja Fy",        "Fy",  _fmt(fy, 1), "MPa",   "Baja BJ 37/41/50"],
            ["Modulus elastisitas baja E", "E",   "200,000",    "MPa",   "SNI 1729:2020 Pasal A3.2"],
        ]
        hdr_color = STEEL_GRAY
    t = _data_table(
        ["Parameter", "Simbol", "Nilai", "Satuan", "Keterangan"],
        rows, s,
        col_widths=[5*cm, 2*cm, 2.5*cm, 2*cm, 4.5*cm],
        header_color=hdr_color,
    )
    return [t]


def _build_geometry_section(input_data: dict, output_data: dict, calc_type: str, s) -> list:
    if calc_type == "concrete_beam":
        eff_d = output_data.get("effective_depth_d_mm", 0)
        rows = [
            ["Lebar penampang",       "b",   _fmt(input_data.get("width_b_mm"), 1),           "mm", "—"],
            ["Tinggi total",          "h",   _fmt(input_data.get("height_h_mm"), 1),           "mm", "—"],
            ["Selimut beton bersih",  "cc",  _fmt(input_data.get("cover_cc_mm"), 1),           "mm", "—"],
            ["Diameter sengkang",     "Øs",  _fmt(input_data.get("stirrup_diameter_mm"), 1),   "mm", "—"],
            ["Diameter tulangan",     "Ø",   _fmt(input_data.get("bar_diameter_mm"), 1),       "mm", "—"],
            ["Tinggi efektif",        "d",   _fmt(eff_d, 1),                                   "mm", "d = h−cc−Øs−Ø/2"],
            ["Panjang bentang",       "L",   _fmt(input_data.get("span_l_m"), 2),              "m",  "Simply supported"],
        ]
        hdr_color = BLUE
    else:
        rows = [
            ["Designasi profil",          "—",   output_data.get("profile_designation", "—"), "—",    "—"],
            ["Tinggi profil",             "H",   _fmt(input_data.get("height_h_mm"), 1),       "mm",   "—"],
            ["Lebar sayap",               "B",   _fmt(input_data.get("flange_width_b_mm"), 1), "mm",   "—"],
            ["Tebal badan",               "tw",  _fmt(input_data.get("web_thickness_tw_mm"), 1), "mm", "—"],
            ["Tebal sayap",               "tf",  _fmt(input_data.get("flange_thickness_tf_mm"), 1), "mm","—"],
            ["Modulus elastis Sx",        "Sx",  _fmt(output_data.get("sx_cm3"), 1),           "cm³",  "—"],
            ["Modulus plastis Zx",        "Zx",  _fmt(output_data.get("zx_cm3"), 1),           "cm³",  "—"],
            ["Berat sendiri profil",      "W",   _fmt(output_data.get("weight_per_m_kgm"), 1), "kg/m", "—"],
            ["Panjang bentang",           "L",   _fmt(input_data.get("span_l_m"), 2),          "m",    "Simply supported"],
        ]
        hdr_color = STEEL_GRAY
    t = _data_table(
        ["Dimensi", "Simbol", "Nilai", "Satuan", "Keterangan"],
        rows, s,
        col_widths=[5*cm, 1.8*cm, 2.5*cm, 1.8*cm, 4.9*cm],
        header_color=hdr_color,
    )
    return [t]


def _build_loading_section(input_data: dict, output_data: dict, calc_type: str, s) -> list:
    wd = input_data.get("dead_load_w_knm", 0)
    wl = input_data.get("live_load_w_knm", 0)
    L  = input_data.get("span_l_m", 0)
    rows = [
        ["Beban mati merata",   "wD",       _fmt(wd, 3), "kN/m", "Beban mati eksternal"],
    ]
    if calc_type == "steel_beam":
        sw = output_data.get("self_weight_knm", 0)
        rows += [
            ["Berat sendiri profil", "SW",    _fmt(sw, 4), "kN/m", "W × 9.81 / 1000"],
            ["Beban mati total",     "wD,tot", _fmt(wd + sw, 4), "kN/m", "wD + SW"],
        ]
    rows += [
        ["Beban hidup merata",  "wL",       _fmt(wl, 3), "kN/m", "—"],
        ["Panjang bentang",     "L",        _fmt(L, 2),  "m",    "Simply supported"],
    ]
    t = _data_table(
        ["Jenis Beban", "Simbol", "Nilai", "Satuan", "Keterangan"],
        rows, s,
        col_widths=[5*cm, 1.8*cm, 2.5*cm, 1.8*cm, 4.9*cm],
    )
    return [t]


def _build_combination_section(input_data: dict, output_data: dict, calc_type: str, s) -> list:
    wu = output_data.get("wu_knm", 0)
    wd = input_data.get("dead_load_w_knm", 0)
    wl = input_data.get("live_load_w_knm", 0)
    elems = [Paragraph("Referensi: SNI 1727:2020 Pasal 5.3.1c — Kombinasi beban LRFD dasar", s["body"])]
    if calc_type == "concrete_beam":
        formula = (
            f"U = 1.2D + 1.6L\n"
            f"wu = 1.2 × wD + 1.6 × wL\n"
            f"wu = 1.2 × {_fmt(wd,3)} + 1.6 × {_fmt(wl,3)}\n"
            f"wu = {_fmt(wu,3)} kN/m"
        )
    else:
        sw = output_data.get("self_weight_knm", 0)
        wdt = wd + sw
        formula = (
            f"U = 1.2(D + SW) + 1.6L\n"
            f"wu = 1.2 × (wD + SW) + 1.6 × wL\n"
            f"wu = 1.2 × ({_fmt(wd,3)} + {_fmt(sw,4)}) + 1.6 × {_fmt(wl,3)}\n"
            f"wu = 1.2 × {_fmt(wdt,4)} + 1.6 × {_fmt(wl,3)}\n"
            f"wu = {_fmt(wu,3)} kN/m"
        )
    elems.append(Paragraph(formula, s["formula"]))
    rows = [["wu (beban terfaktor)", _fmt(wu, 3), "kN/m"]]
    t = _data_table(["Parameter", "Nilai", "Satuan"], rows, s,
                    col_widths=[8*cm, 4*cm, 4*cm])
    elems.append(t)
    return elems


def _build_forces_section(input_data: dict, output_data: dict, calc_type: str, s) -> list:
    wu = output_data.get("wu_knm", 0)
    mu = output_data.get("mu_ultimate_knm", 0)
    L  = input_data.get("span_l_m", 0)

    formula = (f"Mu = wu × L² / 8\n"
               f"Mu = {_fmt(wu,3)} × {_fmt(L,2)}² / 8\n"
               f"Mu = {_fmt(mu,2)} kN·m")
    if calc_type == "concrete_beam":
        vu = output_data.get("vu_ultimate_kn", 0)
        formula += (f"\n\nVu = wu × L / 2\n"
                    f"Vu = {_fmt(wu,3)} × {_fmt(L,2)} / 2\n"
                    f"Vu = {_fmt(vu,2)} kN")

    elems = [Paragraph(formula, s["formula"])]
    rows = [["Momen ultimit Mu", _fmt(mu, 2), "kN·m", "wu·L²/8"]]
    if calc_type == "concrete_beam":
        vu = output_data.get("vu_ultimate_kn", 0)
        rows.append(["Geser ultimit Vu", _fmt(vu, 2), "kN", "wu·L/2"])
    t = _data_table(["Gaya Dalam", "Nilai", "Satuan", "Rumus"], rows, s,
                    col_widths=[5.5*cm, 3*cm, 2.5*cm, 5*cm])
    elems.append(t)
    return elems


def _build_capacity_section(input_data: dict, output_data: dict, calc_type: str, s) -> list:
    elems = []
    if calc_type == "concrete_beam":
        fc   = input_data.get("fc_prime_mpa", 0)
        fy   = input_data.get("fy_mpa", 0)
        b    = input_data.get("width_b_mm", 0)
        d    = output_data.get("effective_depth_d_mm", 0)
        phi  = output_data.get("phi_factor", 0.9)
        b1   = output_data.get("beta1", 0)
        rmin = output_data.get("rho_min", 0)
        rmax = output_data.get("rho_max", 0)
        rreq = output_data.get("rho_required", 0)
        asreq  = output_data.get("as_required_mm2", 0)
        asmin  = output_data.get("as_min_mm2", 0)
        asdes  = output_data.get("as_design_mm2", 0)
        bararea= output_data.get("bar_area_mm2", 0)
        nbars  = output_data.get("num_bars", 0)
        bar_d  = input_data.get("bar_diameter_mm", 0)
        a      = output_data.get("a_block_mm", 0)
        mn     = output_data.get("mn_knm", 0)
        phmn   = output_data.get("phi_mn_knm", 0)
        mu     = output_data.get("mu_ultimate_knm", 0)

        # Sub-section 8.1
        elems.append(Paragraph("8.1  Faktor β₁ (Blok Tegangan Ekivalen)", s["subsection"]))
        if fc <= 28:
            b1_formula = f"fc' = {_fmt(fc,1)} MPa ≤ 28 MPa  →  β₁ = 0.85"
        elif fc >= 56:
            b1_formula = f"fc' = {_fmt(fc,1)} MPa ≥ 56 MPa  →  β₁ = 0.65 (minimum)"
        else:
            b1_formula = (f"fc' = {_fmt(fc,1)} MPa\n"
                          f"β₁ = 0.85 − 0.05 × (fc'−28)/7\n"
                          f"β₁ = 0.85 − 0.05 × ({_fmt(fc,1)}−28)/7\n"
                          f"β₁ = {_fmt(b1,4)}")
        elems.append(Paragraph(b1_formula, s["formula"]))

        # Sub-section 8.2
        elems.append(Paragraph("8.2  Rasio Tulangan (ρ)", s["subsection"]))
        rn = mu * 1e6 / (phi * b * d**2)
        rho_formula = (
            f"ρ_min = max(0.25√fc'/fy , 1.4/fy)\n"
            f"ρ_min = max(0.25×√{_fmt(fc,1)}/{_fmt(fy,1)} , 1.4/{_fmt(fy,1)})\n"
            f"ρ_min = {rmin:.5f}\n\n"
            f"ρ_balanced = (0.85 × β₁ × fc'/fy) × (600/(600+fy))\n"
            f"ρ_max = 0.75 × ρ_balanced = {rmax:.5f}\n\n"
            f"Rn = Mu/(φ × b × d²) = {_fmt(mu,2)} × 10⁶/({_fmt(phi,2)} × {_fmt(b,1)} × {_fmt(d,1)}²)\n"
            f"Rn = {rn:.4f} MPa\n\n"
            f"ρ_req = (0.85 × fc'/fy) × (1 − √(1 − 2Rn/(0.85 × fc')))\n"
            f"ρ_req = {rreq:.5f}"
        )
        elems.append(Paragraph(rho_formula, s["formula"]))

        # Sub-section 8.3
        elems.append(Paragraph("8.3  Luas Tulangan", s["subsection"]))
        as_formula = (
            f"As_req = ρ_req × b × d = {rreq:.5f} × {_fmt(b,1)} × {_fmt(d,1)} = {_fmt(asreq,1)} mm²\n"
            f"As_min = ρ_min × b × d = {rmin:.5f} × {_fmt(b,1)} × {_fmt(d,1)} = {_fmt(asmin,1)} mm²\n"
            f"As_design = max(As_req, As_min) → dibulatkan ke jumlah batang utuh\n"
            f"Luas 1 batang D{_fmt(bar_d,0)} = π × D²/4 = {_fmt(bararea,2)} mm²\n"
            f"n = ceil(As_design / bar_area) = {nbars} batang\n"
            f"As_design = {nbars} × {_fmt(bararea,2)} = {_fmt(asdes,1)} mm²"
        )
        elems.append(Paragraph(as_formula, s["formula"]))

        # Sub-section 8.4
        elems.append(Paragraph("8.4  Tinggi Blok Tekan dan Kapasitas Momen", s["subsection"]))
        mn_formula = (
            f"a = As × fy / (0.85 × fc' × b)\n"
            f"a = {_fmt(asdes,1)} × {_fmt(fy,1)} / (0.85 × {_fmt(fc,1)} × {_fmt(b,1)})\n"
            f"a = {_fmt(a,2)} mm\n\n"
            f"Mn = As × fy × (d − a/2)\n"
            f"Mn = {_fmt(asdes,1)} × {_fmt(fy,1)} × ({_fmt(d,1)} − {_fmt(a,2)}/2) / 10⁶\n"
            f"Mn = {_fmt(mn,2)} kN·m\n\n"
            f"φMn = φ × Mn = {_fmt(phi,2)} × {_fmt(mn,2)}\n"
            f"φMn = {_fmt(phmn,2)} kN·m"
        )
        elems.append(Paragraph(mn_formula, s["formula"]))

        rows = [
            ["β₁", _fmt(b1, 4), "—", "Faktor blok tegangan (SNI 2847:2019 Ps. 22.2.2.4.3)"],
            ["ρ_min", f"{rmin:.5f}", "—", "max(0.25√fc'/fy , 1.4/fy)"],
            ["ρ_max", f"{rmax:.5f}", "—", "0.75 × ρ_balanced"],
            ["ρ_required", f"{rreq:.5f}", "—", "Dari persamaan Rn"],
            ["As_required", _fmt(asreq, 1), "mm²", "ρ_req × b × d"],
            ["As_min", _fmt(asmin, 1), "mm²", "ρ_min × b × d"],
            [f"As_design ({nbars}×D{_fmt(bar_d,0)})", _fmt(asdes, 1), "mm²", "n × bar_area"],
            ["a (blok tekan)", _fmt(a, 2), "mm", "As × fy/(0.85 × fc' × b)"],
            ["Mn", _fmt(mn, 2), "kN·m", "As × fy × (d−a/2)"],
            ["φ", _fmt(phi, 2), "—", "SNI 2847:2019 Tabel 21.2.2"],
            ["φMn", _fmt(phmn, 2), "kN·m", "φ × Mn"],
        ]
        elems.append(Spacer(1, 6))
        t = _data_table(["Parameter", "Nilai", "Satuan", "Rumus / Referensi"], rows, s,
                        col_widths=[4.5*cm, 3*cm, 2.5*cm, 6*cm], header_color=BLUE)
        elems.append(t)

    else:
        fy   = input_data.get("fy_mpa", 0)
        b    = input_data.get("flange_width_b_mm", 0)
        tf   = input_data.get("flange_thickness_tf_mm", 0)
        Zx   = output_data.get("zx_cm3", 0)
        Sx   = output_data.get("sx_cm3", 0)
        lf   = output_data.get("lambda_f", 0)
        lpf  = output_data.get("lambda_pf", 0)
        lrf  = output_data.get("lambda_rf", 0)
        compact  = output_data.get("is_compact", True)
        mp   = output_data.get("mp_knm", 0)
        mn   = output_data.get("mn_knm", output_data.get("phi_mn_knm", 0) / output_data.get("phi_factor", 0.9))
        phi  = output_data.get("phi_factor", 0.9)
        phmn = output_data.get("phi_mn_knm", 0)

        # Sub-section 8.1
        elems.append(Paragraph("8.1  Cek Kelangsingan Sayap (SNI 1729:2020 Tabel B4.1b)", s["subsection"]))
        compact_str = "KOMPAK" if compact else "TIDAK KOMPAK"
        comp_formula = (
            f"λ_f  = (B/2) / tf = ({_fmt(b,1)}/2) / {_fmt(tf,1)}\n"
            f"λ_f  = {_fmt(lf,3)}\n\n"
            f"λ_pf = 0.38 × √(E/Fy) = 0.38 × √(200000/{_fmt(fy,1)})\n"
            f"λ_pf = {_fmt(lpf,3)}\n\n"
            f"λ_rf = 1.0 × √(E/Fy)\n"
            f"λ_rf = {_fmt(lrf,3)}\n\n"
            f"λ_f {'≤' if compact else '>'} λ_pf  →  Penampang {compact_str}"
        )
        elems.append(Paragraph(comp_formula, s["formula"]))

        # Sub-section 8.2
        elems.append(Paragraph("8.2  Momen Plastis dan Kapasitas Lentur", s["subsection"]))
        if compact:
            mn_formula = (
                f"Mp = Fy × Zx = {_fmt(fy,1)} × {_fmt(Zx,1)} cm³ × 1000 / 10⁶\n"
                f"Mp = {_fmt(mp,2)} kN·m\n\n"
                f"Penampang kompak + Lb ≤ Lp (diasumsikan) → Mn = Mp\n"
                f"Mn = {_fmt(mn,2)} kN·m\n\n"
                f"φMn = φ × Mn = {_fmt(phi,2)} × {_fmt(mn,2)}\n"
                f"φMn = {_fmt(phmn,2)} kN·m"
            )
        else:
            mn_formula = (
                f"Mp = Fy × Zx = {_fmt(mp,2)} kN·m\n"
                f"Mr = 0.7 × Fy × Sx = 0.7 × {_fmt(fy,1)} × {_fmt(Sx,1)} cm³ / 1000 kN·m\n\n"
                f"Mn = Mp − (Mp − Mr) × (λ_f − λ_pf) / (λ_rf − λ_pf)  [SNI 1729:2020 F3-1]\n"
                f"Mn = {_fmt(mn,2)} kN·m\n\n"
                f"φMn = φ × Mn = {_fmt(phi,2)} × {_fmt(mn,2)}\n"
                f"φMn = {_fmt(phmn,2)} kN·m"
            )
        elems.append(Paragraph(mn_formula, s["formula"]))

        rows = [
            ["λ_f (sayap)",             _fmt(lf,  3), "—",    "(B/2)/tf"],
            ["λ_pf (batas kompak)",     _fmt(lpf, 3), "—",    "0.38√(E/Fy)"],
            ["λ_rf (batas tak kompak)", _fmt(lrf, 3), "—",    "1.0√(E/Fy)"],
            ["Klasifikasi penampang",   compact_str,   "—",    "λ_f ≤ λ_pf → kompak?"],
            ["Mp (momen plastis)",      _fmt(mp,  2),  "kN·m", "Fy × Zx"],
            ["Mn (momen nominal)",      _fmt(mn,  2),  "kN·m", "Mp (kompak) / F3-1"],
            ["φ",                       _fmt(phi, 2),  "—",    "SNI 1729:2020 B3.4a"],
            ["φMn",                     _fmt(phmn,2),  "kN·m", "φ × Mn"],
        ]
        elems.append(Spacer(1, 6))
        t = _data_table(["Parameter", "Nilai", "Satuan", "Rumus / Referensi"], rows, s,
                        col_widths=[4.5*cm, 3*cm, 2.5*cm, 6*cm], header_color=STEEL_GRAY)
        elems.append(t)

    return elems


def _build_summary_section(input_data: dict, output_data: dict, calc_type: str, s) -> list:
    mu   = output_data.get("mu_ultimate_knm", 0)
    phmn = output_data.get("phi_mn_knm", 0)
    cr   = output_data.get("capacity_ratio", 0)
    wu   = output_data.get("wu_knm", 0)

    if calc_type == "concrete_beam":
        left_rows  = [
            ("wu terfaktor",         f"{_fmt(wu,3)} kN/m"),
            ("Mu ultimit",           f"{_fmt(mu,2)} kN·m"),
            ("Vu ultimit",           f"{_fmt(output_data.get('vu_ultimate_kn',0),2)} kN"),
            ("d efektif",            f"{_fmt(output_data.get('effective_depth_d_mm',0),1)} mm"),
        ]
        right_rows = [
            ("As design",            f"{_fmt(output_data.get('as_design_mm2',0),1)} mm²"),
            ("Jumlah tulangan",      f"{output_data.get('num_bars',0)} batang D{input_data.get('bar_diameter_mm',0)}"),
            ("a (blok tekan)",       f"{_fmt(output_data.get('a_block_mm',0),2)} mm"),
            ("φMn kapasitas",        f"{_fmt(phmn,2)} kN·m"),
        ]
    else:
        compact_str = "Kompak" if output_data.get("is_compact") else "Tidak Kompak"
        left_rows  = [
            ("SW berat sendiri",     f"{_fmt(output_data.get('self_weight_knm',0),4)} kN/m"),
            ("wu terfaktor",         f"{_fmt(wu,3)} kN/m"),
            ("Mu ultimit",           f"{_fmt(mu,2)} kN·m"),
            ("Klasifikasi sayap",    compact_str),
        ]
        right_rows = [
            ("Mp momen plastis",     f"{_fmt(output_data.get('mp_knm',0),2)} kN·m"),
            ("Mn momen nominal",     f"{_fmt(output_data.get('mn_knm', phmn/output_data.get('phi_factor',0.9)),2)} kN·m"),
            ("φ faktor reduksi",     f"{_fmt(output_data.get('phi_factor',0.9),2)}"),
            ("φMn kapasitas",        f"{_fmt(phmn,2)} kN·m"),
        ]

    # Inner tables: total harus <= lebar kolom outer (7.8 cm)
    left_tbl  = _two_col_table(left_rows,  s, col_widths=[3.5*cm, 4.0*cm])
    right_tbl = _two_col_table(right_rows, s, col_widths=[3.5*cm, 4.0*cm])

    outer = Table([[left_tbl, Spacer(0.4*cm, 1), right_tbl]],
                  colWidths=[7.7*cm, 0.6*cm, 7.7*cm])
    outer.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                                ("LEFTPADDING", (0,0), (-1,-1), 0),
                                ("RIGHTPADDING",(0,0), (-1,-1), 0)]))

    # Final check row
    ok_str    = "≤ 1.0 → AMAN" if cr <= 1.0 else "> 1.0 → TIDAK AMAN"
    bg_color  = GREEN_BG if cr <= 1.0 else RED_BG
    chk_rows  = [
        [Paragraph("Momen terfaktor Mu",         s["cell_bold"]),
         Paragraph(_fmt(mu, 2),                  s["cell"]),
         Paragraph("kN·m", s["cell"]),
         Paragraph("—", s["cell"])],
        [Paragraph("Kapasitas tereduksi φMn",    s["cell_bold"]),
         Paragraph(_fmt(phmn, 2),                s["cell"]),
         Paragraph("kN·m", s["cell"]),
         Paragraph("—", s["cell"])],
        [Paragraph("Rasio Mu/φMn",               s["cell_bold"]),
         Paragraph(_fmt(cr, 4),                  s["cell_bold"]),
         Paragraph("—",  s["cell"]),
         Paragraph(ok_str, s["cell_bold"])],
    ]
    chk_tbl = Table(chk_rows, colWidths=[5.5*cm, 3*cm, 2.5*cm, 5*cm])
    chk_tbl.setStyle(TableStyle(_TS_BASE + [
        ("ROWBACKGROUNDS", (0,0), (-1,-2), [WHITE, LIGHT]),
        ("BACKGROUND",     (0,-1), (-1,-1), bg_color),
        ("GRID",           (0,0), (-1,-1), 0.4, BORDER),
        ("LINEABOVE",      (0,-1), (-1,-1), 1.0, BORDER),
    ]))

    return [outer, Spacer(1, 8), chk_tbl]


def _build_conclusion_section(output_data: dict, s) -> list:
    status = output_data.get("status", "TIDAK AMAN")
    cr     = output_data.get("capacity_ratio", 0)
    ok_str = "≤ 1.0 → Kapasitas penampang mencukupi" if cr <= 1.0 else "> 1.0 → Kapasitas TIDAK mencukupi. Perlu redesign"
    style  = s["status_safe"] if status == "AMAN" else s["status_unsafe"]
    bg     = GREEN_BG if status == "AMAN" else RED_BG
    border = GREEN    if status == "AMAN" else RED

    status_data = [
        [Paragraph(f"ELEMEN  {status}", style)],
        [Paragraph(f"Rasio kapasitas  Mu/φMn = {_fmt(cr, 4)}  {ok_str}", s["body"])],
    ]
    status_tbl = Table(status_data, colWidths=[16*cm])
    status_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("BOX",           (0,0), (-1,-1), 1.5, border),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    return [status_tbl]


def _build_disclaimer_section(calc_type: str, generated_by: str, meta: dict, s, engineer_data: dict | None = None) -> list:
    if calc_type == "concrete_beam":
        assumptions = [
            "Balok sederhana (simply supported), beban merata seragam",
            "Tulangan tunggal (singly reinforced), penampang segi empat",
            "φ = 0.90 berlaku (tension-controlled, dijamin via ρ_max = 0.75ρ_balanced)",
            "Geser, torsi, dan lendutan tidak dicek dalam perhitungan ini",
        ]
    else:
        assumptions = [
            "Balok sederhana (simply supported), beban merata seragam",
            "LTB (Lateral-Torsional Buckling) diasumsikan tidak mengontrol (Lb ≤ Lp) — WAJIB diverifikasi",
            "Hanya kelangsingan sayap yang dicek; badan diasumsikan kompak",
            "Defleksi, geser, dan sambungan tidak dicek dalam perhitungan ini",
        ]

    asmp_text = "  •  ".join(assumptions)
    text = (
        f"PERINGATAN: Laporan ini dibuat secara otomatis oleh AG Structural Analysis Suite dan "
        f"bersifat INDIKATIF SEMATA. Asumsi: {asmp_text}. "
        f"Laporan ini WAJIB diperiksa ulang oleh Engineer Struktur berwenang (Insinyur Profesional / "
        f"Ahli K3 Konstruksi) sebelum digunakan dalam dokumen desain resmi, gambar kerja, atau "
        f"pengurusan ijin mendirikan bangunan. Penyedia aplikasi tidak bertanggung jawab atas "
        f"penggunaan hasil tanpa verifikasi engineer berwenang."
    )

    # Signature table — isi data engineer jika tersedia
    eng = engineer_data or {}
    eng_name     = eng.get("name", "")     or ""
    eng_position = eng.get("position", "") or ""
    eng_skk      = eng.get("skk", "")      or ""

    sig_data = [
        [Paragraph(h, s["table_header"]) for h in
         ["Nama Engineer", "No. SKK", "Jabatan", "Tanggal Periksa", "Tanda Tangan"]],
        [Paragraph(eng_name     or "________________________", s["cell"]),
         Paragraph(eng_skk      or "________________________", s["cell"]),
         Paragraph(eng_position or "________________________", s["cell"]),
         Paragraph("________________________", s["cell"]),
         Paragraph("________________________", s["cell"])],
    ]
    sig_tbl = Table(sig_data, colWidths=[3.5*cm, 3.5*cm, 3*cm, 3*cm, 3*cm])
    sig_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), NAVY),
        ("GRID",          (0,0), (-1,-1), 0.4, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,1), (-1,-1), 28),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))

    fv = meta.get("formula_version", "1.1.0") if isinstance(meta, dict) else "1.1.0"
    footer_note = (
        f"Dokumen digenerate oleh AG-SAS Formula Engine v{fv} "
        f"pada {datetime.now().strftime('%d %B %Y, %H:%M')} oleh {generated_by}. "
        f"Rumus dan persyaratan teknis mengacu pada SNI yang diterbitkan oleh "
        f"Badan Standardisasi Nasional (BSN), Indonesia."
    )

    return [
        Paragraph(text, s["disclaimer"]),
        Spacer(1, 10),
        Paragraph("Persetujuan Engineer Perencana", s["subsection"]),
        sig_tbl,
        Spacer(1, 8),
        Paragraph(footer_note, s["small"]),
    ]


# ── Section 12: Gambar Teknik ──────────────────────────────────────────────────

def _build_figures_section(
    calc_type: str,
    input_data: dict,
    output_data: dict,
    figure_snapshots: list | None,
    s: dict,
) -> list:
    """
    Masukkan gambar teknik ke laporan PDF.

    Jika figure_snapshots diberikan, gunakan PNG yang sudah tersimpan.
    Jika tidak, generate on-the-fly dari data kalkulasi.
    """
    from app.reporting.figures.figure_builder import build_figures_for_calc

    elems = []

    # Ambil FigureSpec — dari snapshot DB atau generate baru
    if figure_snapshots:
        # Konversi FigureSnapshot DB ke FigureSpec-like objects
        visible = sorted(
            [f for f in figure_snapshots if getattr(f, "is_visible", True)],
            key=lambda f: f.order_index,
        )
        png_items = [(f.figure_number, f.caption, f.png_data, f.unit) for f in visible]
    else:
        # Generate on-the-fly
        specs = build_figures_for_calc(
            calc_type=calc_type,
            input_data=input_data,
            output_data=output_data,
            section="12",
        )
        png_items = [(f.figure_number, f.caption, f.png_bytes, f.unit) for f in specs]

    if not png_items:
        elems.append(Paragraph("Tidak ada gambar teknik tersedia.", s["body"]))
        return elems

    # ── Daftar Gambar (TOF) ─────────────────────────────────────────────────
    elems.append(Paragraph("Daftar Gambar", s["subsection"]))
    tof_rows = []
    for num, cap, _, unit in png_items:
        # Strip "Gambar X.Y  " prefix dari caption
        tof_label = cap.replace(f"Gambar {num}  ", "") if cap.startswith(f"Gambar {num}") else cap
        tof_rows.append([
            Paragraph(f"Gambar {num}", s["cell_bold"]),
            Paragraph(tof_label, s["cell"]),
            Paragraph(unit, s["cell"]),
        ])
    tof_tbl = Table(tof_rows, colWidths=[2.5*cm, 12*cm, 1.5*cm])
    tof_tbl.setStyle(TableStyle(_TS_BASE + [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT]),
    ]))
    elems.append(tof_tbl)
    elems.append(Spacer(1, 14))

    # ── Gambar ───────────────────────────────────────────────────────────────
    # Lebar gambar maksimum = lebar area teks A4 = 16cm
    PAGE_W = 16 * cm   # 210 - 25 - 20 mm = 165mm ≈ 16.5cm — gunakan 16cm

    for num, cap, png_bytes, unit in png_items:
        # Buat ReportLab Image dari bytes
        img_buf = io.BytesIO(png_bytes)
        rl_img = RLImage(img_buf)
        # Scale to page width, maintain aspect
        orig_w, orig_h = rl_img.imageWidth, rl_img.imageHeight
        if orig_w > 0:
            scale = PAGE_W / orig_w
            rl_img.drawWidth  = PAGE_W
            rl_img.drawHeight = orig_h * scale
        else:
            rl_img.drawWidth  = PAGE_W
            rl_img.drawHeight = PAGE_W * 0.45

        # Caption di bawah
        cap_style = ParagraphStyle(
            "fig_cap", parent=s["small"],
            alignment=1,           # TA_CENTER
            fontSize=8,
            textColor=STEEL_GRAY,
            fontName=_FREG,
            spaceAfter=2,
        )
        unit_label = f"  [Satuan: {unit}]" if unit and unit != "—" else ""
        caption_para = Paragraph(f"<i>{cap}{unit_label}</i>", cap_style)

        # Frame gambar
        fig_tbl = Table(
            [[rl_img], [caption_para]],
            colWidths=[PAGE_W],
        )
        fig_tbl.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("BACKGROUND",    (0, 0), (-1, 0), LIGHT),
            ("BACKGROUND",    (0, 1), (-1, 1), WHITE),
        ]))

        elems.append(KeepTogether([fig_tbl, Spacer(1, 12)]))

    return elems
