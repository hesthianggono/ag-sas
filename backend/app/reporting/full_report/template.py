"""
Page Template, Styles, Header/Footer, Watermark — AG-SAS Full Report
======================================================================
Menyediakan:
  - Palet warna konsisten
  - ParagraphStyle untuk semua tipe teks
  - build_doc()  → SimpleDocTemplate dengan margin laporan
  - make_page_template()  → PageTemplate dengan header/footer
  - watermark_canvas()  → DRAFT / FINAL diagonal watermark
"""
from __future__ import annotations

import math
import os
from typing import NamedTuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate

# ── Ukuran halaman ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4          # 595.3 × 841.9 pt
MARGIN_L = 3.0 * cm
MARGIN_R = 2.5 * cm
MARGIN_T = 2.5 * cm
MARGIN_B = 2.5 * cm
HEADER_H = 1.4 * cm
FOOTER_H = 1.2 * cm

# ── Palet warna ────────────────────────────────────────────────────────────────
class Palette:
    NAVY        = colors.HexColor("#1e3a5f")
    BLUE        = colors.HexColor("#2563eb")
    STEEL       = colors.HexColor("#475569")
    LIGHT_GRAY  = colors.HexColor("#f1f5f9")
    MID_GRAY    = colors.HexColor("#94a3b8")
    LINE_GRAY   = colors.HexColor("#cbd5e1")
    GREEN       = colors.HexColor("#16a34a")
    RED         = colors.HexColor("#dc2626")
    AMBER       = colors.HexColor("#d97706")
    WHITE       = colors.white
    BLACK       = colors.black
    TABLE_HEAD  = colors.HexColor("#1e3a5f")   # header baris tabel
    TABLE_ALT   = colors.HexColor("#f8fafc")   # baris selang-seling
    WATERMARK   = colors.HexColor("#e2e8f0")   # warna watermark DRAFT

P = Palette  # alias pendek


# ── Font Unicode ────────────────────────────────────────────────────────────────
def _setup_fonts() -> tuple[str, str, str, str]:
    """
    Daftarkan Arial / Liberation Sans TTF agar karakter Unicode tampil benar.
    Cek beberapa lokasi: Windows, Linux (Render/Docker), fallback Helvetica.
    """
    # Kandidat path: Windows → Linux symlink (Dockerfile) → Liberation Sans asli
    font_search = [
        # Windows
        (r"C:\Windows\Fonts\arial.ttf",   r"C:\Windows\Fonts\arialbd.ttf",
         r"C:\Windows\Fonts\ariali.ttf",   r"C:\Windows\Fonts\arialbi.ttf"),
        # Linux symlink yang dibuat di Dockerfile
        ("/usr/share/fonts/truetype/msttcorefonts/arial.ttf",
         "/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf",
         "/usr/share/fonts/truetype/msttcorefonts/ariali.ttf",
         "/usr/share/fonts/truetype/msttcorefonts/arialbi.ttf"),
        # Liberation Sans (metric-compatible dengan Arial)
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"),
    ]

    for reg_p, bold_p, ital_p, bdit_p in font_search:
        if all(os.path.exists(p) for p in (reg_p, bold_p, ital_p, bdit_p)):
            try:
                pdfmetrics.registerFont(TTFont("ArialFR",  reg_p))
                pdfmetrics.registerFont(TTFont("ArialFB",  bold_p))
                pdfmetrics.registerFont(TTFont("ArialFI",  ital_p))
                pdfmetrics.registerFont(TTFont("ArialFBI", bdit_p))
                return ("ArialFR", "ArialFB", "ArialFI", "ArialFBI")
            except Exception:
                continue

    # Fallback jika tidak ada font TTF sama sekali
    return ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-Bold")


FREG, FBOLD, FITAL, FBDIT = _setup_fonts()


