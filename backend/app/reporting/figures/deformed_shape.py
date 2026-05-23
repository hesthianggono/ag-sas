"""
Deformed Shape Figure — AG-SAS
================================
Menghasilkan gambar bentuk deformasi struktur:
  - Overlay garis asli (abu-abu) dan bentuk deformasi (biru/ungu)
  - Skala deformasi ditampilkan
  - Untuk SSB: bentuk sinus kuartat (elastika teori)
"""
from __future__ import annotations
import numpy as np
import matplotlib.patches as mpatches

from app.reporting.figures.base import FIG_STYLE, fig_to_png_bytes, make_fig, watermark
from app.reporting.figures.model_view import draw_pin_support, draw_roller_support


def _elastic_curve_ssb(x: np.ndarray, L: float) -> np.ndarray:
    """
    Defleksi elastika SSB dengan UDL (dinormalisasi ke 1 di midspan):
    y(x) = (x/L) * (1 - x/L) * (1 + (x/L) - (x/L)^2)  [bentuk mendekati]
    Lebih presisi: y = wu/(24EI) * x*(L^3 - 2L*x^2 + x^3)
    Di sini kita normalisasi sehingga y_max = 1.
    """
    xi = x / L
    y = xi * (1 - xi) * (1 + xi - xi ** 2)
    y_max = np.max(np.abs(y))
    return -y / y_max if y_max > 0 else y   # ke bawah


def generate_deformed_shape(
    span_l: float,
    wu_knm: float,
    scale_factor: float = 50.0,
    caption: str = "",
    n_points: int = 101,
) -> bytes:
    """
    Generate gambar bentuk deformasi SSB.

    Parameters
    ----------
    scale_factor : faktor perbesaran deformasi untuk visualisasi
    """
    L = span_l
    x = np.linspace(0, L, n_points)
    beam_y = 0.3
    beam_h = 0.04
    sup_size = L * 0.033

    # Defleksi (dinormalisasi, lalu dikali skala visual)
    y_norm = _elastic_curve_ssb(x, L)
    delta_vis = y_norm * L * 0.12   # skala visual proporsional

    fig, ax = make_fig(width_in=9.0, height_in=4.2)

    # ── Garis asli (undeformed) ───────────────────────────────────────────────
    ax.plot([0, L], [beam_y, beam_y], "--",
            color=FIG_STYLE.NEUTRAL, lw=1.2, alpha=0.7, label="Posisi awal", zorder=2)

    # ── Bentuk deformasi ─────────────────────────────────────────────────────
    y_def = beam_y + delta_vis
    ax.fill_between(x, beam_y, y_def, alpha=0.25, color=FIG_STYLE.DEFORM_COLOR)
    ax.plot(x, y_def, color=FIG_STYLE.DEFORM_COLOR, lw=2.2,
            label=f"Bentuk deformasi (skala ×{scale_factor:.0f})", zorder=4)

    # ── Anotasi defleksi maks ─────────────────────────────────────────────────
    i_max = int(np.argmin(y_def))
    x_max = x[i_max]
    y_max_vis = y_def[i_max]
    delta_max_vis = abs(y_max_vis - beam_y)

    ax.annotate("",
                xy=(x_max, y_max_vis),
                xytext=(x_max, beam_y),
                arrowprops=dict(arrowstyle="<->", color=FIG_STYLE.DEFORM_COLOR,
                                lw=1.2, mutation_scale=8))
    ax.text(x_max + L * 0.04, y_max_vis + delta_max_vis * 0.5,
            f"δmax  @  x = {x_max:.2f} m\n(skala visual ×{scale_factor:.0f})",
            fontsize=7.5, color=FIG_STYLE.DEFORM_COLOR, va="center")

    # ── Balok dan tumpuan ─────────────────────────────────────────────────────
    ax.add_patch(mpatches.FancyBboxPatch(
        (0, beam_y - beam_h / 2), L, beam_h,
        boxstyle="square,pad=0", facecolor=FIG_STYLE.NEUTRAL,
        edgecolor=FIG_STYLE.STEEL_GRAY, linewidth=0.8, alpha=0.4, zorder=3
    ))
    draw_pin_support(ax, 0, beam_y - beam_h / 2, size=sup_size)
    draw_roller_support(ax, L, beam_y - beam_h / 2, size=sup_size)

    # ── UDL arrows kecil ──────────────────────────────────────────────────────
    for xi in np.linspace(0, L, 9):
        ax.annotate("", xy=(xi, beam_y + beam_h / 2),
                    xytext=(xi, beam_y + beam_h / 2 + L * 0.07),
                    arrowprops=dict(arrowstyle="-|>", color=FIG_STYLE.LOAD_COLOR,
                                    lw=0.9, mutation_scale=6))
    ax.plot([0, L], [beam_y + beam_h / 2 + L * 0.07] * 2,
            color=FIG_STYLE.LOAD_COLOR, lw=1.2)

    # ── Title & axes ─────────────────────────────────────────────────────────
    ax.set_title(f"Bentuk Deformasi Struktur  (Faktor Skala {scale_factor:.0f}×)\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")
    ax.set_xlabel("Panjang Bentang (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)

    margin = L * 0.08
    ax.set_xlim(-margin, L + margin)
    ax.set_ylim(y_max_vis - L * 0.05, beam_y + L * 0.16)
    ax.yaxis.set_visible(False)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([0, L / 4, L / 2, 3 * L / 4, L])
    ax.set_xticklabels(["0", f"{L/4:.2f}", f"{L/2:.2f}", f"{3*L/4:.2f}", f"{L:.2f}"])

    ax.legend(fontsize=7, loc="upper right", framealpha=0.9, edgecolor=FIG_STYLE.NEUTRAL)
    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)
