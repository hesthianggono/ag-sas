"""
BAB 11 — Gambar Teknik (dan Lampiran)
=======================================
11.1 Gambar Teknik (embed dari FigureSnapshot / build on-the-fly)
Lampiran A — Referensi Tabel Material (opsional)
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm, mm
from reportlab.platypus import PageBreak, Paragraph, Spacer, HRFlowable

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import h1, h2, p, spacer, note, numbered_table
from app.reporting.full_report.figure_embedder import embed_figure
from app.reporting.full_report.template import P, build_styles

_S = build_styles()


def build_s11(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 11, "GAMBAR TEKNIK")

    story.append(p(
        "Bagian ini memuat gambar teknik hasil analisis struktur yang "
        "dihasilkan secara otomatis oleh sistem AG-SAS dari data perhitungan."
    ))

    figure_snaps = data.figure_snapshots or []

    if figure_snaps:
        # Gunakan gambar yang sudah di-generate dan disimpan
        visible = sorted(
            [f for f in figure_snaps if getattr(f, "is_visible", True)],
            key=lambda f: getattr(f, "order_index", 0),
        )
        if not visible:
            story.append(note("Tidak ada gambar yang aktif (is_visible = True)."))
        else:
            for snap in visible:
                png_bytes = getattr(snap, "png_data", None)
                caption   = getattr(snap, "caption", "") or getattr(snap, "title", "Gambar")
                if png_bytes:
                    story += embed_figure(ctx, png_bytes, caption)
    elif config.include_figures:
        # Generate on-the-fly
        try:
            from app.reporting.figures.figure_builder import build_figures_for_calc
            specs = build_figures_for_calc(
                calc_type=data.calc_type,
                input_data=data.input_data,
                output_data=data.output_data,
                calc_title=data.calc_title,
                section="11",
                deform_scale=config.deform_scale,
            )
            for spec in specs:
                story += embed_figure(ctx, spec.png_bytes, spec.title)
        except Exception as e:
            story.append(note(f"Gambar tidak dapat di-generate: {e}"))
    else:
        story.append(note("Pembuatan gambar teknik dinonaktifkan dalam konfigurasi laporan."))

    # ── Lampiran A — Tabel Referensi ──────────────────────────────────────
    if config.show_appendix:
        story += _build_appendix_a(ctx, config, data)

    return story


def _build_appendix_a(ctx, config, data) -> list[Any]:
    story: list[Any] = []
    story.append(PageBreak())

    label = ctx.appendix("Tabel Referensi Material")
    story.append(Paragraph(f"<b>{label}</b>", _S["H1"]))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=P.NAVY, spaceAfter=4 * mm))

    # Tabel fc → Ec
    story.append(p(
        "Tabel berikut berisi nilai modulus elastisitas beton (Ec) untuk "
        "berbagai mutu beton sesuai SNI 2847:2019 Ps. 19.2.2.1."
    ))
    import math
    fc_vals = [17, 20, 25, 28, 30, 35, 40, 45, 50]
    story += [
        Paragraph("<b>" + ctx.appendix_table("Modulus Elastisitas Beton (Ec)") + "</b>",
                  _S["TableCaption"])
    ]

    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    from app.reporting.full_report.template import P as _P

    header = [["f'c (MPa)", "Ec = 4700√f'c (MPa)", "fr = 0,62√f'c (MPa)"]]
    rows   = [
        [f"{fc}", f"{4700*math.sqrt(fc):,.0f}", f"{0.62*math.sqrt(fc):.2f}"]
        for fc in fc_vals
    ]
    tbl = Table(header + rows, colWidths=[4 * cm, 6 * cm, 6 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), _P.TABLE_HEAD),
        ("TEXTCOLOR",     (0, 0), (-1, 0), _P.WHITE),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID",          (0, 0), (-1, -1), 0.4, _P.LINE_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_P.WHITE, _P.TABLE_ALT]),
    ]))
    story.append(tbl)
    story.append(spacer(6))

    return story
