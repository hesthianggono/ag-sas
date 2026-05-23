from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)

    name: str = Field(max_length=255)
    location: str = Field(max_length=255)
    client_name: str = Field(max_length=255)
    consultant_name: Optional[str] = Field(default=None, max_length=255)
    building_type: str = Field(max_length=100)  # e.g., "Gedung Kantor", "Rumah Tinggal"
    num_floors: int = Field(default=1)
    structural_system: str = Field(max_length=100)  # e.g., "Rangka Momen Khusus"
    primary_material: str = Field(max_length=100)  # e.g., "Beton Bertulang", "Baja"
    applicable_standards: str = Field(
        default="SNI 1727:2020,SNI 1726:2019,SNI 2847:2019,SNI 1729:2020"
    )
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