# ── ParagraphStyles ────────────────────────────────────────────────────────────
def build_styles() -> dict[str, ParagraphStyle]:
    """Return dict of ParagraphStyle yang digunakan di seluruh laporan."""
    base = getSampleStyleSheet()

    def s(name, **kw) -> ParagraphStyle:
        parent = kw.pop("parent", "Normal")
        return ParagraphStyle(name, parent=base[parent], **kw)

    styles: dict[str, ParagraphStyle] = {}

    # ── Judul dokumen (cover) ──────────────────────────────────────────────────
    styles["DocTitle"] = s("DocTitle",
        fontName=FBOLD, fontSize=18, textColor=P.NAVY,
        alignment=TA_CENTER, spaceAfter=6, leading=22)

    styles["DocSubtitle"] = s("DocSubtitle",
        fontName=FITAL, fontSize=12, textColor=P.STEEL,
        alignment=TA_CENTER, spaceAfter=4, leading=15)

    styles["CoverMeta"] = s("CoverMeta",
        fontName=FREG, fontSize=10, textColor=P.STEEL,
        alignment=TA_CENTER, spaceAfter=3, leading=14)

    styles["CoverMetaBold"] = s("CoverMetaBold",
        fontName=FBOLD, fontSize=10, textColor=P.NAVY,
        alignment=TA_CENTER, spaceAfter=3, leading=14)

    # ── Heading bab ───────────────────────────────────────────────────────────
    styles["H1"] = s("H1",
        fontName=FBOLD, fontSize=14, textColor=P.NAVY,
        spaceBefore=14, spaceAfter=6, leading=18,
        keepWithNext=1)

    styles["H2"] = s("H2",
        fontName=FBOLD, fontSize=12, textColor=P.NAVY,
        spaceBefore=10, spaceAfter=4, leading=16,
        keepWithNext=1)

    styles["H3"] = s("H3",
        fontName=FBOLD, fontSize=11, textColor=P.STEEL,
        spaceBefore=8, spaceAfter=3, leading=14,
        keepWithNext=1)

    # ── Teks utama ────────────────────────────────────────────────────────────
    styles["Body"] = s("Body",
        fontName=FREG, fontSize=10, textColor=P.BLACK,
        alignment=TA_JUSTIFY, leading=15, spaceAfter=4)

    styles["BodyLeft"] = s("BodyLeft",
        fontName=FREG, fontSize=10, textColor=P.BLACK,
        alignment=TA_LEFT, leading=15, spaceAfter=4)

    styles["Small"] = s("Small",
        fontName=FREG, fontSize=9, textColor=P.STEEL,
        leading=13, spaceAfter=2)

    styles["SmallBold"] = s("SmallBold",
        fontName=FBOLD, fontSize=9, textColor=P.NAVY,
        leading=13, spaceAfter=2)

    # ── Caption tabel / gambar ─────────────────────────────────────────────────
    styles["TableCaption"] = s("TableCaption",
        fontName=FBOLD, fontSize=9, textColor=P.NAVY,
        alignment=TA_LEFT, spaceBefore=4, spaceAfter=2, leading=12)

    styles["FigureCaption"] = s("FigureCaption",
        fontName=FITAL, fontSize=9, textColor=P.STEEL,
        alignment=TA_CENTER, spaceBefore=3, spaceAfter=6, leading=12)

    # ── Tabel header / isi ────────────────────────────────────────────────────
    styles["TH"] = s("TH",
        fontName=FBOLD, fontSize=9, textColor=P.WHITE,
        alignment=TA_CENTER, leading=12)

    styles["TD"] = s("TD",
        fontName=FREG, fontSize=9, textColor=P.BLACK,
        alignment=TA_CENTER, leading=12)

    styles["TDLeft"] = s("TDLeft",
        fontName=FREG, fontSize=9, textColor=P.BLACK,
        alignment=TA_LEFT, leading=12)

    styles["TDRight"] = s("TDRight",
        fontName=FREG, fontSize=9, textColor=P.BLACK,
        alignment=TA_RIGHT, leading=12)

    styles["TDBold"] = s("TDBold",
        fontName=FBOLD, fontSize=9, textColor=P.NAVY,
        alignment=TA_CENTER, leading=12)

    # ── TOC entries ───────────────────────────────────────────────────────────
    styles["TocH1"] = s("TocH1",
        fontName=FBOLD, fontSize=10, textColor=P.NAVY,
        spaceBefore=4, spaceAfter=1, leading=14)

    styles["TocH2"] = s("TocH2",
        fontName=FREG, fontSize=9.5, textColor=P.BLACK,
        leftIndent=16, spaceBefore=1, spaceAfter=1, leading=13)

    styles["TocH3"] = s("TocH3",
        fontName=FREG, fontSize=9, textColor=P.STEEL,
        leftIndent=30, spaceBefore=0, spaceAfter=1, leading=12)

    # ── Persamaan ─────────────────────────────────────────────────────────────
    styles["Equation"] = s("Equation",
        fontName=FREG, fontSize=10, textColor=P.BLACK,
        alignment=TA_CENTER, spaceBefore=4, spaceAfter=4, leading=15)

    # ── Keterangan / catatan ──────────────────────────────────────────────────
    styles["Note"] = s("Note",
        fontName=FITAL, fontSize=9, textColor=P.STEEL,
        leftIndent=12, leading=13, spaceAfter=4)

    styles["Warning"] = s("Warning",
        fontName=FBOLD, fontSize=9, textColor=P.RED,
        leftIndent=12, leading=13, spaceAfter=4)

    styles["OK"] = s("OK",
        fontName=FBOLD, fontSize=9, textColor=P.GREEN,
        leftIndent=12, leading=13, spaceAfter=4)

    # ── Header/footer teks ─────────────────────────────────────────────────────
    styles["HeaderText"] = s("HeaderText",
        fontName=FBOLD, fontSize=8, textColor=P.NAVY,
        alignment=TA_LEFT, leading=10)

    styles["FooterText"] = s("FooterText",
        fontName=FREG, fontSize=8, textColor=P.STEEL,
        alignment=TA_LEFT, leading=10)

    return styles


