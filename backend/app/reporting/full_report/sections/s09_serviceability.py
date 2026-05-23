"""
BAB 9 — Kemampuan Layan (Serviceability)
==========================================
9.1 Kontrol Lendutan
9.2 Kontrol Retak (khusus beton)
"""
from __future__ import annotations

import math
from typing import Any

from reportlab.lib.units import cm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, h3, p, spacer, kv_table, numbered_table,
    note, warning, ok_text, status_label,
)


def build_s09(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 9, "KEMAMPUAN LAYAN")

    inp = data.input_data  or {}
    out = data.output_data or {}

    L  = float(inp.get("span_m", 0.0))
    is_concrete = data.calc_type == "concrete_beam"
    is_steel    = data.calc_type == "steel_beam"

    # ── 9.1 Kontrol Lendutan ─────────────────────────────────────────────
    story += h2(ctx, "Kontrol Lendutan")

    delta_actual = float(out.get("deflection_mm") or out.get("delta_mm") or 0.0)
    delta_allow  = float(out.get("delta_allow_mm") or (L * 1000 / 360 if L > 0 else 0.0))
    ok_defl      = delta_actual <= delta_allow if delta_allow > 0 else None

    story.append(p(
        f"Lendutan maksimum diperiksa sesuai {config.sni_load} terhadap "
        f"batas lendutan izin. Untuk balok dengan beban hidup, batas lendutan "
        f"umumnya adalah <b>L/360</b>."
    ))

    if L > 0:
        story.append(p(
            f"Batas lendutan izin: δ_izin = L/360 = "
            f"{L*1000:.0f} / 360 = <b>{delta_allow:.1f} mm</b>"
        ))

    eq_d = ctx.equation()
    story.append(p(
        f"Lendutan elastik maksimum (beban layanan):   "
        f"δ = 5wL⁴/(384EI)   {eq_d}",
        "Equation"
    ))

    defl_rows = [
        ["Lendutan aktual",  "δ",      f"{delta_actual:.2f}", "mm"],
        ["Lendutan izin",    "δ_izin", f"{delta_allow:.2f}",  "mm"],
        ["Rasio δ/δ_izin",  "—",      f"{delta_actual/delta_allow:.3f}" if delta_allow > 0 else "—", "—"],
        ["Status",          "—",      status_label(ok_defl if ok_defl is not None else True), "—"],
    ]
    story += numbered_table(
        ctx,
        "Kontrol Lendutan",
        ["Parameter", "Simbol", "Nilai", "Satuan"],
        defl_rows,
        col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
        col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
    )

    if ok_defl is False:
        story.append(warning(
            f"Lendutan MELAMPAUI BATAS: δ = {delta_actual:.2f} mm > δ_izin = {delta_allow:.2f} mm"
        ))
    elif ok_defl:
        story.append(ok_text(
            f"Lendutan memenuhi syarat: δ = {delta_actual:.2f} mm ≤ δ_izin = {delta_allow:.2f} mm"
        ))

    # ── 9.2 Kontrol Retak (beton saja) ────────────────────────────────────
    if is_concrete:
        story += h2(ctx, "Kontrol Retak")
        story.append(p(
            f"Kontrol lebar retak dilakukan sesuai {config.sni_concrete} "
            f"Pasal 24.3. Lebar retak izin untuk kondisi lingkungan normal "
            f"adalah <b>w_izin = 0,40 mm</b> (interior) atau <b>0,33 mm</b> (eksterior)."
        ))

        w_crack  = float(out.get("crack_width_mm") or 0.0)
        w_allow  = 0.40
        ok_crack = w_crack <= w_allow if w_crack > 0 else None

        if w_crack > 0:
            crack_rows = [
                ["Lebar retak aktual",  "w",      f"{w_crack:.3f}", "mm"],
                ["Lebar retak izin",    "w_izin", f"{w_allow:.2f}", "mm"],
                ["Status",             "—",      status_label(ok_crack if ok_crack is not None else True), "—"],
            ]
            story += numbered_table(
                ctx,
                "Kontrol Lebar Retak",
                ["Parameter", "Simbol", "Nilai", "Satuan"],
                crack_rows,
                col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
                col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
            )
            if ok_crack is False:
                story.append(warning(
                    f"Lebar retak MELAMPAUI BATAS: w = {w_crack:.3f} mm > w_izin = {w_allow:.2f} mm"
                ))
            elif ok_crack:
                story.append(ok_text(
                    f"Lebar retak memenuhi syarat: w = {w_crack:.3f} mm ≤ w_izin = {w_allow:.2f} mm"
                ))
        else:
            story.append(note(
                "Data lebar retak tidak tersedia dalam output perhitungan ini."
            ))

    story.append(spacer(4))
    return story
