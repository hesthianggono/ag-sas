// ── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

// ── Project ───────────────────────────────────────────────────────────────────

export interface Project {
  id: number;
  owner_id: number;
  name: string;
  location: string;
  client_name: string;
  consultant_name: string | null;
  building_type: string;
  num_floors: number;
  structural_system: string;
  primary_material: string;
  applicable_standards: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  location: string;
  client_name: string;
  consultant_name?: string;
  building_type: string;
  num_floors: number;
  structural_system: string;
  primary_material: string;
  applicable_standards: string;
  description?: string;
}

// ── Steel Profile ─────────────────────────────────────────────────────────────

export interface SteelProfile {
  id: number;
  category: string;
  designation: string;
  height_h: number;
  flange_width_b: number;
  web_thickness_tw: number;
  flange_thickness_tf: number;
  area_a: number;
  ix: number;
  sx: number;
  zx: number;
  rx: number;
  ry: number;
  weight_per_m: number;
}

// ── Calculation ───────────────────────────────────────────────────────────────

export interface ConcreteBeamInput {
  project_id: number;
  title: string;
  width_b_mm: number;
  height_h_mm: number;
  cover_cc_mm: number;
  bar_diameter_mm: number;
  stirrup_diameter_mm: number;
  fc_prime_mpa: number;
  fy_mpa: number;
  span_l_m: number;
  dead_load_w_knm: number;
  live_load_w_knm: number;
  notes?: string;
}

export interface SteelBeamInput {
  project_id: number;
  title: string;
  profile_id: number;
  fy_mpa: number;
  span_l_m: number;
  dead_load_w_knm: number;
  live_load_w_knm: number;
  notes?: string;
}

export interface CalculationRecord {
  id: number;
  project_id: number;
  user_id: number;
  calc_type: "concrete_beam" | "steel_beam";
  title: string;
  formula_version: string;
  standard_references: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  status: "AMAN" | "TIDAK AMAN" | "ERROR";
  notes: string | null;
  created_at: string;
}

export type CalcStatus = "AMAN" | "TIDAK AMAN" | "ERROR";

// ── Report ────────────────────────────────────────────────────────────────────

export interface ReportRecord {
  id: number;
  calc_id: number;
  figure_count?: number;
  user_id: number;
  project_id: number;
  calc_type: "concrete_beam" | "steel_beam";
  title: string;
  formula_version: string;
  standard_references: string;
  generated_at: string;
  generated_by_name: string;
  project_name: string;
  project_location: string;
  client_name: string;
  consultant_name: string | null;
  building_type: string;
  num_floors: number;
  structural_system: string;
  primary_material: string;
  input_snapshot: Record<string, unknown>;
  output_snapshot: Record<string, unknown>;
}
