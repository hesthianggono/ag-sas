"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Images, ArrowLeft, FileText, Loader2, AlertTriangle } from "lucide-react";
import { reportsApi } from "@/lib/api";
import { figuresApi } from "@/lib/figuresApi";
import type { FigureSnapshot } from "@/lib/figuresApi";
import type { ReportRecord } from "@/types";
import FigureManager from "@/components/report/FigureManager";

export default function ReportFiguresPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reportId = searchParams ? Number(searchParams.get("report_id")) : 0;

  const [report, setReport] = useState<ReportRecord | null>(null);
  const [figures, setFigures] = useState<FigureSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) {
      setError("report_id tidak ditemukan di URL.");
      setLoading(false);
      return;
    }
    Promise.all([
      reportsApi.get(reportId),
      figuresApi.listByReport(reportId),
    ])
      .then(([rRes, fRes]) => {
        setReport(rRes.data);
        setFigures(fRes.data);
      })
      .catch(() => setError("Gagal memuat data laporan."))
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin mr-3" />
        <span>Memuat gambar teknik…</span>
      </div>
    );
  }

  if (error || !reportId) {
    return (
      <div className="engineering-card p-8 text-center text-red-600">
        <AlertTriangle className="w-10 h-10 mx-auto mb-3" />
        <p>{error || "Parameter report_id diperlukan."}</p>
        <button
          onClick={() => router.push("/report")}
          className="mt-4 text-sm text-brand-600 hover:underline"
        >
          ← Kembali ke daftar laporan
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* ── Header ── */}
      <div className="mb-8">
        <button
          onClick={() => router.push(`/report/${reportId}`)}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-navy mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Kembali ke laporan
        </button>
        <h1 className="text-2xl font-bold text-navy flex items-center gap-3">
          <Images className="w-6 h-6" />
          Manajer Gambar Teknik
        </h1>
        {report && (
          <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
            <FileText className="w-4 h-4" />
            <span>{report.title}</span>
            <span className="text-slate-300">·</span>
            <span>{report.project_name}</span>
          </div>
        )}
        <p className="text-slate-400 text-xs mt-1">
          Generate, preview, edit caption, dan kelola visibilitas gambar untuk laporan PDF ini.
        </p>
      </div>

      {/* ── Figure Manager ── */}
      <FigureManager
        reportId={reportId}
        calcId={report?.calc_id ?? 0}
        figures={figures}
        onFiguresChange={setFigures}
      />
    </div>
  );
}
