"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText, Download, Eye, Filter, RefreshCw,
  CheckCircle2, XCircle, Loader2, BookOpen,
} from "lucide-react";
import { projectsApi, calcApi, reportsApi } from "@/lib/api";
import { formatDate, statusBg } from "@/lib/utils";
import type { Project, CalculationRecord, ReportRecord } from "@/types";

type Tab = "calculations" | "reports";

interface EngineerModal {
  calcId: number;
  name: string;
  position: string;
  skk: string;
}

export default function ReportPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("calculations");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<number>(0);
  const [calculations, setCalculations] = useState<CalculationRecord[]>([]);
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [generating, setGenerating] = useState<Set<number>>(new Set());
  const [downloading, setDownloading] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  // Modal state untuk engineer data
  const [engineerModal, setEngineerModal] = useState<EngineerModal | null>(null);

  useEffect(() => {
    projectsApi.list().then(({ data }) => {
      setProjects(data);
      if (data.length > 0) setSelectedProject(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    calcApi.getByProject(selectedProject)
      .then(({ data }) => setCalculations(data))
      .catch(() => {});
    reportsApi.list(selectedProject)
      .then(({ data }) => setReports(data))
      .catch(() => {});
  }, [selectedProject]);

  async function handleDownload(reportId: number, title: string) {
    setDownloading((prev) => new Set(prev).add(reportId));
    setError(null);
    try {
      const safe = title.replace(/[^a-zA-Z0-9_\-]/g, "_").slice(0, 40);
      await reportsApi.downloadPdf(reportId, `AG-SAS_${safe}_${reportId}.pdf`);
    } catch (e: any) {
      setError(`Gagal download: ${e?.message ?? "coba lagi"}`);
    } finally {
      setDownloading((prev) => {
        const next = new Set(prev);
        next.delete(reportId);
        return next;
      });
    }
  }

  // Buka modal engineer sebelum generate
  function openEngineerModal(calcId: number) {
    setEngineerModal({ calcId, name: "", position: "", skk: "" });
  }

  async function handleGenerate() {
    if (!engineerModal) return;
    const { calcId, name, position, skk } = engineerModal;
    setEngineerModal(null);
    setError(null);
    setGenerating((prev) => new Set(prev).add(calcId));
    try {
      const { data } = await reportsApi.generate(calcId, name || undefined, position || undefined, skk || undefined);
      setReports((prev) => [data, ...prev]);
      setTab("reports");
      router.push(`/report/${data.id}`);
    } catch {
      setError("Gagal membuat laporan. Coba lagi.");
    } finally {
      setGenerating((prev) => {
        const next = new Set(prev);
        next.delete(calcId);
        return next;
      });
    }
  }

  const calcTypeLabel = (t: string) =>
    t === "concrete_beam" ? "Balok Beton" : "Balok Baja";

  return (
    <div>
      {/* ── Header ── */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy flex items-center gap-3">
          <FileText className="w-6 h-6" />
          Laporan Perhitungan
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Generate, preview, dan download laporan PDF perhitungan struktur
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* ── Project Filter ── */}
      <div className="engineering-card p-4 mb-6 flex items-center gap-4">
        <Filter className="w-4 h-4 text-slate-400 flex-shrink-0" />
        <select
          className="engineering-input max-w-xs"
          value={selectedProject}
          onChange={(e) => setSelectedProject(+e.target.value)}
        >
          <option value={0} disabled>Pilih proyek...</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <span className="text-sm text-slate-400 ml-2">
          {calculations.length} perhitungan &nbsp;·&nbsp; {reports.length} laporan tersimpan
        </span>
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 mb-4 border-b border-slate-200">
        {(["calculations", "reports"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t === "calculations" ? (
              <span className="flex items-center gap-2"><BookOpen className="w-3.5 h-3.5" />Perhitungan ({calculations.length})</span>
            ) : (
              <span className="flex items-center gap-2"><FileText className="w-3.5 h-3.5" />Laporan Tersimpan ({reports.length})</span>
            )}
          </button>
        ))}
      </div>

      {/* ── TAB: Calculations ── */}
      {tab === "calculations" && (
        <>
          {calculations.length === 0 ? (
            <EmptyState text="Tidak ada perhitungan untuk proyek ini" />
          ) : (
            <div className="engineering-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-navy text-white text-xs">
                  <tr>
                    {["#", "Judul", "Tipe", "Tanggal", "Status", "Aksi"].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {calculations.map((c, i) => {
                    const isGenerating = generating.has(c.id);
                    return (
                      <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 text-slate-400 font-mono text-xs">{i + 1}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{c.title}</td>
                        <td className="px-4 py-3 text-slate-500">{calcTypeLabel(c.calc_type)}</td>
                        <td className="px-4 py-3 text-slate-400 text-xs">{formatDate(c.created_at)}</td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-1 rounded-full border font-semibold ${statusBg(c.status)}`}>
                            {c.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => openEngineerModal(c.id)}
                            disabled={isGenerating}
                            className="inline-flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-md transition-colors"
                          >
                            {isGenerating ? (
                              <><Loader2 className="w-3 h-3 animate-spin" />Membuat...</>
                            ) : (
                              <><FileText className="w-3 h-3" />Buat Laporan</>
                            )}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* ── TAB: Saved Reports ── */}
      {tab === "reports" && (
        <>
          {reports.length === 0 ? (
            <EmptyState text="Belum ada laporan tersimpan. Klik 'Buat Laporan' di tab Perhitungan." />
          ) : (
            <div className="engineering-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-navy text-white text-xs">
                  <tr>
                    {["#", "Judul Laporan", "Tipe", "Tanggal Generate", "Dibuat Oleh", "Aksi"].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {reports.map((r, i) => {
                    const status = (r.output_snapshot as Record<string, unknown>)?.status as string | undefined;
                    return (
                      <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 text-slate-400 font-mono text-xs">{i + 1}</td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-slate-900">{r.title}</div>
                          <div className="text-xs text-slate-400">{r.project_name}</div>
                        </td>
                        <td className="px-4 py-3 text-slate-500">{calcTypeLabel(r.calc_type)}</td>
                        <td className="px-4 py-3 text-slate-400 text-xs">{formatDate(r.generated_at)}</td>
                        <td className="px-4 py-3 text-slate-500 text-xs">{r.generated_by_name}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => router.push(`/report/${r.id}`)}
                              className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-medium"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              Preview
                            </button>
                            <span className="text-slate-300">|</span>
                            <button
                              onClick={() => handleDownload(r.id, r.title)}
                              disabled={downloading.has(r.id)}
                              className="inline-flex items-center gap-1 text-brand-600 hover:text-brand-800 disabled:opacity-50 text-xs font-medium"
                            >
                              {downloading.has(r.id)
                                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Proses...</>
                                : <><Download className="w-3.5 h-3.5" />PDF</>}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* ── Disclaimer ── */}
      <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-xs text-amber-700 font-medium">
          ⚠ Semua laporan dibuat otomatis dan bersifat indikatif.
          Wajib diperiksa oleh Engineer Struktur berwenang sebelum digunakan dalam dokumen resmi.
        </p>
      </div>

      {/* ── Modal: Data Engineer ── */}
      {engineerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <h2 className="text-base font-bold text-navy mb-1">Data Engineer Pemeriksa</h2>
            <p className="text-xs text-slate-500 mb-5">
              Opsional — data ini akan muncul di tabel persetujuan laporan PDF.
              Kosongkan jika belum ditentukan.
            </p>
            <div className="space-y-4">
              <div>
                <label className="engineering-label">Nama Engineer</label>
                <input
                  className="engineering-input"
                  placeholder="contoh: Ir. H. Budi Santoso, M.T."
                  value={engineerModal.name}
                  onChange={(e) => setEngineerModal({ ...engineerModal, name: e.target.value })}
                />
              </div>
              <div>
                <label className="engineering-label">Jabatan / Keahlian</label>
                <input
                  className="engineering-input"
                  placeholder="contoh: Ahli Madya Teknik Struktur Bangunan Gedung"
                  value={engineerModal.position}
                  onChange={(e) => setEngineerModal({ ...engineerModal, position: e.target.value })}
                />
              </div>
              <div>
                <label className="engineering-label">Nomor SKK (Sertifikat Kompetensi Kerja)</label>
                <input
                  className="engineering-input"
                  placeholder="contoh: 6.1.23.1.7.2.00001"
                  value={engineerModal.skk}
                  onChange={(e) => setEngineerModal({ ...engineerModal, skk: e.target.value })}
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={handleGenerate}
                className="flex-1 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <FileText className="w-4 h-4" />
                Buat Laporan
              </button>
              <button
                onClick={() => setEngineerModal(null)}
                className="flex-1 border border-slate-300 text-slate-700 text-sm font-medium py-2.5 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Batal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="engineering-card p-16 text-center text-slate-400">
      <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p className="text-sm">{text}</p>
    </div>
  );
}
