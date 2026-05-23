/**
 * Full Report API client — AG-SAS
 * Endpoints: /api/v1/full-reports
 */
import api from "./api";

function getAuthToken(): string | null {
  return typeof window !== "undefined" ? localStorage.getItem("ag_sas_token") : null;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface EngineerInfo {
  name:     string;
  position: string;
  skk:      string;
}

export interface FullReport {
  id:               number;
  user_id:          number;
  calc_id:          number;
  doc_number:       string;
  revision:         string;
  status:           "DRAFT" | "FINAL";
  report_title:     string;
  report_subtitle:  string | null;
  project_name:     string | null;
  project_location: string | null;
  owner:            string | null;
  company_name:     string;
  engineers:        EngineerInfo[];
  include_figures:  boolean;
  show_watermark:   boolean;
  show_appendix:    boolean;
  deform_scale:     number;
  created_at:       string;
  generated_at:     string | null;
}

export interface CreateFullReportRequest {
  calc_id:          number;
  doc_number?:      string;
  revision?:        string;
  status?:          "DRAFT" | "FINAL";
  report_title?:    string;
  report_subtitle?: string;
  project_name?:    string;
  project_location?:string;
  owner?:           string;
  company_name?:    string;
  engineers?:       EngineerInfo[];
  include_figures?: boolean;
  show_watermark?:  boolean;
  show_appendix?:   boolean;
  deform_scale?:    number;
}

export type UpdateFullReportRequest = Partial<Omit<CreateFullReportRequest, "calc_id">>;

// ── API ────────────────────────────────────────────────────────────────────

export const fullReportApi = {
  create: (data: CreateFullReportRequest) =>
    api.post<FullReport>("/full-reports", data),

  list: (calc_id?: number) =>
    api.get<FullReport[]>("/full-reports", { params: calc_id ? { calc_id } : {} }),

  get: (id: number) =>
    api.get<FullReport>(`/full-reports/${id}`),

  update: (id: number, data: UpdateFullReportRequest) =>
    api.patch<FullReport>(`/full-reports/${id}`, data),

  delete: (id: number) =>
    api.delete(`/full-reports/${id}`),

  /** Download PDF — menggunakan fetch() + Bearer token agar auth header dikirim */
  async downloadPdf(report: FullReport): Promise<void> {
    const token = getAuthToken();
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/full-reports/${report.id}/pdf`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Gagal mengunduh PDF");
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `laporan_${report.doc_number.replace(/\//g, "-")}_Rev${report.revision}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
