from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON, Text


class ReportRecord(SQLModel, table=True):
    __tablename__ = "report_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    calc_id: int = Field(foreign_key="calculation_records.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    project_id: int = Field(foreign_key="projects.id", index=True)

    calc_type: str = Field(max_length=50)   # "concrete_beam" | "steel_beam"
    title: str = Field(max_length=255)
    formula_version: str = Field(default="1.1.0", max_length=20)
    standard_references: str = Field(default="")

    # Snapshot at generation time — denormalized for full audit trail
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by_name: str = Field(max_length=255)

    # Project metadata snapshot
    project_name: str = Field(max_length=255)
    project_location: str = Field(max_length=255)
    client_name: str = Field(max_length=255)
    consultant_name: Optional[str] = Field(default=None, max_length=255)
    building_type: str = Field(max_length=100)
    num_floors: int = Field(default=1)
    structural_system: str = Field(max_length=100)
    primary_material: str = Field(max_length=100)

    # Calculation data snapshots
    input_snapshot: dict = Field(default={}, sa_column=Column(JSON))
    output_snapshot: dict = Field(default={}, sa_column=Column(JSON))

    # Engineer approval data (opsional, diisi saat generate)
    engineer_name: Optional[str] = Field(default=None, max_length=255)
    engineer_position: Optional[str] = Field(default=None, max_length=255)
    engineer_skk: Optional[str] = Field(default=None, max_length=100)

    # Rendered HTML stored for instant preview
    html_content: Optional[str] = Field(default=None, sa_column=Column(Text))
