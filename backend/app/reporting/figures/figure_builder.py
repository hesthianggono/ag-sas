"""
Figure Builder — AG-SAS
========================
Orkestrasi: menghasilkan semua gambar teknik untuk satu record kalkulasi.

Fungsi utama:
  build_figures_for_calc(calc_type, input_data, output_data, ...)
      -> list[FigureSpec]

Setiap FigureSpec berisi:
  - metadata lengkap (nomor, caption, load case, satuan, timestamp)
  - png_bytes  (PNG image)
  - json_data  (data diagram mentah)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.reporting.figures.base import (
    FigureSpec, FigureCaptionBuilder, FIG_STYLE,
)
from app.reporting.figures.model_view import generate_model_view
from app.reporting.figures.load_diagram import generate_load_diagram
from app.reporting.figures.internal_force_diagram import (
    generate_shear_diagram,
    generate_moment_diagram,
)
from app.reporting.figures.reaction_diagram import generate_reaction_diagram
from app.reporting.figures.deformed_shape import generate_deformed_shape
from app.reporting.figures.utilization_map import generate_utilization_map


def build_figures_for_calc(
    *,
    calc_type: str,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    calc_title: str = "",
    source_result_id: int | None = None,
    section: str = "4",
    deform_scale: float = 50.0,
) -> list[FigureSpec]:
    """
    Hasilkan semua gambar teknik untuk satu kalkulasi.

    Parameters
    ----------
    calc_type        : "concrete_beam" | "steel_beam"
    input_data       : data input kalkulasi
    output_data      : data output/hasil kalkulasi
    calc_title       : judul kalkulasi (untuk caption)
    source_result_id : FK CalculationRecord.id
    section          : nomor seksi laporan (default "4")
    deform_scale     : faktor skala deformasi visual

    Returns
    -------
    list[FigureSpec], berurut sesuai urutan laporan
    """
    cb = FigureCaptionBuilder(section=section)
    now = datetime.utcnow()
    figures: list[FigureSpec] = []

    L  = float(input_data.get("span_l_m", 1.0))
    wu = float(output_data.get("wu_knm", 0))
    wd = float(input_data.get("dead_load_w_knm", 0))
    wl = float(input_data.get("live_load_w_knm", 0))
    mu = float(output_data.get("mu_ultimate_knm", 0))
    cr = float(output_data.get("capacity_ratio", 0))
    phi_mn = float(output_data.get("phi_mn_knm", 0))

    # Rincian penampang
    if calc_type == "concrete_beam":
        b  = input_data.get("width_b_mm", 300)
        h  = input_data.get("height_h_mm", 600)
        section_label = f"b/h = {b}/{h} mm"
    else:
        section_label = output_data.get("profile_designation", "WF")

    load_comb = "1.2D + 1.6L"

    # ── 1. Model Struktur ────────────────────────────────────────────────────
    num, cap = cb.next("model_view", "Model Struktur")
    png = generate_model_view(
        span_l=L, section_label=section_label,
        calc_type=calc_type, input_data=input_data,
        caption=cap,
    )
    figures.append(FigureSpec(
        figure_key="model_view",
        title="Model Struktur",
        caption=cap,
        figure_number=num,
        section=section,
        load_case=None,
        load_combination=None,
        scale_factor=None,
        unit="m",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"span_l": L, "section": section_label, "calc_type": calc_type},
        order_index=cb.order_of("model_view"),
    ))

    # ── 2. Diagram Pembebanan ─────────────────────────────────────────────────
    num, cap = cb.next("load_diagram", "Diagram Pembebanan",
                       suffix=f"Kombinasi {load_comb}")
    png = generate_load_diagram(
        span_l=L, wu_knm=wu, wd_knm=wd, wl_knm=wl, caption=cap,
    )
    figures.append(FigureSpec(
        figure_key="load_diagram",
        title="Diagram Pembebanan",
        caption=cap,
        figure_number=num,
        section=section,
        load_case="DL+LL",
        load_combination=load_comb,
        scale_factor=None,
        unit="kN/m",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"wu": wu, "wd": wd, "wl": wl, "L": L},
        order_index=cb.order_of("load_diagram"),
    ))

    # ── 3. Diagram Reaksi Tumpuan ─────────────────────────────────────────────
    num, cap = cb.next("reaction_diagram", "Diagram Reaksi Tumpuan",
                       suffix=f"Kombinasi {load_comb}")
    png = generate_reaction_diagram(span_l=L, wu_knm=wu, caption=cap)
    RA = wu * L / 2
    figures.append(FigureSpec(
        figure_key="reaction_diagram",
        title="Diagram Reaksi Tumpuan",
        caption=cap,
        figure_number=num,
        section=section,
        load_case="DL+LL",
        load_combination=load_comb,
        scale_factor=None,
        unit="kN",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"RA": RA, "RB": RA, "wu": wu, "L": L},
        order_index=cb.order_of("reaction_diagram"),
    ))

    # ── 4. Diagram Gaya Geser ─────────────────────────────────────────────────
    num, cap = cb.next("shear_diagram", "Diagram Gaya Geser V(x)",
                       suffix=f"Kombinasi {load_comb}")
    png = generate_shear_diagram(span_l=L, wu_knm=wu, caption=cap)
    V_max = wu * L / 2
    figures.append(FigureSpec(
        figure_key="shear_diagram",
        title="Diagram Gaya Geser",
        caption=cap,
        figure_number=num,
        section=section,
        load_case="DL+LL",
        load_combination=load_comb,
        scale_factor=None,
        unit="kN",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"V_max": V_max, "V_min": -V_max, "wu": wu, "L": L},
        order_index=cb.order_of("shear_diagram"),
    ))

    # ── 5. Diagram Momen Lentur ───────────────────────────────────────────────
    num, cap = cb.next("moment_diagram", "Diagram Momen Lentur M(x)",
                       suffix=f"Kombinasi {load_comb}")
    png = generate_moment_diagram(span_l=L, wu_knm=wu, mu_knm=mu, caption=cap)
    figures.append(FigureSpec(
        figure_key="moment_diagram",
        title="Diagram Momen Lentur",
        caption=cap,
        figure_number=num,
        section=section,
        load_case="DL+LL",
        load_combination=load_comb,
        scale_factor=None,
        unit="kN·m",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"M_max": mu, "wu": wu, "L": L},
        order_index=cb.order_of("moment_diagram"),
    ))

    # ── 6. Bentuk Deformasi ───────────────────────────────────────────────────
    num, cap = cb.next("deformed_shape", "Bentuk Deformasi Struktur",
                       suffix=f"Faktor skala {deform_scale:.0f}×")
    png = generate_deformed_shape(
        span_l=L, wu_knm=wu, scale_factor=deform_scale, caption=cap,
    )
    figures.append(FigureSpec(
        figure_key="deformed_shape",
        title="Bentuk Deformasi",
        caption=cap,
        figure_number=num,
        section=section,
        load_case="DL+LL",
        load_combination=load_comb,
        scale_factor=deform_scale,
        unit="m (dikali faktor skala)",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"scale_factor": deform_scale, "wu": wu, "L": L},
        order_index=cb.order_of("deformed_shape"),
    ))

    # ── 7. Peta Rasio Utilisasi ───────────────────────────────────────────────
    num, cap = cb.next("utilization_map", "Peta Rasio Utilisasi Elemen")
    png = generate_utilization_map(
        mu_knm=mu, phi_mn_knm=phi_mn, capacity_ratio=cr,
        calc_type=calc_type, input_data=input_data, output_data=output_data,
        caption=cap,
    )
    figures.append(FigureSpec(
        figure_key="utilization_map",
        title="Peta Rasio Utilisasi",
        caption=cap,
        figure_number=num,
        section=section,
        load_case="DL+LL",
        load_combination=load_comb,
        scale_factor=None,
        unit="—",
        timestamp=now,
        source_result_id=source_result_id,
        source="backend",
        png_bytes=png,
        svg_data=None,
        json_data={"mu": mu, "phi_mn": phi_mn, "capacity_ratio": cr},
        order_index=cb.order_of("utilization_map"),
    ))

    return figures
