"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Calculator, Layers, FileText, Clock, CheckCircle, XCircle, Download } from "lucide-react";
import { projectsApi, calcApi } from "@/lib/api";
import { formatDate, statusBg } from "@/lib/utils";
import type { Project, CalculationRecord } from "@/types";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [calculations, setCalculations] = useState<CalculationRecord[]>([]);

  useEffect(() => {
    projectsApi.get(+id).then(({ data }) => setProject(data)).catch(() => {});
    calcApi.getByProject(+id).then(({ data }) => setCalculations(data)).catch(() => {});
  }, [id]);

  if (!project) return <div className="text-slate-400 text-sm">Memuat...</div>;

  return (
    <div>
      <div className="flex items-center gap-3 mb-8">
        <Link href="/projects" className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-navy">
          <ChevronLeft className="w-4 h-4" /> Proyek
        </Link>
        <span className="text-slate-300">/</span>
        <span className="text-sm font-semibold text-navy">{project.name}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Project Info */}
        <div className="lg:col-span-1 space-y-4">
          <div className="engineering-card p-5">
            <h2 className="section-title">Data Proyek</h2>
            <dl className="space-y-2.5">
              {[
                ["Nama", project.name],
                ["Lokasi", project.location],
                ["Pemberi Tugas", project.client_name],
                ["Konsultan", project.consultant_name || "-"],
                ["Jenis Bangunan", project.building_type],
                ["Jumlah Lantai", `${project.num_floors} lantai`],
                ["Sistem Struktur", project.structural_system],
                ["Material Utama", project.primary_material],
                ["Dibuat", formatDate(project.created_at)],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between items-start gap-2">
                  <dt className="text-xs text-slate-400 flex-shrink-0">{k}</dt>
                  <dd className="text-xs font-medium text-slate-800 text-right">{v}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="engineering-card p-5">
            <h2 className="section-title">Standar Desain</h2>
            <div className="flex flex-wrap gap-1.5">
              {project.applicable_standards.split(",").map((s) => (
                <span key={s} className="text-xs bg-brand-50 text-brand-700 border border-brand-200 px-2 py-0.5 rounded">
                  {s.trim()}
                </span>
              ))}
            </div>
          </div>

          {/* Quick Calc Links */}
          <div className="engineering-card p-5">
            <h2 className="section-title">Perhitungan</h2>
            <div className="space-y-2">
              <Link href={`/concrete?project_id=${id}`}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-brand-50 border border-transparent hover:border-brand-200 transition-all group">
                <Calculator className="w-4 h-4 text-brand-600" />
                <span className="text-sm font-medium text-slate-700">Balok Beton</span>
              </Link>
              <Link href={`/steel?project_id=${id}`}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-brand-50 border border-transparent hover:border-brand-200 transition-all group">
                <Layers className="w-4 h-4 text-brand-600" />
                <span className="text-sm font-medium text-slate-700">Balok Baja WF</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Calculation History */}
        <div className="lg:col-span-2">
          <div className="engineering-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title mb-0 border-0 pb-0">Riwayat Perhitungan</h2>
              <span className="text-xs text-slate-400">{calculations.length} perhitungan</span>
            </div>

            {calculations.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Calculator className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Belum ada perhitungan untuk proyek ini</p>
              </div>
            ) : (
              <div className="space-y-3">
                {calculations.map((calc) => (
                  <div key={calc.id}
                    className="flex items-start justify-between p-4 rounded-lg border border-slate-200 hover:border-brand-300 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-md bg-slate-100 flex items-center justify-center mt-0.5">
                        {calc.calc_type === "concrete_beam" ? (
                          <Calculator className="w-4 h-4 text-slate-500" />
                        ) : (
                          <Layers className="w-4 h-4 text-slate-500" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{calc.title}</p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {calc.calc_type === "concrete_beam" ? "Balok Beton" : "Balok Baja"} ·
                          {" "}{formatDate(calc.created_at)}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5 font-mono">{calc.standard_references.split(",")[0]}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-full border font-semibold ${statusBg(calc.status)}`}>
                        {calc.status}
                      </span>
                      <button
                        onClick={() => calcApi.downloadPdf(calc.id, `AG-SAS_${calc.calc_type}_${calc.id}.pdf`)}
                        className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded transition-colors"
                        title="Download PDF"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
