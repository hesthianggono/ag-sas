"""
Load Diagram Figure — AG-SAS
=============================
Menghasilkan diagram pembebanan:
  - Beban merata terdistribusi (UDL) dengan panah
  - Nilai wu, wD, wL ditampilkan
  - Garis balok dan tumpuan
"""
from __future__ import annotations
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Polygon, FancyBboxPatch

from app.reporting.figures.base import FIG_STYLE, fig_to_png_bytes, make_fig, watermark
from app.reporting.figures.model_view import draw_pin_support, draw_roller_support


def generate_load_diagram(
    span_l: float,
    wu_knm: float,
    wd_knm: float,
    wl_knm: float,
    caption: str = "",
    show_characteristic: bool = True,
) -> bytes:
    """
    Generate diagram pembebanan UDL.

    Parameters
    ----------
    span_l   : bentang (m)
    wu_knm   : beban terfaktor (kN/m)
    wd_knm   : beban mati (kN/m)
    wl_knm   : beban hidup (kN/m)
    """
    fig, ax = make_fig(width_in=9.0, height_in=4.0)

    L = span_l
    beam_y = 0.2
    beam_h = 0.05
    sup_size = L * 0.033
    arrow_h = L * 0.18   # tinggi panah beban

    # ── UDL arrows (panah beban merata) ──────────────────────────────────────
    n_arrows = max(8, int(L * 3))
    x_arr = np.linspace(0, L, n_arrows)
    for x in x_arr:
        ax.annotate("",
                    xy=(x, beam_y + beam_h / 2),
                    xytext=(x, beam_y + beam_h / 2 + arrow_h),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=FIG_STYLE.LOAD_COLOR,
                        lw=1.2,
                        mutation_scale=8,
                    ))

    # Garis atas UDL
    ax.plot([0, L], [beam_y + beam_h / 2 + arrow_h, beam_y + beam_h / 2 + arrow_h],
            color=FIG_STYLE.LOAD_COLOR, lw=2.0, zorder=4)

    # Label wu
    ax.text(L / 2, beam_y + beam_h / 2 + arrow_h + L * 0.04,
            f"wu = {wu_knm:.3f} kN/m",
            fontsize=9, ha="center", color=FIG_STYLE.LOAD_COLOR, fontweight="bold")

    # ── Beam ─────────────────────────────────────────────────────────────────
    beam_rect = FancyBboxPatch(
        (0, beam_y - beam_h / 2), L, beam_h,
        boxstyle="square,pad=0",
        facecolor=FIG_STYLE.BLUE, edgecolor=FIG_STYLE.NAVY,
        linewidth=1.2, alpha=0.85, zorder=3
    )
    ax.add_patch(beam_rect)

    # ── Tumpuan ───────────────────────────────────────────────────────────────
    draw_pin_support(ax, 0, beam_y - beam_h / 2, size=sup_size)
    draw_roller_support(ax, L, beam_y - beam_h / 2, size=sup_size)

    # ── Dimensi span ─────────────────────────────────────────────────────────
    dim_y = beam_y - beam_h / 2 - L * 0.2
    ax.annotate("", xy=(L, dim_y), xytext=(0, dim_y),
                arrowprops=dict(arrowstyle="<->", color=FIG_STYLE.NAVY, lw=1.0))
    ax.text(L / 2, dim_y - L * 0.05, f"L = {L:.2f} m",
            fontsize=8, ha="center", color=FIG_STYLE.NAVY, fontweight="bold")

    # ── Legend beban ─────────────────────────────────────────────────────────
    if show_characteristic:
        legend_items = [
            mpatches.Patch(color=FIG_STYLE.LOAD_COLOR, label=f"wu = 1.2D + 1.6L = {wu_knm:.3f} kN/m"),
            mpatches.Patch(color=FIG_STYLE.NEUTRAL, label=f"wD = {wd_knm:.3f} kN/m  |  wL = {wl_knm:.3f} kN/m"),
        ]
        ax.legend(handles=legend_items, loc="upper right", fontsize=7,
                  framealpha=0.9, edgecolor=FIG_STYLE.NEUTRAL)

    # ── Title & axes ─────────────────────────────────────────────────────────
    ax.set_title(f"Diagram Pembebanan — UDL Terfaktor\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")
    ax.set_xlabel("Panjang Bentang (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)

    margin = L * 0.08
    ax.set_xlim(-margin, L + margin)
    y_max = beam_y + beam_h / 2 + arrow_h + L * 0.18
    ax.set_ylim(dim_y - L * 0.1, y_max)

    ax.yaxis.set_visible(False)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([0, L / 4, L / 2, 3 * L / 4, L])
    ax.set_xticklabels(["0", f"{L/4:.2f}", f"{L/2:.2f}", f"{3*L/4:.2f}", f"{L:.2f}"])

    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)
