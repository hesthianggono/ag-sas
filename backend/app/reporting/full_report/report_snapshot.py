"""
Report Snapshot — AG-SAS Full Report
======================================
FullReportConfig  : konfigurasi laporan (metadata, engineer, opsi)
FullReportData    : data kalkulasi yang di-snapshot untuk laporan
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional


@dataclass
class EngineerInfo:
    """Data engineer yang menandatangani laporan."""
    name: str
    position: str = ""
    skk: str = ""


@dataclass
class FullReportConfig:
    """
    Konfigurasi metadata laporan.
    Dilewatkan ke semua builder section.
    """
    # Identitas dokumen
    doc_number: str = "AG-SAS/RPT/001"
    revision: str = "A"
    status: str = "DRAFT"               # "DRAFT" | "FINAL"
    report_date: Optional[date] = None  # None → pakai tanggal hari ini

    # Judul & deskripsi
    report_title: str = "Laporan Perhitungan Struktur"
    report_subtitle: str = ""

    # Proyek
    project_name: str = ""
    project_location: str = ""
    owner: str = ""

    # Perusahaan
    company_name: str = "AG Structural Analysis Suite"

    # Engineer (opsional, untuk halaman cover + tanda tangan)
    engineers: list[EngineerInfo] = field(default_factory=list)

    # Opsi gambar
    show_watermark: bool = True
    deform_scale: float = 50.0
    include_figures: bool = True

    # Referensi SNI yang berlaku
    sni_concrete: str = "SNI 2847:2019"
    sni_load: str = "SNI 1727:2020"
    sni_steel: str = "SNI 1729:2020"
    sni_quake: str = "SNI 1726:2019"

    # Pengaturan PDF
    show_appendix: bool = True
    language: str = "id"    # "id" = Bahasa Indonesia


@dataclass
class FullReportData:
    """
    Snapshot data kalkulasi untuk laporan.
    Semua field opsional — builder section akan skip jika None.
    """
    calc_type: str = ""        # "concrete_beam" | "steel_beam"
    calc_title: str = ""
    calc_id: Optional[int] = None
    report_id: Optional[int] = None

    # Input data (dict dari calculation_records.input_data)
    input_data: dict[str, Any] = field(default_factory=dict)

    # Output data (dict dari calculation_records.output_data)
    output_data: dict[str, Any] = field(default_factory=dict)

    # Gambar teknik (FigureSnapshot objects, opsional)
    figure_snapshots: list[Any] = field(default_factory=list)

    # Metadata tambahan
    generated_at: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
