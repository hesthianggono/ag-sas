"use client";

import { useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  FileText, Download, Loader2, Plus, Trash2,
  ChevronDown, ChevronUp, Settings,
} from "lucide-react";
import {
  fullReportApi,
  CreateFullReportRequest,
  FullReport,
  EngineerInfo,
} from "@/lib/fullReportApi";

// ── Schema ─────────────────────────────────────────────────────────────────
const engineerSchema = z.object({
  name:     z.string().min(1, "Nama wajib diisi"),
  position: z.string().default(""),
  skk:      z.string().default(""),
});

const formSchema = z.object({
  doc_number:       z.string().min(1),
  revision:         z.string().min(1),
  status:           z.enum(["DRAFT", "FINAL"]),
  report_title:     z.string().min(1),
  report_subtitle:  z.string().default(""),
  project_name:     z.string().default(""),
  project_location: z.string().default(""),
  owner:            z.string().default(""),
  company_name:     z.string().min(1),
  engineers:        z.array(engineerSchema).default([]),
  include_figures:  z.boolean().default(true),
  show_watermark:   z.boolean().default(true),
  show_appendix:    z.boolean().default(true),
  deform_scale:     z.number().min(1).max(500).default(50),
});

type FormValues = z.infer<typeof formSchema>;

// ── Props ──────────────────────────────────────────────────────────────────
interface Props {
  calcId: number;
  existingReport?: FullReport | null;
  onSaved?: (report: FullReport) => void;
}

