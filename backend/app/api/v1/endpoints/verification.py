"""
Endpoint Verification & Validation Framework.

GET  /verification/benchmarks          — daftar semua benchmark
GET  /verification/benchmarks/{id}     — detail satu benchmark
POST /verification/run                 — jalankan satu atau semua benchmark
GET  /verification/results/{result_id} — ambil hasil berdasarkan ID sesi
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.verification.benchmarks.registry import get_benchmark, list_benchmarks
from app.verification.regression.runner import run_benchmark, run_all
from app.verification.reports.formatter import result_to_api_dict, session_to_api_dict
from app.verification.models import StructureType

router = APIRouter(prefix="/verification", tags=["Verification & Validation"])

# In-memory store untuk hasil sesi (production: ganti dengan DB)
_session_store: dict[str, dict] = {}


# ── Response helpers ──────────────────────────────────────────────────────────

def _benchmark_summary(b) -> dict:
    return {
        "benchmark_id":    b.benchmark_id,
        "title":           b.title,
        "description":     b.description,
        "structure_type":  b.structure_type.value,
        "level":           b.level.value,
        "source_reference": b.source_reference,
        "tags":            b.tags,
        "active":          b.active,
        "expected_count":  len(b.expected_values),
        "expected_values": [
            {
                "quantity":      ev.quantity,
                "value":         ev.value,
                "unit":          ev.unit,
                "tolerance_rel": ev.tolerance_rel,
                "notes":         ev.notes,
            }
            for ev in b.expected_values
        ],
        "input_data": b.input_data,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/benchmarks")
def get_benchmarks(
    structure_type: Optional[str] = Query(None, description="Filter: beam_2d, frame_2d, truss_2d, ..."),
    tag:            Optional[str] = Query(None, description="Filter by tag"),
    active_only:    bool          = Query(True,  description="Hanya tampilkan benchmark aktif"),
):
    """
    Daftar semua benchmark case yang terdaftar.

    Bisa difilter berdasarkan structure_type dan tag.
    """
    benchmarks = list_benchmarks(
        structure_type=structure_type,
        tag=tag,
        active_only=active_only,
    )
    return {
        "total": len(benchmarks),
        "benchmarks": [_benchmark_summary(b) for b in benchmarks],
    }


@router.get("/benchmarks/{benchmark_id}")
def get_benchmark_detail(benchmark_id: str):
    """Detail satu benchmark case."""
    b = get_benchmark(benchmark_id)
    if b is None:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' tidak ditemukan.")
    return _benchmark_summary(b)


class RunRequest(BaseModel):
    benchmark_id: Optional[str] = None   # None = jalankan semua
    active_only:  bool = True


@router.post("/run")
def run_verification(req: RunRequest):
    """
    Jalankan verifikasi.

    - Jika `benchmark_id` diisi: jalankan satu benchmark saja.
    - Jika kosong: jalankan semua benchmark aktif.

    Hasil sesi disimpan sementara dan dapat diakses via `/results/{session_id}`.
    """
    if req.benchmark_id:
        b = get_benchmark(req.benchmark_id)
        if b is None:
            raise HTTPException(status_code=404, detail=f"Benchmark '{req.benchmark_id}' tidak ditemukan.")
        result = run_benchmark(req.benchmark_id)
        result_dict = result_to_api_dict(result)
        # Simpan sebagai mini-session
        _session_store[result.result_id] = {
            "type": "single",
            "data": result_dict,
        }
        return {
            "type": "single",
            "session_id": result.result_id,
            "result": result_dict,
        }
    else:
        session = run_all(active_only=req.active_only)
        session_dict = session_to_api_dict(session)
        _session_store[session.session_id] = {
            "type": "session",
            "data": session_dict,
        }
        return {
            "type": "session",
            "session_id": session.session_id,
            "result": session_dict,
        }


@router.get("/results/{result_id}")
def get_result(result_id: str):
    """
    Ambil hasil verifikasi berdasarkan session_id atau result_id.

    ID diperoleh dari response POST /verification/run.
    """
    stored = _session_store.get(result_id)
    if stored is None:
        raise HTTPException(
            status_code=404,
            detail=f"Hasil '{result_id}' tidak ditemukan. Jalankan POST /verification/run terlebih dahulu.",
        )
    return stored
