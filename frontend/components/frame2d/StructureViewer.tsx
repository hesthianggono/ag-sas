"use client";
/**
 * StructureViewer — SVG-based 2D structural diagram viewer for Frame2D results.
 *
 * Shows: undeformed structure, deformed shape, N / V / M diagrams.
 * Controls: deformation scale, show/hide labels, diagram toggles, SVG export.
 */

import React, { useMemo, useRef, useState, useCallback } from "react";

// ─── Types (mirrors API response) ────────────────────────────────────────────

interface NodeData {
  index: number;
  x_m: number;
  y_m: number;
}

interface SupportData {
  node_index: number;
  fix_ux: boolean;
  fix_uy: boolean;
  fix_rz: boolean;
}

interface NodalLoadData {
  node_index: number;
  fx_kn: number;
  fy_kn: number;
  mz_knm: number;
}

interface ElementData {
  index: number;
  node_i: number;
  node_j: number;
  udl_kn_per_m: number;
}

interface DiagramPoint {
  x: number;
  gx: number; gy: number;
  N: number; V: number; M: number;
  N_gx: number; N_gy: number;
  V_gx: number; V_gy: number;
  M_gx: number; M_gy: number;
  def_gx: number; def_gy: number;
}

interface ElementDiagram {
  element_index: number;
  node_i: number;
  node_j: number;
  length_m: number;
  angle_deg: number;
  N_max_kn: number; N_min_kn: number;
  V_max_kn: number; V_min_kn: number;
  M_max_knm: number; M_min_knm: number;
  points: DiagramPoint[];
}

interface GlobalExtremes {
  N_max_kn: number; N_min_kn: number;
  V_max_kn: number; V_min_kn: number;
  M_max_knm: number; M_min_knm: number;
  max_deflection_m: number;
}

interface DiagramData {
  global_extremes: GlobalExtremes;
  elements: ElementDiagram[];
}

export interface StructureViewerProps {
  nodes: NodeData[];
  elements: ElementData[];
  supports: SupportData[];
  nodalLoads: NodalLoadData[];
  diagrams: DiagramData;
}

// ─── Viewport helpers ─────────────────────────────────────────────────────────

const SVG_W = 800;
const SVG_H = 500;
const MARGIN = 60;

function buildTransform(nodes: NodeData[]) {
  if (!nodes.length) return { toSvg: (x: number, y: number) => [0, 0] as [number, number], scale: 1 };
  const xs = nodes.map((n) => n.x_m);
  const ys = nodes.map((n) => n.y_m);
  let minX = Math.min(...xs), maxX = Math.max(...xs);
  let minY = Math.min(...ys), maxY = Math.max(...ys);

  // add padding
  const rangeX = maxX - minX || 1;
  const rangeY = maxY - minY || 1;
  minX -= rangeX * 0.15;
  maxX += rangeX * 0.15;
  minY -= rangeY * 0.25;
  maxY += rangeY * 0.25;

  const scaleX = (SVG_W - 2 * MARGIN) / (maxX - minX);
  const scaleY = (SVG_H - 2 * MARGIN) / (maxY - minY);
  const scale = Math.min(scaleX, scaleY);

  const toSvg = (gx: number, gy: number): [number, number] => [
    MARGIN + (gx - minX) * scale,
    SVG_H - MARGIN - (gy - minY) * scale, // flip Y (SVG y-down, structural y-up)
  ];

  return { toSvg, scale };
}

// ─── Diagram scale helpers ────────────────────────────────────────────────────

