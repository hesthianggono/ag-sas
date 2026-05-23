"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import {
  FlaskConical, ArrowLeft, Search, Tag,
  ChevronDown, ChevronUp, BookOpen, CheckCircle,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface ExpectedValue {
  quantity: string;
  value: number;
  unit: string;
  tolerance_rel: number;
  notes: string;
}

interface Benchmark {
  benchmark_id: string;
  title: string;
  description: string;
  structure_type: string;
  level: string;
  source_reference: string;
  tags: string[];
  active: boolean;
  expected_count: number;
  expected_values: ExpectedValue[];
  input_data: Record<string, unknown>;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const LEVEL_LABELS: Record<string, { label: string; color: string }> = {
  L1_analytical: { label: "L1 — Analitik Eksak",  color: "bg-emerald-100 text-emerald-700" },
  L2_textbook:   { label: "L2 — Textbook",        color: "bg-blue-100 text-blue-700" },
  L3_comparison: { label: "L3 — Perbandingan",    color: "bg-purple-100 text-purple-700" },
  L4_benchmark:  { label: "L4 — Benchmark Komunitas", color: "bg-amber-100 text-amber-700" },
};

const TYPE_LABELS: Record<string, string> = {
  beam_2d:  "Balok 2D",
  frame_2d: "Portal 2D",
  truss_2d: "Truss 2D",
  frame_3d: "Portal 3D",
  plate:    "Pelat",
  other:    "Lainnya",
};

function LevelBadge({ level }: { level: string }) {
  const l = LEVEL_LABELS[level] ?? { label: level, color: "bg-slate-100 text-slate-600" };
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${l.color}`}>
      {l.label}
    </span>
  );
}

// ── Benchmark Card ────────────────────────────────────────────────────────────

function BenchmarkCard({ b }: { b: Benchmark }) {
  const [showExpected, setShowExpected] = useState(false);
  const [showInput, setShowInput] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-slate-800 text-sm">{b.title}</h3>
              {b.active && (
                <span className="text-[10px] bg-green-100 text-green-700 font-bold px-1.5 py-0.5 rounded">
                  AKTIF
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">{b.benchmark_id}</p>
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">{b.description}</p>
          </div>
          <div className="flex flex-col gap-1.5 items-end shrink-0">
            <LevelBadge level={b.level} />
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
              {TYPE_LABELS[b.structure_type] ?? b.structure_type}
            </span>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mt-3">
          {b.tags.map((t) => (
            <span key={t} className="flex items-center gap-1 text-[11px] bg-slate-50 text-slate-500 border border-slate-200 px-2 py-0.5 rounded">
              <Tag className="w-2.5 h-2.5" />
              {t}
            </span>
          ))}
        </div>

        {/* Reference */}
        <div className="mt-3 flex items-start gap-2 text-xs text-slate-500">
          <BookOpen className="w-3.5 h-3.5 mt-0.5 shrink-0 text-slate-400" />
          <span>{b.source_reference}</span>
        </div>

        {/* Expand buttons */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setShowExpected(!showExpected)}
            className="flex items-center gap-1.5 text-xs text-brand-600 hover:text-brand-700 font-medium"
          >
            {showExpected ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            {b.expected_count} Expected Values
          </button>
          <button
            onClick={() => setShowInput(!showInput)}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 font-medium"
          >
            {showInput ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            Input Data
          </button>
        </div>
      </div>

      {/* Expected values table */}
      {showExpected && (
        <div className="border-t border-slate-100 overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-50">
              <tr className="text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-2 text-left font-medium">Besaran</th>
                <th className="px-4 py-2 text-right font-medium">Nilai</th>
                <th className="px-4 py-2 text-right font-medium">Toleransi</th>
                <th className="px-4 py-2 text-left font-medium">Catatan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {b.expected_values.map((ev) => (
                <tr key={ev.quantity}>
                  <td className="px-4 py-2 font-mono text-slate-700">{ev.quantity}</td>
                  <td className="px-4 py-2 text-right font-mono font-semibold">
                    {ev.value.toPrecision(6)} <span className="text-slate-400 font-normal">{ev.unit}</span>
                  </td>
                  <td className="px-4 py-2 text-right font-mono">{(ev.tolerance_rel * 100).toFixed(2)}%</td>
                  <td className="px-4 py-2 text-slate-500 max-w-xs">{ev.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Input data */}
      {showInput && (
        <div className="border-t border-slate-100 bg-slate-50 px-5 py-3">
          <pre className="text-xs text-slate-600 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(b.input_data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function BenchmarkListPage() {
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    fetch(`${API_BASE}/verification/benchmarks?active_only=false`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => setBenchmarks(d.benchmarks ?? []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const structureTypes = Array.from(new Set(benchmarks.map((b) => b.structure_type)));

  const filtered = benchmarks.filter((b) => {
    const matchSearch = search === "" ||
      b.title.toLowerCase().includes(search.toLowerCase()) ||
      b.benchmark_id.toLowerCase().includes(search.toLowerCase()) ||
      b.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
    const matchType = filterType === "all" || b.structure_type === filterType;
    return matchSearch && matchType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/verification" className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-brand-600" />
            Benchmark Cases
          </h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Daftar kasus uji untuk verifikasi solver
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Cari benchmark..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
        >
          <option value="all">Semua Tipe</option>
          {structureTypes.map((t) => (
            <option key={t} value={t}>{TYPE_LABELS[t] ?? t}</option>
          ))}
        </select>
      </div>

      {/* Content */}
      {loading && (
        <div className="text-center py-16 text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
          <p>Memuat benchmark...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-sm text-red-700">
          Gagal memuat: {error}. Pastikan backend berjalan.
        </div>
      )}

      {!loading && !error && (
        <>
          <p className="text-sm text-slate-500">
            Menampilkan <strong>{filtered.length}</strong> dari {benchmarks.length} benchmark
          </p>
          <div className="space-y-4">
            {filtered.map((b) => <BenchmarkCard key={b.benchmark_id} b={b} />)}
          </div>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <CheckCircle className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p>Tidak ada benchmark yang cocok dengan filter ini.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// RefreshCw used in loading state but not imported above
function RefreshCw({ className }: { className?: string }) {
  return <FlaskConical className={className} />;
}
