"""
Full Report API Endpoints — AG-SAS
=====================================
POST   /full-reports                    Buat record laporan baru
GET    /full-reports                    Daftar laporan milik user
GET    /full-reports/{id}               Detail satu laporan
PATCH  /full-reports/{id}               Update metadata laporan
DELETE /full-reports/{id}               Hapus laporan
GET    /full-reports/{id}/pdf           Download PDF (StreamingResponse)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import io

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.full_report import (
    FullReportCreateRequest, FullReportUpdateRequest, FullReportResponse,
)
from app.services import full_report_service as svc

router = APIRouter(prefix="/full-reports", tags=["full-reports"])


@router.post("", response_model=FullReportResponse, status_code=201)
def create_report(
    req: FullReportCreateRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rec = svc.create_full_report(req, user.id, session)
    return FullReportResponse.from_record(rec)


@router.get("", response_model=list[FullReportResponse])
def list_reports(
    calc_id: int | None = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    recs = svc.list_full_reports(user.id, session, calc_id=calc_id)
    return [FullReportResponse.from_record(r) for r in recs]


@router.get("/{report_id}", response_model=FullReportResponse)
def get_report(
    report_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rec = svc.get_full_report(report_id, user.id, session)
    return FullReportResponse.from_record(rec)


@router.patch("/{report_id}", response_model=FullReportResponse)
def update_report(
    report_id: int,
    req: FullReportUpdateRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rec = svc.update_full_report(report_id, req, user.id, session)
    return FullReportResponse.from_record(rec)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    svc.delete_full_report(report_id, user.id, session)


@router.get("/{report_id}/pdf")
def download_pdf(
    report_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Generate dan stream PDF laporan rekayasa lengkap."""
    pdf_bytes = svc.generate_full_report_pdf(report_id, user.id, session)

    # Ambil nama file
    rec = svc.get_full_report(report_id, user.id, session)
    filename = f"laporan_{rec.doc_number.replace('/', '-')}_Rev{rec.revision}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