function diagramScale(max: number, min: number, desiredPixels: number, coordScale: number): number {
  const absMax = Math.max(Math.abs(max), Math.abs(min));
  if (absMax < 1e-9) return 1;
  return desiredPixels / absMax / coordScale;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SupportSymbol({
  cx, cy, fix_ux, fix_uy, fix_rz, toSvg, scale,
}: {
  cx: number; cy: number;
  fix_ux: boolean; fix_uy: boolean; fix_rz: boolean;
  toSvg: (x: number, y: number) => [number, number];
  scale: number;
}) {
  const [sx, sy] = toSvg(cx, cy);
  const s = Math.min(scale * 0.18, 14);

  if (fix_ux && fix_uy && fix_rz) {
    // Fixed: filled rectangle
    return (
      <g>
        <rect x={sx - s} y={sy} width={s * 2} height={s * 0.8} fill="#4b5563" />
        <line x1={sx - s * 1.5} y1={sy + s * 0.8} x2={sx + s * 1.5} y2={sy + s * 0.8}
          stroke="#4b5563" strokeWidth={1.5} />
      </g>
    );
  }
  if (fix_ux && fix_uy) {
    // Pin: triangle
    const h = s * 1.1;
    return (
      <g>
        <polygon points={`${sx},${sy} ${sx - h * 0.65},${sy + h} ${sx + h * 0.65},${sy + h}`}
          fill="none" stroke="#4b5563" strokeWidth={1.5} />
        <line x1={sx - h * 0.8} y1={sy + h + 2} x2={sx + h * 0.8} y2={sy + h + 2}
          stroke="#4b5563" strokeWidth={1.5} />
      </g>
    );
  }
  if (fix_uy) {
    // Roller: triangle + circle
    const h = s * 1.1;
    return (
      <g>
        <polygon points={`${sx},${sy} ${sx - h * 0.65},${sy + h} ${sx + h * 0.65},${sy + h}`}
          fill="none" stroke="#4b5563" strokeWidth={1.5} />
        <circle cx={sx} cy={sy + h + 4} r={3} fill="none" stroke="#4b5563" strokeWidth={1.5} />
      </g>
    );
  }
  return null;
}

function ArrowLoad({ x1, y1, x2, y2, label, color = "#f59e0b" }: {
  x1: number; y1: number; x2: number; y2: number; label: string; color?: string;
}) {
  const dx = x2 - x1; const dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  if (len < 1) return null;
  const ux = dx / len; const uy = dy / len;
  const arrowSize = 8;
  // Arrowhead at end
  const ax = x2 - ux * arrowSize; const ay = y2 - uy * arrowSize;
  const perpX = -uy * arrowSize * 0.4; const perpY = ux * arrowSize * 0.4;
  const headPts = `${x2},${y2} ${ax + perpX},${ay + perpY} ${ax - perpX},${ay - perpY}`;
  return (
    <g>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={2} />
      <polygon points={headPts} fill={color} />
      <text x={x1} y={y1 - 4} fontSize={9} fill={color} textAnchor="middle">{label}</text>
    </g>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

type DiagramMode = "none" | "N" | "V" | "M" | "deformed";

export default function StructureViewer({
  nodes, elements, supports, nodalLoads, diagrams,
}: StructureViewerProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  // Controls
  const [showLabels, setShowLabels] = useState(true);
  const [showLoads, setShowLoads] = useState(true);
  const [diagramMode, setDiagramMode] = useState<DiagramMode>("M");
  const [diagScale, setDiagScale] = useState(50); // desired diagram width in px

  const { toSvg, scale } = useMemo(() => buildTransform(nodes), [nodes]);

  // Build node coord map
  const nodeCoords = useMemo(() => {
    const m: Record<number, NodeData> = {};
    nodes.forEach((n) => (m[n.index] = n));
    return m;
  }, [nodes]);

  // ── Export SVG ────────────────────────────────────────────────────────────

  const exportSvg = useCallback((filename: string) => {
    if (!svgRef.current) return;
    const blob = new Blob([svgRef.current.outerHTML], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  // ── Diagram polygon points ────────────────────────────────────────────────

  function getDiagramPolygon(elemDiag: ElementDiagram, mode: "N" | "V" | "M"): string {
    const keyGx = `${mode}_gx` as keyof DiagramPoint;
    const keyGy = `${mode}_gy` as keyof DiagramPoint;

    const ge = diagrams.global_extremes;
    const absMax = mode === "N"
      ? Math.max(Math.abs(ge.N_max_kn), Math.abs(ge.N_min_kn))
      : mode === "V"
      ? Math.max(Math.abs(ge.V_max_kn), Math.abs(ge.V_min_kn))
      : Math.max(Math.abs(ge.M_max_knm), Math.abs(ge.M_min_knm));

    if (absMax < 1e-9) return "";

    const pixPerUnit = diagScale / absMax;

    // baseline: element axis points
    const baseline = elemDiag.points.map((p) => {
      const [sx, sy] = toSvg(p.gx, p.gy);
      return `${sx},${sy}`;
    });

    // tip: diagram offset points
    const tips = elemDiag.points.map((p) => {
      const valGx = (p[keyGx] as number - p.gx) * scale * pixPerUnit + (toSvg(p.gx, p.gy)[0]);
      const valGy = (p[keyGy] as number - p.gy) * scale * pixPerUnit;
      const [bx, by] = toSvg(p.gx, p.gy);
      // offset in SVG coords: normal direction already encoded in N_gx-gx / N_gy-gy
      const offX = (p[keyGx] as number - p.gx) * scale * pixPerUnit;
      const offY = -(p[keyGy] as number - p.gy) * scale * pixPerUnit; // flip Y
      return `${bx + offX},${by + offY}`;
    });

    return [...baseline, ...[...tips].reverse()].join(" ");
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  const diagramColors: Record<DiagramMode, string> = {
    none: "transparent",
    N: "#3b82f6",
    V: "#10b981",
    M: "#f59e0b",
    deformed: "#a855f7",
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center bg-slate-800 rounded-lg px-4 py-3">
        {/* Diagram mode */}
        <span className="text-xs text-slate-400 font-medium">Diagram:</span>
        {(["none", "deformed", "N", "V", "M"] as DiagramMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setDiagramMode(m)}
            className={`px-3 py-1 rounded text-xs font-bold transition-colors ${
              diagramMode === m
                ? "bg-brand-600 text-white"
                : "bg-slate-700 text-slate-300 hover:bg-slate-600"
            }`}
          >
            {m === "none" ? "Struktur" : m === "deformed" ? "Deformasi" : `Gaya ${m}`}
          </button>
        ))}

        <span className="text-slate-600">|</span>

        {/* Scale slider */}
        {diagramMode !== "none" && diagramMode !== "deformed" && (
          <label className="flex items-center gap-2 text-xs text-slate-400">
            Skala:
            <input
              type="range" min={10} max={120} step={5}
              value={diagScale}
              onChange={(e) => setDiagScale(Number(e.target.value))}
              className="w-24 accent-brand-500"
            />
            <span className="text-slate-300 w-6">{diagScale}</span>
          </label>
        )}

        {/* Toggles */}
        <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
          <input type="checkbox" checked={showLabels}
            onChange={(e) => setShowLabels(e.target.checked)} className="accent-brand-500" />
          Label
        </label>
        <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
          <input type="checkbox" checked={showLoads}
            onChange={(e) => setShowLoads(e.target.checked)} className="accent-brand-500" />
          Beban
        </label>

        <span className="text-slate-600">|</span>

        {/* Export */}
        <button
          onClick={() => exportSvg(`frame2d-${diagramMode}.svg`)}
          className="px-3 py-1 rounded text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors"
        >
          ⬇ SVG
        </button>
      </div>

      {/* SVG canvas */}
      <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          width="100%"
          style={{ maxHeight: 520 }}
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Grid (subtle) */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth={0.5} />
            </pattern>
          </defs>
          <rect width={SVG_W} height={SVG_H} fill="url(#grid)" />

          {/* ── Diagram polygons ── */}
          {(diagramMode === "N" || diagramMode === "V" || diagramMode === "M") &&
            diagrams.elements.map((ed) => {
              const pts = getDiagramPolygon(ed, diagramMode);
              return pts ? (
                <polygon
                  key={`diag-${ed.element_index}`}
                  points={pts}
                  fill={diagramColors[diagramMode] + "33"}
                  stroke={diagramColors[diagramMode]}
                  strokeWidth={1}
                />
              ) : null;
            })}

          {/* ── Deformed shape ── */}
          {diagramMode === "deformed" &&
            diagrams.elements.map((ed) => {
              const pts = ed.points.map((p) => {
                const [sx, sy] = toSvg(p.def_gx, p.def_gy);
                return `${sx},${sy}`;
              });
              return (
                <polyline
                  key={`def-${ed.element_index}`}
                  points={pts.join(" ")}
                  fill="none"
                  stroke={diagramColors.deformed}
                  strokeWidth={2}
                  strokeDasharray="6 3"
                />
              );
            })}

          {/* ── Undeformed elements ── */}
          {elements.map((el) => {
            const ni = nodeCoords[el.node_i];
            const nj = nodeCoords[el.node_j];
            if (!ni || !nj) return null;
            const [x1, y1] = toSvg(ni.x_m, ni.y_m);
            const [x2, y2] = toSvg(nj.x_m, nj.y_m);
            return (
              <g key={`el-${el.index}`}>
                <line x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke="#64748b" strokeWidth={2.5} strokeLinecap="round" />
                {/* UDL indicator */}
                {showLoads && el.udl_kn_per_m !== 0 && (() => {
                  // draw small downward arrows along element
                  const nArr = 5;
                  return Array.from({ length: nArr }).map((_, k) => {
                    const t = (k + 1) / (nArr + 1);
                    const mx = x1 + (x2 - x1) * t;
                    const my = y1 + (y2 - y1) * t;
                    const len = 18 * Math.sign(el.udl_kn_per_m);
                    return (
                      <line key={k}
                        x1={mx} y1={my - len} x2={mx} y2={my}
                        stroke="#f59e0b" strokeWidth={1.5}
                        markerEnd="url(#arrow-udl)"
                      />
                    );
                  });
                })()}
                {showLabels && (
                  <text
                    x={(x1 + x2) / 2}
                    y={(y1 + y2) / 2 - 6}
                    fontSize={9}
                    fill="#94a3b8"
                    textAnchor="middle"
                  >
                    E{el.index}
                  </text>
                )}
              </g>
            );
          })}

          {/* ── Nodal loads ── */}
          {showLoads &&
            nodalLoads.map((nl, idx) => {
              const n = nodeCoords[nl.node_index];
              if (!n) return null;
              const [sx, sy] = toSvg(n.x_m, n.y_m);
              const arrLen = 36;
              return (
                <g key={`nl-${idx}`}>
                  {nl.fx_kn !== 0 && (
                    <ArrowLoad
                      x1={sx - Math.sign(nl.fx_kn) * arrLen} y1={sy}
                      x2={sx} y2={sy}
                      label={`${nl.fx_kn}kN`}
                    />
                  )}
                  {nl.fy_kn !== 0 && (
                    <ArrowLoad
                      x1={sx} y1={sy + Math.sign(nl.fy_kn) * arrLen}
                      x2={sx} y2={sy}
                      label={`${nl.fy_kn}kN`}
                    />
                  )}
                </g>
              );
            })}

          {/* ── Diagram value labels at extremes ── */}
          {(diagramMode === "N" || diagramMode === "V" || diagramMode === "M") &&
            diagrams.elements.map((ed) => {
              // Find point with max absolute value
              const key = diagramMode as "N" | "V" | "M";
              const absMax = Math.max(...ed.points.map((p) => Math.abs(p[key])));
              const pt = ed.points.find((p) => Math.abs(p[key]) === absMax);
              if (!pt || absMax < 1e-6) return null;
              const keyGx = `${key}_gx` as keyof DiagramPoint;
              const keyGy = `${key}_gy` as keyof DiagramPoint;
              const ge = diagrams.global_extremes;
              const absMaxGlobal = key === "N"
                ? Math.max(Math.abs(ge.N_max_kn), Math.abs(ge.N_min_kn))
                : key === "V"
                ? Math.max(Math.abs(ge.V_max_kn), Math.abs(ge.V_min_kn))
                : Math.max(Math.abs(ge.M_max_knm), Math.abs(ge.M_min_knm));
              const pixPerUnit = diagScale / (absMaxGlobal || 1);
              const [bx, by] = toSvg(pt.gx, pt.gy);
              const offX = (pt[keyGx] as number - pt.gx) * scale * pixPerUnit;
              const offY = -(pt[keyGy] as number - pt.gy) * scale * pixPerUnit;
              const unit = key === "M" ? "kN·m" : "kN";
              return showLabels ? (
                <text
                  key={`dlabel-${ed.element_index}`}
                  x={bx + offX}
                  y={by + offY - 4}
                  fontSize={9}
                  fill={diagramColors[diagramMode]}
                  textAnchor="middle"
                >
                  {pt[key].toFixed(1)} {unit}
                </text>
              ) : null;
            })}

          {/* ── Supports ── */}
          {supports.map((sup, idx) => {
            const n = nodeCoords[sup.node_index];
            if (!n) return null;
            return (
              <SupportSymbol
                key={`sup-${idx}`}
                cx={n.x_m} cy={n.y_m}
                fix_ux={sup.fix_ux} fix_uy={sup.fix_uy} fix_rz={sup.fix_rz}
                toSvg={toSvg} scale={scale}
              />
            );
          })}

          {/* ── Nodes ── */}
          {nodes.map((n) => {
            const [sx, sy] = toSvg(n.x_m, n.y_m);
            return (
              <g key={`node-${n.index}`}>
                <circle cx={sx} cy={sy} r={4} fill="#e2e8f0" stroke="#475569" strokeWidth={1.5} />
                {showLabels && (
                  <text x={sx + 6} y={sy - 6} fontSize={9} fill="#94a3b8">{n.index}</text>
                )}
              </g>
            );
          })}

          {/* ── Legend ── */}
          <g transform={`translate(${SVG_W - 120}, 12)`}>
            <rect width={110} height={60} rx={4} fill="#0f172a" fillOpacity={0.85} />
            <text x={6} y={14} fontSize={9} fill="#94a3b8" fontWeight="bold">
              {diagramMode === "none" ? "Struktur" :
               diagramMode === "deformed" ? "Deformasi (diper)" :
               diagramMode === "N" ? "Gaya Aksial N (kN)" :
               diagramMode === "V" ? "Gaya Geser V (kN)" :
               "Momen Lentur M (kN·m)"}
            </text>
            {diagramMode !== "none" && diagramMode !== "deformed" && (
              <>
                <text x={6} y={28} fontSize={8} fill="#94a3b8">
                  Max:{" "}
                  {diagramMode === "N"
                    ? diagrams.global_extremes.N_max_kn.toFixed(2)
                    : diagramMode === "V"
                    ? diagrams.global_extremes.V_max_kn.toFixed(2)
                    : diagrams.global_extremes.M_max_knm.toFixed(2)}
                </text>
                <text x={6} y={42} fontSize={8} fill="#94a3b8">
                  Min:{" "}
                  {diagramMode === "N"
                    ? diagrams.global_extremes.N_min_kn.toFixed(2)
                    : diagramMode === "V"
                    ? diagrams.global_extremes.V_min_kn.toFixed(2)
                    : diagrams.global_extremes.M_min_knm.toFixed(2)}
                </text>
                <line x1={6} y1={50} x2={100} y2={50}
                  stroke={diagramColors[diagramMode]} strokeWidth={2} />
              </>
            )}
            {diagramMode === "deformed" && (
              <text x={6} y={28} fontSize={8} fill="#94a3b8">
                δ_max: {(diagrams.global_extremes.max_deflection_m * 1000).toFixed(3)} mm
              </text>
            )}
          </g>
        </svg>
      </div>

      {/* Diagram value table for current mode */}
      {diagramMode !== "none" && diagramMode !== "deformed" && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-slate-300 border-collapse">
            <thead>
              <tr className="bg-slate-800 text-slate-400">
                <th className="px-3 py-2 text-left">Elemen</th>
                <th className="px-3 py-2 text-right">
                  {diagramMode === "M" ? "M_max (kN·m)" : `${diagramMode}_max (kN)`}
                </th>
                <th className="px-3 py-2 text-right">
                  {diagramMode === "M" ? "M_min (kN·m)" : `${diagramMode}_min (kN)`}
                </th>
              </tr>
            </thead>
            <tbody>
              {diagrams.elements.map((ed) => (
                <tr key={ed.element_index} className="border-t border-slate-700">
                  <td className="px-3 py-1.5">E{ed.element_index}</td>
                  <td className="px-3 py-1.5 text-right font-mono">
                    {(diagramMode === "N" ? ed.N_max_kn : diagramMode === "V" ? ed.V_max_kn : ed.M_max_knm).toFixed(3)}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">
                    {(diagramMode === "N" ? ed.N_min_kn : diagramMode === "V" ? ed.V_min_kn : ed.M_min_knm).toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
