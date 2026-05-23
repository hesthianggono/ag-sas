"""
HTTP Request/Response Schemas untuk Calculation API
=====================================================
Schema ini digunakan HANYA di API layer.
Nama field menyertakan satuan secara eksplisit (_mm, _mpa, _knm, _m)
untuk mencegah ambiguitas di request JSON.

Schema ini BERBEDA dari app.calculation.types yang digunakan
di calculation engine (pure Python, zero web dependency).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Concrete Beam Request ─────────────────────────────────────────────────────

class ConcreteBeamRequest(BaseModel):
    """HTTP request body untuk perhitungan balok beton bertulang."""

    # Meta (dipisah dari parameter teknis)
    project_id: int = Field(..., description="ID proyek")
    title: str = Field("Balok Beton Bertulang", description="Judul perhitungan")
    notes: Optional[str] = Field(None, description="Catatan tambahan")

    # Dimensi penampang — satuan: mm
    width_b_mm: float = Field(..., gt=0, description="Lebar balok b [mm]")
    height_h_mm: float = Field(..., gt=0, description="Tinggi balok h [mm]")
    cover_cc_mm: float = Field(..., gt=0, description="Selimut beton bersih cc [mm]")
    bar_diameter_mm: float = Field(..., gt=0, description="Diameter tulangan utama Ø [mm]")
    stirrup_diameter_mm: float = Field(10.0, gt=0, description="Diameter sengkang Øs [mm]")

    # Material — satuan: MPa
    fc_prime_mpa: float = Field(..., gt=0, description="Mutu beton fc' [MPa]")
    fy_mpa: float = Field(..., gt=0, description="Mutu baja tulangan fy [MPa]")

    # Beban dan geometri
    span_l_m: float = Field(..., gt=0, description="Panjang bentang L [m]")
    dead_load_w_knm: float = Field(..., ge=0, description="Beban mati merata wD [kN/m]")
    live_load_w_knm: float = Field(..., ge=0, description="Beban hidup merata wL [kN/m]")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "title": "Balok B1 - Lantai 1",
                "width_b_mm": 300,
                "height_h_mm": 600,
                "cover_cc_mm": 40,
                "bar_diameter_mm": 19,
                "stirrup_diameter_mm": 10,
                "fc_prime_mpa": 25,
                "fy_mpa": 400,
                "span_l_m": 6.0,
                "dead_load_w_knm": 20.0,
                "live_load_w_knm": 15.0,
            }
        }


# ── Steel Beam Request ────────────────────────────────────────────────────────

class SteelBeamRequest(BaseModel):
    """HTTP request body untuk perhitungan balok baja WF."""

    # Meta
    project_id: int = Field(..., description="ID proyek")
    title: str = Field("Balok Baja WF", description="Judul perhitungan")
    notes: Optional[str] = Field(None, description="Catatan tambahan")

    # Referensi profil
    profile_id: int = Field(..., description="ID profil baja dari database")

    # Material
    fy_mpa: float = Field(250.0, gt=0, description="Kuat leleh baja Fy [MPa]")

    # Beban dan geometri
    span_l_m: float = Field(..., gt=0, description="Panjang bentang L [m]")
    dead_load_w_knm: float = Field(..., ge=0, description="Beban mati merata wD (tanpa berat sendiri) [kN/m]")
    live_load_w_knm: float = Field(..., ge=0, description="Beban hidup merata wL [kN/m]")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": 1,
                "title": "Balok Atap BA-1",
                "profile_id": 8,
                "fy_mpa": 250,
                "span_l_m": 8.0,
                "dead_load_w_knm": 15.0,
                "live_load_w_knm": 12.0,
            }
        }


# ── Calculation Record Response ───────────────────────────────────────────────

class CalculationRecordResponse(BaseModel):
    """Response schema untuk satu record perhitungan yang tersimpan."""
    id: int
    project_id: int
    user_id: int
    calc_type: str
    title: str
    formula_version: str
    standard_references: str
    input_data: dict
    output_data: dict
    status: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
