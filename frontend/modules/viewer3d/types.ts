// ── Structural Model Types ──────────────────────────────────────────────────
// Designed for future 3D frame analysis (Direct Stiffness Method)

export interface StructNode {
  id: string;
  x: number;   // m, global X
  y: number;   // m, global Y
  z: number;   // m, global Z
  label?: string;
}

export interface StructElement {
  id: string;
  nodeI: string;   // start node id
  nodeJ: string;   // end node id
  sectionId: string;
  materialId: string;
  type: "beam" | "column" | "brace";
  label?: string;
}

export type SupportType = "fixed" | "pinned" | "roller_x" | "roller_z";

export interface Support {
  nodeId: string;
  type: SupportType;
  // DOF restraints: [ux, uy, uz, rx, ry, rz] — true = restrained
  dof: [boolean, boolean, boolean, boolean, boolean, boolean];
}

export interface NodalLoad {
  nodeId: string;
  fx: number;   // kN
  fy: number;   // kN
  fz: number;   // kN
  mx: number;   // kN·m
  my: number;   // kN·m
  mz: number;   // kN·m
  label?: string;
}

export interface Section {
  id: string;
  name: string;
  type: "WF" | "HSS" | "rectangular" | "circular" | "custom";
  area_cm2?: number;
  ix_cm4?: number;
  iy_cm4?: number;
  zx_cm3?: number;
  // Additional props for future FEM
  [key: string]: unknown;
}

export interface Material {
  id: string;
  name: string;
  type: "steel" | "concrete" | "composite";
  E_gpa: number;   // Modulus elastisitas [GPa]
  fy_mpa?: number; // Yield strength [MPa] — steel
  fc_mpa?: number; // Compressive strength [MPa] — concrete
}

export interface StructureModel {
  name: string;
  description?: string;
  nodes: StructNode[];
  elements: StructElement[];
  supports: Support[];
  loads: NodalLoad[];
  sections: Section[];
  materials: Material[];
}

// ── Selection state for UI ─────────────────────────────────────────────────

export type SelectionType = "node" | "element";

export interface Selection {
  type: SelectionType;
  id: string;
}
