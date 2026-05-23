"""
BAB 3 — Dasar Perencanaan
===========================
3.1 Peraturan dan Standar
3.2 Metode Analisis
3.3 Asumsi Perencanaan
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, p, spacer, numbered_table, note,
)


def build_s03(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 3, "DASAR PERENCANAAN")

    # ── 3.1 Peraturan dan Standar ─────────────────────────────────────────
    story += h2(ctx, "Peraturan dan Standar yang Digunakan")

    is_concrete = data.calc_type == "concrete_beam"
    is_steel    = data.calc_type == "steel_beam"

    sni_rows = [
        [config.sni_load,
         "Tata Cara Pembebanan Minimum untuk Perancangan Bangunan Gedung"],
    ]
    if is_concrete or not data.calc_type:
        sni_rows.append([
            config.sni_concrete,
            "Persyaratan Beton Struktural untuk Bangunan Gedung",
        ])
    if is_steel or not data.calc_type:
        sni_rows.append([
            config.sni_steel,
            "Spesifikasi untuk Bangunan Gedung Baja Struktural",
        ])
    sni_rows += [
        [config.sni_quake,
         "Tata Cara Perencanaan Ketahanan Gempa untuk Struktur Bangunan Gedung"],
        ["AISC 360-16",
         "Specification for Structural Steel Buildings (referensi tambahan)"],
        ["ACI 318-19",
         "Building Code Requirements for Structural Concrete (referensi tambahan)"],
    ]

    story += numbered_table(
        ctx,
        "Peraturan dan Standar Perencanaan",
        ["Nomor SNI / Kode", "Judul"],
        sni_rows,
        col_widths=[4.5 * cm, None],
        col_align=["LEFT", "LEFT"],
    )

    # ── 3.2 Metode Analisis ───────────────────────────────────────────────
    story += h2(ctx, "Metode Analisis")
    story.append(p(
        "Analisis struktur dilakukan dengan metode <b>Elastis Linier</b> "
        "menggunakan asumsi balok sederhana (simply supported beam) dengan "
        "beban merata seragam (Uniformly Distributed Load / UDL). "
        "Kombinasi beban mengikuti kaidah LRFD (Load and Resistance Factor Design)."
    ))
    story.append(p(
        "Perhitungan gaya dalam (momen lentur dan gaya geser) diperoleh dari "
        "persamaan mekanika klasik untuk balok statis tertentu. "
        "Kontrol kapasitas penampang dilakukan terhadap seluruh kombinasi "
        "pembebanan terfaktor yang menghasilkan gaya dalam terbesar."
    ))

    # ── 3.3 Asumsi Perencanaan ────────────────────────────────────────────
    story += h2(ctx, "Asumsi Perencanaan")
    story.append(p("Asumsi yang digunakan dalam perencanaan ini adalah:"))
    story.append(p(
        "a) Balok diasumsikan sebagai elemen lentur satu dimensi (1D);<br/>"
        "b) Distribusi beban dianggap seragam (UDL) sepanjang bentang;<br/>"
        "c) Kondisi tumpuan: sendi di ujung kiri, rol di ujung kanan;<br/>"
        "d) Material berperilaku linier elastis dalam kondisi layan;<br/>"
        "e) Efek P-delta dan perubahan geometri diabaikan;<br/>"
        "f) Balok tidak memiliki gaya aksial signifikan;<br/>"
        "g) Pengaruh susut dan rangkak tidak diperhitungkan secara eksplisit."
    ))
    story.append(note(
        "Asumsi-asumsi di atas sesuai dengan ruang lingkup analisis "
        "yang didukung oleh AG-SAS pada versi ini."
    ))

    story.append(spacer(4))
    return story