# ── SimpleDocTemplate ──────────────────────────────────────────────────────────
def build_doc(buffer, doc_info: dict | None = None) -> SimpleDocTemplate:
    """
    Buat SimpleDocTemplate A4 dengan margin laporan konsultan.

    doc_info opsional: {"title": ..., "author": ..., "subject": ...}
    """
    info = doc_info or {}
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T + HEADER_H + 4 * mm,
        bottomMargin=MARGIN_B + FOOTER_H + 4 * mm,
        title=info.get("title", "Laporan Rekayasa Struktur"),
        author=info.get("author", "AG-SAS"),
        subject=info.get("subject", "Structural Analysis"),
        creator="AG-SAS v1.0",
    )
    return doc


# ── Header / Footer canvas callback ──────────────────────────────────────────
class DocMeta(NamedTuple):
    project_title: str = "Proyek Tidak Disebutkan"
    doc_number: str = "AG-SAS/RPT/001"
    revision: str = "A"
    company_name: str = "AG Structural Analysis Suite"
    status: str = "DRAFT"          # "DRAFT" | "FINAL"
    show_watermark: bool = True


def make_header_footer_cb(meta: DocMeta):
    """
    Return canvas callback `on_page(canvas, doc)` untuk header & footer.
    Dipanggil oleh ReportLab setiap kali halaman baru di-render.
    """
    def on_page(c, doc):
        c.saveState()
        w, h = A4

        # ── Watermark diagonal ─────────────────────────────────────────────
        if meta.show_watermark and meta.status == "DRAFT":
            _draw_watermark(c, w, h, "DRAFT")

        page_no = doc.page

        # ── Header ────────────────────────────────────────────────────────
        hx = MARGIN_L
        hy = h - MARGIN_T - HEADER_H
        hw = w - MARGIN_L - MARGIN_R

        # Garis atas header
        c.setStrokeColor(P.NAVY)
        c.setLineWidth(1.5)
        c.line(hx, hy + HEADER_H, hx + hw, hy + HEADER_H)

        # Garis bawah header (tipis)
        c.setLineWidth(0.5)
        c.setStrokeColor(P.LINE_GRAY)
        c.line(hx, hy, hx + hw, hy)

        # Teks header kiri: nama perusahaan
        c.setFont(FBOLD, 8)
        c.setFillColor(P.NAVY)
        c.drawString(hx, hy + HEADER_H * 0.55, meta.company_name)

        # Teks header tengah: judul proyek
        c.setFont(FITAL, 8)
        c.setFillColor(P.STEEL)
        c.drawCentredString(hx + hw / 2, hy + HEADER_H * 0.55, meta.project_title)

        # Teks header kanan: nomor dokumen + revisi
        c.setFont(FREG, 8)
        c.setFillColor(P.STEEL)
        doc_rev = f"{meta.doc_number} | Rev. {meta.revision}"
        c.drawRightString(hx + hw, hy + HEADER_H * 0.55, doc_rev)

        # ── Footer ────────────────────────────────────────────────────────
        fy = MARGIN_B
        fw = hw

        c.setStrokeColor(P.LINE_GRAY)
        c.setLineWidth(0.5)
        c.line(hx, fy + FOOTER_H, hx + fw, fy + FOOTER_H)

        c.setStrokeColor(P.NAVY)
        c.setLineWidth(1.2)
        c.line(hx, fy, hx + fw, fy)

        # Teks footer kiri
        c.setFont(FREG, 7.5)
        c.setFillColor(P.STEEL)
        c.drawString(hx, fy + FOOTER_H * 0.35,
                     "AG-SAS — Analisis Struktur Teknik Sipil")

        # Status DRAFT/FINAL di tengah footer
        if meta.status == "DRAFT":
            c.setFont(FBOLD, 7.5)
            c.setFillColor(P.AMBER)
        else:
            c.setFont(FBOLD, 7.5)
            c.setFillColor(P.GREEN)
        c.drawCentredString(hx + fw / 2, fy + FOOTER_H * 0.35,
                            f"[ {meta.status} ]")

        # Nomor halaman di kanan
        c.setFont(FREG, 7.5)
        c.setFillColor(P.STEEL)
        c.drawRightString(hx + fw, fy + FOOTER_H * 0.35,
                          f"Halaman {page_no}")

        c.restoreState()

    return on_page