// ── Component ──────────────────────────────────────────────────────────────
export default function FullReportSettings({ calcId, existingReport, onSaved }: Props) {
  const [saving,     setSaving]     = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error,      setError]      = useState<string | null>(null);
  const [success,    setSuccess]    = useState<string | null>(null);
  const [showEng,    setShowEng]    = useState(false);
  const [showAdv,    setShowAdv]    = useState(false);

  const {
    register, handleSubmit, control, watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: existingReport
      ? {
          doc_number:       existingReport.doc_number,
          revision:         existingReport.revision,
          status:           existingReport.status,
          report_title:     existingReport.report_title,
          report_subtitle:  existingReport.report_subtitle || "",
          project_name:     existingReport.project_name || "",
          project_location: existingReport.project_location || "",
          owner:            existingReport.owner || "",
          company_name:     existingReport.company_name,
          engineers:        existingReport.engineers,
          include_figures:  existingReport.include_figures,
          show_watermark:   existingReport.show_watermark,
          show_appendix:    existingReport.show_appendix,
          deform_scale:     existingReport.deform_scale,
        }
      : {
          doc_number:    "AG-SAS/RPT/001",
          revision:      "A",
          status:        "DRAFT",
          report_title:  "Laporan Perhitungan Struktur",
          company_name:  "AG Structural Analysis Suite",
          include_figures: true,
          show_watermark:  true,
          show_appendix:   true,
          deform_scale:    50,
          engineers:       [],
        },
  });

  const { fields: engFields, append: addEng, remove: removeEng } =
    useFieldArray({ control, name: "engineers" });

  // ── Save (create or update) ──────────────────────────────────────────
  const onSubmit = async (values: FormValues) => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      let saved: FullReport;
      if (existingReport) {
        const res = await fullReportApi.update(existingReport.id, values);
        saved = res.data;
      } else {
        const req: CreateFullReportRequest = { calc_id: calcId, ...values };
        const res = await fullReportApi.create(req);
        saved = res.data;
      }
      setSuccess("Pengaturan laporan berhasil disimpan.");
      onSaved?.(saved);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Gagal menyimpan laporan.");
    } finally {
      setSaving(false);
    }
  };

  // ── Download PDF ──────────────────────────────────────────────────────
  const handleDownload = async () => {
    if (!existingReport) {
      setError("Simpan pengaturan terlebih dahulu sebelum download PDF.");
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      await fullReportApi.downloadPdf(existingReport);
      setSuccess("PDF berhasil diunduh.");
    } catch (e: any) {
      setError(e.message || "Gagal mengunduh PDF.");
    } finally {
      setGenerating(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            Laporan Rekayasa Lengkap
          </h2>
        </div>
        <button
          onClick={handleDownload}
          disabled={!existingReport || generating}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        >
          {generating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {generating ? "Generating PDF..." : "Download PDF"}
        </button>
      </div>

      {/* Alerts */}
      {error   && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}
      {success && <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">{success}</div>}

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

        {/* Identitas Dokumen */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <h3 className="font-medium text-gray-800">Identitas Dokumen</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Field label="Nomor Dokumen" error={errors.doc_number?.message}>
              <input {...register("doc_number")} className={inputCls} />
            </Field>
            <Field label="Revisi" error={errors.revision?.message}>
              <input {...register("revision")} className={inputCls} />
            </Field>
            <Field label="Status">
              <select {...register("status")} className={inputCls}>
                <option value="DRAFT">DRAFT</option>
                <option value="FINAL">FINAL</option>
              </select>
            </Field>
          </div>
        </div>

        {/* Judul & Proyek */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <h3 className="font-medium text-gray-800">Judul &amp; Proyek</h3>
          <div className="grid grid-cols-1 gap-4">
            <Field label="Judul Laporan" error={errors.report_title?.message}>
              <input {...register("report_title")} className={inputCls} />
            </Field>
            <Field label="Sub-Judul (opsional)">
              <input {...register("report_subtitle")} className={inputCls} />
            </Field>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Nama Proyek">
                <input {...register("project_name")} className={inputCls} />
              </Field>
              <Field label="Lokasi Proyek">
                <input {...register("project_location")} className={inputCls} />
              </Field>
              <Field label="Pemilik Proyek">
                <input {...register("owner")} className={inputCls} />
              </Field>
              <Field label="Nama Perusahaan">
                <input {...register("company_name")} className={inputCls} />
              </Field>
            </div>
          </div>
        </div>

        {/* Engineer */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <button
            type="button"
            onClick={() => setShowEng(!showEng)}
            className="w-full flex items-center justify-between text-left"
          >
            <h3 className="font-medium text-gray-800">Tim Perencana (opsional)</h3>
            {showEng ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showEng && (
            <div className="mt-4 space-y-3">
              {engFields.map((field, idx) => (
                <div key={field.id} className="grid grid-cols-3 gap-3 items-end">
                  <Field label="Nama">
                    <input {...register(`engineers.${idx}.name`)} className={inputCls} />
                  </Field>
                  <Field label="Jabatan">
                    <input {...register(`engineers.${idx}.position`)} className={inputCls} />
                  </Field>
                  <div className="flex gap-2 items-end">
                    <Field label="No. SKK" className="flex-1">
                      <input {...register(`engineers.${idx}.skk`)} className={inputCls} />
                    </Field>
                    <button
                      type="button"
                      onClick={() => removeEng(idx)}
                      className="mb-0.5 p-2 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
              <button
                type="button"
                onClick={() => addEng({ name: "", position: "", skk: "" })}
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
              >
                <Plus className="h-4 w-4" /> Tambah Engineer
              </button>
            </div>
          )}
        </div>

        {/* Advanced */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <button
            type="button"
            onClick={() => setShowAdv(!showAdv)}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-2">
              <Settings className="h-4 w-4 text-gray-500" />
              <h3 className="font-medium text-gray-800">Pengaturan Lanjutan</h3>
            </div>
            {showAdv ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showAdv && (
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <CheckboxField
                label="Sertakan Gambar"
                {...register("include_figures")}
              />
              <CheckboxField
                label="Watermark DRAFT"
                {...register("show_watermark")}
              />
              <CheckboxField
                label="Tampilkan Lampiran"
                {...register("show_appendix")}
              />
              <Field label="Faktor Skala Deformasi">
                <input
                  type="number"
                  {...register("deform_scale", { valueAsNumber: true })}
                  className={inputCls}
                  min={1}
                  max={500}
                />
              </Field>
            </div>
          )}
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 bg-gray-900 text-white rounded-lg
                       hover:bg-gray-800 disabled:opacity-50 text-sm font-medium"
          >
            {saving && <Loader2 className="h-4 w-4 animate-spin" />}
            {existingReport ? "Perbarui Pengaturan" : "Simpan &amp; Buat Laporan"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────
const inputCls =
  "w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

function Field({
  label, error, children, className,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  );
}

function CheckboxField({
  label, ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
      <input type="checkbox" className="w-4 h-4 rounded border-gray-300" {...props} />
      {label}
    </label>
  );
}
