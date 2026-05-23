"use client";
import { useState } from "react";
import Link from "next/link";
import {
  CheckCircle, XCircle, SkipForward, AlertCircle,
  Play, RefreshCw, FlaskConical, List, Clock,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

type CheckStatus = "PASS" | "FAIL" | "SKIP" | "ERROR";

interface QuantityCheck {
  quantity: string;
  expected: number;
  actual: number | null;
  unit: string;
  abs_error: number;
  rel_error: number;
  tolerance_rel: number;
  status: CheckStatus;
  message: string;
}

interface BenchmarkResult {
  result_id: string;
  benchmark_id: string;
  title: string;
  timestamp_utc: string;
  overall_status: CheckStatus;
  solver_name: string;
  solver_version: string;
  summary: { passed: number; failed: number; skipped: number; total: number };
  checks: QuantityCheck[];
}

interface SessionResult {
  session_id: string;
  timestamp_utc: string;
  summary: { total: number; passed: number; failed: number; skipped: number };
  results: BenchmarkResult[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function statusIcon(status: CheckStatus, size = "w-5 h-5") {
  if (status === "PASS")  return <CheckCircle  className={`${size} text-emerald-500`} />;
  if (status === "FAIL")  return <XCircle      className={`${size} text-red-500`} />;
  if (status === "SKIP")  return <SkipForward  className={`${size} text-slate-400`} />;
  return                         <AlertCircle  className={`${size} text-amber-500`} />;
}

function statusBadge(status: CheckStatus) {
  const cls: Record<CheckStatus, string> = {
    PASS:  "bg-emerald-100 text-emerald-700",
    FAIL:  "bg-red-100 text-red-700",
    SKIP:  "bg-slate-100 text-slate-500",
    ERROR: "bg-amber-100 text-amber-700",
  };
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded ${cls[status]}`}>
      {statusIcon(status, "w-3.5 h-3.5")}
      {status}
    </span>
  );
}

function formatRelError(v: number) {
  if (!isFinite(v) || isNaN(v)) return "—";
  return (v * 100).toFixed(4) + "%";
}

function formatTimestamp(ts: string) {
  try { return new Date(ts).toLocaleString("id-ID"); }
  catch { return ts; }
}

// ── Benchmark Result Card ─────────────────────────────────────────────────────

function BenchmarkCard({ result }: { result: BenchmarkResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`rounded-xl border bg-white shadow-sm overflow-hidden transition-all
      ${result.overall_status === "FAIL" ? "border-red-200" :
        result.overall_status === "PASS" ? "border-emerald-200" : "border-slate-200"}`}>
      <button
        className="w-full flex items-center gap-3 px-5 py-4 hover:bg-slate-50 transition-colors text-left"
        onClick={() => setExpanded(!expanded)}
      >
        {statusIcon(result.overall_status)}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-800 text-sm truncate">{result.title}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {result.benchmark_id} · {result.solver_name || "no solver"} · {formatTimestamp(result.timestamp_utc)}
          </p>
        </div>
        <div className="flex items-center gap-3 ml-4 shrink-0">
          <span className="text-xs text-slate-500">
            {result.summary.passed}/{result.summary.total} checks
          </span>
          {statusBadge(result.overall_status)}
          <span className={`text-xs text-slate-400 transition-transform ${expanded ? "rotate-90" : ""}`}>›</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-slate-100 overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-50">
              <tr className="text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-2 text-left font-medium w-8"></th>
                <th className="px-4 py-2 text-left font-medium">Besaran</th>
                <th className="px-4 py-2 text-right font-medium">Expected</th>
                <th className="px-4 py-2 text-right font-medium">Actual</th>
                <th className="px-4 py-2 text-right font-medium">Rel. Error</th>
                <th className="px-4 py-2 text-right font-medium">Tolerance</th>
                <th className="px-4 py-2 text-left font-medium">Catatan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {result.checks.map((c) => (
                <tr key={c.quantity} className={
                  c.status === "FAIL" ? "bg-red-50" :
                  c.status === "PASS" ? "" : "bg-slate-50"
                }>
                  <td className="px-4 py-2">{statusIcon(c.status, "w-4 h-4")}</td>
                  <td className="px-4 py-2 font-mono text-slate-700">{c.quantity}</td>
                  <td className="px-4 py-2 text-right font-mono">{c.expected.toPrecision(6)} {c.unit}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {c.actual !== null ? `${c.actual.toPrecision(6)} ${c.unit}` : <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-4 py-2 text-right font-mono">{formatRelError(c.rel_error)}</td>
                  <td className="px-4 py-2 text-right font-mono">{(c.tolerance_rel * 100).toFixed(2)}%</td>
                  <td className="px-4 py-2 text-slate-500 max-w-xs truncate">{c.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Summary Bar ───────────────────────────────────────────────────────────────

function SummaryBar({ summary }: { summary: SessionResult["summary"] }) {
  const items = [
    { label: "Total",   value: summary.total,   color: "text-slate-700",  bg: "bg-slate-100" },
    { label: "Passed",  value: summary.passed,  color: "text-emerald-700", bg: "bg-emerald-100" },
    { label: "Failed",  value: summary.failed,  color: "text-red-700",    bg: "bg-red-100" },
    { label: "Skipped", value: summary.skipped, color: "text-slate-500",  bg: "bg-slate-100" },
  ];
  return (
    <div className="grid grid-cols-4 gap-3 mb-6">
      {items.map(({ label, value, color, bg }) => (
        <div key={label} className={`${bg} rounded-xl px-5 py-4 text-center`}>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          <p className={`text-xs mt-0.5 ${color} opacity-70`}>{label}</p>
        </div>
      ))}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function VerificationPage() {
  const [session, setSession] = useState<SessionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runAll() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/verification/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active_only: true }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setSession(data.result as SessionResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-brand-600" />
            Verification & Validation
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Validasi solver terhadap solusi analitik dan contoh textbook
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/verification/benchmarks"
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <List className="w-4 h-4" />
            Benchmark List
          </Link>
          <button
            onClick={runAll}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {loading
              ? <RefreshCw className="w-4 h-4 animate-spin" />
              : <Play className="w-4 h-4" />}
            {loading ? "Menjalankan..." : "Run All Benchmarks"}
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3 text-sm text-amber-800">
        <strong>Disclaimer:</strong> AG-SAS adalah engineering calculation assistant.
        Hasil final wajib diperiksa dan disetujui oleh engineer struktur berwenang.
        Benchmark ini memverifikasi konsistensi formula — bukan sertifikasi software.
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-sm text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}. Pastikan backend berjalan di localhost:8000.
        </div>
      )}

      {/* Idle state */}
      {!session && !loading && !error && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 py-16 text-center">
          <FlaskConical className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">Belum ada hasil verifikasi</p>
          <p className="text-slate-400 text-sm mt-1">Klik "Run All Benchmarks" untuk memulai</p>
        </div>
      )}

      {/* Session results */}
      {session && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-700">
                Hasil Verifikasi
                <span className={`ml-2 text-xs font-bold px-2 py-0.5 rounded ${
                  session.summary.failed === 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                }`}>
                  {session.summary.failed === 0 ? "ALL PASS" : `${session.summary.failed} FAILED`}
                </span>
              </p>
              <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                <Clock className="w-3 h-3" />
                {formatTimestamp(session.timestamp_utc)} · Session {session.session_id.slice(0, 8)}…
              </p>
            </div>
          </div>

          <SummaryBar summary={session.summary} />

          <div className="space-y-3">
            {session.results.map((r) => (
              <BenchmarkCard key={r.result_id} result={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
