"""
Traceability — rekaman lengkap setiap run analisis.

Prinsip:
  Setiap hasil perhitungan yang disimpan ke database HARUS disertai
  AnalysisTrace yang dapat mereproduksi ulang perhitungan tersebut.

  AnalysisTrace adalah immutable setelah dibuat — tidak ada perubahan
  yang diperbolehkan setelah trace disimpan.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from app.engineering_kernel import KERNEL_VERSION

# ── Versi saat ini ────────────────────────────────────────────────────────────

CURRENT_KERNEL_VERSION: str = KERNEL_VERSION
CURRENT_CODE_CHECK_VERSION: str = "0.1.0"   # versi app/calculation/


@dataclass(frozen=True)
class SolverVersion:
    """
    Versi komponen perangkat lunak saat analisis dijalankan.

    Diisi otomatis oleh build_trace() menggunakan versi saat ini.
    """
    kernel_version: str
    code_check_version: str
    numpy_version: str
    scipy_version: str

    @classmethod
    def current(cls) -> "SolverVersion":
        """Buat SolverVersion dari library yang terinstal saat ini."""
        try:
            import numpy as np
            numpy_ver = np.__version__
        except ImportError:
            numpy_ver = "not_installed"

        try:
            import scipy
            scipy_ver = scipy.__version__
        except ImportError:
            scipy_ver = "not_installed"

        return cls(
            kernel_version=CURRENT_KERNEL_VERSION,
            code_check_version=CURRENT_CODE_CHECK_VERSION,
            numpy_version=numpy_ver,
            scipy_version=scipy_ver,
        )


@dataclass(frozen=True)
class AnalysisTrace:
    """
    Rekaman lengkap satu sesi analisis.

    Setiap field adalah immutable setelah trace dibuat.
    Trace disimpan bersama hasil analisis di database.

    Attributes:
        trace_id:              UUID unik — dibuat sekali, tidak dapat diubah
        project_id:            ID proyek dari database
        calculation_id:        ID perhitungan (jika ada, e.g. dari CalculationRecord)
        user_id:               ID pengguna yang menjalankan analisis
        timestamp_utc:         Waktu analisis dalam UTC (ISO 8601)
        solver_version:        Versi kernel, code-check, numpy, scipy
        input_snapshot:        Serialisasi JSON dari seluruh input model
        output_snapshot:       Serialisasi JSON dari seluruh output (hasil analisis)
        load_combination_ids:  Daftar ID LoadCombinationRule dari DB yang digunakan
        assumptions:           Asumsi-asumsi yang berlaku dalam analisis ini
        warnings:              Peringatan yang dihasilkan selama analisis
        converged:             Apakah solver konvergen?
        convergence_message:   Pesan konvergensi dari solver
    """
    trace_id: str                      # UUID
    project_id: int
    user_id: int
    timestamp_utc: str                 # ISO 8601

    # Versi perangkat lunak
    solver_version: SolverVersion

    # Snapshot data (JSON string — immutable)
    input_snapshot: str                # JSON dari model input
    output_snapshot: str               # JSON dari hasil analisis

    # Referensi
    load_combination_ids: tuple[int, ...] = field(default_factory=tuple)
    calculation_id: Optional[int] = None

    # Asumsi dan peringatan
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    # Status solver
    converged: bool = True
    convergence_message: str = ""

    def to_dict(self) -> dict:
        """Konversi ke dict untuk penyimpanan di database."""
        d = asdict(self)
        # tuple tidak serializable langsung — konversi ke list untuk JSON
        d["load_combination_ids"] = list(self.load_combination_ids)
        d["assumptions"] = list(self.assumptions)
        d["warnings"] = list(self.warnings)
        return d

    def to_json(self) -> str:
        """Serialisasi ke JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def input_data(self) -> dict:
        """Parse input_snapshot kembali ke dict."""
        return json.loads(self.input_snapshot)

    def output_data(self) -> dict:
        """Parse output_snapshot kembali ke dict."""
        return json.loads(self.output_snapshot)

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def build_trace(
    project_id: int,
    user_id: int,
    input_data: dict,
    output_data: dict,
    load_combination_ids: Optional[list[int]] = None,
    calculation_id: Optional[int] = None,
    assumptions: Optional[list[str]] = None,
    warnings: Optional[list[str]] = None,
    converged: bool = True,
    convergence_message: str = "",
) -> AnalysisTrace:
    """
    Buat AnalysisTrace baru dengan UUID dan timestamp otomatis.

    Args:
        project_id:            ID proyek
        user_id:               ID pengguna
        input_data:            Dict berisi seluruh input model (akan di-JSON-kan)
        output_data:           Dict berisi seluruh hasil analisis
        load_combination_ids:  Daftar ID kombinasi beban dari DB
        calculation_id:        ID record perhitungan (opsional)
        assumptions:           Daftar asumsi analisis
        warnings:              Daftar peringatan dari solver
        converged:             Status konvergensi
        convergence_message:   Pesan konvergensi

    Returns:
        AnalysisTrace yang siap disimpan ke database.
    """
    default_assumptions = [
        "Linear elastic material behavior",
        "Small displacement theory (first-order analysis)",
        "Euler-Bernoulli beam element (shear deformation diabaikan)",
        "Rigid joint (momen ditransfer penuh di joint)",
        "Beban diterapkan secara statis",
    ]

    return AnalysisTrace(
        trace_id=str(uuid.uuid4()),
        project_id=project_id,
        user_id=user_id,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        solver_version=SolverVersion.current(),
        input_snapshot=json.dumps(input_data, ensure_ascii=False, default=str),
        output_snapshot=json.dumps(output_data, ensure_ascii=False, default=str),
        load_combination_ids=tuple(load_combination_ids or []),
        calculation_id=calculation_id,
        assumptions=tuple(assumptions or default_assumptions),
        warnings=tuple(warnings or []),
        converged=converged,
        convergence_message=convergence_message,
    )
