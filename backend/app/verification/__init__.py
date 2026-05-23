"""
AG-SAS Verification & Validation Framework
===========================================
Sistem pengujian untuk memvalidasi solver struktur terhadap
solusi analitik, contoh textbook, dan regression test.

Sumber kebenaran: solusi analitik eksak dan buku teks standar.
SAP2000/ETABS digunakan sebagai pembanding tambahan, BUKAN sumber tunggal.
"""

from app.verification.models import (
    BenchmarkCase,
    BenchmarkResult,
    CheckStatus,
    ExpectedValue,
    QuantityCheck,
    StructureType,
    VerificationLevel,
    VerificationSession,
)
from app.verification.compare import compare_result, compare_quantity
from app.verification.benchmarks.registry import (
    ALL_BENCHMARKS,
    get_benchmark,
    list_benchmarks,
)
from app.verification.regression.runner import run_benchmark, run_all
from app.verification.reports.formatter import (
    format_benchmark_result,
    format_session_report,
)

__all__ = [
    "BenchmarkCase", "BenchmarkResult", "CheckStatus",
    "ExpectedValue", "QuantityCheck", "StructureType",
    "VerificationLevel", "VerificationSession",
    "compare_result", "compare_quantity",
    "ALL_BENCHMARKS", "get_benchmark", "list_benchmarks",
    "run_benchmark", "run_all",
    "format_benchmark_result", "format_session_report",
]
