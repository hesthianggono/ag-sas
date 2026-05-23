"""
PDF Exporter — AG-SAS Full Report
====================================
Thin wrapper atas report_builder.build_full_report().
Disediakan sebagai entry point yang bisa dipanggil dari service layer,
dengan konversi FullReportConfig dari dict / Pydantic model.
"""
from __future__ import annotations

from typing import Any

from app.reporting.full_report.report_builder import build_full_report
from app.reporting.full_report.report_snapshot import (
    FullReportConfig, FullReportData, EngineerInfo,
)


def export_full_report_pdf(
    *,
    config: FullReportConfig | None = None,
    data: FullReportData | None = None,
    # Shortcut params (digunakan jika config/data tidak disediakan)
    calc_type: str = "",
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
    calc_title: str = "",
    calc_id: int | None = None,
    report_id: int | None = None,
    figure_snapshots: list | None = None,
    project_name: str = "",
    project_location: str = "",
    owner: str = "",
    doc_number: str = "AG-SAS/RPT/001",
    revision: str = "A",
    status: str = "DRAFT",
    report_title: str = "Laporan Perhitungan Struktur",
    company_name: str = "AG Structural Analysis Suite",
    engineers: list[dict] | None = None,
    show_watermark: bool = True,
    deform_scale: float = 50.0,
    include_figures: bool = True,
    show_appendix: bool = True,
) -> bytes:
    """
    Generate full report PDF dan return bytes.

    Bisa dipanggil dengan objek config+data yang sudah siap,
    atau dengan parameter individual (shortcut).
    """
    if config is None:
        eng_objects = [
            EngineerInfo(
                name=e.get("name", ""),
                position=e.get("position", ""),
                skk=e.get("skk", ""),
            )
            for e in (engineers or [])
        ]
        config = FullReportConfig(
            doc_number=doc_number,
            revision=revision,
            status=status,
            report_title=report_title,
            project_name=project_name,
            project_location=project_location,
            owner=owner,
            company_name=company_name,
            engineers=eng_objects,
            show_watermark=show_watermark,
            deform_scale=deform_scale,
            include_figures=include_figures,
            show_appendix=show_appendix,
        )

    if data is None:
        data = FullReportData(
            calc_type=calc_type,
            calc_title=calc_title,
            calc_id=calc_id,
            report_id=report_id,
            input_data=input_data or {},
            output_data=output_data or {},
            figure_snapshots=figure_snapshots or [],
        )

    return build_full_report(config, data)
