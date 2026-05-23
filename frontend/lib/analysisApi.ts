import { api } from "./api";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface NodeInput {
  index: number;
  x_m: number;
  y_m: number;
}

export interface MaterialInput {
  E_mpa: number;
}

export interface SectionInput {
  A_cm2: number;
  I_cm4: number;
}

export interface ElementInput {
  index: number;
  node_i: number;
  node_j: number;
  material: MaterialInput;
  section: SectionInput;
  udl_kn_per_m: number;
}

export interface SupportInput {
  node_index: number;
  fix_ux: boolean;
  fix_uy: boolean;
  fix_rz: boolean;
}

export interface NodalLoadInput {
  node_index: number;
  fx_kn: number;
  fy_kn: number;
  mz_knm: number;
}

export interface Frame2DRequest {
  title: string;
  nodes: NodeInput[];
  elements: ElementInput[];
  supports: SupportInput[];
  nodal_loads: NodalLoadInput[];
  notes: string;
}

export interface DiagramPoint {
  x: number;
  N: number; V: number; M: number;
  gx: number; gy: number;
  N_gx: number; N_gy: number;
  V_gx: number; V_gy: number;
  M_gx: number; M_gy: number;
  def_gx: number; def_gy: number;
}

export interface ElementDiagram {
  element_index: number;
  node_i: number; node_j: number;
  length_m: number; angle_deg: number;
  N_max_kn: number; N_min_kn: number;
  V_max_kn: number; V_min_kn: number;
  M_max_knm: number; M_min_knm: number;
  points: DiagramPoint[];
}

export interface DiagramData {
  global_extremes: {
    N_max_kn: number; N_min_kn: number;
    V_max_kn: number; V_min_kn: number;
    M_max_knm: number; M_min_knm: number;
    max_deflection_m: number;
  };
  elements: ElementDiagram[];
}

export interface Frame2DResult {
  run_id: string;
  title: string;
  status: string;
  summary: {
    max_displacement_mm: number;
    max_moment_knm: number;
    max_shear_kn: number;
  };
  displacements: { node: number; ux_mm: number; uy_mm: number; rz_mrad: number }[];
  reactions: { node: number; rx_kn: number; ry_kn: number; mz_knm: number }[];
  element_forces: {
    element: number;
    N_i_kn: number; Vy_i_kn: number; Mz_i_knm: number;
    N_j_kn: number; Vy_j_kn: number; Mz_j_knm: number;
  }[];
  diagrams?: DiagramData;
}

// ── API ───────────────────────────────────────────────────────────────────────

export const analysisApi = {
  runFrame2D: (data: Frame2DRequest) =>
    api.post<Frame2DResult>("/analysis/frame2d/run", data),
  getFrame2DResult: (runId: string) =>
    api.get<Frame2DResult>(`/analysis/frame2d/results/${runId}`),
};
