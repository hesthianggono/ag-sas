"""Pydantic schemas untuk Full Report API."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EngineerInfoSchema(BaseModel):
    name:     str = ""
    position: str = ""
    skk:      str = ""


class FullReportCreateRequest(BaseModel):
    calc_id:          int
    doc_number:       str = "AG-SAS/RPT/001"
    revision:         str = "A"
    status:           str = "DRAFT"
    report_title:     str = "Laporan Perhitungan Struktur"
    report_subtitle:  str = ""
    project_name:     str = ""
    project_location: str = ""
    owner:            str = ""
    company_name:     str = "AG Structural Analysis Suite"
    engineers:        list[EngineerInfoSchema] = []
    include_figures:  bool = True
    show_watermark:   bool = True
    show_appendix:    bool = True
    deform_scale:     float = 50.0


class FullReportUpdateRequest(BaseModel):
    doc_number:       Optional[str]  = None
    revision:         Optional[str]  = None
    status:           Optional[str]  = None
    report_title:     Optional[str]  = None
    report_subtitle:  Optional[str]  = None
    project_name:     Optional[str]  = None
    project_location: Optional[str]  = None
    owner:            Optional[str]  = None
    company_name:     Optional[str]  = None
    engineers:        Optional[list[EngineerInfoSchema]] = None
    include_figures:  Optional[bool] = None
    show_watermark:   Optional[bool] = None
    show_appendix:    Optional[bool] = None
    deform_scale:     Optional[float] = None


class FullReportResponse(BaseModel):
    id:               int
    user_id:          int
    calc_id:          int
    doc_number:       str
    revision:         str
    status:           str
    report_title:     str
    report_subtitle:  Optional[str]
    project_name:     Optional[str]
    project_location: Optional[str]
    owner:            Optional[str]
    company_name:     str
    engineers:        list[EngineerInfoSchema] = []
    include_figures:  bool
    show_watermark:   bool
    show_appendix:    bool
    deform_scale:     float
    created_at:       datetime
    generated_at:     Optional[datetime]

    model_config = {"from_attributes": True}

    @classmethod
    def from_record(cls, rec) -> "FullReportResponse":
        engineers = []
        if rec.config_json:
            try:
                cfg = json.loads(rec.config_json)
                engineers = [
                    EngineerInfoSchema(**e)
                    for e in cfg.get("engineers", [])
                ]
            except Exception:
                pass
        return cls(
            id=rec.id,
            user_id=rec.user_id,
            calc_id=rec.calc_id,
            doc_number=rec.doc_number,
            revision=rec.revision,
            status=rec.status,
            report_title=rec.report_title,
            report_subtitle=rec.report_subtitle,
            project_name=rec.project_name,
            project_location=rec.project_location,
            owner=rec.owner,
            company_name=rec.company_name,
            engineers=engineers,
            include_figures=rec.include_figures,
            show_watermark=rec.show_watermark,
            show_appendix=rec.show_appendix,
            deform_scale=rec.deform_scale,
            created_at=rec.created_at,
            generated_at=rec.generated_at,
        )
