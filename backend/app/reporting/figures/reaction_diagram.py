"""
Reaction Diagram Figure — AG-SAS
==================================
Menghasilkan diagram reaksi tumpuan:
  - RA dan RB (reaksi vertikal)
  - Nilai dengan label dan satuan
"""
from __future__ import annotations
import numpy as np
import matplotlib.patches as mpatches

from app.reporting.figures.base import FIG_STYLE, fig_to_png_bytes, make_fig, watermark
from app.reporting.figures.model_view import draw_pin_support, draw_roller_support


def generate_reaction_diagram(
    span_l: float,
    wu_knm: float,
    caption: str = "",
) -> bytes:
    """
    Generate diagram reaksi tumpuan untuk SSB dengan UDL.

    RA = RB = wu * L / 2
    """
    L = span_l
    RA = wu_knm * L / 2
    RB = RA

    fig, ax = make_fig(width_in=9.0, height_in=4.2)

    beam_y = 0.3
    beam_h = 0.055
    sup_size = L * 0.033
    arrow_h = L * 0.22

    # ── Balok ────────────────────────────────────────────────────────────────
    beam_rect = mpatches.FancyBboxPatch(
        (0, beam_y - beam_h / 2), L, beam_h,
        boxstyle="square,pad=0",
        facecolor=FIG_STYLE.BLUE, edgecolor=FIG_STYLE.NAVY,
        linewidth=1.2, alpha=0.85, zorder=3
    )
    ax.add_patch(beam_rect)

    # ── UDL (kecil, di atas) ──────────────────────────────────────────────────
    n_arr = 10
    for xi in np.linspace(0, L, n_arr):
        ax.annotate("", xy=(xi, beam_y + beam_h / 2),
                    xytext=(xi, beam_y + beam_h / 2 + arrow_h * 0.35),
                    arrowprops=dict(arrowstyle="-|>", color=FIG_STYLE.LOAD_COLOR,
                                    lw=0.9, mutation_scale=6))
    ax.plot([0, L], [beam_y + beam_h / 2 + arrow_h * 0.35] * 2,
            color=FIG_STYLE.LOAD_COLOR, lw=1.5)
    ax.text(L / 2, beam_y + beam_h / 2 + arrow_h * 0.35 + L * 0.03,
            f"wu = {wu_knm:.3f} kN/m",
            fontsize=7.5, ha="center", color=FIG_STYLE.LOAD_COLOR)

    # ── Reaksi RA (panah ke atas dari kiri) ───────────────────────────────────
    # Arah: xytext (bawah) → xy (atas) dengan arrowstyle "-|>" → kepala di xy (atas)
    ax.annotate("",
                xy=(0, beam_y - beam_h / 2),
                xytext=(0, beam_y - beam_h / 2 - arrow_h),
                arrowprops=dict(arrowstyle="-|>", color=FIG_STYLE.GREEN,
                                lw=2.5, mutation_scale=14))
    ax.text(-L * 0.04, beam_y - beam_h / 2 - arrow_h - L * 0.04,
            f"RA = {RA:.2f} kN",
            fontsize=9, ha="center", color=FIG_STYLE.GREEN, fontweight="bold")
    ax.text(-L * 0.04, beam_y - beam_h / 2 - arrow_h * 0.5,
            f"{RA:.2f} kN  ↑",
            fontsize=7.5, ha="center", color=FIG_STYLE.GREEN)

    # ── Reaksi RB (panah ke atas dari kanan) ─────────────────────────────────
    ax.annotate("",
                xy=(L, beam_y - beam_h / 2),
                xytext=(L, beam_y - beam_h / 2 - arrow_h),
                arrowprops=dict(arrowstyle="-|>", color=FIG_STYLE.GREEN,
                                lw=2.5, mutation_scale=14))
    ax.text(L + L * 0.04, beam_y - beam_h / 2 - arrow_h - L * 0.04,
            f"RB = {RB:.2f} kN",
            fontsize=9, ha="center", color=FIG_STYLE.GREEN, fontweight="bold")
    ax.text(L + L * 0.04, beam_y - beam_h / 2 - arrow_h * 0.5,
            f"{RB:.2f} kN  ↑",
            fontsize=7.5, ha="center", color=FIG_STYLE.GREEN)

    # ── Tumpuan ───────────────────────────────────────────────────────────────
    draw_pin_support(ax, 0, beam_y - beam_h / 2, size=sup_size)
    draw_roller_support(ax, L, beam_y - beam_h / 2, size=sup_size)

    # ── Keseimbangan ─────────────────────────────────────────────────────────
    total_load = wu_knm * L
    ax.text(L / 2, beam_y - beam_h / 2 - arrow_h * 1.3,
            f"Kontrol: RA + RB = {RA:.2f} + {RB:.2f} = {RA+RB:.2f} kN  ←→  "
            f"wu·L = {wu_knm:.3f}×{L:.2f} = {total_load:.2f} kN  ✓",
            fontsize=7, ha="center", color=FIG_STYLE.STEEL_GRAY,
            style="italic")

    # ── Title & axes ─────────────────────────────────────────────────────────
    ax.set_title(f"Diagram Reaksi Tumpuan\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")
    ax.set_xlabel("Panjang Bentang (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)

    margin = L * 0.2
    ax.set_xlim(-margin, L + margin)
    ax.set_ylim(beam_y - beam_h / 2 - arrow_h * 1.45, beam_y + beam_h / 2 + arrow_h * 0.65)

    ax.yaxis.set_visible(False)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([0, L / 4, L / 2, 3 * L / 4, L])
    ax.set_xticklabels(["0", f"{L/4:.2f}", f"{L/2:.2f}", f"{3*L/4:.2f}", f"{L:.2f}"])

    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)
