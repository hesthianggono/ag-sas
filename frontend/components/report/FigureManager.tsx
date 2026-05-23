"use client";
import { useState, useCallback } from "react";
import {
  Images, RefreshCw, Download, Loader2, CheckCircle2,
  AlertTriangle, Plus, Eye, EyeOff, SlidersHorizontal,
} from "lucide-react";
import FigureCard from "./FigureCard";
import type { FigureSnapshot } from "@/lib/figuresApi";
import { figuresApi, downloadFigureAsPng } from "@/lib/figuresApi";

interface FigureManagerProps {
  reportId: number;
  calcId: number;
  figures: FigureSnapshot[];
  onFiguresChange: (figures: FigureSnapshot[]) => void;
}

interface EditCaptionModal {
  figure: FigureSnapshot;
  draft: string;
  draftTitle: string;
}

export default function FigureManager({
  reportId,
  calcId,
  figures,
  onFiguresChange,
}: FigureManagerProps) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editModal, setEditModal] = useState<EditCaptionModal | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [deformScale, setDeformScale] = useState(50);
  const [showSettings, setShowSettings] = useState(false);

  // ── Generate backend figures ──────────────────────────────────────────────
  async function handleGenerate(overwrite = false) {
    setGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      const { data } = await figuresApi.generate({
        report_id: reportId,
        section: "12",
        deform_scale: deformScale,
        overwrite,
      });
      onFiguresChange(data);
      setSuccess(`${data.length} gambar berhasil di-generate.`);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e?.message ?? "Gagal generate gambar.");
    } finally {
      setGenerating(false);
    }
  }

  // ── Toggle visibility ─────────────────────────────────────────────────────
  async function handleToggleVisible(id: number, visible: boolean) {
    try {
      const { data } = await figuresApi.update(id, { is_visible: visible });
      onFiguresChange(figures.map((f) => (f.id === id ? data : f)));
    } catch {
      setError("Gagal update visibility.");
    }
  }

  // ── Open edit caption modal ───────────────────────────────────────────────
  function handleEditCaption(figure: FigureSnapshot) {
    setEditModal({ figure, draft: figure.caption, draftTitle: figure.title });
  }

  async function handleSaveCaption() {
    if (!editModal) return;
    setSavingEdit(true);
    try {
      const { data } = await figuresApi.update(editModal.figure.id, {
        caption: editModal.draft,
        title: editModal.draftTitle,
      });
      onFiguresChange(figures.map((f) => (f.id === data.id ? data : f)));
      setEditModal(null);
    } catch {
      setError("Gagal menyimpan caption.");
    } finally {
      setSavingEdit(false);
    }
  }

  // ── Delete figure ─────────────────────────────────────────────────────────
  async function handleDelete(id: number) {
    if (!confirm("Hapus gambar ini dari laporan?")) return;
    try {
      await figuresApi.delete(id);
      onFiguresChange(figures.filter((f) => f.id !== id));
    } catch {
      setError("Gagal menghapus gambar.");
    }
  }

  // ── Download all visible figures ──────────────────────────────────────────
  function handleDownloadAll() {
    const visible = figures.filter((f) => f.is_visible);
    visible.forEach((f, i) => {
      setTimeout(() => downloadFigureAsPng(f), i * 300);
    });
  }

  // ── Show all / hide all ───────────────────────────────────────────────────
  async function handleSetAllVisibility(visible: boolean) {
    for (const f of figures) {
      if (f.is_visible !== visible) {
        await figuresApi.update(f.id, { is_visible: visible });
      }
    }
    const { data } = await figuresApi.listByReport(reportId);
    onFiguresChange(data);
  }

  const visibleCount = figures.filter((f) => f.is_visible).length;

  return (
    <div>
      {/* ── Toolbar ── */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex items-center gap-2">
          <Images className="w-5 h-5 text-navy" />
          <span className="font-bold text-navy text-sm">
            {figures.length} gambar
            {visibleCount < figures.length && (
              <span className="text-slate-400 font-normal ml-1">
                ({visibleCount} ditampilkan)
              </span>
            )}
          </span>
        </div>

        <div className="flex gap-2 ml-auto">
          {/* Settings toggle */}
          <button
            onClick={() => setShowSettings((s) => !s)}
            className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-navy px-2.5 py-1.5 rounded border border-slate-200 hover:border-slate-300 transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Opsi
          </button>

          {figures.length > 0 && (
            <>
              <button
                onClick={() => handleSetAllVisibility(true)}
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-navy px-2.5 py-1.5 rounded border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <Eye className="w-3.5 h-3.5" />
                Tampilkan Semua
              </button>
              <button
                onClick={() => handleSetAllVisibility(false)}
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-navy px-2.5 py-1.5 rounded border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <EyeOff className="w-3.5 h-3.5" />
                Sembunyikan Semua
              </button>
              <button
                onClick={handleDownloadAll}
                className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-navy px-2.5 py-1.5 rounded border border-slate-200 hover:border-slate-300 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Unduh Semua
              </button>
            </>
          )}

          {figures.length > 0 ? (
            <button
              onClick={() => handleGenerate(true)}
              disabled={generating}
              className="inline-flex items-center gap-1.5 text-xs bg-slate-600 hover:bg-slate-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-md font-semibold transition-colors"
            >
              {generating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              Generate Ulang
            </button>
          ) : (
            <button
              onClick={() => handleGenerate(false)}
              disabled={generating}
              className="inline-flex items-center gap-1.5 text-xs bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-md font-semibold transition-colors"
            >
              {generating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Plus className="w-3.5 h-3.5" />
              )}
              Generate Gambar
            </button>
          )}
        </div>
      </div>

      {/* ── Settings panel ── */}
      {showSettings && (
        <div className="mb-4 p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm">
          <div className="flex items-center gap-4 flex-wrap">
            <label className="flex items-center gap-2 text-slate-700 font-medium">
              Faktor Skala Deformasi:
              <input
                type="number"
                min={10}
                max={500}
                step={10}
                value={deformScale}
                onChange={(e) => setDeformScale(+e.target.value)}
                className="engineering-input w-20 text-center py-1"
              />
              <span className="text-slate-400">×</span>
            </label>
            <p className="text-xs text-slate-400 italic">
              Faktor perbesaran visual untuk gambar deformasi (bukan nilai nyata).
            </p>
          </div>
        </div>
      )}

      {/* ── Alerts ── */}
      {error && (
        <div className="mb-4 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">✕</button>
        </div>
      )}
      {success && (
        <div className="mb-4 flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          {success}
          <button onClick={() => setSuccess(null)} className="ml-auto text-green-400 hover:text-green-600">✕</button>
        </div>
      )}

      {/* ── Loading state ── */}
      {generating && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400">
          <Loader2 className="w-10 h-10 animate-spin mb-3 text-brand-500" />
          <p className="text-sm font-medium">Membuat gambar teknik…</p>
          <p className="text-xs mt-1">Model view · Load diagram · V/M diagrams · Deformed shape · Utilization</p>
        </div>
      )}

      {/* ── Empty state ── */}
      {!generating && figures.length === 0 && (
        <div className="engineering-card p-16 text-center text-slate-400">
          <Images className="w-14 h-14 mx-auto mb-4 opacity-25" />
          <p className="text-sm font-semibold text-slate-500 mb-1">Belum ada gambar teknik</p>
          <p className="text-xs mb-5">
            Klik <strong>Generate Gambar</strong> untuk membuat diagram otomatis dari data perhitungan.
          </p>
          <button
            onClick={() => handleGenerate(false)}
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Generate Gambar Teknik
          </button>
        </div>
      )}

      {/* ── Figure grid ── */}
      {!generating && figures.length > 0 && (
        <>
          {/* Figure list of contents mini-table */}
          <div className="mb-5 p-3 bg-navy/5 border border-navy/10 rounded-lg">
            <p className="text-xs font-bold text-navy mb-2">Daftar Gambar</p>
            <div className="grid grid-cols-1 gap-0.5">
              {figures
                .slice()
                .sort((a, b) => a.order_index - b.order_index)
                .map((f) => (
                  <div key={f.id} className="flex items-center gap-2 text-xs">
                    <span className="font-mono text-brand-600 min-w-[2.5rem]">
                      Gambar {f.figure_number}
                    </span>
                    <span className={`flex-1 ${!f.is_visible ? "line-through text-slate-400" : "text-slate-700"}`}>
                      {f.caption.replace(`Gambar ${f.figure_number}  `, "")}
                    </span>
                    {!f.is_visible && (
                      <EyeOff className="w-3 h-3 text-slate-400 flex-shrink-0" />
                    )}
                  </div>
                ))}
            </div>
          </div>

          {/* Grid 2 per baris */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {figures
              .slice()
              .sort((a, b) => a.order_index - b.order_index)
              .map((figure, idx) => (
                <FigureCard
                  key={figure.id}
                  figure={figure}
                  index={idx}
                  onToggleVisible={handleToggleVisible}
                  onEditCaption={handleEditCaption}
                  onDelete={handleDelete}
                />
              ))}
          </div>
        </>
      )}

      {/* ── Edit Caption Modal ── */}
      {editModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6">
            <h2 className="text-base font-bold text-navy mb-4">Edit Caption Gambar</h2>
            <div className="space-y-4">
              <div>
                <label className="engineering-label">Judul Gambar</label>
                <input
                  className="engineering-input"
                  value={editModal.draftTitle}
                  onChange={(e) =>
                    setEditModal({ ...editModal, draftTitle: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="engineering-label">Caption Lengkap</label>
                <textarea
                  className="engineering-input h-24 resize-none"
                  value={editModal.draft}
                  onChange={(e) =>
                    setEditModal({ ...editModal, draft: e.target.value })
                  }
                />
                <p className="text-xs text-slate-400 mt-1">
                  Contoh: "Gambar 12.3  Diagram momen lentur kombinasi 1.2D + 1.6L"
                </p>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={handleSaveCaption}
                disabled={savingEdit}
                className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {savingEdit && <Loader2 className="w-4 h-4 animate-spin" />}
                Simpan
              </button>
              <button
                onClick={() => setEditModal(null)}
                className="flex-1 border border-slate-300 text-slate-700 text-sm font-medium py-2.5 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Batal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Info box ── */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-xs text-blue-700 font-medium">
          ℹ Gambar yang di-generate disimpan sebagai snapshot immutable bersama laporan ini.
          Jika data model diubah setelah laporan dibuat, gambar lama tetap tersimpan sesuai kondisi saat itu.
          Gunakan <strong>Generate Ulang</strong> untuk memperbarui semua gambar.
        </p>
      </div>
    </div>
  );
}
