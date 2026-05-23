"""
BAB 6 — Model Struktur
========================
6.1 Geometri Penampang
6.2 Kondisi Tumpuan
6.3 Parameter Penampang (momen inersia, section modulus, dll.)
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


def build_s06(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 6, "MODEL STRUKTUR")

    inp = data.input_data  or {}
    out = data.output_data or {}

    L = float(inp.get("span_m", 0.0))

    # ── 6.1 Geometri Bentang ──────────────────────────────────────────────
    story += h2(ctx, "Geometri dan Kondisi Tumpuan")
    story.append(p(
        f"Elemen yang dianalisis adalah <b>balok sederhana (simply supported)</b> "
        f"dengan panjang bentang bersih <b>L = {L:.2f} m</b>. "
        f"Tumpuan berupa sendi di ujung kiri (A) dan rol di ujung kanan (B)."
    ))

    story += numbered_table(
        ctx,
        "Parameter Geometri Bentang",
        ["Parameter", "Nilai", "Satuan"],
        [
            ["Panjang bentang", f"{L:.3f}", "m"],
            ["Jenis tumpuan kiri",  "Sendi (Pin)", "—"],
            ["Jenis tumpuan kanan", "Rol (Roller)", "—"],
            ["Model analisis", "Balok Statis Tertentu", "—"],
        ],
        col_widths=[6.0 * cm, 5.0 * cm, 3.0 * cm],
        col_align=["LEFT", "CENTER", "CENTER"],
    )

    # ── 6.2 Geometri Penampang ────────────────────────────────────────────
    story += h2(ctx, "Geometri Penampang")

    is_concrete = data.calc_type == "concrete_beam"
    is_steel    = data.calc_type == "steel_beam"

    if is_concrete:
        b   = float(inp.get("b_mm", 0.0))
        h_s = float(inp.get("h_mm", 0.0))
        cc  = float(inp.get("cover_mm", 40.0))
        # d efektif
        db_main = float(inp.get("main_bar_dia_mm", 19.0))
        d_eff   = h_s - cc - db_main / 2.0

        story.append(p(
            f"Penampang balok beton berbentuk persegi dengan lebar "
            f"<b>b = {b:.0f} mm</b> dan tinggi total <b>h = {h_s:.0f} mm</b>."
        ))
        story += numbered_table(
            ctx,
            "Dimensi Penampang Balok Beton",
            ["Parameter", "Simbol", "Nilai", "Satuan"],
            [
                ["Lebar penampang",          "b",   f"{b:.0f}",       "mm"],
                ["Tinggi total",             "h",   f"{h_s:.0f}",     "mm"],
                ["Selimut beton",            "cc",  f"{cc:.0f}",      "mm"],
                ["Tinggi efektif",           "d",   f"{d_eff:.1f}",   "mm"],
                ["Rasio tinggi/lebar (h/b)", "h/b", f"{h_s/b:.2f}",  "—"],
            ],
            col_widths=[5.5 * cm, 2.0 * cm, 3.5 * cm, 2.5 * cm],
            col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
        )

    elif is_steel:
        profile = inp.get("profile", {}) or {}
        A  = float(profile.get("A_mm2",  0.0))
        Ix = float(profile.get("Ix_mm4", 0.0))
        Sx = float(profile.get("Sx_mm3", 0.0))
        Zx = float(profile.get("Zx_mm3", 0.0))
        d_p  = float(profile.get("d_mm",  0.0))
        bf = float(profile.get("bf_mm", 0.0))
        tf = float(profile.get("tf_mm", 0.0))
        tw = float(profile.get("tw_mm", 0.0))
        name = inp.get("profile_name", "—")

        story.append(p(
            f"Penampang baja menggunakan profil <b>{name}</b> "
            f"(wide flange / H-beam)."
        ))
        rows_steel = [
            ["Nama profil",          "—",  name,               "—"],
            ["Luas penampang",       "A",  f"{A:,.0f}",        "mm²"],
            ["Tinggi profil",        "d",  f"{d_p:.1f}",       "mm"],
            ["Lebar flens",          "bf", f"{bf:.1f}",        "mm"],
            ["Tebal flens",          "tf", f"{tf:.1f}",        "mm"],
            ["Tebal badan",          "tw", f"{tw:.1f}",        "mm"],
            ["Momen inersia (Ix)",   "Ix", f"{Ix/1e6:.2f}×10⁶", "mm⁴"],
            ["Modulus elastis (Sx)", "Sx", f"{Sx/1e3:.1f}×10³",  "mm³"],
            ["Modulus plastis (Zx)", "Zx", f"{Zx/1e3:.1f}×10³",  "mm³"],
        ]
        story += numbered_table(
            ctx,
            f"Properti Penampang Profil {name}",
            ["Parameter", "Simbol", "Nilai", "Satuan"],
            rows_steel,
            col_widths=[5.5 * cm, 2.0 * cm, 4.5 * cm, 2.0 * cm],
            col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
        )

    story.append(spacer(4))
    return story
