"""
Figure Service — AG-SAS
=========================
Service layer untuk manajemen FigureSnapshot:
  - generate_figures_for_report : generate semua gambar backend
  - upload_figure               : simpan gambar dari frontend
  - list_figures                : daftar gambar untuk laporan
  - update_figure               : update caption/visibility/urutan
  - delete_figure               : hapus satu gambar
  - get_figure_png              : ambil bytes PNG untuk PDF embedding
"""
from __future__ import annotations

import base64
from typing import Any

from sqlmodel import Session, select

from app.models.report import ReportRecord
from app.models.figure_snapshot import FigureSnapshot
from app.reporting.figures.figure_builder import build_figures_for_calc


class FigureNotFoundError(LookupError):
    pass

class ReportNotFoundError(LookupError):
    pass


# ── Generate ──────────────────────────────────────────────────────────────────

def generate_figures_for_report(
    *,
    session: Session,
    report_id: int,
    user_id: int,
    section: str = "4",
    deform_scale: float = 50.0,
    overwrite: bool = False,
) -> list[FigureSnapshot]:
    """
    Generate semua gambar teknik backend untuk satu ReportRecord.

    Raises
    ------
    ReportNotFoundError : laporan tidak ditemukan
    """
    report = session.get(ReportRecord, report_id)
    if not report or report.user_id != user_id:
        raise ReportNotFoundError(f"Laporan ID={report_id} tidak ditemukan")

    if overwrite:
        _delete_backend_figures(session, report_id)

    # Build figures dari data kalkulasi yang sudah tersimpan di snapshot
    figure_specs = build_figures_for_calc(
        calc_type=report.calc_type,
        input_data=report.input_snapshot,
        output_data=report.output_snapshot,
        calc_title=report.title,
        source_result_id=report.calc_id,
        section=section,
        deform_scale=deform_scale,
    )

    snapshots: list[FigureSnapshot] = []
    for spec in figure_specs:
        snap = FigureSnapshot(
            report_id=report_id,
            user_id=user_id,
            calc_id=report.calc_id,
            figure_key=spec.figure_key,
            figure_number=spec.figure_number,
            order_index=spec.order_index,
            title=spec.title,
            caption=spec.caption,
            load_case=spec.load_case,
            load_combination=spec.load_combination,
            scale_factor=spec.scale_factor,
            unit=spec.unit,
            png_data=spec.png_bytes,
            svg_data=spec.svg_data,
            json_data=spec.json_data,
            source="backend",
            is_visible=True,
        )
        session.add(snap)
        snapshots.append(snap)

    session.commit()
    for snap in snapshots:
        session.refresh(snap)
    return snapshots


# ── Upload from Frontend ──────────────────────────────────────────────────────

def upload_figure(
    *,
    session: Session,
    report_id: int,
    user_id: int,
    calc_id: int,
    figure_key: str,
    title: str,
    caption: str,
    png_base64: str,
    load_case: str | None = None,
    load_combination: str | None = None,
    scale_factor: float | None = None,
    unit: str = "—",
    json_data: dict[str, Any] | None = None,
) -> FigureSnapshot:
    """Simpan gambar yang dikirim dari frontend (canvas / Three.js snapshot)."""
    try:
        png_bytes = base64.b64decode(png_base64)
    except Exception as e:
        raise ValueError(f"PNG base64 tidak valid: {e}")

    # Hitung order_index berdasarkan jumlah gambar yang sudah ada
    existing = session.exec(
        select(FigureSnapshot)
        .where(FigureSnapshot.report_id == report_id)
        .order_by(FigureSnapshot.order_index.desc())
    ).first()
    next_order = (existing.order_index + 1) if existing else 1

    # Hitung figure_number
    count = session.exec(
        select(FigureSnapshot)
        .where(FigureSnapshot.report_id == report_id)
    ).all()
    section = "4"
    fig_num = f"{section}.{len(count) + 1}"

    snap = FigureSnapshot(
        report_id=report_id,
        user_id=user_id,
        calc_id=calc_id,
        figure_key=figure_key,
        figure_number=fig_num,
        order_index=next_order,
        title=title,
        caption=caption,
        load_case=load_case,
        load_combination=load_combination,
        scale_factor=scale_factor,
        unit=unit,
        png_data=png_bytes,
        json_data=json_data,
        source="frontend",
        is_visible=True,
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap


# ── Query ─────────────────────────────────────────────────────────────────────

def list_figures(
    *,
    session: Session,
    report_id: int,
    user_id: int,
    visible_only: bool = False,
) -> list[FigureSnapshot]:
    """Daftar semua gambar untuk satu laporan, diurutkan by order_index."""
    report = session.get(ReportRecord, report_id)
    if not report or report.user_id != user_id:
        raise ReportNotFoundError(f"Laporan ID={report_id} tidak ditemukan")

    q = (
        select(FigureSnapshot)
        .where(FigureSnapshot.report_id == report_id)
        .order_by(FigureSnapshot.order_index)
    )
    if visible_only:
        q = q.where(FigureSnapshot.is_visible == True)   # noqa: E712
    return list(session.exec(q).all())


def get_figure(
    *, session: Session, figure_id: int, user_id: int,
) -> FigureSnapshot:
    snap = session.get(FigureSnapshot, figure_id)
    if not snap or snap.user_id != user_id:
        raise FigureNotFoundError(f"Gambar ID={figure_id} tidak ditemukan")
    return snap


# ── Update ────────────────────────────────────────────────────────────────────

def update_figure(
    *,
    session: Session,
    figure_id: int,
    user_id: int,
    caption: str | None = None,
    title: str | None = None,
    is_visible: bool | None = None,
    order_index: int | None = None,
) -> FigureSnapshot:
    snap = get_figure(session=session, figure_id=figure_id, user_id=user_id)
    if caption is not None:
        snap.caption = caption
    if title is not None:
        snap.title = title
    if is_visible is not None:
        snap.is_visible = is_visible
    if order_index is not None:
        snap.order_index = order_index
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap


# ── Delete ────────────────────────────────────────────────────────────────────

def delete_figure(*, session: Session, figure_id: int, user_id: int) -> None:
    snap = get_figure(session=session, figure_id=figure_id, user_id=user_id)
    session.delete(snap)
    session.commit()


def _delete_backend_figures(session: Session, report_id: int) -> None:
    snaps = session.exec(
        select(FigureSnapshot)
        .where(FigureSnapshot.report_id == report_id)
        .where(FigureSnapshot.source == "backend")
    ).all()
    for s in snaps:
        session.delete(s)
    session.commit()
