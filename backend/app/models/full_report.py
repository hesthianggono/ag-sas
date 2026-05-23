"""
FullReportRecord — SQLModel untuk tabel full_report_records.
Menyimpan metadata laporan rekayasa lengkap (PDF) per proyek.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class FullReportRecord(SQLModel, table=True):
    __tablename__ = "full_report_records"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relasi ke user dan kalkulasi
    user_id: int     = Field(foreign_key="users.id", index=True)
    calc_id: int     = Field(foreign_key="calculation_records.id", index=True)

    # Metadata dokumen
    doc_number:       str            = Field(default="AG-SAS/RPT/001", max_length=80)
    revision:         str            = Field(default="A",     max_length=10)
    status:           str            = Field(default="DRAFT", max_length=20)
    report_title:     str            = Field(max_length=255)
    report_subtitle:  Optional[str]  = Field(default=None, max_length=255)
    project_name:     Optional[str]  = Field(default=None, max_length=255)
    project_location: Optional[str]  = Field(default=None, max_length=255)
    owner:            Optional[str]  = Field(default=None, max_length=255)
    company_name:     str            = Field(default="AG Structural Analysis Suite",
                                             max_length=255)

    # Konfigurasi laporan (JSON)
    config_json: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    # Timestamps
    created_at:   datetime = Field(default_factory=datetime.utcnow)
    generated_at: Optional[datetime] = Field(default=None)

    # Flag
    include_figures: bool = Field(default=True)
    show_watermark:  bool = Field(default=True)
    show_appendix:   bool = Field(default=True)
    deform_scale:    float = Field(default=50.0)
