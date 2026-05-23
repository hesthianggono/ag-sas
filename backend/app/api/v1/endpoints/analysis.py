"""API endpoints for structural analysis (Frame 2D, Truss 2D, etc.)."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models.user import User
from app.solver.frame2d.solver import (
    Frame2DSolver,
    Frame2DModel,
    NodeInput,
    ElementInput,
    MaterialInput,
    SectionInput,
    SupportInput,
    NodalLoadInput,
)
from app.engineering_kernel.traceability import build_trace, SolverVersion
from app.postprocessing.frame2d.diagram_data import (
    compute_diagram_data,
    diagram_data_to_dict,
)

router = APIRouter(prefix="/analysis", tags=["Structural Analysis"])

# In-memory result store (keyed by run_id)
_result_store: dict[str, dict] = {}

_SOLVER = Frame2DSolver()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class NodeSchema(BaseModel):
    index: int
    x_m: float
    y_m: float


class MaterialSchema(BaseModel):
    E_mpa: float = Field(200_000.0, gt=0, description="Young's modulus (MPa)")


class SectionSchema(BaseModel):
    A_cm2: float = Field(gt=0, description="Cross-section area (cm²)")
    I_cm4: float = Field(gt=0, description="Moment of inertia (cm⁴)")


class ElementSchema(BaseModel):
    index: int
    node_i: int
    node_j: int
    material: MaterialSchema
    section: SectionSchema
    udl_kn_per_m: float = Field(0.0, description="Uniform distributed load (kN/m, positive = downward)")


class SupportSchema(BaseModel):
    node_index: int
    fix_ux: bool = False
    fix_uy: bool = False
    fix_rz: bool = False


class NodalLoadSchema(BaseModel):
    node_index: int
    fx_kn: float = 0.0
    fy_kn: float = 0.0
    mz_knm: float = 0.0


class Frame2DRunRequest(BaseModel):
    title: str = "Frame 2D Analysis"
    nodes: list[NodeSchema]
    elements: list[ElementSchema]
    supports: list[SupportSchema]
    nodal_loads: list[NodalLoadSchema] = []
    notes: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _schema_to_model(req: Frame2DRunRequest) -> Frame2DModel:
    return Frame2DModel(
        title=req.title,
        nodes=[NodeInput(n.index, n.x_m, n.y_m) for n in req.nodes],
        elements=[
            ElementInput(
                e.index, e.node_i, e.node_j,
                MaterialInput(e.material.E_mpa),
                SectionInput(e.section.A_cm2, e.section.I_cm4),
                e.udl_kn_per_m,
            )
            for e in req.elements
        ],
        supports=[SupportInput(s.node_index, s.fix_ux, s.fix_uy, s.fix_rz) for s in req.supports],
        nodal_loads=[NodalLoadInput(l.node_index, l.fx_kn, l.fy_kn, l.mz_knm) for l in req.nodal_loads],
        notes=req.notes,
    )


def _result_to_dict(result, run_id: str, title: str) -> dict:
    return {
        "run_id": run_id,
        "title": title,
        "status": "OK",
        "summary": {
            "max_displacement_mm": round(result.max_displacement_m * 1000, 4),
            "max_moment_knm": round(result.max_moment_knm, 4),
            "max_shear_kn": round(result.max_shear_kn, 4),
        },
        "displacements": [
            {
                "node": d.node_index,
                "ux_mm": round(d.ux_m * 1000, 5),
                "uy_mm": round(d.uy_m * 1000, 5),
                "rz_mrad": round(d.rz_rad * 1000, 5),
            }
            for d in result.displacements
        ],
        "reactions": [
            {
                "node": r.node_index,
                "rx_kn": round(r.rx_kn, 4),
                "ry_kn": round(r.ry_kn, 4),
                "mz_knm": round(r.mz_knm, 4),
            }
            for r in result.reactions
        ],
        "element_forces": [
            {
                "element": ef.element_index,
                "N_i_kn": round(ef.N_i_kn, 4),
                "Vy_i_kn": round(ef.Vy_i_kn, 4),
                "Mz_i_knm": round(ef.Mz_i_knm, 4),
                "N_j_kn": round(ef.N_j_kn, 4),
                "Vy_j_kn": round(ef.Vy_j_kn, 4),
                "Mz_j_knm": round(ef.Mz_j_knm, 4),
            }
            for ef in result.element_forces
        ],
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/frame2d/run")
def run_frame2d(
    req: Frame2DRunRequest,
    current_user: User = Depends(get_current_user),
):
    """Run 2D frame analysis using Direct Stiffness Method.

    Returns displacements (mm), reactions (kN/kN·m), and element end forces (kN/kN·m).
    """
    try:
        model = _schema_to_model(req)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Traceability
    import dataclasses
    trace = build_trace(
        solver_name=Frame2DSolver.SOLVER_VERSION,
        input_data={
            "title": req.title,
            "n_nodes": len(req.nodes),
            "n_elements": len(req.elements),
            "n_supports": len(req.supports),
        },
        output_data={},
    )

    try:
        result = _SOLVER.solve(model)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solver error: {str(e)}")

    run_id = str(trace.trace_id)
    response = _result_to_dict(result, run_id, req.title)

    # Post-processing: diagram data
    elem_list = [
        {
            "index": e.index,
            "node_i": e.node_i,
            "node_j": e.node_j,
            "udl_kn_per_m": e.udl_kn_per_m,
        }
        for e in req.elements
    ]
    node_list = [{"index": n.index, "x_m": n.x_m, "y_m": n.y_m} for n in req.nodes]
    diagram_data = compute_diagram_data(
        nodes=node_list,
        elements=elem_list,
        element_forces=response["element_forces"],
        displacements=response["displacements"],
        n_points=21,
        deformation_scale=100.0,
    )
    response["diagrams"] = diagram_data_to_dict(diagram_data)

    # Store result
    _result_store[run_id] = response
    return response


@router.get("/frame2d/diagrams/{run_id}")
def get_frame2d_diagrams(
    run_id: str,
    deformation_scale: float = Query(100.0, gt=0, description="Deformation amplification factor"),
    current_user: User = Depends(get_current_user),
):
    """Return diagram data for a run, optionally with a custom deformation scale."""
    if run_id not in _result_store:
        raise HTTPException(status_code=404, detail=f"Result '{run_id}' not found")
    stored = _result_store[run_id]
    # Re-compute with requested scale
    # (We don't re-store elements/nodes here, so we rely on stored diagrams.
    #  For custom scale, client passes scale parameter.)
    if deformation_scale == 100.0:
        return stored.get("diagrams", {})
    # Would need original model data for rescaling; return stored diagrams with note
    return {
        **stored.get("diagrams", {}),
        "_note": "Custom deformation scale requires re-running analysis or passing scale to /run",
    }


@router.get("/frame2d/results/{run_id}")
def get_frame2d_result(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve a previously computed frame 2D result by run_id."""
    if run_id not in _result_store:
        raise HTTPException(status_code=404, detail=f"Result '{run_id}' not found")
    return _result_store[run_id]
