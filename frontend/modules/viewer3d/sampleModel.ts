import type { StructureModel } from "./types";

// ── 3×3 bay × 3 story 3D portal frame ─────────────────────────────────────
// Grid: X = [0, 5, 10, 15] m  (3 bays @ 5 m)
//       Z = [0, 5, 10]     m  (2 bays @ 5 m)
//       Y = [0, 4, 8, 12]  m  (ground + 3 floors @ 4 m)
// Total: 4×3×4 = 48 nodes, 144 columns + beams in X + beams in Z = ~168 elements

const X = [0, 5, 10, 15];
const Z_GRID = [0, 5, 10];
const Y = [0, 4, 8, 12];

function nodeId(xi: number, zi: number, yi: number) {
  return `N${xi}${zi}${yi}`;
}

function nodeLabel(xi: number, zi: number, yi: number) {
  return `N(${X[xi]},${Y[yi]},${Z_GRID[zi]})`;
}

// Generate nodes
const nodes = Y.flatMap((y, yi) =>
  Z_GRID.flatMap((z, zi) =>
    X.map((x, xi) => ({
      id: nodeId(xi, zi, yi),
      x,
      y,
      z,
      label: nodeLabel(xi, zi, yi),
    }))
  )
);

// Generate elements
const elements: StructureModel["elements"] = [];

// Columns (Y direction)
for (let yi = 0; yi < Y.length - 1; yi++) {
  for (let zi = 0; zi < Z_GRID.length; zi++) {
    for (let xi = 0; xi < X.length; xi++) {
      elements.push({
        id: `COL-${xi}-${zi}-${yi}`,
        nodeI: nodeId(xi, zi, yi),
        nodeJ: nodeId(xi, zi, yi + 1),
        sectionId: "WF400",
        materialId: "BJ41",
        type: "column",
        label: `Kolom (${X[xi]},${Z_GRID[zi]}) L${yi + 1}`,
      });
    }
  }
}

// Beams in X direction
for (let yi = 1; yi < Y.length; yi++) {
  for (let zi = 0; zi < Z_GRID.length; zi++) {
    for (let xi = 0; xi < X.length - 1; xi++) {
      elements.push({
        id: `BMX-${xi}-${zi}-${yi}`,
        nodeI: nodeId(xi, zi, yi),
        nodeJ: nodeId(xi + 1, zi, yi),
        sectionId: "WF300",
        materialId: "BJ41",
        type: "beam",
        label: `Balok-X (${X[xi]}-${X[xi + 1]},Z=${Z_GRID[zi]}) L${yi}`,
      });
    }
  }
}

// Beams in Z direction
for (let yi = 1; yi < Y.length; yi++) {
  for (let xi = 0; xi < X.length; xi++) {
    for (let zi = 0; zi < Z_GRID.length - 1; zi++) {
      elements.push({
        id: `BMZ-${xi}-${zi}-${yi}`,
        nodeI: nodeId(xi, zi, yi),
        nodeJ: nodeId(xi, zi + 1, yi),
        sectionId: "WF300",
        materialId: "BJ41",
        type: "beam",
        label: `Balok-Z (${X[xi]},${Z_GRID[zi]}-${Z_GRID[zi + 1]}) L${yi}`,
      });
    }
  }
}

// Supports: fixed at all base nodes (y=0)
const supports: StructureModel["supports"] = Z_GRID.flatMap((_, zi) =>
  X.map((_, xi) => ({
    nodeId: nodeId(xi, zi, 0),
    type: "fixed" as const,
    dof: [true, true, true, true, true, true],
  }))
);

// Sample loads at roof level nodes
const loads: StructureModel["loads"] = Z_GRID.flatMap((_, zi) =>
  X.map((_, xi) => ({
    nodeId: nodeId(xi, zi, Y.length - 1),
    fx: 0,
    fy: -50,  // kN downward
    fz: 0,
    mx: 0, my: 0, mz: 0,
    label: "Dead + Live Roof",
  }))
);

// Lateral load on corner node at roof
loads.push({
  nodeId: nodeId(0, 0, Y.length - 1),
  fx: 30, fy: 0, fz: 0,
  mx: 0, my: 0, mz: 0,
  label: "Beban Gempa (Wind)",
});

export const sampleModel: StructureModel = {
  name: "Gedung Portal 3D — 3×2 Bay × 3 Lantai",
  description: "Model contoh struktur gedung baja 3 lantai, 3 bentang arah X, 2 bentang arah Z",
  nodes,
  elements,
  supports,
  loads,
  sections: [
    {
      id: "WF400",
      name: "WF 400×200×8×13",
      type: "WF",
      area_cm2: 84.12,
      ix_cm4: 23700,
      iy_cm4: 1740,
      zx_cm3: 1350,
    },
    {
      id: "WF300",
      name: "WF 300×150×6.5×9",
      type: "WF",
      area_cm2: 46.78,
      ix_cm4: 7210,
      iy_cm4: 508,
      zx_cm3: 538,
    },
  ],
  materials: [
    {
      id: "BJ41",
      name: "Baja BJ-41 (SNI 1729:2020)",
      type: "steel",
      E_gpa: 200,
      fy_mpa: 250,
    },
  ],
};
