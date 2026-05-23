"""
Figure Embedder — AG-SAS Full Report
======================================
Meng-embed gambar matplotlib (PNG bytes) ke dalam PDF ReportLab,
dengan caption bernomor otomatis dari NumberingContext.
"""
from __future__ import annotations

import io
from typing import Any

from reportlab.lib.units import cm, mm
from reportlab.platypus import Image as RLImage, Paragraph, Spacer, KeepTogether

from app.reporting.full_report.numbering import NumberingContext
from app.reporting.full_report.template import P, PAGE_W, MARGIN_L, MARGIN_R, build_styles

_S = build_styles()
USABLE_W = PAGE_W - MARGIN_L - MARGIN_R

# Lebar gambar default: 90% lebar berguna
DEFAULT_IMG_W = USABLE_W * 0.92


def embed_figure(
    ctx: NumberingContext,
    png_bytes: bytes,
    caption_text: str,
    *,
    width: float = DEFAULT_IMG_W,
    keep_together: bool = True,
) -> list[Any]:
    """
    Embed satu gambar PNG ke laporan.

    Return list flowables:
      [caption_para, image, spacer]
    Atau dibungkus KeepTogether agar tidak terpisah halaman.

    Parameters
    ----------
    ctx          : NumberingContext — mengelola penomoran otomatis
    png_bytes    : bytes PNG dari matplotlib
    caption_text : teks singkat, e.g. "Diagram Momen Lentur M(x)"
    width        : lebar gambar di PDF (pt), tinggi proporsional otomatis
    keep_together: wrap dengan KeepTogether agar tidak pecah antar halaman
    """
    caption_full = ctx.figure(caption_text)

    buf = io.BytesIO(png_bytes)
    img = RLImage(buf, width=width)
    img.hAlign = "CENTER"

    flowables: list[Any] = [
        Paragraph(caption_full, _S["FigureCaption"]),
        img,
        Spacer(1, 5 * mm),
    ]

    if keep_together:
        return [KeepTogether(flowables)]
    return flowables


def embed_figure_list(
    ctx: NumberingContext,
    figures: list[tuple[bytes, str]],
    *,
    width: float = DEFAULT_IMG_W,
) -> list[Any]:
    """
    Embed beberapa gambar sekaligus.

    figures: list of (png_bytes, caption_text)
    """
    story: list[Any] = []
    for png_bytes, caption in figures:
        story.extend(embed_figure(ctx, png_bytes, caption, width=width))
    return story
