"""
Section Builder Base — AG-SAS Full Report
==========================================
Kelas dasar dan helper yang digunakan oleh semua section builder (s01–s11).

Setiap section builder adalah fungsi:
    build_sXX(ctx: NumberingContext, config: FullReportConfig, data: FullReportData)
        → list[Flowable]

Helper tersedia via modul ini agar tidak duplikasi kode.
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.template import (
    FBOLD, FREG, FITAL, P, PAGE_W, MARGIN_L, MARGIN_R, build_styles,
)

_S = build_styles()
USABLE_W = PAGE_W - MARGIN_L - MARGIN_R


# ── Shortcut paragraf ─────────────────────────────────────────────────────────
def p(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, _S[style])


def h1(ctx: NumberingContext, num: int, title: str) -> list[Any]:
    """Judul bab (chapter heading) + garis bawah."""
    label = ctx.chapter(num, title)
    return [
        PageBreak(),
        Spacer(1, 4 * mm),
        p(f"<b>{label}</b>", "H1"),
        HRFlowable(width="100%", thickness=1.5, color=P.NAVY, spaceAfter=4 * mm),
    ]


def h2(ctx: NumberingContext, title: str) -> list[Any]:
    label = ctx.subchapter(title)
    return [
        Spacer(1, 2 * mm),
        p(f"<b>{label}</b>", "H2"),
    ]


def h3(ctx: NumberingContext, title: str) -> list[Any]:
    label = ctx.subsubchapter(title)
    return [p(f"<b>{label}</b>", "H3")]


def spacer(h_mm: float = 4) -> Spacer:
    return Spacer(1, h_mm * mm)


def hr(thickness: float = 0.5) -> HRFlowable:
    return HRFlowable(width="100%", thickness=thickness,
                      color=P.LINE_GRAY, spaceAfter=3 * mm)


def note(text: str) -> Paragraph:
    return p(f"<i>Catatan: {text}</i>", "Note")


def warning(text: str) -> Paragraph:
    return p(f"<b>⚠ {text}</b>", "Warning")


def ok_text(text: str) -> Paragraph:
    return p(f"<b>✓ {text}</b>", "OK")


# ── Tabel bernomor ────────────────────────────────────────────────────────────
def numbered_table(
    ctx: NumberingContext,
    caption_text: str,
    header_row: list[str],
    data_rows: list[list[Any]],
    col_widths: list[float] | None = None,
    *,
    col_align: list[str] | None = None,
    footnote: str | None = None,
) -> list[Any]:
    """
    Buat tabel ReportLab bernomor otomatis.

    Urutan flowables:
      1. Caption "Tabel X.Y  ..."
      2. Table (dengan header biru tua + stripe)
      3. Footnote opsional
    """
    caption_full = ctx.table(caption_text)

    aligns = col_align or ["CENTER"] * len(header_row)

    header = [[p(f"<b>{h}</b>", "TH") for h in header_row]]
    rows = []
    for raw_row in data_rows:
        styled = []
        for i, cell in enumerate(raw_row):
            align_style = "TDRight" if aligns[i] == "RIGHT" else (
                          "TDLeft" if aligns[i] == "LEFT" else "TD")
            if isinstance(cell, str):
                styled.append(p(cell, align_style))
            else:
                styled.append(cell)
        rows.append(styled)

    n = len(header_row)
    cw = col_widths or [USABLE_W / n] * n

    row_colors = []
    for i in range(len(rows)):
        if i % 2 == 1:
            row_colors.append(("BACKGROUND", (0, i + 1), (-1, i + 1), P.TABLE_ALT))

    tbl = Table(header + rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), P.TABLE_HEAD),
        ("TEXTCOLOR",     (0, 0), (-1, 0), P.WHITE),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, P.LINE_GRAY),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.0, P.NAVY),
        *row_colors,
        *[("ALIGN", (i, 1), (i, -1), aligns[i]) for i in range(n)],
    ]))

    flowables: list[Any] = [
        p(caption_full, "TableCaption"),
        tbl,
    ]
    if footnote:
        flowables.append(p(f"<i>{footnote}</i>", "Note"))
    flowables.append(spacer(4))
    return flowables


# ── Pasangan label–nilai (dua kolom) ─────────────────────────────────────────
def kv_table(
    rows: list[tuple[str, str]],
    col_widths: tuple[float, float] = (5.5 * cm, None),
) -> Table:
    """
    Tabel sederhana dua kolom: label (tebal) | nilai.
    Berguna untuk ringkasan parameter input/output.
    """
    cw2 = col_widths[1] or (USABLE_W - col_widths[0])
    data = [
        [p(f"<b>{k}</b>", "TDLeft"), p(v, "TDLeft")]
        for k, v in rows
    ]
    tbl = Table(data, colWidths=[col_widths[0], cw2])
    tbl.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.3, P.LINE_GRAY),
    ]))
    return tbl


# ── Status cell (OK / NG) ─────────────────────────────────────────────────────
def status_cell(ok: bool, label_ok: str = "OK", label_ng: str = "TIDAK OK") -> Paragraph:
    if ok:
        return p(f'<font color="{P.GREEN.hexval()}"><b>{label_ok}</b></font>', "TD")
    return p(f'<font color="{P.RED.hexval()}"><b>{label_ng}</b></font>', "TD")


def status_label(ok: bool) -> str:
    return (f'<font color="{P.GREEN.hexval()}"><b>✓ OK</b></font>'
            if ok else
            f'<font color="{P.RED.hexval()}"><b>✗ TIDAK OK</b></font>')
