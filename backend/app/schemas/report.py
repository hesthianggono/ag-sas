"""
Schemas HTTP untuk Report API
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    calc_id: int = Field(..., description="ID CalculationRecord yang akan dibuat laporannya")
    engineer_name: Optional[str] = Field(None, max_length=255, description="Nama engineer pemeriksa")
    engineer_position: Optional[str] = Field(None, max_length=255, description="Jabatan engineer")
    engineer_skk: Optional[str] = Field(None, max_length=100, description="Nomor SKK engineer")

    class Config:
        json_schema_extra = {"example": {"calc_id": 1, "engineer_name": "Ir. Budi", "engineer_position": "Ahli Madya Struktur", "engineer_skk": "SKK-123456"}}


class ReportRecordResponse(BaseModel):
    id: int
    calc_id: int
    user_id: int
    project_id: int
    calc_type: str
    title: str
    formula_version: str
    standard_references: str
    generated_at: datetime
    generated_by_name: str
    project_name: str
    project_location: str
    client_name: str
    consultant_name: Optional[str]
    building_type: str
    num_floors: int
    structural_system: str
    primary_material: str
    input_snapshot: dict
    output_snapshot: dict
    engineer_name: Optional[str] = None
    engineer_position: Optional[str] = None
    engineer_skk: Optional[str] = None
    # html_content omitted — fetch separately via /preview endpoint

    class Config:
        from_attributes = True
