"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText } from "lucide-react";
import { fullReportApi, FullReport } from "@/lib/fullReportApi";
import FullReportSettings from "@/components/report/FullReportSettings";

export default function FullReportPage() {
  const params   = useSearchParams();
  const router   = useRouter();
  const calcId   = Number(params.get("calc_id"));
  const reportId = params.get("report_id") ? Number(params.get("report_id")) : null;

  const [report, setReport] = useState<FullReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    if (!calcId) {
      setError("Parameter calc_id diperlukan.");
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        if (reportId) {
          const res = await fullReportApi.get(reportId);
          setReport(res.data);
        } else {
          // Coba cari laporan yang sudah ada untuk calc ini
          const res = await fullReportApi.list(calcId);
          if (res.data.length > 0) setReport(res.data[0]);
        }
      } catch {
        // Tidak ada laporan → form kosong
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [calcId, reportId]);

  if (!calcId) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Parameter <code>calc_id</code> diperlukan.</p>
        <p className="text-sm mt-1">
          Akses halaman ini dari: <code>/report/full?calc_id=&#123;id&#125;</code>
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => router.back()}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">
              Laporan Rekayasa Lengkap
            </h1>
          </div>
          <p className="text-sm text-gray-500 mt-0.5">
            Isi pengaturan laporan, lalu klik <strong>Download PDF</strong> untuk mengunduh.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      <FullReportSettings
        calcId={calcId}
        existingReport={report}
        onSaved={(saved) => {
          setReport(saved);
          // Update URL agar reload tetap ada report_id
          router.replace(`/report/full?calc_id=${calcId}&report_id=${saved.id}`);
        }}
      />
    </div>
  );
}
