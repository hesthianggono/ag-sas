"""
Internal Force Diagrams — AG-SAS
==================================
Menghasilkan diagram:
  - Gaya aksial N(x)   — hanya untuk Frame2D (opsional untuk balok)
  - Gaya geser  V(x)   — diagram gaya geser
  - Momen lentur M(x)  — diagram momen lentur
"""
from __future__ import annotations
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from app.reporting.figures.base import FIG_STYLE, fig_to_png_bytes, make_fig, watermark


def _ssb_shear(x_arr: np.ndarray, wu: float, L: float) -> np.ndarray:
    """V(x) untuk SSB dengan UDL: V = wu*L/2 - wu*x"""
    return wu * L / 2 - wu * x_arr


def _ssb_moment(x_arr: np.ndarray, wu: float, L: float) -> np.ndarray:
    """M(x) untuk SSB dengan UDL: M = wu*x*(L-x)/2"""
    return wu * x_arr * (L - x_arr) / 2


def generate_shear_diagram(
    span_l: float,
    wu_knm: float,
    caption: str = "",
    n_points: int = 101,
) -> bytes:
    """
    Generate diagram gaya geser V(x).

    Returns PNG bytes.
    """
    L = span_l
    x = np.linspace(0, L, n_points)
    V = _ssb_shear(x, wu_knm, L)

    fig, ax = make_fig(width_in=9.0, height_in=3.5)

    V_max = wu_knm * L / 2
    V_min = -V_max

    # Zona positif dan negatif
    ax.fill_between(x, V, 0, where=(V >= 0), color=FIG_STYLE.POS_ZONE, alpha=0.7,
                    label="V > 0 (geser positif)", zorder=2)
    ax.fill_between(x, V, 0, where=(V < 0), color=FIG_STYLE.NEG_ZONE, alpha=0.7,
                    label="V < 0 (geser negatif)", zorder=2)

    # Garis diagram
    ax.plot(x, V, color=FIG_STYLE.NAVY, lw=2.0, zorder=3)

    # Garis nol
    ax.axhline(0, color=FIG_STYLE.NAVY, lw=1.0, alpha=0.6)

    # Anotasi nilai
    ax.annotate(f"+{V_max:.2f} kN", xy=(0, V_max),
                fontsize=8, color=FIG_STYLE.POS_LINE, fontweight="bold",
                ha="left", va="bottom",
                xytext=(L * 0.05, V_max * 1.08))
    ax.annotate(f"−{V_max:.2f} kN", xy=(L, V_min),
                fontsize=8, color=FIG_STYLE.NEG_LINE, fontweight="bold",
                ha="right", va="top",
                xytext=(L * 0.95, V_min * 1.08))

    # Titik nol (x = L/2)
    ax.plot(L / 2, 0, "o", color=FIG_STYLE.NAVY, markersize=5, zorder=5)
    ax.annotate(f"V=0  @  x={L/2:.2f}m", xy=(L / 2, 0),
                xytext=(L / 2 + L * 0.05, V_max * 0.2),
                fontsize=7, color=FIG_STYLE.NEUTRAL,
                arrowprops=dict(arrowstyle="->", color=FIG_STYLE.NEUTRAL, lw=0.8))

    # Dimensi span bawah
    ax.set_xticks([0, L / 4, L / 2, 3 * L / 4, L])
    ax.set_xticklabels(["0", f"{L/4:.2f}", f"{L/2:.2f}", f"{3*L/4:.2f}", f"{L:.2f}"])

    ax.set_title(f"Diagram Gaya Geser  V(x)\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")
    ax.set_xlabel("Panjang Bentang (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.set_ylabel("Gaya Geser V  (kN)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.set_xlim(-L * 0.02, L * 1.02)
    ax.set_ylim(V_min * 1.25, V_max * 1.25)

    ax.legend(fontsize=7, loc="upper right", framealpha=0.9, edgecolor=FIG_STYLE.NEUTRAL)
    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)


