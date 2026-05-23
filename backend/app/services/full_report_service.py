"""
Full Report Service — AG-SAS
==============================
CRUD dan PDF generation untuk laporan rekayasa lengkap.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.full_report import FullReportRecord
from app.models.figure_snapshot import FigureSnapshot
from app.schemas.full_report import (
    FullReportCreateRequest, FullReportUpdateRequest,
)
from app.reporting.full_report.pdf_exporter import export_full_report_pdf
from app.reporting.full_report.report_snapshot import EngineerInfo


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_full_report(
    req: FullReportCreateRequest,
    user_id: int,
    session: Session,
) -> FullReportRecord:
    """Buat record FullReport baru (belum generate PDF)."""
    # Cek apakah kalkukasi milik user ini
    from app.models.calculation import CalculationRecord  # avoid circular
    calc = session.get(CalculationRecord, req.calc_id)
    if not calc or calc.user_id != user_id:
        raise HTTPException(status_code=404, detail="Calculation not found")

    config_dict = {"engineers": [e.model_dump() for e in req.engineers]}
    rec = FullReportRecord(
        user_id          = user_id,
        calc_id          = req.calc_id,
        doc_number       = req.doc_number,
        revision         = req.revision,
        status           = req.status,
        report_title     = req.report_title,
        report_subtitle  = req.report_subtitle or None,
        project_name     = req.project_name or None,
        project_location = req.project_location or None,
        owner            = req.owner or None,
        company_name     = req.company_name,
        config_json      = json.dumps(config_dict),
        include_figures  = req.include_figures,
        show_watermark   = req.show_watermark,
        show_appendix    = req.show_appendix,
        deform_scale     = req.deform_scale,
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


def get_full_report(
    report_id: int,
    user_id: int,
    session: Session,
) -> FullReportRecord:
    rec = session.get(FullReportRecord, report_id)
    if not rec or rec.user_id != user_id:
        raise HTTPException(status_code=404, detail="Full report not found")
    return rec


def list_full_reports(
    user_id: int,
    session: Session,
    calc_id: Optional[int] = None,
) -> list[FullReportRecord]:
    q = select(FullReportRecord).where(FullReportRecord.user_id == user_id)
    if calc_id:
        q = q.where(FullReportRecord.calc_id == calc_id)
    return list(session.exec(q.order_by(FullReportRecord.created_at.desc())).all())


def update_full_report(
    report_id: int,
    req: FullReportUpdateRequest,
    user_id: int,
    session: Session,
) -> FullReportRecord:
    rec = get_full_report(report_id, user_id, session)
    update_data = req.model_dump(exclude_none=True)

    engineers_list = update_data.pop("engineers", None)
    for k, v in update_data.items():
        setattr(rec, k, v)

    if engineers_list is not None:
        cfg = {}
        if rec.config_json:
            try:
                cfg = json.loads(rec.config_json)
            except Exception:
                pass
        cfg["engineers"] = [e.model_dump() for e in engineers_list]
        rec.config_json = json.dumps(cfg)

    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


def delete_full_report(
    report_id: int,
    user_id: int,
    session: Session,
) -> None:
    rec = get_full_report(report_id, user_id, session)
    session.delete(rec)
    session.commit()


# ── PDF Generation ────────────────────────────────────────────────────────────

def generate_full_report_pdf(
    report_id: int,
    user_id: int,
    session: Session,
) -> bytes:
    """
    Generate PDF laporan rekayasa lengkap.
    Return raw PDF bytes.
    """
    rec = get_full_report(report_id, user_id, session)

    # Ambil data kalkulasi
    from app.models.calculation import CalculationRecord
    calc = session.get(CalculationRecord, rec.calc_id)
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    # Ambil figure snapshots (dari report_records terkait calc, jika ada)
    fig_snaps = list(session.exec(
        select(FigureSnapshot)
        .where(FigureSnapshot.calc_id == rec.calc_id)
        .where(FigureSnapshot.user_id == user_id)
        .where(FigureSnapshot.is_visible == True)
        .order_by(FigureSnapshot.order_index)
    ).all()) if rec.include_figures else []

    # Ambil engineers dari config_json
    engineers_raw = []
    if rec.config_json:
        try:
            cfg = json.loads(rec.config_json)
            engineers_raw = cfg.get("engineers", [])
        except Exception:
            pass

    # Generate PDF
    pdf_bytes = export_full_report_pdf(
        calc_type        = calc.calc_type or "",
        input_data       = calc.input_data or {},
        output_data      = calc.output_data or {},
        calc_title       = calc.title or "",
        calc_id          = calc.id,
        report_id        = rec.id,
        figure_snapshots = fig_snaps or None,
        project_name     = rec.project_name or "",
        project_location = rec.project_location or "",
        owner            = rec.owner or "",
        doc_number       = rec.doc_number,
        revision         = rec.revision,
        status           = rec.status,
        report_title     = rec.report_title,
        company_name     = rec.company_name,
        engineers        = engineers_raw,
        show_watermark   = rec.show_watermark,
        deform_scale     = rec.deform_scale,
        include_figures  = rec.include_figures,
        show_appendix    = rec.show_appendix,
    )

    # Update generated_at
    rec.generated_at = datetime.utcnow()
    session.add(rec)
    session.commit()

    return pdf_bytes
