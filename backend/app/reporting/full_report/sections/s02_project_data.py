"""
BAB 2 — Data Proyek
=====================
2.1 Identitas Proyek
2.2 Tim Perencana
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, p, spacer, kv_table, numbered_table,
)
from app.reporting.full_report.section_builder import USABLE_W
from app.reporting.full_report.template import P


def build_s02(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 2, "DATA PROYEK")

    # ── 2.1 Identitas Proyek ─────────────────────────────────────────────
    story += h2(ctx, "Identitas Proyek")

    from app.reporting.full_report.cover import _fmt_date  # reuse helper

    rows_kv = [
        ("Nama Proyek",      config.project_name or "—"),
        ("Lokasi Proyek",    config.project_location or "—"),
        ("Pemilik Proyek",   config.owner or "—"),
        ("Nomor Dokumen",    config.doc_number),
        ("Revisi",           config.revision),
        ("Status Dokumen",   config.status),
        ("Tanggal Laporan",  _fmt_date(config.report_date)),
    ]
    story.append(kv_table(rows_kv, col_widths=(5.5 * cm, None)))
    story.append(spacer(4))

    # ── 2.2 Tim Perencana ─────────────────────────────────────────────────
    story += h2(ctx, "Tim Perencana")

    engineers = config.engineers or []
    if engineers:
        story += numbered_table(
            ctx,
            "Daftar Tim Perencana",
            ["No.", "Nama", "Jabatan", "No. SKK"],
            [
                [str(i + 1), e.name, e.position or "—", e.skk or "—"]
                for i, e in enumerate(engineers)
            ],
            col_widths=[1.2 * cm, 5.5 * cm, 5.0 * cm, 4.3 * cm],
        )
    else:
        story.append(p(
            "Data tim perencana tidak disertakan dalam laporan ini.",
            "Note"
        ))

    story.append(spacer(4))
    return story
