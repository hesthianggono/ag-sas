from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(
        select(Project).where(Project.owner_id == current_user.id, Project.is_active == True)
    ).all()


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    body: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = Project(owner_id=current_user.id, **body.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(project_id, current_user.id, session)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(project_id, current_user.id, session)
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(project, key, val)
    project.updated_at = datetime.utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = _get_owned_project(project_id, current_user.id, session)
    project.is_active = False
    project.updated_at = datetime.utcnow()
    session.add(project)
    session.commit()


def _get_owned_project(project_id: int, user_id: int, session: Session) -> Project:
    project = session.get(Project, project_id)
    if not project or project.owner_id != user_id or not project.is_active:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    return project
