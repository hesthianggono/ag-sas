"""
Registry semua benchmark cases AG-SAS.

Tambahkan benchmark baru dengan mendaftarkannya di ALL_BENCHMARKS.
"""

from app.verification.benchmarks.simply_supported_beam import (
    BENCHMARK as SSB_UDL_01,
)
from app.verification.benchmarks.cantilever_beam import (
    BENCHMARK as CANT_PL_01,
)
from app.verification.benchmarks.portal_2d import (
    BENCHMARK as PORTAL_2D_01,
)
from app.verification.benchmarks.truss_2d import (
    BENCHMARK as TRUSS_2D_01,
)
from app.verification.models import BenchmarkCase

ALL_BENCHMARKS: list[BenchmarkCase] = [
    SSB_UDL_01,
    CANT_PL_01,
    PORTAL_2D_01,
    TRUSS_2D_01,
]

_INDEX: dict[str, BenchmarkCase] = {b.benchmark_id: b for b in ALL_BENCHMARKS}


def get_benchmark(benchmark_id: str) -> BenchmarkCase | None:
    return _INDEX.get(benchmark_id)


def list_benchmarks(
    structure_type: str | None = None,
    tag: str | None = None,
    active_only: bool = True,
) -> list[BenchmarkCase]:
    result = ALL_BENCHMARKS
    if active_only:
        result = [b for b in result if b.active]
    if structure_type:
        result = [b for b in result if b.structure_type.value == structure_type]
    if tag:
        result = [b for b in result if tag in b.tags]
    return result
