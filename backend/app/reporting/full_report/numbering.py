"""
Auto-Numbering System — AG-SAS Full Report
===========================================
Mengelola penomoran otomatis untuk:
  - Bab (Chapter): 1, 2, 3 ...
  - Subbab: 1.1, 1.2, 2.1 ...
  - Sub-subbab: 1.1.1, 1.1.2 ...
  - Tabel: Tabel 3.1, Tabel 3.2 ...
  - Gambar: Gambar 5.1, Gambar 5.2 ...
  - Persamaan: (7.1), (7.2) ...
  - Lampiran: Lampiran A, Lampiran B ...

Penggunaan:
    ctx = NumberingContext()
    ctx.chapter(1, "Pendahuluan")
    ctx.table("Data Proyek")    → "Tabel 1.1  Data Proyek"
    ctx.figure("Model Struktur") → "Gambar 1.1  Model Struktur"
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TocEntry:
    """Satu baris daftar isi."""
    level: int          # 0=bab, 1=subbab, 2=sub-subbab
    number: str         # "1", "1.1", "1.1.1"
    title: str
    page_ref: str = ""  # diisi setelah render


@dataclass
class TableEntry:
    number: str         # "Tabel 3.2"
    caption: str
    page_ref: str = ""


@dataclass
class FigureEntry:
    number: str         # "Gambar 5.1"
    caption: str
    page_ref: str = ""


class NumberingContext:
    """
    Konteks penomoran untuk satu dokumen laporan.
    Instance tunggal dilewatkan ke semua section builder.
    """

    def __init__(self):
        self._chapter: int = 0
        self._sub: int = 0
        self._subsub: int = 0
        self._table: int = 0
        self._figure: int = 0
        self._equation: int = 0
        self._appendix: int = -1   # 0=A, 1=B, …
        self._appendix_table: int = 0
        self._appendix_figure: int = 0

        self.toc: list[TocEntry] = []
        self.lot: list[TableEntry] = []     # list of tables
        self.lof: list[FigureEntry] = []    # list of figures

    # ── Chapter / Subbab ──────────────────────────────────────────────────────

    def chapter(self, num: int, title: str) -> str:
        """Mulai bab baru. Return label "1  Pendahuluan"."""
        self._chapter = num
        self._sub = 0
        self._subsub = 0
        self._table = 0
        self._figure = 0
        self._equation = 0
        label = f"{num}"
        self.toc.append(TocEntry(level=0, number=label, title=title))
        return f"{label}  {title}"

    def subchapter(self, title: str) -> str:
        """Mulai subbab. Return label "1.1  Judul"."""
        self._sub += 1
        self._subsub = 0
        label = f"{self._chapter}.{self._sub}"
        self.toc.append(TocEntry(level=1, number=label, title=title))
        return f"{label}  {title}"

    def subsubchapter(self, title: str) -> str:
        """Return label "1.1.1  Judul"."""
        self._subsub += 1
        label = f"{self._chapter}.{self._sub}.{self._subsub}"
        self.toc.append(TocEntry(level=2, number=label, title=title))
        return f"{label}  {title}"

    # ── Table ─────────────────────────────────────────────────────────────────

    def table(self, caption: str) -> str:
        """Return "Tabel 3.2  Judul tabel" dan daftarkan ke LoT."""
        self._table += 1
        num = f"Tabel {self._chapter}.{self._table}"
        entry = TableEntry(number=num, caption=caption)
        self.lot.append(entry)
        return f"{num}  {caption}"

    def table_num(self, caption: str) -> tuple[str, str]:
        """Return (number_str, full_caption). Mis: ("Tabel 3.2", "Tabel 3.2  ...")"""
        full = self.table(caption)
        num = f"Tabel {self._chapter}.{self._table}"
        return num, full

    # ── Figure ────────────────────────────────────────────────────────────────

    def figure(self, caption: str) -> str:
        """Return "Gambar 5.1  Judul gambar" dan daftarkan ke LoF."""
        self._figure += 1
        num = f"Gambar {self._chapter}.{self._figure}"
        entry = FigureEntry(number=num, caption=caption)
        self.lof.append(entry)
        return f"{num}  {caption}"

    def figure_num(self, caption: str) -> tuple[str, str]:
        """Return (number_str, full_caption)."""
        full = self.figure(caption)
        num = f"Gambar {self._chapter}.{self._figure}"
        return num, full

    # ── Equation ──────────────────────────────────────────────────────────────

    def equation(self) -> str:
        """Return "(3.2)" untuk referensi persamaan."""
        self._equation += 1
        return f"({self._chapter}.{self._equation})"

    # ── Appendix ──────────────────────────────────────────────────────────────

    def appendix(self, title: str) -> str:
        """Mulai lampiran baru. Return "Lampiran A  Judul"."""
        self._appendix += 1
        self._appendix_table = 0
        self._appendix_figure = 0
        letter = chr(ord("A") + self._appendix)
        self.toc.append(TocEntry(level=0, number=f"Lampiran {letter}", title=title))
        return f"Lampiran {letter}  {title}"

    def appendix_table(self, caption: str) -> str:
        """Return "Tabel A.1  ..."."""
        self._appendix_table += 1
        letter = chr(ord("A") + self._appendix)
        num = f"Tabel {letter}.{self._appendix_table}"
        self.lot.append(TableEntry(number=num, caption=caption))
        return f"{num}  {caption}"

    def appendix_figure(self, caption: str) -> str:
        """Return "Gambar A.1  ..."."""
        self._appendix_figure += 1
        letter = chr(ord("A") + self._appendix)
        num = f"Gambar {letter}.{self._appendix_figure}"
        self.lof.append(FigureEntry(number=num, caption=caption))
        return f"{num}  {caption}"

    # ── State ─────────────────────────────────────────────────────────────────

    @property
    def current_chapter(self) -> int:
        return self._chapter

    @property
    def current_sub(self) -> int:
        return self._sub
