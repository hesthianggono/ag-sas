"""
Format laporan verifikasi untuk display di API, CLI, atau file teks.
"""

from __future__ import annotations

from app.verification.models import (
    BenchmarkResult,
    CheckStatus,
    QuantityCheck,
    VerificationSession,
)

_PASS_ICON  = "✓"
_FAIL_ICON  = "✗"
_SKIP_ICON  = "○"
_ERROR_ICON = "!"


def _status_icon(status: CheckStatus) -> str:
    return {
        CheckStatus.PASS:  _PASS_ICON,
        CheckStatus.FAIL:  _FAIL_ICON,
        CheckStatus.SKIP:  _SKIP_ICON,
        CheckStatus.ERROR: _ERROR_ICON,
    }.get(status, "?")


def format_quantity_check(check: QuantityCheck, indent: int = 4) -> str:
    pad = " " * indent
    icon = _status_icon(check.status)

    if check.actual is None:
        actual_str = "N/A (solver belum tersedia)"
    else:
        actual_str = f"{check.actual:.6g} {check.unit}"

    lines = [
        f"{pad}[{icon}] {check.quantity}",
        f"{pad}    Expected : {check.expected:.6g} {check.unit}",
        f"{pad}    Actual   : {actual_str}",
    ]

    if check.actual is not None:
        if abs(check.expected) > check.tolerance_abs:
            lines.append(f"{pad}    Rel error: {check.rel_error:.2e}  (tol: {check.tolerance_rel:.2e})")
        else:
            lines.append(f"{pad}    Abs error: {check.abs_error:.2e}  (tol_abs: {check.tolerance_abs:.2e})")

    if check.message:
        lines.append(f"{pad}    Note     : {check.message}")

    return "\n".join(lines)


def format_benchmark_result(result: BenchmarkResult) -> str:
    icon = _status_icon(result.overall_status)
    separator = "─" * 70

    lines = [
        separator,
        f"[{icon}] {result.title}",
        f"    Benchmark ID : {result.benchmark_id}",
        f"    Status       : {result.overall_status.value}",
        f"    Passed/Total : {result.passed}/{len(result.checks)}",
        f"    Timestamp    : {result.timestamp_utc}",
        f"    Solver       : {result.solver_name or '-'}  v{result.solver_version or '-'}",
    ]

    if result.notes:
        lines.append(f"    Notes        : {result.notes}")

    lines.append("")
    lines.append("    Checks:")

    for check in result.checks:
        lines.append(format_quantity_check(check, indent=6))
        lines.append("")

    return "\n".join(lines)


def format_session_report(session: VerificationSession) -> str:
    """Format laporan sesi lengkap sebagai teks."""
    double_sep = "═" * 70

    total   = session.total_benchmarks
    passed  = session.total_passed
    failed  = session.total_failed
    skipped = session.total_skipped

    overall_icon = _PASS_ICON if failed == 0 else _FAIL_ICON

    header = "\n".join([
        double_sep,
        "  AG-SAS VERIFICATION REPORT",
        double_sep,
        f"  Session  : {session.session_id}",
        f"  Time     : {session.timestamp_utc}",
        f"  Result   : [{overall_icon}]  "
        f"{passed} passed / {failed} failed / {skipped} skipped / {total} total",
        double_sep,
        "",
    ])

    body = "\n".join(format_benchmark_result(r) for r in session.results)

    footer = "\n".join([
        double_sep,
        "  DISCLAIMER: AG-SAS adalah engineering calculation assistant.",
        "  Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.",
        double_sep,
    ])

    return "\n".join([header, body, footer])


def result_to_api_dict(result: BenchmarkResult) -> dict:
    """Konversi BenchmarkResult ke dict untuk API response."""
    return result.to_dict()


def session_to_api_dict(session: VerificationSession) -> dict:
    """Konversi VerificationSession ke dict untuk API response."""
    return session.to_dict()