def _draw_watermark(c, page_w: float, page_h: float, text: str = "DRAFT"):
    """Gambar teks diagonal samar di tengah halaman."""
    c.saveState()
    c.translate(page_w / 2, page_h / 2)
    c.rotate(45)
    c.setFont(FBOLD, 72)
    c.setFillColor(P.WATERMARK)
    c.setFillAlpha(0.25)
    c.drawCentredString(0, 0, text)
    c.restoreState()


# ── Cover-page canvas (tanpa header/footer) ───────────────────────────────────
def make_cover_cb(meta: DocMeta):
    """Canvas callback khusus halaman cover — tidak ada header/footer normal."""
    def on_cover(c, doc):
        c.saveState()
        w, h = A4
        # Band atas biru tua
        c.setFillColor(P.NAVY)
        c.rect(0, h - 5.5 * cm, w, 5.5 * cm, fill=1, stroke=0)
        # Band bawah biru tua
        c.setFillColor(P.NAVY)
        c.rect(0, 0, w, 2.0 * cm, fill=1, stroke=0)
        # Teks band bawah
        c.setFont(FREG, 8)
        c.setFillColor(P.WHITE)
        c.drawCentredString(w / 2, 0.65 * cm,
                            f"{meta.doc_number}  |  Rev. {meta.revision}  |  {meta.status}")
        c.restoreState()

    return on_cover
