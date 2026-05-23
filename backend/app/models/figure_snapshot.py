"""
FigureSnapshot Model — AG-SAS
================================
Menyimpan gambar teknik sebagai snapshot immutable per laporan.
Setiap gambar disimpan dengan metadata lengkap dan data PNG.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import LargeBinary, Text, JSON


class FigureSnapshot(SQLModel, table=True):
    __tablename__ = "figure_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)

    # ── Relasi ───────────────────────────────────────────────────────────────
    report_id: int = Field(foreign_key="report_records.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    calc_id: int = Field(foreign_key="calculation_records.id", index=True)

    # ── Identitas gambar ──────────────────────────────────────────────────────
    figure_key: str = Field(max_length=80)     # "model_view", "moment_diagram", …
    figure_number: str = Field(max_length=20)  # "4.1", "4.2", …
    order_index: int = Field(default=0)

    # ── Metadata ──────────────────────────────────────────────────────────────
    title: str = Field(max_length=255)
    caption: str = Field(max_length=512)
    load_case: Optional[str] = Field(default=None, max_length=100)
    load_combination: Optional[str] = Field(default=None, max_length=100)
    scale_factor: Optional[float] = Field(default=None)
    unit: str = Field(default="—", max_length=50)

    # ── Data gambar ───────────────────────────────────────────────────────────
    png_data: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    svg_data: Optional[str] = Field(default=None, sa_column=Column(Text))
    json_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # ── Sumber ────────────────────────────────────────────────────────────────
    source: str = Field(default="backend", max_length=20)  # "backend" | "frontend"
    is_visible: bool = Field(default=True)   # apakah ditampilkan di laporan

    # ── Audit ─────────────────────────────────────────────────────────────────
    generated_at: datetime = Field(default_factory=datetime.utcnow)
