from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import JSON


class CalculationRecord(SQLModel, table=True):
    __tablename__ = "calculation_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    user_id: int = Field(foreign_key="users.id")

    calc_type: str = Field(max_length=50)        # "concrete_beam" | "steel_beam"
    title: str = Field(max_length=255)
    formula_version: str = Field(default="1.0.0", max_length=20)
    standard_references: str = Field(default="")  # e.g. "SNI 2847:2019 Pasal 9"

    input_data: dict = Field(default={}, sa_column=Column(JSON))
    output_data: dict = Field(default={}, sa_column=Column(JSON))
    status: str = Field(default="OK", max_length=20)  # "OK" | "NOT_OK" | "ERROR"

    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
