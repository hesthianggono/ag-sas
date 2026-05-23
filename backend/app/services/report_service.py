"""
Service Layer: Laporan Perhitungan
===================================
Tanggung jawab:
  1. Validasi akses (calc milik user)
  2. Ambil data dari CalculationRecord, Project, User
  3. Render HTML menggunakan html_renderer
  4. Simpan ReportRecord ke DB
  5. Generate PDF dari snapshot yang tersimpan
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.models.calculation import CalculationRecord
from app.models.project import Project
from app.models.user import User
from app.models.report import ReportRecord
from app.models.figure_snapshot import FigureSnapshot
from app.reporting.html_renderer import render_report_html
from app.reporting.pdf_generator import generate_calculation_report
from sqlmodel import select


class ReportNotFoundError(LookupError):
    """Raised jika laporan tidak ditemukan atau bukan milik user."""


class CalcNotFoundError(LookupError):
    """Raised jika perhitungan tidak ditemukan atau bukan milik user."""


# ── Generate ──────────────────────────────────────────────────────────────────

def generate_report(
    *,
    session: Session,
    calc_id: int,
    user_id: int,
    engineer_name: str | None = None,
    engineer_position: str | None = None,
    engineer_skk: str | None = None,
) -> ReportRecord:
    """
    Buat ReportRecord baru dari CalculationRecord.
    Render HTML dan simpan ke DB.

    Raises
    ------
    CalcNotFoundError : calc tidak ada atau bukan milik user
    """
    calc = session.get(CalculationRecord, calc_id)
    if not calc or calc.user_id != user_id:
        raise CalcNotFoundError(f"Perhitungan ID={calc_id} tidak ditemukan")

    project = session.get(Project, calc.project_id)
    user    = session.get(User, user_id)

    project_dict = {
        "name":             project.name,
        "location":         project.location,
        "client_name":      project.client_name,
        "consultant_name":  project.consultant_name,
        "building_type":    project.building_type,
        "num_floors":       project.num_floors,
        "structural_system": project.structural_system,
        "primary_material": project.primary_material,
    }

    generated_at = datetime.utcnow()
    generated_by = user.full_name if user else "AG-SAS"

    html = render_report_html(
        calc_type=calc.calc_type,
        title=calc.title,
        project=project_dict,
        input_data=calc.input_data,
        output_data=calc.output_data,
        standard_references=calc.standard_references,
        formula_version=calc.formula_version,
        generated_at=generated_at,
        generated_by=generated_by,
    )

    record = ReportRecord(
        calc_id=calc_id,
        user_id=user_id,
        project_id=calc.project_id,
        calc_type=calc.calc_type,
        title=calc.title,
        formula_version=calc.formula_version,
        standard_references=calc.standard_references,
        generated_at=generated_at,
        generated_by_name=generated_by,
        project_name=project.name,
        project_location=project.location,
        client_name=project.client_name,
        consultant_name=project.consultant_name,
        building_type=project.building_type,
        num_floors=project.num_floors,
        structural_system=project.structural_system,
        primary_material=project.primary_material,
        input_snapshot=calc.input_data,
        output_snapshot=calc.output_data,
        html_content=html,
        engineer_name=engineer_name,
        engineer_position=engineer_position,
        engineer_skk=engineer_skk,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


# ── PDF Download ──────────────────────────────────────────────────────────────

def build_pdf_for_report(*, session: Session, report_id: int, user_id: int) -> bytes:
    """
    Generate PDF dari ReportRecord yang tersimpan.
    Data diambil dari snapshot — tidak re-compute kalkulasi.

    Raises
    ------
    ReportNotFoundError : laporan tidak ada atau bukan milik user
    """
    report = session.get(ReportRecord, report_id)
    if not report or report.user_id != user_id:
        raise ReportNotFoundError(f"Laporan ID={report_id} tidak ditemukan")

    project_data = {
        "name":             report.project_name,
        "location":         report.project_location,
        "client_name":      report.client_name,
        "consultant_name":  report.consultant_name,
        "building_type":    report.building_type,
        "num_floors":       report.num_floors,
        "structural_system": report.structural_system,
        "primary_material": report.primary_material,
        "formula_version":  report.formula_version,
    }

    engineer_data = {
        "name":     report.engineer_name or "",
        "position": report.engineer_position or "",
        "skk":      report.engineer_skk or "",
    }

    # Ambil gambar teknik yang sudah tersimpan untuk laporan ini
    figure_snaps = list(session.exec(
        select(FigureSnapshot)
        .where(FigureSnapshot.report_id == report_id)
        .where(FigureSnapshot.is_visible == True)   # noqa: E712
        .order_by(FigureSnapshot.order_index)
    ).all()) or None

    return generate_calculation_report(
        project_data=project_data,
        calc_type=report.calc_type,
        input_data=report.input_snapshot,
        output_data=report.output_snapshot,
        calc_title=report.title,
        standard_references=report.standard_references,
        generated_by=report.generated_by_name,
        engineer_data=engineer_data,
        figure_snapshots=figure_snaps,
    )


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def get_report_or_404(*, session: Session, report_id: int, user_id: int) -> ReportRecord:
    report = session.get(ReportRecord, report_id)
    if not report or report.user_id != user_id:
        raise ReportNotFoundError(f"Laporan ID={report_id} tidak ditemukan")
    return report
