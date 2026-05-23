from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    location: str
    client_name: str
    consultant_name: Optional[str] = None
    building_type: str
    num_floors: int = 1
    structural_system: str
    primary_material: str
    applicable_standards: str = "SNI 1727:2020,SNI 1726:2019,SNI 2847:2019,SNI 1729:2020"
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    consultant_name: Optional[str] = None
    building_type: Optional[str] = None
    num_floors: Optional[int] = None
    structural_system: Optional[str] = None
    primary_material: Optional[str] = None
    applicable_standards: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    location: str
    client_name: str
    consultant_name: Optional[str]
    building_type: str
    num_floors: int
    structural_system: str
    primary_material: str
    applicable_standards: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
