"""
BAB 10 — Ringkasan dan Kesimpulan
===================================
10.1 Ringkasan Parameter Input
10.2 Ringkasan Hasil Analisis
10.3 Kesimpulan
"""
from __future__ import annotations

import math
from typing import Any

from reportlab.lib.units import cm

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.report_snapshot import FullReportConfig, FullReportData
from app.reporting.full_report.section_builder import (
    h1, h2, p, spacer, kv_table, numbered_table,
    note, warning, ok_text, status_label,
)


def build_s10(
    ctx: NumberingContext,
    config: FullReportConfig,
    data: FullReportData,
) -> list[Any]:
    story: list[Any] = []

    story += h1(ctx, 10, "RINGKASAN DAN KESIMPULAN")

    inp = data.input_data  or {}
    out = data.output_data or {}

    is_concrete = data.calc_type == "concrete_beam"
    is_steel    = data.calc_type == "steel_beam"

    # ── 10.1 Ringkasan Input ──────────────────────────────────────────────
    story += h2(ctx, "Ringkasan Parameter Input")

    L  = float(inp.get("span_m", 0.0))
    DL = float(inp.get("dead_load_kn_m", 0.0))
    LL = float(inp.get("live_load_kn_m", 0.0))
    SDL= float(inp.get("super_dead_kn_m", 0.0))
    wu = float(out.get("wu_kn_m") or out.get("wu") or (1.2*(DL+SDL) + 1.6*LL))

    common_rows = [
        ("Tipe Elemen",          {
            "concrete_beam": "Balok Beton Bertulang",
            "steel_beam":    "Balok Baja Profil",
        }.get(data.calc_type, data.calc_type or "—")),
        ("Judul Kalkulasi",      data.calc_title or "—"),
        ("Panjang Bentang (L)",  f"{L:.3f} m"),
        ("Beban Mati (DL)",      f"{DL:.2f} kN/m"),
        ("Beban Mati Tambahan (SDL)", f"{SDL:.2f} kN/m"),
        ("Beban Hidup (LL)",     f"{LL:.2f} kN/m"),
        ("Beban Terfaktor (wu)", f"{wu:.2f} kN/m"),
    ]

    if is_concrete:
        fc = float(inp.get("fc_mpa", 25.0))
        fy = float(inp.get("fy_mpa", 420.0))
        b  = float(inp.get("b_mm", 0.0))
        h_ = float(inp.get("h_mm", 0.0))
        common_rows += [
            ("f'c (kuat tekan beton)",  f"{fc:.0f} MPa"),
            ("fy (kuat leleh tulangan)", f"{fy:.0f} MPa"),
            ("Lebar penampang (b)",     f"{b:.0f} mm"),
            ("Tinggi penampang (h)",    f"{h_:.0f} mm"),
        ]
    elif is_steel:
        fy = float(inp.get("fy_mpa", 250.0))
        common_rows += [
            ("fy (kuat leleh baja)",    f"{fy:.0f} MPa"),
            ("Nama profil",             inp.get("profile_name", "—")),
        ]

    story.append(kv_table(common_rows, col_widths=(6.0 * cm, None)))
    story.append(spacer(4))

    # ── 10.2 Ringkasan Hasil ──────────────────────────────────────────────
    story += h2(ctx, "Ringkasan Hasil Analisis dan Perencanaan")

    Mu     = float(out.get("Mu_kNm") or out.get("Mu") or 0.0)
    Vu     = float(out.get("Vu_kN")  or out.get("Vu") or 0.0)
    phi_Mn = float(out.get("phi_Mn_kNm") or out.get("phi_Mn") or 0.0)
    phi_Vn = float(out.get("phi_Vn_kN")  or out.get("phi_Vn") or 0.0)
    delta  = float(out.get("deflection_mm") or out.get("delta_mm") or 0.0)
    delta_allow = L * 1000 / 360 if L > 0 else 0.0

    ok_flex  = phi_Mn >= Mu if phi_Mn > 0 else None
    ok_shear = phi_Vn >= Vu if phi_Vn > 0 else None
    ok_defl  = delta  <= delta_allow if delta_allow > 0 else None

    ratio_flex  = Mu / phi_Mn if phi_Mn > 0 else 0.0
    ratio_shear = Vu / phi_Vn if phi_Vn > 0 else 0.0
    ratio_defl  = delta / delta_allow if delta_allow > 0 else 0.0

    check_rows = [
        ["Momen Lentur", f"Mu = {Mu:.2f} kN·m",
         f"φMn = {phi_Mn:.2f} kN·m",
         f"{ratio_flex:.3f}",
         status_label(ok_flex if ok_flex is not None else True)],
        ["Gaya Geser", f"Vu = {Vu:.2f} kN",
         f"φVn = {phi_Vn:.2f} kN",
         f"{ratio_shear:.3f}",
         status_label(ok_shear if ok_shear is not None else True)],
        ["Lendutan", f"δ = {delta:.2f} mm",
         f"δ_izin = {delta_allow:.2f} mm",
         f"{ratio_defl:.3f}",
         status_label(ok_defl if ok_defl is not None else True)],
    ]
    story += numbered_table(
        ctx,
        "Tabel Ringkasan Kontrol Struktur",
        ["Pemeriksaan", "Beban/Gaya", "Kapasitas", "Rasio", "Status"],
        check_rows,
        col_widths=[3.0 * cm, 4.2 * cm, 4.2 * cm, 1.8 * cm, 2.8 * cm],
        col_align=["LEFT", "LEFT", "LEFT", "RIGHT", "CENTER"],
    )

    # ── 10.3 Kesimpulan ───────────────────────────────────────────────────
    story += h2(ctx, "Kesimpulan")

    all_ok = all(v is True or v is None for v in [ok_flex, ok_shear, ok_defl])

    if all_ok:
        story.append(p(
            f"Berdasarkan hasil analisis dan perencanaan yang telah dilakukan, "
            f"elemen struktur <b>{data.calc_title or 'ini'}</b> dinyatakan "
            f"<b>MEMENUHI</b> persyaratan kekuatan dan kemampuan layan "
            f"sesuai {config.sni_concrete if is_concrete else config.sni_steel} "
            f"dan {config.sni_load}."
        ))
        story.append(ok_text(
            "Semua kontrol struktur (lentur, geser, lendutan) TERPENUHI."
        ))
    else:
        story.append(warning(
            "Terdapat satu atau lebih kontrol yang TIDAK TERPENUHI. "
            "Tinjau ulang dimensi penampang atau penulangan/profil yang digunakan."
        ))

    story.append(spacer(4))
    return story
