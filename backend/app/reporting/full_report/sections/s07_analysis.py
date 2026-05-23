"""
BAB 7 — Analisis Struktur
===========================
7.1 Diagram Pembebanan
7.2 Reaksi Tumpuan
7.3 Diagram Gaya Geser
7.4 Diagram Momen Lentur
"""
from __future__ import annotations

import math
from typing import Any

from reportlab.lib.units import cm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, h3, p, spacer, kv_table, numbered_table, note,
)


def build_s07(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 7, "ANALISIS STRUKTUR")

    inp = data.input_data  or {}
    out = data.output_data or {}

    L  = float(inp.get("span_m", 0.0))
    DL = float(inp.get("dead_load_kn_m", 0.0))
    LL = float(inp.get("live_load_kn_m", 0.0))
    SDL= float(inp.get("super_dead_kn_m", 0.0))
    wu = float(out.get("wu_kn_m") or out.get("wu") or (1.2*(DL+SDL) + 1.6*LL))

    # Gaya dalam balok sederhana UDL
    RA = RB = wu * L / 2
    Vmax = RA
    Mmax = wu * L**2 / 8

    # ── 7.1 Persamaan Gaya Dalam ──────────────────────────────────────────
    story += h2(ctx, "Persamaan Gaya Dalam")
    story.append(p(
        f"Untuk balok sederhana dengan beban merata terfaktor "
        f"<b>wu = {wu:.2f} kN/m</b> dan bentang <b>L = {L:.2f} m</b>, "
        f"gaya dalam dihitung dengan persamaan berikut:"
    ))

    eq1 = ctx.equation()
    story.append(p(f"Reaksi tumpuan:   RA = RB = wu·L / 2   {eq1}", "Equation"))

    eq2 = ctx.equation()
    story.append(p(f"Gaya geser:   V(x) = wu·(L/2 − x)   {eq2}", "Equation"))

    eq3 = ctx.equation()
    story.append(p(f"Momen lentur:   M(x) = wu·x·(L − x) / 2   {eq3}", "Equation"))

    eq4 = ctx.equation()
    story.append(p(f"Momen maksimum (x = L/2):   Mu = wu·L² / 8   {eq4}", "Equation"))

    story.append(spacer(2))

    # ── 7.2 Reaksi Tumpuan ────────────────────────────────────────────────
    story += h2(ctx, "Reaksi Tumpuan")
    story += numbered_table(
        ctx,
        "Reaksi Tumpuan Terfaktor",
        ["Tumpuan", "Reaksi", "Nilai", "Satuan"],
        [
            ["A (kiri)",  "RA = wu·L/2",   f"{RA:.2f}",  "kN"],
            ["B (kanan)", "RB = wu·L/2",   f"{RB:.2f}",  "kN"],
            ["Total",     "RA + RB = wu·L", f"{RA+RB:.2f}", "kN"],
        ],
        col_widths=[3.0 * cm, 5.0 * cm, 3.5 * cm, 2.5 * cm],
        col_align=["CENTER", "LEFT", "RIGHT", "CENTER"],
    )
    story.append(p(
        f"Kontrol keseimbangan: RA + RB = {RA+RB:.2f} kN = "
        f"wu · L = {wu:.2f} × {L:.2f} = {wu*L:.2f} kN  ✓"
    ))

    # ── 7.3 Gaya Geser ────────────────────────────────────────────────────
    story += h2(ctx, "Diagram Gaya Geser")
    story.append(p(
        f"Gaya geser maksimum terjadi di tumpuan (x = 0 dan x = L), "
        f"dengan nilai:"
    ))
    story.append(p(
        f"<b>Vu,max = {Vmax:.2f} kN</b>  (di tumpuan A dan B)"
    ))
    story.append(p(f"Gaya geser di midspan (x = L/2) = 0 kN"))

    # ── 7.4 Momen Lentur ──────────────────────────────────────────────────
    story += h2(ctx, "Diagram Momen Lentur")
    story.append(p(
        f"Momen lentur maksimum terjadi di tengah bentang (x = L/2), "
        f"membentuk diagram parabolik dengan nilai:"
    ))
    story.append(p(
        f"<b>Mu,max = wu · L² / 8 = {wu:.2f} × {L:.2f}² / 8 = {Mmax:.2f} kN·m</b>"
    ))

    # Tabel ringkasan
    story += numbered_table(
        ctx,
        "Ringkasan Gaya Dalam Terfaktor",
        ["Lokasi", "Gaya Geser Vu (kN)", "Momen Mu (kN·m)"],
        [
            ["Tumpuan A (x = 0)",         f"{Vmax:.2f}",  "0.00"],
            ["Midspan (x = L/2)",         "0.00",         f"{Mmax:.2f}"],
            ["Tumpuan B (x = L)",         f"{-Vmax:.2f}", "0.00"],
            ["<b>Nilai Desain (maks)</b>", f"<b>{Vmax:.2f}</b>", f"<b>{Mmax:.2f}</b>"],
        ],
        col_widths=[5.5 * cm, 4.5 * cm, 4.0 * cm],
        col_align=["LEFT", "RIGHT", "RIGHT"],
    )

    story.append(spacer(4))
    return story
