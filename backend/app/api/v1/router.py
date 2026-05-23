from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, calculations, steel_profiles, reports, verification, analysis, figures, full_reports

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(calculations.router)
api_router.include_router(steel_profiles.router)
api_router.include_router(reports.router)
api_router.include_router(figures.router)
api_router.include_router(full_reports.router)
api_router.include_router(verification.router)
api_router.include_router(analysis.router)
