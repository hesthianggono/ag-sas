"""
BAB 5 — Pembebanan
====================
5.1 Beban Rencana
5.2 Kombinasi Pembebanan
5.3 Beban Terfaktor
"""
from __future__ import annotations

from typing import Any

from reportlab.lib.units import cm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, p, spacer, kv_table, numbered_table, note,
)


def build_s05(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 5, "PEMBEBANAN")

    inp  = data.input_data  or {}
    out  = data.output_data or {}

    # Ambil nilai dari input
    DL    = float(inp.get("dead_load_kn_m",  0.0))
    LL    = float(inp.get("live_load_kn_m",  0.0))
    SDL   = float(inp.get("super_dead_kn_m", 0.0))
    total_unfact = DL + SDL + LL

    # Beban terfaktor dari output (atau hitung sendiri)
    wu    = float(out.get("wu_kn_m") or out.get("wu") or (1.2*(DL+SDL) + 1.6*LL))
    # Kombinasi dominan
    wu_12_16 = 1.2 * (DL + SDL) + 1.6 * LL
    wu_14    = 1.4 * (DL + SDL)

    # ── 5.1 Beban Rencana ─────────────────────────────────────────────────
    story += h2(ctx, "Beban Rencana")
    story.append(p(
        f"Beban yang bekerja pada elemen struktur ini adalah beban gravitasi "
        f"yang dianggap terdistribusi merata (UDL) sepanjang bentang, "
        f"sesuai {config.sni_load}."
    ))

    load_rows = [
        ["Beban Mati (DL)",          f"{DL:.2f}",   "kN/m", "Berat sendiri elemen dan finishes"],
        ["Beban Mati Tambahan (SDL)", f"{SDL:.2f}",  "kN/m", "Beban permanen non-struktural"],
        ["Beban Hidup (LL)",          f"{LL:.2f}",   "kN/m", "Beban pengguna sesuai fungsi"],
        ["Total Beban Layanan",       f"{total_unfact:.2f}", "kN/m", "DL + SDL + LL"],
    ]
    story += numbered_table(
        ctx,
        "Beban Rencana",
        ["Jenis Beban", "Nilai", "Satuan", "Keterangan"],
        load_rows,
        col_widths=[4.5 * cm, 2.2 * cm, 2.0 * cm, None],
        col_align=["LEFT", "RIGHT", "CENTER", "LEFT"],
    )

    # ── 5.2 Kombinasi Pembebanan ──────────────────────────────────────────
    story += h2(ctx, "Kombinasi Pembebanan (LRFD)")
    story.append(p(
        f"Kombinasi beban terfaktor dihitung sesuai {config.sni_load} Pasal 2.3 "
        f"dengan metode LRFD:"
    ))

    comb_rows = [
        ["Kombinasi 1", "1,4 (DL + SDL)",            f"{wu_14:.2f}",    "kN/m"],
        ["Kombinasi 2", "1,2 (DL + SDL) + 1,6 LL",   f"{wu_12_16:.2f}", "kN/m"],
    ]
    story += numbered_table(
        ctx,
        "Kombinasi Pembebanan Terfaktor",
        ["Kombinasi", "Rumus", "wu", "Satuan"],
        comb_rows,
        col_widths=[3.0 * cm, 6.5 * cm, 2.5 * cm, 2.0 * cm],
        col_align=["CENTER", "LEFT", "RIGHT", "CENTER"],
    )

    # ── 5.3 Beban Terfaktor Desain ────────────────────────────────────────
    story += h2(ctx, "Beban Terfaktor untuk Desain")
    story.append(p(
        f"Beban terfaktor yang digunakan untuk desain adalah nilai terbesar "
        f"dari kombinasi di atas:"
    ))
    story.append(p(
        f"<b>wu = {wu:.2f} kN/m</b>  "
        f"(Kombinasi {'2' if wu_12_16 >= wu_14 else '1'} menentukan)"
    ))
    story.append(note(
        "Kombinasi beban gempa tidak diperhitungkan dalam analisis ini "
        "karena elemen yang dianalisis adalah balok interior yang tidak "
        "menjadi bagian sistem penahan gaya lateral."
    ))

    story.append(spacer(4))
    return story
