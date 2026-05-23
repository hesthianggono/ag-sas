"""
API Layer: Laporan Perhitungan
================================
Endpoint untuk generate, preview, dan download laporan perhitungan.

POST /reports/generate          — Buat ReportRecord baru dari calc_id
GET  /reports/{id}/preview      — Kembalikan HTML laporan (text/html)
GET  /reports/{id}/download     — Kembalikan PDF laporan (StreamingResponse)
GET  /reports/                  — Daftar laporan milik user (opsional filter project_id)
"""
from typing import List, Optional
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlmodel import Session, select

from app.db.session import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.models.report import ReportRecord
from app.schemas.report import GenerateReportRequest, ReportRecordResponse
from app.services.report_service import (
    generate_report, build_pdf_for_report, get_report_or_404,
    CalcNotFoundError, ReportNotFoundError,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "/generate",
    response_model=ReportRecordResponse,
    status_code=201,
    summary="Generate laporan dari perhitungan yang sudah ada",
    description=(
        "Buat ReportRecord baru: render HTML dari CalculationRecord yang dipilih, "
        "lalu simpan ke database. HTML tersimpan untuk preview instan."
    ),
)
def generate_report_endpoint(
    body: GenerateReportRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return generate_report(
            session=session,
            calc_id=body.calc_id,
            user_id=current_user.id,
            engineer_name=body.engineer_name,
            engineer_position=body.engineer_position,
            engineer_skk=body.engineer_skk,
        )
    except CalcNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/",
    response_model=List[ReportRecordResponse],
    summary="Daftar laporan yang sudah digenerate",
)
def list_reports(
    project_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    q = select(ReportRecord).where(ReportRecord.user_id == current_user.id)
    if project_id:
        q = q.where(ReportRecord.project_id == project_id)
    q = q.order_by(ReportRecord.generated_at.desc())
    return session.exec(q).all()


@router.get(
    "/{report_id}/preview",
    response_class=HTMLResponse,
    summary="Preview HTML laporan di browser",
    description="Kembalikan HTML laporan yang sudah tersimpan. Buka di browser untuk preview.",
)
def preview_report(
    report_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        report = get_report_or_404(session=session, report_id=report_id, user_id=current_user.id)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not report.html_content:
        raise HTTPException(status_code=404, detail="HTML preview belum tersedia untuk laporan ini")

    return HTMLResponse(content=report.html_content)


@router.get(
    "/{report_id}/download",
    summary="Download laporan dalam format PDF",
    description=(
        "Generate PDF dari snapshot data laporan dan kembalikan sebagai file download. "
        "PDF menggunakan data yang tersimpan saat laporan digenerate."
    ),
)
def download_report_pdf(
    report_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        pdf_bytes = build_pdf_for_report(session=session, report_id=report_id, user_id=current_user.id)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    report = session.get(ReportRecord, report_id)
    safe_title = report.title.replace(" ", "_").replace("/", "-")[:40]
    filename = f"AG-SAS_{report.calc_type}_{safe_title}_{report_id}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{report_id}",
    response_model=ReportRecordResponse,
    summary="Detail satu laporan",
)
def get_report(
    report_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_report_or_404(session=session, report_id=report_id, user_id=current_user.id)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
