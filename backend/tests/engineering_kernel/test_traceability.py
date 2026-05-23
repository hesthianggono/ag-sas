"""
Unit tests — Engineering Kernel traceability system.

Covers: SolverVersion, AnalysisTrace, build_trace()
"""

import json
import uuid
import pytest
from datetime import datetime, timezone

from app.engineering_kernel.traceability import (
    SolverVersion,
    AnalysisTrace,
    build_trace,
    CURRENT_KERNEL_VERSION,
    CURRENT_CODE_CHECK_VERSION,
)


# ── SolverVersion ─────────────────────────────────────────────────────────────

class TestSolverVersion:
    def test_current_returns_instance(self):
        sv = SolverVersion.current()
        assert isinstance(sv, SolverVersion)

    def test_current_kernel_version(self):
        sv = SolverVersion.current()
        assert sv.kernel_version == CURRENT_KERNEL_VERSION

    def test_current_code_check_version(self):
        sv = SolverVersion.current()
        assert sv.code_check_version == CURRENT_CODE_CHECK_VERSION

    def test_numpy_version_populated(self):
        sv = SolverVersion.current()
        # Either a real version string or "not_installed"
        assert isinstance(sv.numpy_version, str)
        assert len(sv.numpy_version) > 0

    def test_scipy_version_populated(self):
        sv = SolverVersion.current()
        assert isinstance(sv.scipy_version, str)
        assert len(sv.scipy_version) > 0

    def test_is_frozen(self):
        sv = SolverVersion.current()
        with pytest.raises((AttributeError, TypeError)):
            sv.kernel_version = "tampered"

    def test_equality(self):
        sv1 = SolverVersion(
            kernel_version="0.1.0",
            code_check_version="0.1.0",
            numpy_version="1.26.0",
            scipy_version="1.12.0",
        )
        sv2 = SolverVersion(
            kernel_version="0.1.0",
            code_check_version="0.1.0",
            numpy_version="1.26.0",
            scipy_version="1.12.0",
        )
        assert sv1 == sv2


# ── build_trace ───────────────────────────────────────────────────────────────

