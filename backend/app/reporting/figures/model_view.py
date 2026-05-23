"""
Model View Figure — AG-SAS
===========================
Menghasilkan gambar model struktur:
  - Balok sederhana (simply supported) dengan anotasi dimensi
  - Simbol tumpuan: sendi (△) dan rol (△ + garis bawah)
  - Label node, label elemen, dan info penampang opsional
"""
from __future__ import annotations
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.patches import FancyArrowPatch, Polygon
from matplotlib.figure import Figure

from app.reporting.figures.base import FIG_STYLE, fig_to_png_bytes, make_fig, watermark


def draw_pin_support(ax, x: float, y: float, size: float = 0.04):
    """Gambar simbol tumpuan sendi (segitiga + garis)."""
    tri = Polygon(
        [[x, y], [x - size, y - size * 1.5], [x + size, y - size * 1.5]],
        closed=True, facecolor=FIG_STYLE.NAVY, edgecolor=FIG_STYLE.NAVY, zorder=5
    )
    ax.add_patch(tri)
    ax.plot([x - size * 1.4, x + size * 1.4], [y - size * 1.5, y - size * 1.5],
            color=FIG_STYLE.NAVY, lw=1.5, zorder=5)
    # hatch lines below
    for i in range(5):
        xi = x - size * 1.2 + i * size * 0.6
        ax.plot([xi, xi - size * 0.25], [y - size * 1.5, y - size * 2.2],
                color=FIG_STYLE.NAVY, lw=0.8, zorder=4)


def draw_roller_support(ax, x: float, y: float, size: float = 0.04):
    """Gambar simbol tumpuan rol (segitiga + lingkaran kecil)."""
    tri = Polygon(
        [[x, y], [x - size, y - size * 1.5], [x + size, y - size * 1.5]],
        closed=True, facecolor=FIG_STYLE.STEEL_GRAY, edgecolor=FIG_STYLE.NAVY, zorder=5
    )
    ax.add_patch(tri)
    circle = mpatches.Circle(
        (x, y - size * 1.5 - size * 0.6), size * 0.5,
        facecolor=FIG_STYLE.LIGHT_BG, edgecolor=FIG_STYLE.NAVY, lw=1.2, zorder=5
    )
    ax.add_patch(circle)
    ax.plot([x - size * 1.4, x + size * 1.4], [y - size * 1.5 - size * 1.2,
            y - size * 1.5 - size * 1.2],
            color=FIG_STYLE.NAVY, lw=1.5, zorder=5)
    for i in range(5):
        xi = x - size * 1.2 + i * size * 0.6
        ax.plot([xi, xi - size * 0.25],
                [y - size * 1.5 - size * 1.2, y - size * 1.5 - size * 1.9],
                color=FIG_STYLE.NAVY, lw=0.8, zorder=4)


