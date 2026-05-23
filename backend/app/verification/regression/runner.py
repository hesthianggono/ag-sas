"""
Regression runner — jalankan semua benchmark dan kembalikan laporan sesi.

Saat solver FEM belum tersedia, runner akan menggunakan fungsi
analytical_solution() dari masing-masing benchmark sebagai "solver sementara"
untuk memvalidasi bahwa formula analitik sendiri sudah benar.

Ketika solver FEM tersedia, daftarkan di SOLVER_REGISTRY dan ubah
_get_actual_values() untuk memanggil solver sungguhan.
"""

from __future__ import annotations

from typing import Callable, Optional

from app.verification.benchmarks.registry import ALL_BENCHMARKS, get_benchmark
from app.verification.benchmarks import (
    simply_supported_beam,
    cantilever_beam,
    portal_2d,
    truss_2d,
)
from app.verification.compare import compare_result
from app.verification.models import (
    BenchmarkCase,
    BenchmarkResult,
    CheckStatus,
    VerificationSession,
)
from app.engineering_kernel import KERNEL_VERSION


# ── Solver Registry ───────────────────────────────────────────────────────────
#
# Mapping benchmark_id → callable yang mengembalikan dict {quantity: value}.
# Setiap callable menerima input_data dict dari BenchmarkCase.
#
# Fase awal: gunakan analytical_solution() dari modul benchmark itu sendiri
#   sebagai "solver" (memverifikasi bahwa formula sudah benar).
# Fase FEM: ganti dengan panggilan ke solver FEM sungguhan.

def _solve_ssb_udl(input_data: dict) -> dict:
    """FEM solver: simply supported beam with UDL (3 nodes for midspan)."""
    from app.solver.frame2d.solver import (
        Frame2DSolver, Frame2DModel, NodeInput, ElementInput,
        MaterialInput, SectionInput, SupportInput,
    )
    L = input_data["L_m"]
    w = input_data["w_kN_m"]
    E = input_data["E_kN_m2"] / 1e3   # kN/m² → MPa
    I_m4 = input_data["I_m4"]
    I_cm4 = I_m4 * 1e8                 # m⁴ → cm⁴
    A_cm2 = 84.12                       # WF400 area

    model = Frame2DModel(
        title="SSB-UDL-01 FEM",
        nodes=[NodeInput(0, 0.0, 0.0), NodeInput(1, L/2, 0.0), NodeInput(2, L, 0.0)],
        elements=[
            ElementInput(0, 0, 1, MaterialInput(E), SectionInput(A_cm2, I_cm4), udl_kn_per_m=w),
            ElementInput(1, 1, 2, MaterialInput(E), SectionInput(A_cm2, I_cm4), udl_kn_per_m=w),
        ],
        supports=[
            SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=False),
            SupportInput(2, fix_ux=False, fix_uy=True, fix_rz=False),
        ],
    )
    result = Frame2DSolver().solve(model)
    reactions = {r.node_index: r for r in result.reactions}
    disp = {d.node_index: d for d in result.displacements}
    ef0 = result.element_forces[0]

    return {
        "midspan_deflection_mm": abs(disp[1].uy_m) * 1000,
        "max_moment_kNm": abs(ef0.Mz_j_knm),
        "reaction_A_kN": abs(reactions[0].ry_kn),
        "reaction_B_kN": abs(reactions[2].ry_kn),
        "max_shear_kN": abs(ef0.Vy_i_kn),
    }


