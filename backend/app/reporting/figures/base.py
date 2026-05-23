"""
Base Types & Styling — AG-SAS Report Figures
=============================================
Mendefinisikan:
  - FigureSpec     : dataclass untuk satu gambar teknik
  - FigureCaptionBuilder : sistem penomoran gambar otomatis
  - FIG_STYLE      : konstanta warna dan gaya matplotlib
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import matplotlib
matplotlib.use("Agg")          # non-interactive backend — aman untuk server
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure


# ── Color palette (konsisten dengan PDF) ─────────────────────────────────────

class FIG_STYLE:
    NAVY        = "#1e3a5f"
    BLUE        = "#2563eb"
    STEEL_GRAY  = "#475569"
    LIGHT_BG    = "#f8fafc"
    GRID_COLOR  = "#e2e8f0"
    GREEN       = "#16a34a"
    RED         = "#dc2626"
    ORANGE      = "#ea580c"
    AMBER       = "#d97706"
    NEUTRAL     = "#94a3b8"
    WHITE       = "#ffffff"
    # Diagram zone colors
    POS_ZONE    = "#dbeafe"    # momen positif (biru muda)
    NEG_ZONE    = "#fee2e2"    # momen negatif (merah muda)
    POS_LINE    = "#2563eb"    # garis positif
    NEG_LINE    = "#dc2626"    # garis negatif
    LOAD_COLOR  = "#ea580c"    # warna beban
    DEFORM_COLOR= "#7c3aed"    # warna deformasi
    # Utilisasi
    UTIL_SAFE   = "#16a34a"
    UTIL_WARN   = "#d97706"
    UTIL_DANGER = "#dc2626"

    # Matplotlib rcParams defaults
    FONT_FAMILY = "DejaVu Sans"
    FONT_SIZE   = 8
    TITLE_SIZE  = 9
    LABEL_SIZE  = 8

    @staticmethod
    def apply_global():
        """Terapkan gaya global ke matplotlib."""
        plt.rcParams.update({
            "font.family":        "DejaVu Sans",
            "font.size":          8,
            "axes.titlesize":     9,
            "axes.labelsize":     8,
            "xtick.labelsize":    7.5,
            "ytick.labelsize":    7.5,
            "axes.spines.top":    False,
            "axes.spines.right":  False,
            "axes.grid":          True,
            "grid.color":         FIG_STYLE.GRID_COLOR,
            "grid.linewidth":     0.5,
            "grid.alpha":         0.8,
            "figure.facecolor":   FIG_STYLE.WHITE,
            "axes.facecolor":     FIG_STYLE.LIGHT_BG,
            "lines.linewidth":    1.8,
            "savefig.dpi":        150,
            "savefig.bbox":       "tight",
            "savefig.facecolor":  FIG_STYLE.WHITE,
        })


# ── FigureSpec ────────────────────────────────────────────────────────────────

@dataclass
class FigureSpec:
    """Satu gambar teknik dengan metadata lengkap."""
    figure_key: str              # "model_view", "load_diagram", "moment_diagram", …
    title: str                   # "Model Struktur"
    caption: str                 # "Gambar 3.1  Model struktur balok sederhana …"
    figure_number: str           # "3.1"
    section: str                 # "3"
    load_case: str | None        # "DL+LL", None
    load_combination: str | None # "1.2D + 1.6L", None
    scale_factor: float | None   # untuk deformasi: 50, 100, dsb.
    unit: str                    # "kN, m"
    timestamp: datetime          # waktu generate
    source_result_id: int | None # FK ke CalculationRecord / ReportRecord
    source: str                  # "backend" | "frontend"
    png_bytes: bytes             # PNG image bytes
    svg_data: str | None         # SVG teks (opsional)
    json_data: dict[str, Any] | None  # data mentah diagram

    order_index: int = 0


# ── Auto-caption Builder ──────────────────────────────────────────────────────

class FigureCaptionBuilder:
    """
    Membangun penomoran gambar otomatis.

    Contoh penggunaan:
        builder = FigureCaptionBuilder(section="4")
        cap = builder.next("model_view", "Model struktur portal 2D")
        # -> FigureMeta(number="4.1", caption="Gambar 4.1  Model struktur portal 2D")
    """

    _DEFAULT_SECTION = "4"

    def __init__(self, section: str = _DEFAULT_SECTION):
        self._section = section
        self._counter = 0
        self._index: dict[str, int] = {}   # figure_key -> order_index

    def next(self, figure_key: str, base_title: str,
             suffix: str = "") -> tuple[str, str]:
        """
        Return (figure_number, caption).
        suffix bisa berisi detail, mis. "kombinasi COMB-01" atau "faktor skala 50×".
        """
        self._counter += 1
        self._index[figure_key] = self._counter
        num = f"{self._section}.{self._counter}"
        caption_title = f"{base_title}{(' — ' + suffix) if suffix else ''}"
        caption = f"Gambar {num}  {caption_title}"
        return num, caption

    def order_of(self, figure_key: str) -> int:
        return self._index.get(figure_key, 0)


# ── Helper: fig_to_png_bytes ──────────────────────────────────────────────────

def fig_to_png_bytes(fig: Figure, dpi: int = 150) -> bytes:
    """Konversi Figure matplotlib ke bytes PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def fig_to_svg_str(fig: Figure) -> str:
    """Konversi Figure matplotlib ke string SVG."""
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def make_fig(width_in: float = 8.0, height_in: float = 3.5) -> tuple[Figure, Any]:
    """Buat Figure + Axes dengan gaya standar AG-SAS."""
    FIG_STYLE.apply_global()
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    fig.patch.set_facecolor(FIG_STYLE.WHITE)
    ax.set_facecolor(FIG_STYLE.LIGHT_BG)
    return fig, ax


def watermark(ax, text: str = "AG-SAS"):
    """Tambahkan watermark ringan."""
    ax.text(0.99, 0.01, text,
            transform=ax.transAxes,
            fontsize=6.5, color=FIG_STYLE.NEUTRAL,
            ha="right", va="bottom", alpha=0.6,
            fontfamily="DejaVu Sans")