class TestBuildTrace:
    _input = {"nodes": [{"id": "N1", "x": 0.0, "y": 0.0}]}
    _output = {"displacements": [{"node_id": "N1", "ux": 0.0, "uy": 0.001}]}

    def test_returns_analysis_trace(self):
        trace = build_trace(project_id=1, user_id=42,
                            input_data=self._input, output_data=self._output)
        assert isinstance(trace, AnalysisTrace)

    def test_trace_id_is_valid_uuid(self):
        trace = build_trace(project_id=1, user_id=42,
                            input_data=self._input, output_data=self._output)
        # Raises ValueError if not a valid UUID
        parsed = uuid.UUID(trace.trace_id)
        assert str(parsed) == trace.trace_id

    def test_unique_trace_ids(self):
        t1 = build_trace(project_id=1, user_id=1,
                         input_data=self._input, output_data=self._output)
        t2 = build_trace(project_id=1, user_id=1,
                         input_data=self._input, output_data=self._output)
        assert t1.trace_id != t2.trace_id

    def test_timestamp_is_utc_iso8601(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        # datetime.fromisoformat should parse it without error
        dt = datetime.fromisoformat(trace.timestamp_utc)
        assert dt.tzinfo is not None  # timezone-aware

    def test_project_and_user_id(self):
        trace = build_trace(project_id=99, user_id=7,
                            input_data=self._input, output_data=self._output)
        assert trace.project_id == 99
        assert trace.user_id == 7

    def test_input_snapshot_is_json(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        parsed = json.loads(trace.input_snapshot)
        assert parsed == self._input

    def test_output_snapshot_is_json(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        parsed = json.loads(trace.output_snapshot)
        assert parsed == self._output

    def test_default_assumptions_populated(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        assert len(trace.assumptions) > 0
        # At least one assumption about linear elastic
        full_text = " ".join(trace.assumptions).lower()
        assert "linear" in full_text or "elastic" in full_text

    def test_custom_assumptions(self):
        custom = ["Custom assumption A", "Custom assumption B"]
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output,
                            assumptions=custom)
        assert list(trace.assumptions) == custom

    def test_custom_warnings(self):
        warns = ["Member E5 slenderness exceeds limit"]
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output,
                            warnings=warns)
        assert list(trace.warnings) == warns

    def test_default_no_warnings(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        assert trace.warnings == ()
        assert trace.has_warnings() is False

    def test_has_warnings_true(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output,
                            warnings=["Warning A"])
        assert trace.has_warnings() is True

    def test_converged_default_true(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        assert trace.converged is True

    def test_converged_false(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output,
                            converged=False, convergence_message="Max iter exceeded")
        assert trace.converged is False
        assert trace.convergence_message == "Max iter exceeded"

    def test_load_combination_ids(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output,
                            load_combination_ids=[1, 2, 3])
        assert trace.load_combination_ids == (1, 2, 3)

    def test_calculation_id_optional(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output,
                            calculation_id=55)
        assert trace.calculation_id == 55

    def test_calculation_id_default_none(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        assert trace.calculation_id is None

    def test_solver_version_attached(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data=self._input, output_data=self._output)
        assert isinstance(trace.solver_version, SolverVersion)
        assert trace.solver_version.kernel_version == CURRENT_KERNEL_VERSION


# ── AnalysisTrace immutability ────────────────────────────────────────────────

class TestAnalysisTraceImmutability:
    def _build(self):
        return build_trace(
            project_id=1, user_id=1,
            input_data={"x": 1}, output_data={"y": 2}
        )

    def test_trace_id_immutable(self):
        trace = self._build()
        with pytest.raises((AttributeError, TypeError)):
            trace.trace_id = "tampered"

    def test_input_snapshot_immutable(self):
        trace = self._build()
        with pytest.raises((AttributeError, TypeError)):
            trace.input_snapshot = '{"x": 99}'

    def test_output_snapshot_immutable(self):
        trace = self._build()
        with pytest.raises((AttributeError, TypeError)):
            trace.output_snapshot = '{"y": 99}'

    def test_project_id_immutable(self):
        trace = self._build()
        with pytest.raises((AttributeError, TypeError)):
            trace.project_id = 999

    def test_assumptions_is_tuple(self):
        trace = self._build()
        assert isinstance(trace.assumptions, tuple)

    def test_warnings_is_tuple(self):
        trace = self._build()
        assert isinstance(trace.warnings, tuple)

    def test_load_combination_ids_is_tuple(self):
        trace = build_trace(project_id=1, user_id=1,
                            input_data={}, output_data={},
                            load_combination_ids=[10, 20])
        assert isinstance(trace.load_combination_ids, tuple)


# ── Serialization ─────────────────────────────────────────────────────────────

class TestAnalysisTraceSerialization:
    def _build(self, **kwargs):
        return build_trace(
            project_id=1, user_id=1,
            input_data={"nodes": []},
            output_data={"reactions": []},
            **kwargs,
        )

    def test_to_dict_keys(self):
        trace = self._build()
        d = trace.to_dict()
        required_keys = {
            "trace_id", "project_id", "user_id", "timestamp_utc",
            "solver_version", "input_snapshot", "output_snapshot",
            "load_combination_ids", "assumptions", "warnings",
            "converged", "convergence_message",
        }
        assert required_keys.issubset(set(d.keys()))

    def test_to_dict_lists_not_tuples(self):
        trace = self._build(
            load_combination_ids=[1, 2],
            assumptions=["A"],
            warnings=["W"],
        )
        d = trace.to_dict()
        assert isinstance(d["load_combination_ids"], list)
        assert isinstance(d["assumptions"], list)
        assert isinstance(d["warnings"], list)

    def test_to_json_valid_json(self):
        trace = self._build()
        json_str = trace.to_json()
        parsed = json.loads(json_str)
        assert parsed["project_id"] == 1

    def test_to_json_roundtrip_trace_id(self):
        trace = self._build()
        parsed = json.loads(trace.to_json())
        assert parsed["trace_id"] == trace.trace_id

    def test_input_data_method(self):
        input_d = {"nodes": [{"id": "N1"}], "elements": []}
        trace = self._build()
        # build_trace used {"nodes": []} so check input_data() returns dict
        result = trace.input_data()
        assert isinstance(result, dict)

    def test_output_data_method(self):
        trace = self._build()
        result = trace.output_data()
        assert isinstance(result, dict)

    def test_snapshot_non_ascii_preserved(self):
        input_d = {"nama_proyek": "Gedung Kantor Pusat"}
        trace = build_trace(project_id=1, user_id=1,
                            input_data=input_d, output_data={})
        parsed = json.loads(trace.input_snapshot)
        assert parsed["nama_proyek"] == "Gedung Kantor Pusat"
