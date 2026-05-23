"""
API Layer: Gambar Teknik (Report Figures)
==========================================
POST  /figures/generate              — Generate semua gambar backend untuk laporan
POST  /figures/upload                — Upload gambar dari frontend (snapshot)
GET   /figures/report/{report_id}    — Daftar gambar untuk satu laporan
GET   /figures/{figure_id}           — Detail + PNG base64
GET   /figures/{figure_id}/png       — Stream PNG langsung (untuk <img src>)
PATCH /figures/{figure_id}           — Update caption / visibility / urutan
DELETE/figures/{figure_id}           — Hapus gambar
"""
from __future__ import annotations

import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.db.session import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.figure import (
    FigureSnapshotResponse,
    FigureUpdateRequest,
    FigureUploadRequest,
    GenerateFiguresRequest,
)
from app.services.figure_service import (
    generate_figures_for_report,
    upload_figure,
    list_figures,
    get_figure,
    update_figure,
    delete_figure,
    FigureNotFoundError,
    ReportNotFoundError,
)

router = APIRouter(prefix="/figures", tags=["Figures"])


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=List[FigureSnapshotResponse],
    status_code=201,
    summary="Generate semua gambar teknik backend untuk satu laporan",
)
def generate_figures(
    body: GenerateFiguresRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        snaps = generate_figures_for_report(
            session=session,
            report_id=body.report_id,
            user_id=current_user.id,
            section=body.section,
            deform_scale=body.deform_scale,
            overwrite=body.overwrite,
        )
    except ReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [FigureSnapshotResponse.from_snapshot(s) for s in snaps]


# ── Upload from Frontend ──────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=FigureSnapshotResponse,
    status_code=201,
    summary="Upload gambar dari frontend (canvas/Three.js snapshot)",
)
def upload_frontend_figure(
    body: FigureUploadRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        snap = upload_figure(
            session=session,
            report_id=body.report_id,
            user_id=current_user.id,
            calc_id=body.calc_id,
            figure_key=body.figure_key,
            title=body.title,
            caption=body.caption,
            png_base64=body.png_base64,
            load_case=body.load_case,
            load_combination=body.load_combination,
            scale_factor=body.scale_factor,
            unit=body.unit,
            json_data=body.json_data,
        )
    except (ReportNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return FigureSnapshotResponse.from_snapshot(snap)


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "/report/{report_id}",
    response_model=List[FigureSnapshotResponse],
    summary="Daftar semua gambar untuk satu laporan",
)
def list_report_figures(
    report_id: int,
    visible_only: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        snaps = list_figures(
            session=session, report_id=report_id,
            user_id=current_user.id, visible_only=visible_only,
        )
    except ReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [FigureSnapshotResponse.from_snapshot(s) for s in snaps]


# ── Detail + PNG stream ───────────────────────────────────────────────────────

@router.get(
    "/{figure_id}",
    response_model=FigureSnapshotResponse,
    summary="Detail satu gambar",
)
def get_figure_detail(
    figure_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        snap = get_figure(session=session, figure_id=figure_id, user_id=current_user.id)
    except FigureNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FigureSnapshotResponse.from_snapshot(snap)


@router.get(
    "/{figure_id}/png",
    summary="Stream PNG gambar langsung",
    description="Kembalikan PNG sebagai image/png. Gunakan sebagai <img src> dengan auth header.",
)
def stream_figure_png(
    figure_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        snap = get_figure(session=session, figure_id=figure_id, user_id=current_user.id)
    except FigureNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return StreamingResponse(
        io.BytesIO(snap.png_data),
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{snap.figure_key}_{figure_id}.png"'},
    )


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{figure_id}",
    response_model=FigureSnapshotResponse,
    summary="Update caption, visibility, atau urutan gambar",
)
def patch_figure(
    figure_id: int,
    body: FigureUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        snap = update_figure(
            session=session,
            figure_id=figure_id,
            user_id=current_user.id,
            caption=body.caption,
            title=body.title,
            is_visible=body.is_visible,
            order_index=body.order_index,
        )
    except FigureNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FigureSnapshotResponse.from_snapshot(snap)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{figure_id}",
    status_code=204,
    summary="Hapus gambar dari laporan",
)
def remove_figure(
    figure_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        delete_figure(session=session, figure_id=figure_id, user_id=current_user.id)
    except FigureNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