def generate_moment_diagram(
    span_l: float,
    wu_knm: float,
    mu_knm: float,
    caption: str = "",
    n_points: int = 101,
) -> bytes:
    """
    Generate diagram momen lentur M(x).

    Diagram digambar dengan konvensi struktural Indonesia:
    Momen positif (sagging) digambar ke BAWAH (sisi tarik bawah).

    Returns PNG bytes.
    """
    L = span_l
    x = np.linspace(0, L, n_points)
    M = _ssb_moment(x, wu_knm, L)   # positif = sagging

    fig, ax = make_fig(width_in=9.0, height_in=4.0)

    # Diagram M digambar ke bawah (konvensi struktural)
    M_plot = -M   # invert untuk konvensi "sagging = bawah"

    ax.fill_between(x, M_plot, 0, where=(M_plot <= 0), color=FIG_STYLE.POS_ZONE, alpha=0.75,
                    label="Momen sagging (+)", zorder=2)
    ax.plot(x, M_plot, color=FIG_STYLE.BLUE, lw=2.2, zorder=3)
    ax.axhline(0, color=FIG_STYLE.NAVY, lw=1.0, alpha=0.6)

    # Titik momen maksimum
    i_max = int(np.argmax(M))
    x_max = x[i_max]
    M_max = M[i_max]

    ax.plot(x_max, -M_max, "^", color=FIG_STYLE.RED, markersize=8, zorder=6,
            label=f"Momen maks = {M_max:.2f} kN·m")
    ax.annotate(f"Mu = {mu_knm:.2f} kN·m\n(max @ x = {x_max:.2f} m)",
                xy=(x_max, -M_max),
                xytext=(x_max + L * 0.08, -M_max * 0.65),
                fontsize=8, color=FIG_STYLE.RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=FIG_STYLE.RED, lw=1.0))

    # Garis vertikal di titik maks
    ax.plot([x_max, x_max], [0, -M_max], "--", color=FIG_STYLE.NEUTRAL, lw=0.8, alpha=0.7)

    ax.set_xticks([0, L / 4, L / 2, 3 * L / 4, L])
    ax.set_xticklabels(["0", f"{L/4:.2f}", f"{L/2:.2f}", f"{3*L/4:.2f}", f"{L:.2f}"])

    # Y-ticks dengan label positif (balik tanda — sagging ke bawah konvensi)
    import matplotlib.ticker as ticker
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{abs(v):.1f}"))

    ax.set_title(f"Diagram Momen Lentur  M(x)  [sagging (+) ke bawah]\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")
    ax.set_xlabel("Panjang Bentang (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.set_ylabel("Momen Lentur M  (kN·m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.set_xlim(-L * 0.02, L * 1.02)

    ax.legend(fontsize=7, loc="upper right", framealpha=0.9, edgecolor=FIG_STYLE.NEUTRAL)
    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)


def generate_axial_diagram(
    x_vals: list[float],
    N_vals: list[float],
    span_l: float,
    caption: str = "",
) -> bytes:
    """
    Generate diagram gaya aksial N(x) — untuk Frame2D.
    x_vals, N_vals: data mentah dari post-processing.
    """
    x = np.array(x_vals)
    N = np.array(N_vals)

    fig, ax = make_fig(width_in=9.0, height_in=3.5)

    ax.fill_between(x, N, 0, where=(N >= 0), color=FIG_STYLE.NEG_ZONE, alpha=0.7,
                    label="N > 0 (tekan)")
    ax.fill_between(x, N, 0, where=(N < 0), color=FIG_STYLE.POS_ZONE, alpha=0.7,
                    label="N < 0 (tarik)")
    ax.plot(x, N, color=FIG_STYLE.NAVY, lw=2.0, zorder=3)
    ax.axhline(0, color=FIG_STYLE.NAVY, lw=1.0, alpha=0.6)

    ax.set_title(f"Diagram Gaya Aksial  N(x)\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")
    ax.set_xlabel("Panjang Elemen (m)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.set_ylabel("Gaya Aksial N  (kN)", fontsize=8, color=FIG_STYLE.STEEL_GRAY)
    ax.legend(fontsize=7, loc="upper right", framealpha=0.9)
    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)
