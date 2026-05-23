"use client";
import { useState } from "react";
import Link from "next/link";
import {
  FlaskConical, ArrowLeft, Search, CheckCircle,
  XCircle, SkipForward, AlertCircle, Clock,
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

interface StoredResult {
  type: "single" | "session";
  data: {
    result_id?: string;
    session_id?: string;
    benchmark_id?: string;
    title?: string;
    timestamp_utc?: string;
    overall_status?: CheckStatus;
    solver_name?: string;
    summary?: { passed: number; failed: number; skipped: number; total: number };
    checks?: QuantityCheck[];
    results?: Array<{
      result_id: string;
      benchmark_id: string;
      title: string;
      timestamp_utc: string;
      overall_status: CheckStatus;
      summary: { passed: number; failed: number; skipped: number; total: number };
      checks: QuantityCheck[];
    }>;
  };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function statusIcon(status: CheckStatus) {
  if (status === "PASS")  return <CheckCircle  className="w-4 h-4 text-emerald-500" />;
  if (status === "FAIL")  return <XCircle      className="w-4 h-4 text-red-500" />;
  if (status === "SKIP")  return <SkipForward  className="w-4 h-4 text-slate-400" />;
  return                         <AlertCircle  className="w-4 h-4 text-amber-500" />;
}

function formatRelError(v: number) {
  if (!isFinite(v) || isNaN(v)) return "—";
  return (v * 100).toFixed(4) + "%";
}

function formatTimestamp(ts: string) {
  try { return new Date(ts).toLocaleString("id-ID"); }
  catch { return ts; }
}

// ── Checks Table ──────────────────────────────────────────────────────────────

function ChecksTable({ checks }: { checks: QuantityCheck[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="w-full text-xs">
        <thead className="bg-slate-50">
          <tr className="text-slate-500 uppercase tracking-wide text-[10px]">
            <th className="px-4 py-2 text-left w-8"></th>
            <th className="px-4 py-2 text-left">Besaran</th>
            <th className="px-4 py-2 text-right">Expected</th>
            <th className="px-4 py-2 text-right">Actual</th>
            <th className="px-4 py-2 text-right">Rel. Error</th>
            <th className="px-4 py-2 text-right">Toleransi</th>
            <th className="px-4 py-2 text-left">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {checks.map((c) => (
            <tr key={c.quantity}
              className={c.status === "FAIL" ? "bg-red-50" : c.status === "SKIP" ? "bg-slate-50" : ""}
            >
              <td className="px-4 py-2">{statusIcon(c.status)}</td>
              <td className="px-4 py-2 font-mono text-slate-700">{c.quantity}</td>
              <td className="px-4 py-2 text-right font-mono">{c.expected?.toPrecision(6)} {c.unit}</td>
              <td className="px-4 py-2 text-right font-mono">
                {c.actual !== null && c.actual !== undefined
                  ? `${c.actual.toPrecision(6)} ${c.unit}`
                  : <span className="text-slate-400">—</span>}
              </td>
              <td className="px-4 py-2 text-right font-mono">{formatRelError(c.rel_error)}</td>
              <td className="px-4 py-2 text-right font-mono">{(c.tolerance_rel * 100).toFixed(2)}%</td>
              <td className="px-4 py-2">
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded
                  ${c.status === "PASS" ? "bg-emerald-100 text-emerald-700" :
                    c.status === "FAIL" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-500"}`}>
                  {c.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ResultLookupPage() {
  const [resultId, setResultId] = useState("");
  const [result, setResult] = useState<StoredResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function lookup() {
    if (!resultId.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/verification/results/${resultId.trim()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Hasil tidak ditemukan.`);
      const data: StoredResult = await res.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const data = result?.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/verification" className="p-2 rounded-lg hover:bg-slate-100 text-slate-500">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-brand-600" />
            Hasil Verifikasi
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">Cari hasil berdasarkan Session ID</p>
        </div>
      </div>

      {/* Lookup */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Masukkan Session ID atau Result ID..."
          value={resultId}
          onChange={(e) => setResultId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && lookup()}
          className="flex-1 px-4 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
        />
        <button
          onClick={lookup}
          disabled={loading || !resultId.trim()}
          className="px-5 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-lg hover:bg-brand-700 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          Cari
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="space-y-4">
          {/* Session header */}
          <div className="bg-white rounded-xl border border-slate-200 px-5 py-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="font-semibold text-slate-800 text-sm">
                  {result?.type === "session" ? "Sesi Verifikasi Penuh" : data.title ?? "Benchmark Result"}
                </p>
                {data.session_id && (
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    Session ID: {data.session_id}
                  </p>
                )}
                <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3" />
                  {formatTimestamp(data.timestamp_utc ?? "")}
                </p>
              </div>
              {data.summary && (
                <div className="flex gap-3">
                  {[
                    { label: "Passed",  v: data.summary.passed,  c: "text-emerald-700 bg-emerald-100" },
                    { label: "Failed",  v: data.summary.failed,  c: "text-red-700 bg-red-100" },
                    { label: "Skipped", v: data.summary.skipped, c: "text-slate-500 bg-slate-100" },
                    { label: "Total",   v: data.summary.total,   c: "text-slate-700 bg-slate-100" },
                  ].map(({ label, v, c }) => (
                    <div key={label} className={`text-center px-3 py-1.5 rounded-lg ${c}`}>
                      <p className="text-lg font-bold">{v}</p>
                      <p className="text-[10px]">{label}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Single result checks */}
          {result?.type === "single" && data.checks && (
            <div>
              <p className="text-sm font-semibold text-slate-700 mb-2">Detail Checks</p>
              <ChecksTable checks={data.checks} />
            </div>
          )}

          {/* Session results list */}
          {result?.type === "session" && data.results && (
            <div className="space-y-4">
              {data.results.map((r) => (
                <div key={r.result_id} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                  <div className={`px-5 py-3 flex items-center gap-3 ${
                    r.overall_status === "FAIL" ? "bg-red-50 border-b border-red-100" :
                    r.overall_status === "PASS" ? "bg-emerald-50 border-b border-emerald-100" :
                    "bg-slate-50 border-b border-slate-100"
                  }`}>
                    {statusIcon(r.overall_status)}
                    <div className="flex-1">
                      <p className="font-semibold text-slate-800 text-sm">{r.title}</p>
                      <p className="text-xs text-slate-400 font-mono">{r.benchmark_id}</p>
                    </div>
                    <span className="text-xs text-slate-500">
                      {r.summary.passed}/{r.summary.total} checks
                    </span>
                  </div>
                  <ChecksTable checks={r.checks} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
