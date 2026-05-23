from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AG Structural Analysis Suite — Platform perhitungan dan laporan struktur baja & beton "
        "berbasis standar SNI Indonesia. "
        "⚠ Semua hasil wajib diperiksa oleh Engineer Struktur berwenang."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

import os

# Baca ALLOWED_ORIGINS dari env (diisi saat deploy), fallback ke localhost
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
)
_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",   # semua preview Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
