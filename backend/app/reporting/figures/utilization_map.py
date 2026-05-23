"""
Utilization Map Figure — AG-SAS
=================================
Menghasilkan gambar rasio utilisasi elemen:
  - Gauge horizontal Mu / φMn
  - Skala warna: hijau (<0.7) → kuning (0.7–1.0) → merah (>1.0)
  - Tabel ringkasan utilisasi
"""
from __future__ import annotations
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.colorbar import ColorbarBase
from matplotlib.cm import ScalarMappable

from app.reporting.figures.base import FIG_STYLE, fig_to_png_bytes, make_fig, watermark


def _util_color(ratio: float) -> str:
    """Warna berdasarkan rasio utilisasi."""
    if ratio <= 0.70:
        return FIG_STYLE.UTIL_SAFE
    elif ratio <= 1.00:
        return FIG_STYLE.UTIL_WARN
    else:
        return FIG_STYLE.UTIL_DANGER


def generate_utilization_map(
    mu_knm: float,
    phi_mn_knm: float,
    capacity_ratio: float,
    calc_type: str,
    input_data: dict,
    output_data: dict,
    caption: str = "",
) -> bytes:
    """
    Generate gambar rasio utilisasi elemen.

    Returns PNG bytes.
    """
    cr = capacity_ratio
    cr_clamped = min(cr, 1.5)   # clip untuk tampilan
    bar_color = _util_color(cr)
    status_str = "AMAN ✓" if cr <= 1.0 else "TIDAK AMAN ✗"
    status_color = FIG_STYLE.UTIL_SAFE if cr <= 1.0 else FIG_STYLE.UTIL_DANGER

    fig, ax = make_fig(width_in=8.5, height_in=4.5)

    # ── Gauge bar horizontal ─────────────────────────────────────────────────
    bar_y = 0.68
    bar_h = 0.18
    bar_x0, bar_x1 = 0.05, 0.95

    # Background track
    ax.add_patch(mpatches.FancyBboxPatch(
        (bar_x0, bar_y), bar_x1 - bar_x0, bar_h,
        boxstyle="round,pad=0.005", transform=ax.transAxes,
        facecolor="#e2e8f0", edgecolor="#cbd5e1", lw=1.0,
        zorder=2, clip_on=False
    ))

    # Zona aman (0–0.7): hijau
    safe_end = min(0.7, cr_clamped / 1.5)
    ax.add_patch(mpatches.FancyBboxPatch(
        (bar_x0, bar_y), safe_end * (bar_x1 - bar_x0), bar_h,
        boxstyle="square,pad=0", transform=ax.transAxes,
        facecolor="#bbf7d0", edgecolor="none", zorder=3, clip_on=False
    ))
    # Zona peringatan (0.7–1.0): kuning
    if cr_clamped > 0.7:
        warn_start = 0.7 / 1.5
        warn_end = min(1.0, cr_clamped) / 1.5
        ax.add_patch(mpatches.FancyBboxPatch(
            (bar_x0 + warn_start * (bar_x1 - bar_x0), bar_y),
            (warn_end - warn_start) * (bar_x1 - bar_x0), bar_h,
            boxstyle="square,pad=0", transform=ax.transAxes,
            facecolor="#fde68a", edgecolor="none", zorder=3, clip_on=False
        ))
    # Zona bahaya (>1.0): merah
    if cr_clamped > 1.0:
        danger_start = 1.0 / 1.5
        danger_end = cr_clamped / 1.5
        ax.add_patch(mpatches.FancyBboxPatch(
            (bar_x0 + danger_start * (bar_x1 - bar_x0), bar_y),
            (danger_end - danger_start) * (bar_x1 - bar_x0), bar_h,
            boxstyle="square,pad=0", transform=ax.transAxes,
            facecolor="#fca5a5", edgecolor="none", zorder=3, clip_on=False
        ))

    # Pointer (needle) — posisi cr
    ptr_x = bar_x0 + (cr_clamped / 1.5) * (bar_x1 - bar_x0)
    ax.annotate("",
                xy=(ptr_x, bar_y + bar_h + 0.05),
                xytext=(ptr_x, bar_y - 0.08),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=bar_color,
                                lw=2.0, mutation_scale=12),
                zorder=6)

    # Label skala
    for val, label in [(0, "0"), (0.5, "0.5"), (0.7, "0.7"), (1.0, "1.0"), (1.5, "1.5")]:
        xp = bar_x0 + (val / 1.5) * (bar_x1 - bar_x0)
        ax.text(xp, bar_y - 0.12, label, ha="center", va="top",
                fontsize=7.5, color=FIG_STYLE.STEEL_GRAY,
                transform=ax.transAxes)
        ax.plot([xp, xp], [bar_y - 0.02, bar_y], transform=ax.transAxes,
                color=FIG_STYLE.STEEL_GRAY, lw=0.8, zorder=7, clip_on=False)

    # Label CR
    ax.text(ptr_x, bar_y + bar_h + 0.10,
            f"Mu/φMn = {cr:.4f}",
            ha="center", va="bottom", fontsize=10,
            color=bar_color, fontweight="bold",
            transform=ax.transAxes)
    ax.text(ptr_x, bar_y + bar_h + 0.22,
            status_str, ha="center", va="bottom",
            fontsize=13, color=status_color, fontweight="bold",
            transform=ax.transAxes)

    # Label zona
    ax.text(bar_x0 + 0.17, bar_y + bar_h / 2, "AMAN", ha="center", va="center",
            fontsize=7.5, color=FIG_STYLE.UTIL_SAFE, fontweight="bold",
            transform=ax.transAxes)
    ax.text(bar_x0 + 0.47, bar_y + bar_h / 2, "PERINGATAN", ha="center", va="center",
            fontsize=7, color=FIG_STYLE.UTIL_WARN, fontweight="bold",
            transform=ax.transAxes)
    if cr <= 1.5:
        ax.text(bar_x0 + 0.75, bar_y + bar_h / 2, "TIDAK AMAN", ha="center", va="center",
                fontsize=7, color=FIG_STYLE.UTIL_DANGER, fontweight="bold",
                transform=ax.transAxes)

    # X label gauge
    ax.text((bar_x0 + bar_x1) / 2, bar_y - 0.22, "Rasio Utilisasi  Mu / φMn",
            ha="center", fontsize=8, color=FIG_STYLE.STEEL_GRAY,
            transform=ax.transAxes)

    # ── Tabel ringkasan ───────────────────────────────────────────────────────
    rows_label = ["Mu (kN·m)", "φMn (kN·m)", "Rasio Mu/φMn", "Status"]
    rows_value = [
        f"{mu_knm:.2f}",
        f"{phi_mn_knm:.2f}",
        f"{cr:.4f}",
        status_str,
    ]
    tbl_x0 = 0.1
    row_h  = 0.075
    tbl_y0 = 0.38
    for i, (lbl, val) in enumerate(zip(rows_label, rows_value)):
        y_row = tbl_y0 - i * row_h
        bg = "#f0fdf4" if i % 2 == 0 else "#f8fafc"
        ax.add_patch(mpatches.FancyBboxPatch(
            (tbl_x0, y_row - row_h * 0.5), 0.4, row_h,
            boxstyle="square,pad=0", transform=ax.transAxes,
            facecolor=bg, edgecolor="#e2e8f0", lw=0.5, zorder=2, clip_on=False))
        ax.text(tbl_x0 + 0.02, y_row, lbl, ha="left", va="center",
                fontsize=8, color=FIG_STYLE.NAVY, fontweight="bold",
                transform=ax.transAxes)
        color_val = status_color if lbl == "Status" else FIG_STYLE.NAVY
        ax.text(tbl_x0 + 0.38, y_row, val, ha="right", va="center",
                fontsize=8, color=color_val,
                fontweight="bold" if lbl == "Status" else "normal",
                transform=ax.transAxes)

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.set_title(f"Peta Rasio Utilisasi Elemen\n{caption}",
                 fontsize=8.5, color=FIG_STYLE.NAVY, pad=8, loc="left")

    ax.axis("off")
    watermark(ax)
    fig.tight_layout()
    return fig_to_png_bytes(fig)
