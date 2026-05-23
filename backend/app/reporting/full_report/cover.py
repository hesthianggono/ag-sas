"""
Cover Page — AG-SAS Full Report
=================================
Menghasilkan halaman cover profesional format laporan konsultan Indonesia.

Layout (atas → bawah):
  - Band biru tua (via canvas callback)
  - Logo / nama perusahaan (putih di atas band)
  - [Spasi]
  - Judul laporan (besar, biru)
  - Subjudul / tipe laporan
  - Garis pemisah
  - Tabel info: Proyek, Lokasi, Nomor Laporan, Tanggal, Revisi
  - Tabel engineer (opsional): nama, jabatan, SKK
  - [Spasi]
  - Band bawah (via canvas, lihat template.py)
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from reportlab.lib.units import cm, mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    HRFlowable, NextPageTemplate, PageBreak, Paragraph, Spacer, Table,
    TableStyle,
)

from app.reporting.full_report.template import (
    FBDIT, FBOLD, FITAL, FREG, P, build_styles,
)

_S = build_styles()


def _p(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, _S[style])


def build_cover(config) -> list[Any]:
    """
    Hasilkan flowables halaman cover.

    config: FullReportConfig (lihat report_snapshot.py)
    """
    story: list[Any] = []

    # Ganti ke PageTemplate "cover" (tanpa header/footer normal)
    story.append(NextPageTemplate("cover"))

    # Band biru tua sudah digambar via canvas callback — cukup spacer
    # untuk mendorong konten ke bawah band atas (5.5 cm)
    story.append(Spacer(1, 6.0 * cm))

    # ── Teks di atas band (ditulis dengan warna putih) ─────────────────────
    story.append(_p(
        f'<font color="white"><b>{config.company_name}</b></font>',
        "DocTitle"
    ))
    story.append(_p(
        '<font color="white">Konsultan Struktur &amp; Rekayasa Sipil</font>',
        "DocSubtitle"
    ))

    story.append(Spacer(1, 3.0 * cm))

    # ── Judul laporan ──────────────────────────────────────────────────────
    story.append(_p(config.report_title, "DocTitle"))
    story.append(_p(config.report_subtitle or "Laporan Perhitungan Struktur", "DocSubtitle"))

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="90%", thickness=1.5,
                             color=P.NAVY, spaceAfter=6 * mm))

    # ── Tabel informasi proyek ─────────────────────────────────────────────
    info_data = [
        ["Nama Proyek",  ":", config.project_name or "—"],
        ["Lokasi",       ":", config.project_location or "—"],
        ["Pemilik",      ":", config.owner or "—"],
        ["No. Dokumen",  ":", config.doc_number],
        ["Tanggal",      ":", _fmt_date(config.report_date)],
        ["Revisi",       ":", config.revision],
        ["Status",       ":", config.status],
    ]
    info_rows = [
        [
            _p(f"<b>{r[0]}</b>", "CoverMetaBold"),
            _p(r[1], "CoverMeta"),
            _p(r[2], "CoverMeta"),
        ]
        for r in info_data
    ]

    info_table = Table(
        info_rows,
        colWidths=[4.5 * cm, 0.5 * cm, 9.5 * cm],
        hAlign="CENTER",
    )
    info_table.setStyle(TableStyle([
        ("ALIGN",     (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",    (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)

    # ── Tabel engineer (opsional) ──────────────────────────────────────────
    engineers = getattr(config, "engineers", None) or []
    if engineers:
        story.append(Spacer(1, 8 * mm))
        story.append(HRFlowable(width="90%", thickness=0.5,
                                 color=P.LINE_GRAY, spaceAfter=4 * mm))
        story.append(_p("<b>Disiapkan oleh:</b>", "CoverMetaBold"))
        story.append(Spacer(1, 3 * mm))

        eng_header = [
            [_p("<b>Nama</b>", "TH"), _p("<b>Jabatan</b>", "TH"), _p("<b>No. SKK</b>", "TH")],
        ]
        def _eng_val(e, key):
            if hasattr(e, key):
                return getattr(e, key) or "—"
            if isinstance(e, dict):
                return e.get(key) or "—"
            return "—"

        eng_rows = [
            [
                _p(_eng_val(e, "name"), "TD"),
                _p(_eng_val(e, "position"), "TD"),
                _p(_eng_val(e, "skk"), "TD"),
            ]
            for e in engineers
        ]
        eng_table = Table(
            eng_header + eng_rows,
            colWidths=[6.0 * cm, 5.0 * cm, 5.0 * cm],
            hAlign="CENTER",
        )
        eng_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), P.TABLE_HEAD),
            ("TEXTCOLOR",     (0, 0), (-1, 0), P.WHITE),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("GRID",          (0, 0), (-1, -1), 0.4, P.LINE_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [P.WHITE, P.TABLE_ALT]),
        ]))
        story.append(eng_table)

    # Pindah ke PageTemplate normal untuk halaman berikutnya
    story.append(NextPageTemplate("normal"))
    story.append(PageBreak())

    return story


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fmt_date(d) -> str:
    if d is None:
        return date.today().strftime("%d %B %Y")
    if isinstance(d, (date, datetime)):
        MONTHS_ID = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember",
        }
        return f"{d.day} {MONTHS_ID[d.month]} {d.year}"
    return str(d)
