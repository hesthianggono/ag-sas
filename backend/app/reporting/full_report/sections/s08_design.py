"""
BAB 8 — Perencanaan Penampang
================================
8.1 Kontrol Kapasitas Lentur
8.2 Kontrol Kapasitas Geser
8.3 Penulangan (untuk beton)
8.4 Kontrol Kompaktitas Profil (untuk baja)
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


def build_s08(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 8, "PERENCANAAN PENAMPANG")

    if data.calc_type == "concrete_beam":
        story += _concrete_design(ctx, config, data)
    elif data.calc_type == "steel_beam":
        story += _steel_design(ctx, config, data)
    else:
        story.append(p("Tipe kalkulasi tidak dikenali.", "Note"))

    story.append(spacer(4))
    return story


# ── Beton ─────────────────────────────────────────────────────────────────────
def _concrete_design(ctx, config, data) -> list[Any]:
    story: list[Any] = []
    inp = data.input_data  or {}
    out = data.output_data or {}

    fc   = float(inp.get("fc_mpa", 25.0))
    fy   = float(inp.get("fy_mpa", 420.0))
    fyt  = float(inp.get("fyt_mpa", fy))
    b    = float(inp.get("b_mm", 300.0))
    h_s  = float(inp.get("h_mm", 500.0))
    cc   = float(inp.get("cover_mm", 40.0))
    db_main = float(inp.get("main_bar_dia_mm", 19.0))
    d    = h_s - cc - db_main / 2.0

    # Gaya dalam dari output
    Mu   = float(out.get("Mu_kNm") or out.get("Mu") or 0.0)
    Vu   = float(out.get("Vu_kN")  or out.get("Vu")  or 0.0)

    # Kapasitas dari output (jika tersedia)
    phi_Mn = float(out.get("phi_Mn_kNm") or out.get("phi_Mn") or 0.0)
    phi_Vn = float(out.get("phi_Vn_kN")  or out.get("phi_Vn")  or 0.0)
    As_req = float(out.get("As_req_mm2") or out.get("As_req") or 0.0)
    As_prov= float(out.get("As_prov_mm2")or out.get("As_prov") or 0.0)

    # Fallback hitung manual jika output kosong
    beta1 = max(0.65, min(0.85, 0.85 - 0.05 * max(0, (fc - 28) / 7)))
    phi_b = 0.90
    phi_v = 0.75
    if phi_Mn == 0.0 and As_prov > 0:
        a  = As_prov * fy / (0.85 * fc * b)
        phi_Mn = phi_b * As_prov * fy * (d - a / 2) / 1e6
    if phi_Vn == 0.0:
        Vc = 0.17 * math.sqrt(fc) * b * d / 1000.0
        phi_Vn = phi_v * Vc

    ok_flex = phi_Mn >= Mu if phi_Mn > 0 else None
    ok_shear = phi_Vn >= Vu if phi_Vn > 0 else None
    ratio_flex  = Mu / phi_Mn  if phi_Mn > 0 else 0.0
    ratio_shear = Vu / phi_Vn  if phi_Vn > 0 else 0.0

    # ── 8.1 Kontrol Lentur ────────────────────────────────────────────────
    story += h2(ctx, "Kontrol Kapasitas Lentur")
    story.append(p(
        f"Kapasitas lentur nominal dihitung berdasarkan {config.sni_concrete} "
        f"dengan faktor reduksi kekuatan <b>φ = {phi_b}</b>."
    ))

    flex_rows = [
        ["Momen ultimat",           "Mu",    f"{Mu:.2f}",    "kN·m"],
        ["Kapasitas lentur desain",  "φMn",   f"{phi_Mn:.2f}", "kN·m"],
        ["Rasio utilisasi",         "Mu/φMn", f"{ratio_flex:.3f}", "—"],
        ["Status",                  "—",      status_label(ok_flex if ok_flex is not None else True), "—"],
    ]
    story += numbered_table(
        ctx,
        "Kontrol Kapasitas Lentur",
        ["Parameter", "Simbol", "Nilai", "Satuan"],
        flex_rows,
        col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
        col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
    )

    if ok_flex is False:
        story.append(warning(
            f"Kapasitas lentur TIDAK MENCUKUPI: Mu = {Mu:.2f} kN·m > φMn = {phi_Mn:.2f} kN·m"
        ))
    elif ok_flex:
        story.append(ok_text(
            f"Kapasitas lentur mencukupi: Mu = {Mu:.2f} kN·m ≤ φMn = {phi_Mn:.2f} kN·m"
        ))

    # ── 8.2 Penulangan ────────────────────────────────────────────────────
    story += h2(ctx, "Penulangan Lentur")

    # rho
    rho_min1 = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy)
    rho_max  = 0.75 * (0.85 * beta1 * fc / fy) * (600.0 / (600.0 + fy))
    As_min   = rho_min1 * b * d
    As_max   = rho_max  * b * d

    prov_bar = inp.get("main_bars", "—")
    story.append(p(
        f"Penulangan yang dipasang: <b>{prov_bar}</b> "
        f"(As,terpasang = {As_prov:.0f} mm²)."
    ))

    tul_rows = [
        ["As minimum",    f"ρ_min · b · d", f"{As_min:.0f}",  "mm²"],
        ["As diperlukan", "Dari analisis",    f"{As_req:.0f}",  "mm²"],
        ["As terpasang",  f"{prov_bar}",      f"{As_prov:.0f}", "mm²"],
        ["As maksimum",   f"ρ_max · b · d",   f"{As_max:.0f}",  "mm²"],
        ["Status As_min",  "—", status_label(As_prov >= As_min), "—"],
        ["Status As_max",  "—", status_label(As_prov <= As_max), "—"],
    ]
    story += numbered_table(
        ctx,
        "Kontrol Luas Tulangan Lentur",
        ["Parameter", "Keterangan", "Nilai", "Satuan"],
        tul_rows,
        col_widths=[4.5 * cm, 4.0 * cm, 3.0 * cm, 2.5 * cm],
        col_align=["LEFT", "LEFT", "RIGHT", "CENTER"],
    )

    # ── 8.3 Kontrol Geser ─────────────────────────────────────────────────
    story += h2(ctx, "Kontrol Kapasitas Geser")
    story.append(p(
        f"Kapasitas geser nominal dihitung sesuai {config.sni_concrete} "
        f"dengan faktor reduksi <b>φ = {phi_v}</b>."
    ))

    Vc_kN  = 0.17 * math.sqrt(fc) * b * d / 1000.0
    phi_Vc = phi_v * Vc_kN

    shr_rows = [
        ["Gaya geser ultimat",         "Vu",    f"{Vu:.2f}",     "kN"],
        ["Kapasitas geser beton",      "Vc",    f"{Vc_kN:.2f}",  "kN"],
        ["Kapasitas geser desain",     "φVn",   f"{phi_Vn:.2f}", "kN"],
        ["Rasio utilisasi",            "Vu/φVn", f"{ratio_shear:.3f}", "—"],
        ["Status",                     "—",     status_label(ok_shear if ok_shear is not None else True), "—"],
    ]
    story += numbered_table(
        ctx,
        "Kontrol Kapasitas Geser",
        ["Parameter", "Simbol", "Nilai", "Satuan"],
        shr_rows,
        col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
        col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
    )

    if ok_shear is False:
        story.append(warning(
            f"Kapasitas geser TIDAK MENCUKUPI: Vu = {Vu:.2f} kN > φVn = {phi_Vn:.2f} kN"
        ))
    elif ok_shear:
        story.append(ok_text(
            f"Kapasitas geser mencukupi: Vu = {Vu:.2f} kN ≤ φVn = {phi_Vn:.2f} kN"
        ))

    return story


# ── Baja ──────────────────────────────────────────────────────────────────────
def _steel_design(ctx, config, data) -> list[Any]:
    story: list[Any] = []
    inp = data.input_data  or {}
    out = data.output_data or {}

    fy = float(inp.get("fy_mpa", 250.0))
    fu = float(inp.get("fu_mpa", 410.0))
    E  = 200_000.0

    Mu = float(out.get("Mu_kNm") or out.get("Mu") or 0.0)
    Vu = float(out.get("Vu_kN")  or out.get("Vu") or 0.0)

    phi_Mn = float(out.get("phi_Mn_kNm") or out.get("phi_Mn") or 0.0)
    phi_Vn = float(out.get("phi_Vn_kN")  or out.get("phi_Vn") or 0.0)
    compact = out.get("section_compact", True)
    Lr_check= out.get("LTB_check", True)

    ok_flex  = phi_Mn >= Mu if phi_Mn > 0 else None
    ok_shear = phi_Vn >= Vu if phi_Vn > 0 else None
    ratio_flex  = Mu / phi_Mn  if phi_Mn > 0 else 0.0
    ratio_shear = Vu / phi_Vn  if phi_Vn > 0 else 0.0

    # ── 8.1 Kompaktitas ───────────────────────────────────────────────────
    story += h2(ctx, "Kontrol Kompaktitas Penampang")
    story.append(p(
        f"Kontrol kompaktitas flens dan badan dilakukan sesuai "
        f"{config.sni_steel} Tabel B4.1."
    ))
    story.append(p(
        f"Status penampang: <b>{'KOMPAK' if compact else 'NON-KOMPAK / LANGSING'}</b>"
    ))

    # ── 8.2 Kontrol Lentur ────────────────────────────────────────────────
    story += h2(ctx, "Kontrol Kapasitas Lentur")
    flex_rows = [
        ["Momen ultimat",           "Mu",    f"{Mu:.2f}",      "kN·m"],
        ["Kapasitas lentur desain",  "φMn",   f"{phi_Mn:.2f}",  "kN·m"],
        ["Rasio utilisasi",         "Mu/φMn", f"{ratio_flex:.3f}", "—"],
        ["Status",                  "—",      status_label(ok_flex if ok_flex is not None else True), "—"],
    ]
    story += numbered_table(
        ctx,
        "Kontrol Kapasitas Lentur Baja",
        ["Parameter", "Simbol", "Nilai", "Satuan"],
        flex_rows,
        col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
        col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
    )

    if ok_flex is False:
        story.append(warning(
            f"Kapasitas lentur TIDAK MENCUKUPI: Mu = {Mu:.2f} kN·m > φMn = {phi_Mn:.2f} kN·m"
        ))
    elif ok_flex:
        story.append(ok_text(
            f"Kapasitas lentur mencukupi: Mu = {Mu:.2f} kN·m ≤ φMn = {phi_Mn:.2f} kN·m"
        ))

    # ── 8.3 Kontrol Geser ─────────────────────────────────────────────────
    story += h2(ctx, "Kontrol Kapasitas Geser")
    shr_rows = [
        ["Gaya geser ultimat",     "Vu",     f"{Vu:.2f}",     "kN"],
        ["Kapasitas geser desain", "φVn",    f"{phi_Vn:.2f}", "kN"],
        ["Rasio utilisasi",        "Vu/φVn", f"{ratio_shear:.3f}", "—"],
        ["Status",                 "—",      status_label(ok_shear if ok_shear is not None else True), "—"],
    ]
    story += numbered_table(
        ctx,
        "Kontrol Kapasitas Geser Baja",
        ["Parameter", "Simbol", "Nilai", "Satuan"],
        shr_rows,
        col_widths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm],
        col_align=["LEFT", "CENTER", "RIGHT", "CENTER"],
    )

    if ok_shear is False:
        story.append(warning(
            f"Kapasitas geser TIDAK MENCUKUPI: Vu = {Vu:.2f} kN > φVn = {phi_Vn:.2f} kN"
        ))
    elif ok_shear:
        story.append(ok_text(
            f"Kapasitas geser mencukupi: Vu = {Vu:.2f} kN ≤ φVn = {phi_Vn:.2f} kN"
        ))

    return story
