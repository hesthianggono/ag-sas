from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.steel_profile import SteelProfile
from pydantic import BaseModel

router = APIRouter(prefix="/steel-profiles", tags=["Steel Profiles"])


class SteelProfileResponse(BaseModel):
    id: int
    category: str
    designation: str
    height_h: float
    flange_width_b: float
    web_thickness_tw: float
    flange_thickness_tf: float
    area_a: float
    ix: float
    sx: float
    zx: float
    rx: float
    ry: float
    weight_per_m: float

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SteelProfileResponse])
def list_profiles(
    category: Optional[str] = Query(None, description="WF, H-Beam, CNP, UNP, Siku, Hollow"),
    session: Session = Depends(get_session),
):
    q = select(SteelProfile)
    if category:
        q = q.where(SteelProfile.category == category)
    return session.exec(q.order_by(SteelProfile.category, SteelProfile.height_h)).all()


@router.get("/categories")
def list_categories(session: Session = Depends(get_session)):
    profiles = session.exec(select(SteelProfile.category).distinct()).all()
    return {"categories": sorted(set(profiles))}
