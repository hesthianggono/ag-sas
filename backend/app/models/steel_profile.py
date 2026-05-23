from typing import Optional
from sqlmodel import Field, SQLModel


class SteelProfile(SQLModel, table=True):
    __tablename__ = "steel_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(max_length=20, index=True)   # WF, H-Beam, CNP, UNP, Siku, Hollow
    designation: str = Field(max_length=50, index=True) # e.g. "WF 200x100x5.5x8"

    # Cross-section dimensions (mm)
    height_h: float       # Overall height H (mm)
    flange_width_b: float # Flange width B (mm)
    web_thickness_tw: float
    flange_thickness_tf: float
    fillet_r: Optional[float] = Field(default=None)

    # Section properties
    area_a: float         # Cross-section area (cm²)
    ix: float             # Moment of inertia x-x (cm⁴)
    iy: float             # Moment of inertia y-y (cm⁴)
    sx: float             # Section modulus x-x (cm³)
    sy: float             # Section modulus y-y (cm³)
    zx: float             # Plastic section modulus x-x (cm³)
    zy: float             # Plastic section modulus y-y (cm³)
    rx: float             # Radius of gyration x-x (cm)
    ry: float             # Radius of gyration y-y (cm)
    weight_per_m: float   # Unit weight (kg/m)
