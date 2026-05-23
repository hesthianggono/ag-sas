"""
Struktur data untuk Verification & Validation Framework AG-SAS.

Prinsip:
  Setiap benchmark case mendefinisikan input, expected result (dari solusi
  analitik atau referensi terpercaya), dan tolerance. Sistem ini TIDAK
  mengklaim kesetaraan dengan SAP2000/ETABS — software tersebut digunakan
  hanya sebagai pembanding tambahan, bukan sumber kebenaran tunggal.

  Sumber kebenaran: solusi analitik (matematika), textbook standar,
  dan uji silang antar metode independen.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ── Enums ─────────────────────────────────────────────────────────────────────

class StructureType(str, Enum):
    BEAM_2D        = "beam_2d"
    FRAME_2D       = "frame_2d"
    TRUSS_2D       = "truss_2d"
    FRAME_3D       = "frame_3d"
    PLATE          = "plate"
    OTHER          = "other"


class VerificationLevel(str, Enum):
    """Hierarki V&V — semakin tinggi level, semakin kuat dasar verifikasi."""
    L1_ANALYTICAL  = "L1_analytical"   # Solusi analitik eksak
    L2_TEXTBOOK    = "L2_textbook"     # Contoh manual dari buku teks standar
    L3_COMPARISON  = "L3_comparison"   # Uji silang dengan software lain
    L4_BENCHMARK   = "L4_benchmark"    # Benchmark komunitas (NAFEMS, AISC)


class CheckStatus(str, Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    SKIP    = "SKIP"    # solver belum tersedia
    ERROR   = "ERROR"   # exception saat menjalankan


# ── Benchmark Case ────────────────────────────────────────────────────────────

@dataclass
class ExpectedValue:
    """
    Satu nilai yang diharapkan dari solver.

    Attributes:
        quantity:     Nama besaran fisik (misal "midspan_deflection_mm")
        value:        Nilai yang diharapkan
        unit:         Satuan display (informasi saja — solver menggunakan satuan internal)
        tolerance_rel: Toleransi relatif (misal 0.001 = 0.1%)
        tolerance_abs: Toleransi absolut (digunakan jika nilai mendekati nol)
        notes:        Catatan derivasi atau referensi pasal
    """
    quantity: str
    value: float
    unit: str
    tolerance_rel: float = 0.001      # default 0.1% relative
    tolerance_abs: float = 1e-9       # absolute fallback
    notes: str = ""


@dataclass
class BenchmarkCase:
    """
    Definisi lengkap satu kasus verifikasi.

    Attributes:
        benchmark_id:    Identifier unik (slug, e.g. "ssb_udl_01")
        title:           Judul singkat kasus
        description:     Deskripsi problem
        structure_type:  Jenis struktur
        level:           Level V&V
        source_reference: Referensi (buku, pasal, halaman)
        input_data:      Dict berisi semua parameter input
        expected_values: Daftar nilai yang diharapkan
        tags:            Tag untuk filtering (misal ["beam", "deflection"])
        active:          Apakah benchmark ini dijalankan secara default
    """
    benchmark_id: str
    title: str
    description: str
    structure_type: StructureType
    level: VerificationLevel
    source_reference: str
    input_data: dict[str, Any]
    expected_values: list[ExpectedValue]
    tags: list[str] = field(default_factory=list)
    active: bool = True

    def get_expected(self, quantity: str) -> Optional[ExpectedValue]:
        for ev in self.expected_values:
            if ev.quantity == quantity:
                return ev
        return None


# ── Comparison Result ─────────────────────────────────────────────────────────

@dataclass
class QuantityCheck:
    """
    Hasil perbandingan satu besaran fisik.

    Attributes:
        quantity:       Nama besaran
        expected:       Nilai yang diharapkan
        actual:         Nilai dari solver (None jika solver belum tersedia)
        unit:           Satuan display
        abs_error:      |actual - expected|
        rel_error:      |actual - expected| / |expected|  (0 jika expected = 0)
        tolerance_rel:  Toleransi relatif
        tolerance_abs:  Toleransi absolut
        status:         PASS / FAIL / SKIP / ERROR
        message:        Pesan detail
    """
    quantity: str
    expected: float
    actual: Optional[float]
    unit: str
    abs_error: float
    rel_error: float
    tolerance_rel: float
    tolerance_abs: float
    status: CheckStatus
    message: str = ""


@dataclass
class BenchmarkResult:
    """
    Hasil lengkap satu run benchmark.

    Attributes:
        result_id:       UUID unik run ini
        benchmark_id:    ID benchmark yang dijalankan
        title:           Judul benchmark
        timestamp_utc:   Waktu run
        checks:          Daftar hasil perbandingan per besaran
        overall_status:  PASS jika semua checks PASS, FAIL jika ada yang FAIL
        solver_name:     Nama solver yang digunakan
        solver_version:  Versi solver
        notes:           Catatan tambahan
    """
    result_id: str
    benchmark_id: str
    title: str
    timestamp_utc: str
    checks: list[QuantityCheck]
    overall_status: CheckStatus
    solver_name: str = ""
    solver_version: str = ""
    notes: str = ""

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    @property
    def skipped(self) -> int:
        return sum(1 for c in self.checks if c.status == CheckStatus.SKIP)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "benchmark_id": self.benchmark_id,
            "title": self.title,
            "timestamp_utc": self.timestamp_utc,
            "overall_status": self.overall_status.value,
            "solver_name": self.solver_name,
            "solver_version": self.solver_version,
            "notes": self.notes,
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "total": len(self.checks),
            },
            "checks": [
                {
                    "quantity": c.quantity,
                    "expected": c.expected,
                    "actual": c.actual,
                    "unit": c.unit,
                    "abs_error": c.abs_error,
                    "rel_error": c.rel_error,
                    "tolerance_rel": c.tolerance_rel,
                    "status": c.status.value,
                    "message": c.message,
                }
                for c in self.checks
            ],
        }


# ── Session summary ───────────────────────────────────────────────────────────

@dataclass
class VerificationSession:
    """
    Ringkasan satu sesi verifikasi (satu kali 'run all').

    Attributes:
        session_id:    UUID sesi
        timestamp_utc: Waktu sesi
        results:       Daftar BenchmarkResult
    """
    session_id: str
    timestamp_utc: str
    results: list[BenchmarkResult] = field(default_factory=list)

    @classmethod
    def new(cls) -> "VerificationSession":
        return cls(
            session_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )

    @property
    def total_benchmarks(self) -> int:
        return len(self.results)

    @property
    def total_passed(self) -> int:
        return sum(1 for r in self.results if r.overall_status == CheckStatus.PASS)

    @property
    def total_failed(self) -> int:
        return sum(1 for r in self.results if r.overall_status == CheckStatus.FAIL)

    @property
    def total_skipped(self) -> int:
        return sum(1 for r in self.results if r.overall_status == CheckStatus.SKIP)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "timestamp_utc": self.timestamp_utc,
            "summary": {
                "total": self.total_benchmarks,
                "passed": self.total_passed,
                "failed": self.total_failed,
                "skipped": self.total_skipped,
            },
            "results": [r.to_dict() for r in self.results],
        }
