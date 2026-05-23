"""
BAB 4 — Material
==================
4.1 Material Beton (untuk concrete_beam)
4.2 Material Baja Tulangan (untuk concrete_beam)
4.3 Material Baja Profil (untuk steel_beam)
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


def build_s04(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 4, "SPESIFIKASI MATERIAL")

    inp = data.input_data or {}
    is_concrete = data.calc_type == "concrete_beam"
    is_steel    = data.calc_type == "steel_beam"

    # ── 4.1 Beton ─────────────────────────────────────────────────────────
    if is_concrete:
        story += h2(ctx, "Beton Struktural")

        fc = inp.get("fc_mpa", 25.0)
        # Turunan dari fc
        wc    = 2400.0          # kg/m³ normal weight
        Ec    = 4700 * math.sqrt(fc)  # MPa (SNI 2847:2019 Ps. 19.2.2.1)
        fr    = 0.62 * math.sqrt(fc)  # MPa modulus of rupture
        beta1 = 0.85 - 0.05 * max(0, (fc - 28) / 7)
        beta1 = max(0.65, min(0.85, beta1))
        eps_u = 0.003

        story.append(p(
            f"Material beton yang digunakan adalah beton normal ({wc:.0f} kg/m³) "
            f"dengan kuat tekan silinder rencana <b>f'c = {fc:.0f} MPa</b> "
            f"sesuai {config.sni_concrete}."
        ))

        story += numbered_table(
            ctx,
            "Properti Material Beton",
            ["Parameter", "Simbol", "Nilai", "Satuan"],
            [
                ["Kuat tekan silinder",         "f'c",   f"{fc:.1f}",       "MPa"],
                ["Berat jenis beton normal",     "wc",    f"{wc:.0f}",       "kg/m³"],
                ["Modulus elastisitas",          "Ec",    f"{Ec:,.0f}",      "MPa"],
                ["Modulus of rupture",           "fr",    f"{fr:.2f}",       "MPa"],
                ["Faktor blok tegangan (β₁)",    "β₁",    f"{beta1:.3f}",    "—"],
                ["Regangan tekan ultimit",       "εcu",   "0.003",           "—"],
            ],
            col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
            col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
        )

    # ── 4.2 Baja Tulangan ─────────────────────────────────────────────────
    if is_concrete:
        story += h2(ctx, "Baja Tulangan")

        fy  = inp.get("fy_mpa", 420.0)
        fyt = inp.get("fyt_mpa", fy)
        Es  = 200_000.0
        eps_y = fy / Es

        story.append(p(
            f"Baja tulangan lentur menggunakan baja ulir (deformed) mutu "
            f"<b>fy = {fy:.0f} MPa</b>. "
            f"Baja tulangan geser menggunakan mutu <b>fyt = {fyt:.0f} MPa</b>."
        ))

        story += numbered_table(
            ctx,
            "Properti Material Baja Tulangan",
            ["Parameter", "Simbol", "Nilai", "Satuan"],
            [
                ["Kuat leleh tulangan lentur",  "fy",    f"{fy:.0f}",        "MPa"],
                ["Kuat leleh tulangan geser",   "fyt",   f"{fyt:.0f}",       "MPa"],
                ["Modulus elastisitas baja",    "Es",    f"{Es:,.0f}",       "MPa"],
                ["Regangan leleh (fy/Es)",      "εy",    f"{eps_y:.4f}",     "—"],
            ],
            col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
            col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
        )

    # ── 4.3 Baja Profil ───────────────────────────────────────────────────
    if is_steel:
        story += h2(ctx, "Baja Profil Struktural")

        fy   = inp.get("fy_mpa", 250.0)
        fu   = inp.get("fu_mpa", 410.0)
        Es   = 200_000.0
        G    = 77_000.0
        eps_y = fy / Es

        story.append(p(
            f"Baja profil struktural yang digunakan adalah baja mutu "
            f"<b>BJ {int(fu)} (fy = {fy:.0f} MPa, fu = {fu:.0f} MPa)</b> "
            f"sesuai SNI atau setara ASTM A36 / A572."
        ))

        story += numbered_table(
            ctx,
            "Properti Material Baja Profil",
            ["Parameter", "Simbol", "Nilai", "Satuan"],
            [
                ["Kuat leleh",              "fy",  f"{fy:.0f}",    "MPa"],
                ["Kuat tarik putus",        "fu",  f"{fu:.0f}",    "MPa"],
                ["Modulus elastisitas",     "E",   f"{Es:,.0f}",   "MPa"],
                ["Modulus geser",           "G",   f"{G:,.0f}",    "MPa"],
                ["Regangan leleh",          "εy",  f"{eps_y:.4f}", "—"],
                ["Rasio Poisson",           "ν",   "0.30",         "—"],
            ],
            col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
            col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
        )

    if not is_concrete and not is_steel:
        story.append(p(
            "Spesifikasi material tidak tersedia — tipe kalkulasi tidak dikenali.",
            "Note"
        ))

    story.append(spacer(4))
    return story
