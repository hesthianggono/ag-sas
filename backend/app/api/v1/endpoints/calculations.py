"""
API Layer: Perhitungan Struktur
================================
Endpoint ini HANYA bertanggung jawab untuk:
  1. Validasi request HTTP (field types, required fields)
  2. Memanggil service layer
  3. Menerjemahkan service exceptions → HTTP error codes
  4. Mengembalikan HTTP response

Semua logika bisnis (kalkulasi, validasi engineering, persistensi) ada di service layer.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
import io

from app.db.session import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.calculation import CalculationRecord
from app.schemas.calculation import (
    ConcreteBeamRequest, SteelBeamRequest, CalculationRecordResponse,
)
from app.services.calculation_service import (
    run_concrete_beam, run_steel_beam,
    ProjectNotFoundError, ProfileNotFoundError, CalculationValidationError,
)
from app.reporting.pdf_generator import generate_calculation_report

router = APIRouter(prefix="/calculations", tags=["Calculations"])


# ── Concrete Beam ─────────────────────────────────────────────────────────────

@router.post(
    "/concrete-beam",
    response_model=CalculationRecordResponse,
    status_code=201,
    summary="Hitung balok beton bertulang sederhana",
    description="Desain lentur singly reinforced, simply supported (SNI 2847:2019).",
)
def calculate_concrete_beam(
    body: ConcreteBeamRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        record = run_concrete_beam(
            session=session,
            user_id=current_user.id,
            project_id=body.project_id,
            title=body.title,
            notes=body.notes,
            width_b_mm=body.width_b_mm,
            height_h_mm=body.height_h_mm,
            cover_cc_mm=body.cover_cc_mm,
            bar_diameter_mm=body.bar_diameter_mm,
            stirrup_diameter_mm=body.stirrup_diameter_mm,
            fc_prime_mpa=body.fc_prime_mpa,
            fy_mpa=body.fy_mpa,
            span_l_m=body.span_l_m,
            dead_load_w_knm=body.dead_load_w_knm,
            live_load_w_knm=body.live_load_w_knm,
        )
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CalculationValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return record


# ── Steel Beam ────────────────────────────────────────────────────────────────

@router.post(
    "/steel-beam",
    response_model=CalculationRecordResponse,
    status_code=201,
    summary="Hitung balok baja WF sederhana",
    description="Desain lentur LRFD, simply supported, cek kompak/tidak kompak (SNI 1729:2020).",
)
def calculate_steel_beam(
    body: SteelBeamRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        record = run_steel_beam(
            session=session,
            user_id=current_user.id,
            project_id=body.project_id,
            title=body.title,
            notes=body.notes,
            profile_id=body.profile_id,
            fy_mpa=body.fy_mpa,
            span_l_m=body.span_l_m,
            dead_load_w_knm=body.dead_load_w_knm,
            live_load_w_knm=body.live_load_w_knm,
        )
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CalculationValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return record


# ── History ───────────────────────────────────────────────────────────────────

@router.get(
    "/project/{project_id}",
    response_model=List[CalculationRecordResponse],
    summary="Daftar perhitungan untuk satu proyek",
)
def get_project_calculations(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    return session.exec(
        select(CalculationRecord)
        .where(CalculationRecord.project_id == project_id)
        .order_by(CalculationRecord.created_at.desc())
    ).all()


@router.get(
    "/{calc_id}",
    response_model=CalculationRecordResponse,
    summary="Detail satu perhitungan",
)
def get_calculation(
    calc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    record = session.get(CalculationRecord, calc_id)
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Perhitungan tidak ditemukan")
    return record


# ── PDF Report ────────────────────────────────────────────────────────────────

@router.get(
    "/{calc_id}/report/pdf",
    summary="Download laporan PDF",
    description="Generate dan download laporan perhitungan dalam format PDF.",
)
def download_report_pdf(
    calc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    record = session.get(CalculationRecord, calc_id)
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Perhitungan tidak ditemukan")

    project = session.get(Project, record.project_id)
    project_data = {
        "name": project.name,
        "location": project.location,
        "client_name": project.client_name,
        "consultant_name": project.consultant_name,
        "building_type": project.building_type,
        "num_floors": project.num_floors,
        "structural_system": project.structural_system,
        "primary_material": project.primary_material,
        "formula_version": record.formula_version,
    }

    pdf_bytes = generate_calculation_report(
        project_data=project_data,
        calc_type=record.calc_type,
        input_data=record.input_data,
        output_data=record.output_data,
        calc_title=record.title,
        standard_references=record.standard_references,
    )

    filename = f"AG-SAS_{record.calc_type}_{calc_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
