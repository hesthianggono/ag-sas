"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Download, ExternalLink, Loader2,
  FileText, Calendar, User, Building2, Images,
} from "lucide-react";
import { reportsApi } from "@/lib/api";
import { figuresApi } from "@/lib/figuresApi";
import type { FigureSnapshot } from "@/lib/figuresApi";
import { formatDate, statusBg } from "@/lib/utils";
import type { ReportRecord } from "@/types";
import FigureManager from "@/components/report/FigureManager";

type Tab = "preview" | "figures";

export default function ReportPreviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const reportId = Number(id);

  const [report, setReport] = useState<ReportRecord | null>(null);
  const [figures, setFigures] = useState<FigureSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("preview");

  const handleDownload = useCallback(async () => {
    if (!report) return;
    setDownloading(true);
    try {
      const safe = report.title.replace(/[^a-zA-Z0-9_\-]/g, "_").slice(0, 40);
      await reportsApi.downloadPdf(reportId, `AG-SAS_${safe}_${reportId}.pdf`);
    } catch (e: any) {
      setError(`Gagal download PDF: ${e?.message ?? "coba lagi"}`);
    } finally {
      setDownloading(false);
    }
  }, [report, reportId]);

  useEffect(() => {
    Promise.all([
      reportsApi.get(reportId),
      figuresApi.listByReport(reportId).catch(() => ({ data: [] as FigureSnapshot[] })),
    ])
      .then(([rRes, fRes]) => {
        setReport(rRes.data);
        setFigures(fRes.data);
      })
      .catch(() => setError("Laporan tidak ditemukan atau akses ditolak."))
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        <span>Memuat laporan...</span>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="engineering-card p-12 text-center">
        <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
        <p className="text-slate-500 mb-4">{error || "Laporan tidak ditemukan."}</p>
        <button onClick={() => router.push("/report")} className="btn-primary text-sm">
          Kembali ke Laporan
        </button>
      </div>
    );
  }

  const status = (report.output_snapshot as Record<string, unknown>)?.status as string | undefined;
  const capacityRatio = (report.output_snapshot as Record<string, unknown>)?.capacity_ratio as number | undefined;
  const calcTypeLabel = report.calc_type === "concrete_beam" ? "Balok Beton Bertulang" : "Balok Baja WF";
  const previewUrl = reportsApi.previewUrl(reportId);

  return (
    <div>
      {/* ── Breadcrumb & Header ── */}
      <div className="mb-6">
        <button
          onClick={() => router.push("/report")}
          className="flex items-center gap-1.5 text-slate-400 hover:text-slate-700 text-sm mb-3 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Kembali ke Daftar Laporan
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-navy">{report.title}</h1>
            <p className="text-slate-500 text-sm mt-1">{calcTypeLabel} &nbsp;·&nbsp; {report.project_name}</p>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <a
              href={previewUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Buka di Tab Baru
            </a>
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white rounded-lg text-sm font-semibold transition-colors"
            >
              {downloading
                ? <><Loader2 className="w-4 h-4 animate-spin" />Proses...</>
                : <><Download className="w-4 h-4" />Download PDF</>}
            </button>
          </div>
        </div>
      </div>

      {/* ── Report Meta Cards ── */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetaCard icon={Building2} label="Proyek" value={report.project_name} />
        <MetaCard icon={Calendar} label="Tanggal Generate" value={formatDate(report.generated_at)} />
        <MetaCard icon={User} label="Dibuat Oleh" value={report.generated_by_name} />
        <MetaCard icon={FileText} label="Formula Version" value={report.formula_version} />
      </div>

      {/* ── Status & Capacity Ratio ── */}
      {status && (
        <div className={`mb-6 rounded-lg border-2 px-5 py-3 flex items-center gap-4 ${
          status === "AMAN"
            ? "bg-green-50 border-green-400"
            : "bg-red-50 border-red-400"
        }`}>
          <span className="text-2xl">{status === "AMAN" ? "✅" : "❌"}</span>
          <div>
            <p className={`font-bold text-base ${status === "AMAN" ? "text-green-700" : "text-red-700"}`}>
              ELEMEN {status}
            </p>
            {capacityRatio !== undefined && (
              <p className="text-sm text-slate-600">
                Rasio kapasitas Mu/φMn = <strong>{capacityRatio.toFixed(3)}</strong>
                {status === "AMAN" ? " ≤ 1.0 → OK" : " > 1.0 → Perlu redesign"}
              </p>
            )}
          </div>
          <div className={`ml-auto text-center px-4 py-2 rounded-md text-white font-bold ${
            status === "AMAN" ? "bg-green-600" : "bg-red-600"
          }`}>
            <div className="text-lg">{capacityRatio?.toFixed(2) ?? "—"}</div>
            <div className="text-xs opacity-80">Mu/φMn</div>
          </div>
        </div>
      )}

      {/* ── Tabs ── */}
      <div className="flex gap-1 mb-4 border-b border-slate-200">
        {([
          { key: "preview", label: "Preview Laporan", icon: FileText },
          { key: "figures", label: `Gambar Teknik (${figures.length})`, icon: Images },
        ] as { key: Tab; label: string; icon: React.ElementType }[]).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === key
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* ── Tab: Preview ── */}
      {activeTab === "preview" && (
        <div className="engineering-card overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <FileText className="w-4 h-4 text-navy" />
              Preview Laporan HTML
            </span>
            <span className="text-xs text-slate-400">
              Laporan PDF mencakup gambar teknik dari tab Gambar Teknik
            </span>
          </div>
          <PreviewFrame reportId={reportId} />
        </div>
      )}

      {/* ── Tab: Figures ── */}
      {activeTab === "figures" && (
        <FigureManager
          reportId={reportId}
          calcId={report?.calc_id ?? 0}
          figures={figures}
          onFiguresChange={setFigures}
        />
      )}

      {/* ── Action buttons ── */}
      <div className="mt-6 flex gap-3">
        <button
          onClick={handleDownload}
          disabled={downloading}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white rounded-lg text-sm font-semibold transition-colors"
        >
          {downloading
            ? <><Loader2 className="w-4 h-4 animate-spin" />Proses...</>
            : <><Download className="w-4 h-4" />Download PDF</>}
        </button>
        <button
          onClick={() => router.push("/report")}
          className="inline-flex items-center gap-2 px-5 py-2.5 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Kembali
        </button>
      </div>

      {/* ── Disclaimer ── */}
      <div className="mt-5 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-xs text-amber-700 font-medium">
          ⚠ Laporan ini dibuat otomatis dan bersifat indikatif.
          Wajib diperiksa oleh Engineer Struktur berwenang sebelum digunakan dalam dokumen resmi.
        </p>
      </div>
    </div>
  );
}

function MetaCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="engineering-card p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-slate-400" />
        <span className="text-xs text-slate-400 font-medium">{label}</span>
      </div>
      <p className="text-sm font-semibold text-slate-800 truncate">{value}</p>
    </div>
  );
}

function PreviewFrame({ reportId }: { reportId: number }) {
  const [srcDoc, setSrcDoc] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(false);

  useEffect(() => {
    // Fetch HTML content via API (which handles auth) and render in srcdoc
    import("@/lib/api").then(({ api }) => {
      api.get(`/reports/${reportId}/preview`, {
        headers: { Accept: "text/html" },
        responseType: "text",
      })
        .then((res) => setSrcDoc(res.data as string))
        .catch(() => setErr(true))
        .finally(() => setLoading(false));
    });
  }, [reportId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Memuat preview...
      </div>
    );
  }

  if (err || !srcDoc) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <p className="text-sm">Preview tidak tersedia.</p>
      </div>
    );
  }

  return (
    <iframe
      srcDoc={srcDoc}
      className="w-full"
      style={{ height: "900px", border: "none" }}
      title="Report Preview"
    />
  );
}
