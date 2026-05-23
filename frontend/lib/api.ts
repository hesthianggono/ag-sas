import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("ag_sas_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("ag_sas_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; full_name: string; password: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
};

// ── Projects ──────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: () => api.get("/projects/"),
  create: (data: unknown) => api.post("/projects/", data),
  get: (id: number) => api.get(`/projects/${id}`),
  update: (id: number, data: unknown) => api.put(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
};

// ── Calculations ──────────────────────────────────────────────────────────────

export const calcApi = {
  concreteBeam: (data: unknown) => api.post("/calculations/concrete-beam", data),
  steelBeam: (data: unknown) => api.post("/calculations/steel-beam", data),
  getByProject: (projectId: number) =>
    api.get(`/calculations/project/${projectId}`),
  get: (id: number) => api.get(`/calculations/${id}`),

  /**
   * Generate laporan dari calc_id lalu langsung download PDF-nya.
   * Urutan: POST /reports/generate → GET /reports/{id}/download
   */
  downloadPdf: async (calcId: number, filename?: string): Promise<void> => {
    // 1. Generate report record
    const { data: report } = await api.post("/reports/generate", { calc_id: calcId });
    const reportId: number = report.id;

    // 2. Download PDF via fetch (agar bisa kirim Authorization header)
    const token = typeof window !== "undefined" ? localStorage.getItem("ag_sas_token") : null;
    const res = await fetch(`${API_URL}/api/v1/reports/${reportId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail ?? `HTTP ${res.status}`);
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = filename ?? `AG-SAS_laporan_${calcId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

// ── Steel Profiles ────────────────────────────────────────────────────────────

export const steelProfilesApi = {
  list: (category?: string) =>
    api.get("/steel-profiles/", { params: category ? { category } : {} }),
  categories: () => api.get("/steel-profiles/categories"),
};

// ── Reports ───────────────────────────────────────────────────────────────────

export const reportsApi = {
  generate: (
    calc_id: number,
    engineer_name?: string,
    engineer_position?: string,
    engineer_skk?: string,
  ) => api.post("/reports/generate", {
    calc_id,
    ...(engineer_name     ? { engineer_name }     : {}),
    ...(engineer_position ? { engineer_position } : {}),
    ...(engineer_skk      ? { engineer_skk }      : {}),
  }),
  list: (project_id?: number) =>
    api.get("/reports/", { params: project_id ? { project_id } : {} }),
  get: (id: number) => api.get(`/reports/${id}`),
  previewUrl: (id: number) => `${API_URL}/api/v1/reports/${id}/preview`,
  downloadUrl: (id: number) => `${API_URL}/api/v1/reports/${id}/download`,

  /** Download PDF with Authorization header → saves file to disk. */
  async downloadPdf(id: number, filename?: string): Promise<void> {
    const token = typeof window !== "undefined" ? localStorage.getItem("ag_sas_token") : null;
    const res = await fetch(`${API_URL}/api/v1/reports/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail ?? `HTTP ${res.status}`);
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = filename ?? `AG-SAS_laporan_${id}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};
