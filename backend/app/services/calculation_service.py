"""
Service Layer: Orchestrasi Perhitungan Struktur
================================================
Lapisan ini memisahkan logika bisnis dari API layer.

Tanggung jawab:
  1. Validasi input engineering (domain rules, bukan HTTP validation)
  2. Resolve referensi ke DB (profil baja, proyek)
  3. Memanggil calculation engine (pure Python, zero web dependency)
  4. Membangun snapshot input/output untuk audit trail
  5. Menyimpan CalculationRecord ke database
  6. Mengembalikan record yang tersimpan

Lapisan ini TIDAK:
  - Menangani HTTP request/response (itu tugas API layer)
  - Berisi logika formula (itu tugas calculation engine)
  - Berisi logika rendering PDF (itu tugas reporting engine)
"""
from __future__ import annotations
import dataclasses
from typing import Optional
from sqlmodel import Session

from app.models.calculation import CalculationRecord
from app.models.project import Project
from app.models.steel_profile import SteelProfile
from app.calculation.types import (
    ConcreteBeamParams, SteelBeamParams, DesignStatus
)
from app.calculation.concrete.beam_calculator import design_concrete_beam
from app.calculation.steel.beam_calculator import design_steel_beam


class CalculationValidationError(ValueError):
    """Raised jika parameter engineering tidak valid."""


class ProjectNotFoundError(LookupError):
    """Raised jika proyek tidak ditemukan atau bukan milik user."""


class ProfileNotFoundError(LookupError):
    """Raised jika profil baja tidak ditemukan."""


# ── Concrete Beam ─────────────────────────────────────────────────────────────

def run_concrete_beam(
    *,
    session: Session,
    user_id: int,
    project_id: int,
    title: str,
    notes: Optional[str],
    # Dimensi penampang [mm]
    width_b_mm: float,
    height_h_mm: float,
    cover_cc_mm: float,
    bar_diameter_mm: float,
    stirrup_diameter_mm: float,
    # Material [MPa]
    fc_prime_mpa: float,
    fy_mpa: float,
    # Beban dan geometri
    span_l_m: float,
    dead_load_w_knm: float,
    live_load_w_knm: float,
) -> CalculationRecord:
    """
    Jalankan perhitungan balok beton bertulang dan simpan hasilnya.

    Raises
    ------
    ProjectNotFoundError   : Proyek tidak ada atau bukan milik user
    CalculationValidationError : Parameter engineering tidak valid
    """
    _assert_project_ownership(project_id, user_id, session)

    params = ConcreteBeamParams(
        width_b_mm=width_b_mm,
        height_h_mm=height_h_mm,
        cover_cc_mm=cover_cc_mm,
        bar_diameter_mm=bar_diameter_mm,
        stirrup_diameter_mm=stirrup_diameter_mm,
        fc_prime_mpa=fc_prime_mpa,
        fy_mpa=fy_mpa,
        span_l_m=span_l_m,
        dead_load_w_knm=dead_load_w_knm,
        live_load_w_knm=live_load_w_knm,
    )

    errors = params.validate()
    if errors:
        raise CalculationValidationError("; ".join(errors))

    result = design_concrete_beam(params)

    # Input snapshot: hanya parameter engineering (tanpa meta API)
    input_snapshot = {
        "width_b_mm": width_b_mm,
        "height_h_mm": height_h_mm,
        "cover_cc_mm": cover_cc_mm,
        "bar_diameter_mm": bar_diameter_mm,
        "stirrup_diameter_mm": stirrup_diameter_mm,
        "fc_prime_mpa": fc_prime_mpa,
        "fy_mpa": fy_mpa,
        "span_l_m": span_l_m,
        "dead_load_w_knm": dead_load_w_knm,
        "live_load_w_knm": live_load_w_knm,
    }

    return _persist(
        session=session,
        project_id=project_id,
        user_id=user_id,
        calc_type="concrete_beam",
        title=title,
        notes=notes,
        result=result,
        input_snapshot=input_snapshot,
    )


# ── Steel Beam ────────────────────────────────────────────────────────────────

def run_steel_beam(
    *,
    session: Session,
    user_id: int,
    project_id: int,
    title: str,
    notes: Optional[str],
    profile_id: int,
    fy_mpa: float,
    span_l_m: float,
    dead_load_w_knm: float,
    live_load_w_knm: float,
) -> CalculationRecord:
    """
    Jalankan perhitungan balok baja dan simpan hasilnya.

    Raises
    ------
    ProjectNotFoundError   : Proyek tidak ada atau bukan milik user
    ProfileNotFoundError   : Profil baja tidak ditemukan
    CalculationValidationError : Parameter engineering tidak valid
    """
    _assert_project_ownership(project_id, user_id, session)

    profile = session.get(SteelProfile, profile_id)
    if not profile:
        raise ProfileNotFoundError(f"Profil baja ID={profile_id} tidak ditemukan")

    params = SteelBeamParams(
        profile_designation=profile.designation,
        height_h_mm=profile.height_h,
        flange_width_b_mm=profile.flange_width_b,
        web_thickness_tw_mm=profile.web_thickness_tw,
        flange_thickness_tf_mm=profile.flange_thickness_tf,
        sx_cm3=profile.sx,
        zx_cm3=profile.zx,
        weight_per_m_kgm=profile.weight_per_m,
        fy_mpa=fy_mpa,
        span_l_m=span_l_m,
        dead_load_w_knm=dead_load_w_knm,
        live_load_w_knm=live_load_w_knm,
    )

    errors = params.validate()
    if errors:
        raise CalculationValidationError("; ".join(errors))

    result = design_steel_beam(params)

    input_snapshot = {
        "profile_id": profile_id,
        "profile_designation": profile.designation,
        "fy_mpa": fy_mpa,
        "span_l_m": span_l_m,
        "dead_load_w_knm": dead_load_w_knm,
        "live_load_w_knm": live_load_w_knm,
    }

    return _persist(
        session=session,
        project_id=project_id,
        user_id=user_id,
        calc_type="steel_beam",
        title=title,
        notes=notes,
        result=result,
        input_snapshot=input_snapshot,
    )


# ── Helper privat ─────────────────────────────────────────────────────────────

def _assert_project_ownership(project_id: int, user_id: int, session: Session) -> None:
    project = session.get(Project, project_id)
    if not project or project.owner_id != user_id or not project.is_active:
        raise ProjectNotFoundError(f"Proyek ID={project_id} tidak ditemukan")


def _persist(
    *,
    session: Session,
    project_id: int,
    user_id: int,
    calc_type: str,
    title: str,
    notes: Optional[str],
    result,
    input_snapshot: dict,
) -> CalculationRecord:
    """Simpan hasil kalkulasi ke database dan kembalikan record."""
    output_dict = dataclasses.asdict(result)
    # Konversi enum ke string untuk JSON storage
    output_dict["status"] = result.status.value
    output_dict["meta"] = dataclasses.asdict(result.meta)

    record = CalculationRecord(
        project_id=project_id,
        user_id=user_id,
        calc_type=calc_type,
        title=title,
        formula_version=result.meta.formula_version,
        standard_references=result.meta.standard_references,
        input_data=input_snapshot,
        output_data=output_dict,
        status=result.status.value,
        notes=notes,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
