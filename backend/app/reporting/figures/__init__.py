"""
Automatic Report Figures — AG-SAS
===================================
Modul ini menghasilkan gambar teknik (engineering figures) secara otomatis
dari data perhitungan struktur untuk dimasukkan ke laporan PDF.

Sub-modul:
  base.py                 — FigureSpec, auto-caption, gaya gambar
  model_view.py           — Model struktur (undeformed)
  load_diagram.py         — Diagram pembebanan
  internal_force_diagram.py — Diagram N, V, M
  deformed_shape.py       — Deformasi struktur
  reaction_diagram.py     — Reaksi tumpuan
  utilization_map.py      — Rasio utilisasi elemen
  figure_builder.py       — Orkestrasi semua gambar per kalkulasi
"""

from app.reporting.figures.base import FigureSpec, FigureCaptionBuilder, FIG_STYLE
from app.reporting.figures.figure_builder import build_figures_for_calc

__all__ = [
    "FigureSpec",
    "FigureCaptionBuilder",
    "FIG_STYLE",
    "build_figures_for_calc",
]
