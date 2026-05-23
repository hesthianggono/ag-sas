"""
Report Builder — AG-SAS Full Report
=====================================
Orkestrasi semua section builder untuk menghasilkan laporan lengkap.

Urutan render:
  1. Cover
  2. TOC (diisi setelah semua section, jadi di-inject setelah render)
  3. Daftar Tabel
  4. Daftar Gambar
  5. Bab 1–11 + Lampiran
"""
from __future__ import annotations

import io
from typing import Any

from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.template import (
    MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B,
    HEADER_H, FOOTER_H,
    PAGE_W, PAGE_H,
    DocMeta, build_doc,
    make_header_footer_cb,
    make_cover_cb,
)
from app.reporting.full_report.cover import build_cover
from app.reporting.full_report.toc import (
    build_toc_section, build_lot_section, build_lof_section,
)
from app.reporting.full_report.sections import (
    build_s01, build_s02, build_s03, build_s04, build_s05,
    build_s06, build_s07, build_s08, build_s09, build_s10,
    build_s11,
)


def build_full_report(
    config: FullReportConfig,
    data: FullReportData,
) -> bytes:
    """
    Render laporan rekayasa lengkap dan return PDF bytes.

    Parameters
    ----------
    config : FullReportConfig  — metadata, opsi, engineer info
    data   : FullReportData    — data kalkulasi (input + output + figures)

    Returns
    -------
    bytes  — PDF raw bytes siap disimpan / dikirim ke client
    """
    buf = io.BytesIO()

    # ── Metadata PDF ──────────────────────────────────────────────────────
    meta = DocMeta(
        project_title  = config.project_name or config.report_title,
        doc_number     = config.doc_number,
        revision       = config.revision,
        company_name   = config.company_name,
        status         = config.status,
        show_watermark = config.show_watermark,
    )

    doc_info = {
        "title":   config.report_title,
        "author":  config.company_name,
        "subject": f"Laporan Struktur — {config.project_name}",
    }
    doc = build_doc(buf, doc_info)

    # ── PageTemplates ─────────────────────────────────────────────────────
    # Ukuran frame (area konten = A4 dikurangi margin + header + footer)
    frame_x  = MARGIN_L
    frame_y  = MARGIN_B + FOOTER_H + 4 * mm
    frame_w  = PAGE_W - MARGIN_L - MARGIN_R
    frame_h  = PAGE_H - MARGIN_T - MARGIN_B - HEADER_H - FOOTER_H - 8 * mm

    normal_frame = Frame(frame_x, frame_y, frame_w, frame_h,
                         leftPadding=0, rightPadding=0,
                         topPadding=0, bottomPadding=0)

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)

    normal_tmpl = PageTemplate(
        id="normal",
        frames=[normal_frame],
        onPage=make_header_footer_cb(meta),
    )
    cover_tmpl = PageTemplate(
        id="cover",
        frames=[cover_frame],
        onPage=make_cover_cb(meta),
    )
    doc.addPageTemplates([cover_tmpl, normal_tmpl])

    # ── Numbering context ─────────────────────────────────────────────────
    ctx = NumberingContext()

    # ── Build story: all content sections first ───────────────────────────
    # (TOC diisi setelah ctx.toc terisi dari section builders)
    content_story: list[Any] = []

    content_story += build_s01(ctx, config, data)
    content_story += build_s02(ctx, config, data)
    content_story += build_s03(ctx, config, data)
    content_story += build_s04(ctx, config, data)
    content_story += build_s05(ctx, config, data)
    content_story += build_s06(ctx, config, data)
    content_story += build_s07(ctx, config, data)
    content_story += build_s08(ctx, config, data)
    content_story += build_s09(ctx, config, data)
    content_story += build_s10(ctx, config, data)
    content_story += build_s11(ctx, config, data)

    # ── Front matter (setelah ctx terisi) ─────────────────────────────────
    front_story: list[Any] = []
    front_story += build_cover(config)
    front_story += build_toc_section(ctx)
    front_story += build_lot_section(ctx)
    front_story += build_lof_section(ctx)

    # ── Gabungkan & render ─────────────────────────────────────────────────
    full_story = front_story + content_story
    doc.build(full_story)

    return buf.getvalue()
