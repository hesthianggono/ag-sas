"""
Full Engineering Report — AG-SAS
==================================
Modul untuk menghasilkan laporan rekayasa struktur lengkap
berformat laporan konsultan Indonesia.

Sub-modul:
  numbering.py     — sistem auto-numbering (bab, tabel, gambar, persamaan)
  template.py      — gaya halaman, header/footer, watermark, styles
  cover.py         — halaman cover profesional
  toc.py           — daftar isi, daftar tabel, daftar gambar
  section_builder.py — base helpers section builders
  table_builder.py — helper tabel bernomor
  figure_embedder.py — embed gambar matplotlib dengan caption
  sections/        — builder per bab (s01–s11)
  report_builder.py — orkestrasi semua bab
  pdf_exporter.py  — ekspor PDF final
  report_snapshot.py — snapshot immutable data laporan
"""
from app.reporting.full_report.report_builder import build_full_report
from app.reporting.full_report.report_snapshot import FullReportConfig

__all__ = ["build_full_report", "FullReportConfig"]