def generate_model_view(
    span_l: float,
    section_label: str,
    calc_type: str,
    input_data: dict,
    caption: str = "",
) -> bytes:
    """
    Generate model struktur balok sederhana sebagai PNG bytes.

    Parameters
    ----------
    span_l        : panjang bentang (m)
    section_label : mis. "b/h = 300/600 mm" atau "WF 350×175×7×11"
    calc_type     : "concrete_beam" | "steel_beam"
    input_data    : dict data input kalkulasi
    caption       : teks caption untuk judul gambar

    Returns
    -------
    bytes PNG
    """
    fig, ax = make_fig(width_in=9.0, height_in=3.8)

    # Koordinat normalized (beam from 0 to L, y=0)
    L = span_l
    beam_y = 0.3
    beam_h = 0.06  # tinggi beam dalam unit L
    sup_size = L * 0.035

    # Gambar balok (persegi panjang)
    beam_color = FIG_STYLE.BLUE if calc_type == "concrete_beam" else FIG_STYLE.STEEL_GRAY
    beam_rect = mpatches.FancyBboxPatch(
        (0, beam_y - beam_h / 2), L, beam_h,
        boxstyle="square,pad=0",
        facecolor=beam_color, edgecolor=FIG_STYLE.NAVY,
        linewidth=1.2, alpha=0.85, zorder=3
    )
    ax.add_patch(beam_rect)

    # Penampang cross-section inset (sketsa kecil)
    cs_x = L + L * 0.05
    cs_y = beam_y
    if calc_type == "concrete_beam":
        b = input_data.get("width_b_mm", 300) / 1000
        h = input_data.get("height_h_mm", 600) / 1000
        scale = 0.6 / max(b, h)
        bv, hv = b * scale, h * scale
        cs_rect = mpatches.FancyBboxPatch(
            (cs_x, cs_y - hv / 2), bv, hv,
            boxstyle="square,pad=0",
            facecolor=FIG_STYLE.BLUE, edgecolor=FIG_STYLE.NAVY,
            linewidth=1.0, alpha=0.7, zorder=3
        )
        ax.add_patch(cs_rect)
        ax.annotate(f"b={input_data.get('width_b_mm',300)}\nh={input_data.get('height_h_mm',600)} mm",
                    xy=(cs_x + bv / 2, cs_y - hv / 2 - 0.06),
                    fontsize=6.5, ha="center", color=FIG_STYLE.NAVY)
    else:
        hw = input_data.get("height_h_mm", 350) / 1000
        bw = input_data.get("flange_width_b_mm", 175) / 1000
        tw = input_data.get("web_thickness_tw_mm", 7) / 1000
        tf = input_data.get("flange_thickness_tf_mm", 11) / 1000
        scale = 0.6 / max(hw, bw)
        hv, bv, twv, tfv = hw*scale, bw*scale, tw*scale, tf*scale
        # Web
        ax.add_patch(mpatches.FancyBboxPatch(
            (cs_x + (bv - twv) / 2, cs_y - hv / 2 + tfv), twv, hv - 2*tfv,
            boxstyle="square,pad=0", facecolor=FIG_STYLE.STEEL_GRAY,
            edgecolor=FIG_STYLE.NAVY, lw=0.8, alpha=0.8, zorder=3))
        # Top flange
        ax.add_patch(mpatches.FancyBboxPatch(
            (cs_x, cs_y + hv / 2 - tfv), bv, tfv,
            boxstyle="square,pad=0", facecolor=FIG_STYLE.STEEL_GRAY,
            edgecolor=FIG_STYLE.NAVY, lw=0.8, alpha=0.8, zorder=3))
        # Bottom flange
        ax.add_patch(mpatches.FancyBboxPatch(
            (cs_x, cs_y - hv / 2), bv, tfv,
            boxstyle="square,pad=0", facecolor=FIG_STYLE.STEEL_GRAY,
            edgecolor=FIG_STYLE.NAVY, lw=0.8, alpha=0.8, zorder=3))
        ax.annotate(section_label.replace("×", "×\n") if len(section_label) > 15 else section_label,
                    xy=(cs_x + bv / 2, cs_y - hv / 2 - 0.06),
                    fontsize=6, ha="center", color=FIG_STYLE.NAVY)

    ax.annotate("", xy=(cs_x, beam_y), xytext=(L + L * 0.01, beam_y),
                arrowprops=dict(arrowstyle="-", color=FIG_STYLE.NEUTRAL, lw=0.8, linestyle="dashed"))

    # Tumpuan sendi kiri
    draw_pin_support(ax, 0, beam_y - beam_h / 2, size=sup_size)
    # Tumpuan rol kanan
    draw_roller_support(ax, L, beam_y - beam_h / 2, size=sup_size)

    # Label node
    node_kwargs = dict(fontsize=7.5, ha="center", va="bottom",
                       color=FIG_STYLE.NAVY, fontweight="bold")
    ax.text(0, beam_y + beam_h / 2 + 0.04, "A", **node_kwargs)
    ax.text(L, beam_y + beam_h / 2 + 0.04, "B", **node_kwargs)

    # Dimensi span
    dim_y = beam_y - beam_h / 2 - 0.22
    ax.annotate("", xy=(L, dim_y), xytext=(0, dim_y),
                arrowprops=dict(arrowstyle="<->", color=FIG_STYLE.NAVY, lw=1.0))
    ax.text(L / 2, dim_y - 0.06, f"L = {L:.2f} m",
            fontsize=8, ha="center", color=FIG_STYLE.NAVY, fontweight="bold")

    # Label tumpuan
    ax.text(0, beam_y - beam_h / 2 - sup_size * 4.5, "Sendi",
            fontsize=6.5, ha="center", color=FIG_STYLE.STEEL_GRAY)
    ax.text(L, beam_y - beam_h / 2 - sup_size * 4.5, "Rol",
            fontsize=6.5, ha="center", color=FIG_STYLE.STEEL_GRAY)

    # Label elemen
    ax.text(L / 2, beam_y + 0.0, "E1",
            fontsize=7, ha="center", va="center",
            color=FIG_STYLE.WHITE, fontweight="bold")

    # Judul gambar
    type_label = "Balok Beton Bertulang" if calc_type == "concrete_beam" else "Balok Baja Profil WF"
    ax.set_title(f"Model Struktur — {type_label}\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")

    # Axis
    margin = L * 0.15
    ax.set_xlim(-margin, L + L * 0.55)
    ax.set_ylim(beam_y - 0.45, beam_y + 0.35)
    ax.set_xlabel("Panjang Elemen (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.set_aspect("equal")
    ax.grid(False)
    ax.tick_params(left=False, bottom=True)
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Axis X ticks
    ax.set_xticks([0, L / 4, L / 2, 3 * L / 4, L])
    ax.set_xticklabels(["0", f"{L/4:.2f}", f"{L/2:.2f}", f"{3*L/4:.2f}", f"{L:.2f}"])

    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)
