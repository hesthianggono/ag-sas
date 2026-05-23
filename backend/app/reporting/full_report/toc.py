"""
Table of Contents, List of Tables, List of Figures — AG-SAS Full Report
========================================================================
Menghasilkan:
  - Daftar Isi  (TOC)
  - Daftar Tabel (LoT)
  - Daftar Gambar (LoF)

Setelah semua section di-render, NumberingContext.toc / .lot / .lof sudah
terisi — tinggal panggil build_toc_section(ctx) untuk membuat flowables-nya.
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, Spacer, Table, TableStyle,
)

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.template import (
    FBOLD, FREG, P, PAGE_W, MARGIN_L, MARGIN_R, build_styles,
)

_S = build_styles()
_USABLE_W = PAGE_W - MARGIN_L - MARGIN_R


def _p(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, _S[style])


# ── Daftar Isi ────────────────────────────────────────────────────────────────
def build_toc_section(ctx: NumberingContext) -> list[Any]:
    """
    Return flowables halaman Daftar Isi.
    Dipanggil SETELAH semua section builder selesai mengisi ctx.toc.
    """
    story: list[Any] = []

    story.append(_p("<b>DAFTAR ISI</b>", "H1"))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=P.NAVY, spaceAfter=4 * mm))

    for entry in ctx.toc:
        if entry.level == 0:
            # Bab / Lampiran — tebal, tanpa indent
            row = [
                _p(f"<b>{entry.number}</b>", "TocH1"),
                _p("", "TocH1"),
                _p(f"<b>{entry.title}</b>", "TocH1"),
                _p("", "TocH1"),
            ]
            col_w = [1.8 * cm, 0.3 * cm, _USABLE_W - 1.8 * cm - 0.3 * cm - 1.2 * cm, 1.2 * cm]
        elif entry.level == 1:
            row = [
                _p("", "TocH2"),
                _p(f"  {entry.number}", "TocH2"),
                _p(entry.title, "TocH2"),
                _p("", "TocH2"),
            ]
            col_w = [0.5 * cm, 1.6 * cm, _USABLE_W - 0.5 * cm - 1.6 * cm - 1.2 * cm, 1.2 * cm]
        else:
            row = [
                _p("", "TocH3"),
                _p(f"    {entry.number}", "TocH3"),
                _p(entry.title, "TocH3"),
                _p("", "TocH3"),
            ]
            col_w = [1.0 * cm, 2.0 * cm, _USABLE_W - 1.0 * cm - 2.0 * cm - 1.2 * cm, 1.2 * cm]

        tbl = Table([row], colWidths=col_w)
        tbl.setStyle(TableStyle([
            ("VALIGN",    (0, 0), (-1, -1), "BOTTOM"),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        story.append(tbl)

    story.append(PageBreak())
    return story


# ── Daftar Tabel ──────────────────────────────────────────────────────────────
def build_lot_section(ctx: NumberingContext) -> list[Any]:
    """Return flowables halaman Daftar Tabel."""
    story: list[Any] = []

    if not ctx.lot:
        return story

    story.append(_p("<b>DAFTAR TABEL</b>", "H1"))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=P.NAVY, spaceAfter=4 * mm))

    header = [
        [
            _p("<b>Nomor</b>", "TH"),
            _p("<b>Judul Tabel</b>", "TH"),
            _p("<b>Hal.</b>", "TH"),
        ]
    ]
    rows = [
        [
            _p(e.number, "TD"),
            _p(e.caption, "TDLeft"),
            _p(e.page_ref or "—", "TD"),
        ]
        for e in ctx.lot
    ]

    col_w = [2.5 * cm, _USABLE_W - 2.5 * cm - 1.5 * cm, 1.5 * cm]
    tbl = Table(header + rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(_list_table_style(len(rows)))
    story.append(tbl)
    story.append(PageBreak())
    return story


# ── Daftar Gambar ─────────────────────────────────────────────────────────────
def build_lof_section(ctx: NumberingContext) -> list[Any]:
    """Return flowables halaman Daftar Gambar."""
    story: list[Any] = []

    if not ctx.lof:
        return story

    story.append(_p("<b>DAFTAR GAMBAR</b>", "H1"))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=P.NAVY, spaceAfter=4 * mm))

    header = [
        [
            _p("<b>Nomor</b>", "TH"),
            _p("<b>Judul Gambar</b>", "TH"),
            _p("<b>Hal.</b>", "TH"),
        ]
    ]
    rows = [
        [
            _p(e.number, "TD"),
            _p(e.caption, "TDLeft"),
            _p(e.page_ref or "—", "TD"),
        ]
        for e in ctx.lof
    ]

    col_w = [2.5 * cm, _USABLE_W - 2.5 * cm - 1.5 * cm, 1.5 * cm]
    tbl = Table(header + rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(_list_table_style(len(rows)))
    story.append(tbl)
    story.append(PageBreak())
    return story


# ── TableStyle helper ─────────────────────────────────────────────────────────
def _list_table_style(n_data_rows: int) -> TableStyle:
    row_colors = []
    for i in range(n_data_rows):
        bg = P.TABLE_ALT if i % 2 == 1 else P.WHITE
        row_colors.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))

    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), P.TABLE_HEAD),
        ("TEXTCOLOR",     (0, 0), (-1, 0), P.WHITE),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("ALIGN",         (1, 0), (1, -1), "LEFT"),
        ("ALIGN",         (2, 0), (2, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID",          (0, 0), (-1, -1), 0.4, P.LINE_GRAY),
        *row_colors,
    ])
