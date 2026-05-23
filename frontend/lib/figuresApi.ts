/**
 * Figures API — AG-SAS
 * =====================
 * Client API untuk manajemen gambar teknik laporan.
 */
import { api } from "./api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FigureSnapshot {
  id: number;
  report_id: number;
  calc_id: number;
  figure_key: string;       // "model_view", "moment_diagram", …
  figure_number: string;    // "4.1", "4.2", …
  order_index: number;
  title: string;
  caption: string;
  load_case: string | null;
  load_combination: string | null;
  scale_factor: number | null;
  unit: string;
  source: "backend" | "frontend";
  is_visible: boolean;
  generated_at: string;
  json_data: Record<string, unknown> | null;
  png_base64: string;       // PNG encoded as base64
}

export interface GenerateFiguresRequest {
  report_id: number;
  section?: string;           // default "4"
  deform_scale?: number;      // default 50
  overwrite?: boolean;        // default false
}

export interface FigureUpdateRequest {
  caption?: string;
  title?: string;
  is_visible?: boolean;
  order_index?: number;
}

export interface FigureUploadRequest {
  report_id: number;
  calc_id: number;
  figure_key: string;
  title: string;
  caption: string;
  load_case?: string;
  load_combination?: string;
  scale_factor?: number;
  unit?: string;
  png_base64: string;
  json_data?: Record<string, unknown>;
}

// ── API ───────────────────────────────────────────────────────────────────────

export const figuresApi = {
  /** Generate semua gambar backend untuk satu laporan. */
  generate: (data: GenerateFiguresRequest) =>
    api.post<FigureSnapshot[]>("/figures/generate", data),

  /** Upload gambar dari frontend (canvas/Three.js snapshot). */
  upload: (data: FigureUploadRequest) =>
    api.post<FigureSnapshot>("/figures/upload", data),

  /** Daftar semua gambar untuk satu laporan. */
  listByReport: (reportId: number, visibleOnly?: boolean) =>
    api.get<FigureSnapshot[]>(`/figures/report/${reportId}`, {
      params: visibleOnly ? { visible_only: true } : {},
    }),

  /** Detail satu gambar. */
  get: (figureId: number) =>
    api.get<FigureSnapshot>(`/figures/${figureId}`),

  /** Update caption, visibility, atau urutan. */
  update: (figureId: number, data: FigureUpdateRequest) =>
    api.patch<FigureSnapshot>(`/figures/${figureId}`, data),

  /** Hapus gambar. */
  delete: (figureId: number) =>
    api.delete(`/figures/${figureId}`),

  /**
   * URL langsung PNG (butuh auth header).
   * Gunakan fetchPng() untuk download dengan token.
   */
  pngUrl: (figureId: number) =>
    `${API_URL}/api/v1/figures/${figureId}/png`,

  /** Download PNG dengan auth header dan kembalikan Object URL. */
  async fetchPngObjectUrl(figureId: number): Promise<string> {
    const token =
      typeof window !== "undefined" ? localStorage.getItem("ag_sas_token") : null;
    const res = await fetch(`${API_URL}/api/v1/figures/${figureId}/png`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Konversi base64 PNG menjadi data URL siap untuk <img src>. */
export function pngBase64ToDataUrl(base64: string): string {
  return `data:image/png;base64,${base64}`;
}

/** Capture canvas elemen sebagai base64 PNG. */
export function captureCanvasAsBase64(canvas: HTMLCanvasElement): string {
  const dataUrl = canvas.toDataURL("image/png");
  return dataUrl.replace(/^data:image\/png;base64,/, "");
}

/** Download FigureSnapshot sebagai file PNG. */
export function downloadFigureAsPng(fig: FigureSnapshot): void {
  const link = document.createElement("a");
  link.href = pngBase64ToDataUrl(fig.png_base64);
  const safeName = fig.title.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 40);
  link.download = `AG-SAS_${fig.figure_number.replace(".", "-")}_${safeName}.png`;
  document.body.appendChild(link);
  link.click();
  link.remove();
}