def _solve_cant_pl(input_data: dict) -> dict:
    """FEM solver: cantilever with tip point load."""
    from app.solver.frame2d.solver import (
        Frame2DSolver, Frame2DModel, NodeInput, ElementInput,
        MaterialInput, SectionInput, SupportInput, NodalLoadInput,
    )
    L = input_data["L_m"]
    P = input_data["P_kN"]
    E = input_data["E_kN_m2"] / 1e3
    I_cm4 = input_data["I_m4"] * 1e8
    A_cm2 = 84.12

    model = Frame2DModel(
        title="CANT-PL-01 FEM",
        nodes=[NodeInput(0, 0.0, 0.0), NodeInput(1, L, 0.0)],
        elements=[ElementInput(0, 0, 1, MaterialInput(E), SectionInput(A_cm2, I_cm4))],
        supports=[SupportInput(0, fix_ux=True, fix_uy=True, fix_rz=True)],
        nodal_loads=[NodalLoadInput(1, fy_kn=-P)],
    )
    result = Frame2DSolver().solve(model)
    reactions = {r.node_index: r for r in result.reactions}
    disp = {d.node_index: d for d in result.displacements}

    return {
        "tip_deflection_mm": abs(disp[1].uy_m) * 1000,
        "tip_rotation_rad": abs(disp[1].rz_rad),
        "fixed_end_moment_kNm": abs(reactions[0].mz_knm),
        "max_shear_kN": abs(result.element_forces[0].Vy_i_kn),
        "reaction_vertical_kN": abs(reactions[0].ry_kn),
    }


def _solve_portal_2d(input_data: dict) -> dict:
    return portal_2d.equilibrium_check(
        H=input_data["H_kN"],
        h=input_data["h_m"],
        b=input_data["b_m"],
    )


def _solve_truss_2d(input_data: dict) -> dict:
    return truss_2d.method_of_joints(
        P=input_data["P_kN"],
        span=input_data["span_m"],
        rise=input_data["rise_m"],
    )


SOLVER_REGISTRY: dict[str, Callable[[dict], dict]] = {
    "ssb_udl_01":    _solve_ssb_udl,
    "cant_pl_01":    _solve_cant_pl,
    "portal_2d_01":  _solve_portal_2d,
    "truss_2d_01":   _solve_truss_2d,
}


# ── Runner ────────────────────────────────────────────────────────────────────

def run_benchmark(benchmark_id: str) -> BenchmarkResult:
    """
    Jalankan satu benchmark dan kembalikan hasilnya.

    Jika solver tidak terdaftar di SOLVER_REGISTRY, semua checks akan SKIP.
    """
    benchmark = get_benchmark(benchmark_id)
    if benchmark is None:
        raise ValueError(f"Benchmark tidak ditemukan: '{benchmark_id}'")

    solver_fn = SOLVER_REGISTRY.get(benchmark_id)

    if solver_fn is None:
        # Solver belum tersedia — semua checks SKIP
        actual_values: dict = {}
        solver_name = "not_available"
    else:
        try:
            actual_values = solver_fn(benchmark.input_data)
            solver_name = "frame2d-dsm-v1.0" if benchmark_id in ("ssb_udl_01", "cant_pl_01") else "analytical_formula"
        except Exception as exc:
            # Solver error — kembalikan result dengan status ERROR
            from app.verification.models import QuantityCheck
            import uuid, datetime, timezone
            checks = [
                QuantityCheck(
                    quantity=ev.quantity,
                    expected=ev.value,
                    actual=None,
                    unit=ev.unit,
                    abs_error=float("nan"),
                    rel_error=float("nan"),
                    tolerance_rel=ev.tolerance_rel,
                    tolerance_abs=ev.tolerance_abs,
                    status=CheckStatus.ERROR,
                    message=f"Solver error: {exc}",
                )
                for ev in benchmark.expected_values
            ]
            from datetime import datetime, timezone
            return BenchmarkResult(
                result_id=str(uuid.uuid4()),
                benchmark_id=benchmark_id,
                title=benchmark.title,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                checks=checks,
                overall_status=CheckStatus.ERROR,
                solver_name="error",
                notes=str(exc),
            )

    return compare_result(
        benchmark=benchmark,
        actual_values=actual_values,
        solver_name=solver_name,
        solver_version=KERNEL_VERSION,
    )


def run_all(active_only: bool = True) -> VerificationSession:
    """
    Jalankan semua benchmark yang terdaftar dan kembalikan laporan sesi.

    Args:
        active_only: Hanya jalankan benchmark dengan active=True

    Returns:
        VerificationSession berisi semua BenchmarkResult.
    """
    session = VerificationSession.new()

    benchmarks = ALL_BENCHMARKS
    if active_only:
        benchmarks = [b for b in benchmarks if b.active]

    for benchmark in benchmarks:
        result = run_benchmark(benchmark.benchmark_id)
        session.results.append(result)

    return session
