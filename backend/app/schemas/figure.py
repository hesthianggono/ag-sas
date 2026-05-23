"""
Figure Schemas — AG-SAS
=========================
Pydantic schemas untuk API gambar teknik.
"""
from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, computed_field


class FigureSnapshotResponse(BaseModel):
    """Response schema untuk satu FigureSnapshot."""
    id: int
    report_id: int
    calc_id: int
    figure_key: str
    figure_number: str
    order_index: int
    title: str
    caption: str
    load_case: Optional[str]
    load_combination: Optional[str]
    scale_factor: Optional[float]
    unit: str
    source: str
    is_visible: bool
    generated_at: datetime
    json_data: Optional[dict[str, Any]]
    # png_data di-encode sebagai base64 untuk JSON transport
    png_base64: str = Field(description="PNG image encoded as base64 string")

    model_config = {"from_attributes": True}

    @classmethod
    def from_snapshot(cls, snap) -> "FigureSnapshotResponse":
        return cls(
            id=snap.id,
            report_id=snap.report_id,
            calc_id=snap.calc_id,
            figure_key=snap.figure_key,
            figure_number=snap.figure_number,
            order_index=snap.order_index,
            title=snap.title,
            caption=snap.caption,
            load_case=snap.load_case,
            load_combination=snap.load_combination,
            scale_factor=snap.scale_factor,
            unit=snap.unit,
            source=snap.source,
            is_visible=snap.is_visible,
            generated_at=snap.generated_at,
            json_data=snap.json_data,
            png_base64=base64.b64encode(snap.png_data).decode("utf-8"),
        )


class FigureUpdateRequest(BaseModel):
    """Untuk update caption, visibility, atau urutan."""
    caption: Optional[str] = Field(None, max_length=512)
    title: Optional[str] = Field(None, max_length=255)
    is_visible: Optional[bool] = None
    order_index: Optional[int] = None


class FigureUploadRequest(BaseModel):
    """Upload gambar dari frontend (Three.js/Canvas snapshot)."""
    report_id: int
    calc_id: int
    figure_key: str
    title: str
    caption: str
    load_case: Optional[str] = None
    load_combination: Optional[str] = None
    scale_factor: Optional[float] = None
    unit: str = "—"
    png_base64: str = Field(description="PNG image encoded as base64")
    json_data: Optional[dict[str, Any]] = None


class GenerateFiguresRequest(BaseModel):
    """Request untuk generate semua gambar backend untuk satu laporan."""
    report_id: int
    section: str = Field("4", description="Nomor seksi laporan (mis. '4')")
    deform_scale: float = Field(50.0, description="Faktor skala deformasi visual")
    overwrite: bool = Field(False, description="Hapus gambar lama sebelum generate ulang")
