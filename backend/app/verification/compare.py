"""
Fungsi perbandingan hasil solver vs. expected result.

Semua perbandingan menggunakan kriteria:
  - Relative error  = |actual - expected| / max(|expected|, tol_abs)
  - Pass jika rel_error <= tolerance_rel ATAU abs_error <= tolerance_abs
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.verification.models import (
    BenchmarkCase,
    BenchmarkResult,
    CheckStatus,
    ExpectedValue,
    QuantityCheck,
)


def compare_quantity(
    quantity: str,
    expected: float,
    actual: Optional[float],
    unit: str,
    tolerance_rel: float,
    tolerance_abs: float,
) -> QuantityCheck:
    """
    Bandingkan satu nilai aktual dengan expected.

    Args:
        quantity:      Nama besaran fisik
        expected:      Nilai yang diharapkan
        actual:        Nilai dari solver (None = solver belum tersedia)
        unit:          Satuan display
        tolerance_rel: Toleransi relatif (misal 0.001 = 0.1%)
        tolerance_abs: Toleransi absolut (fallback untuk nilai mendekati nol)

    Returns:
        QuantityCheck dengan status PASS/FAIL/SKIP.
    """
    if actual is None:
        return QuantityCheck(
            quantity=quantity,
            expected=expected,
            actual=None,
            unit=unit,
            abs_error=float("nan"),
            rel_error=float("nan"),
            tolerance_rel=tolerance_rel,
            tolerance_abs=tolerance_abs,
            status=CheckStatus.SKIP,
            message="Solver belum tersedia untuk benchmark ini.",
        )

    abs_error = abs(actual - expected)

    # Hindari pembagian nol: gunakan tolerance_abs sebagai denominator minimum
    denom = max(abs(expected), tolerance_abs)
    rel_error = abs_error / denom

    passed = (rel_error <= tolerance_rel) or (abs_error <= tolerance_abs)

    if passed:
        status = CheckStatus.PASS
        message = (
            f"OK — rel_error={rel_error:.2e} <= tol={tolerance_rel:.2e}"
            if abs(expected) > tolerance_abs
            else f"OK — abs_error={abs_error:.2e} <= tol_abs={tolerance_abs:.2e}"
        )
    else:
        status = CheckStatus.FAIL
        message = (
            f"FAIL — expected={expected:.6g} {unit}, "
            f"actual={actual:.6g} {unit}, "
            f"rel_error={rel_error:.2e} > tol={tolerance_rel:.2e}"
        )

    return QuantityCheck(
        quantity=quantity,
        expected=expected,
        actual=actual,
        unit=unit,
        abs_error=abs_error,
        rel_error=rel_error,
        tolerance_rel=tolerance_rel,
        tolerance_abs=tolerance_abs,
        status=status,
        message=message,
    )


def compare_result(
    benchmark: BenchmarkCase,
    actual_values: dict[str, Optional[float]],
    solver_name: str = "",
    solver_version: str = "",
    notes: str = "",
) -> BenchmarkResult:
    """
    Jalankan perbandingan lengkap untuk satu benchmark.

    Args:
        benchmark:      Definisi benchmark (expected values & tolerances)
        actual_values:  Dict {quantity: nilai_aktual} dari solver.
                        Jika quantity tidak ada di dict, dianggap None (SKIP).
        solver_name:    Nama solver yang digunakan
        solver_version: Versi solver
        notes:          Catatan tambahan

    Returns:
        BenchmarkResult lengkap.
    """
    checks: list[QuantityCheck] = []

    for ev in benchmark.expected_values:
        actual = actual_values.get(ev.quantity)
        check = compare_quantity(
            quantity=ev.quantity,
            expected=ev.value,
            actual=actual,
            unit=ev.unit,
            tolerance_rel=ev.tolerance_rel,
            tolerance_abs=ev.tolerance_abs,
        )
        checks.append(check)

    # Overall status: PASS hanya jika semua PASS; SKIP jika semua SKIP
    statuses = {c.status for c in checks}
    if not checks:
        overall = CheckStatus.SKIP
    elif CheckStatus.FAIL in statuses or CheckStatus.ERROR in statuses:
        overall = CheckStatus.FAIL
    elif statuses == {CheckStatus.SKIP}:
        overall = CheckStatus.SKIP
    else:
        overall = CheckStatus.PASS

    return BenchmarkResult(
        result_id=str(uuid.uuid4()),
        benchmark_id=benchmark.benchmark_id,
        title=benchmark.title,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        checks=checks,
        overall_status=overall,
        solver_name=solver_name,
        solver_version=solver_version,
        notes=notes,
    )
