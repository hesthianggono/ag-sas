"use client";
import { useState } from "react";
import { Grid3x3, Play, Plus, Trash2, AlertTriangle, CheckCircle, ChevronDown, ChevronUp } from "lucide-react";
import { analysisApi, Frame2DRequest, Frame2DResult, NodeInput, ElementInput, SupportInput, NodalLoadInput } from "@/lib/analysisApi";
import { formatNumber } from "@/lib/utils";
import StructureViewer from "@/components/frame2d/StructureViewer";

// ── Default example: simply supported beam ─────────────────────────────────
const DEFAULT_NODES: NodeInput[] = [
  { index: 0, x_m: 0, y_m: 0 },
  { index: 1, x_m: 3, y_m: 0 },
  { index: 2, x_m: 6, y_m: 0 },
];
const DEFAULT_ELEMENTS: ElementInput[] = [
  { index: 0, node_i: 0, node_j: 1, material: { E_mpa: 200000 }, section: { A_cm2: 84.12, I_cm4: 23700 }, udl_kn_per_m: 20 },
  { index: 1, node_i: 1, node_j: 2, material: { E_mpa: 200000 }, section: { A_cm2: 84.12, I_cm4: 23700 }, udl_kn_per_m: 20 },
];
const DEFAULT_SUPPORTS: SupportInput[] = [
  { node_index: 0, fix_ux: true, fix_uy: true, fix_rz: false },
  { node_index: 2, fix_ux: false, fix_uy: true, fix_rz: false },
];
const DEFAULT_LOADS: NodalLoadInput[] = [];

const F = (v: number, d = 3) => formatNumber(v, d);

export default function Frame2DPage() {
  const [title, setTitle] = useState("Balok Sederhana — UDL 20 kN/m");
  const [nodes, setNodes] = useState<NodeInput[]>(DEFAULT_NODES);
  const [elements, setElements] = useState<ElementInput[]>(DEFAULT_ELEMENTS);
  const [supports, setSupports] = useState<SupportInput[]>(DEFAULT_SUPPORTS);
  const [loads, setLoads] = useState<NodalLoadInput[]>(DEFAULT_LOADS);
  const [result, setResult] = useState<Frame2DResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>("displacements");

  async function handleRun() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const req: Frame2DRequest = { title, nodes, elements, supports, nodal_loads: loads, notes: "" };
      const { data } = await analysisApi.runFrame2D(req);
      setResult(data);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : JSON.stringify(detail) || "Terjadi kesalahan.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy flex items-center gap-3">
          <Grid3x3 className="w-6 h-6" />
          Analisis Portal 2D
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Direct Stiffness Method — balok & kolom, beban terpusat & merata (LRFD linear elastik)
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* ── Input Panel ── */}
        <div className="space-y-4">

          {/* Title */}
          <div className="engineering-card p-5">
            <label className="engineering-label">Judul Perhitungan</label>
            <input className="engineering-input" value={title}
              onChange={e => setTitle(e.target.value)} placeholder="Contoh: Portal Lantai 1" />
          </div>

          {/* Nodes */}
          <div className="engineering-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title mb-0 border-0 pb-0 text-xs">TITIK SIMPUL (Node)</h3>
              <button onClick={() => setNodes(n => [...n, { index: n.length, x_m: 0, y_m: 0 }])}
                className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-semibold">
                <Plus className="w-3 h-3" /> Tambah
              </button>
            </div>
            <div className="space-y-2">
              <div className="grid grid-cols-4 gap-2 text-xs text-slate-400 font-semibold px-1">
                <span>No.</span><span>X (m)</span><span>Y (m)</span><span></span>
              </div>
              {nodes.map((n, i) => (
                <div key={i} className="grid grid-cols-4 gap-2 items-center">
                  <span className="text-xs font-mono text-slate-500 pl-1">{n.index}</span>
                  <input type="number" step="0.1" value={n.x_m} onChange={e => {
                    const copy = [...nodes]; copy[i] = { ...n, x_m: +e.target.value }; setNodes(copy);
                  }} className="engineering-input text-xs py-1.5" />
                  <input type="number" step="0.1" value={n.y_m} onChange={e => {
                    const copy = [...nodes]; copy[i] = { ...n, y_m: +e.target.value }; setNodes(copy);
                  }} className="engineering-input text-xs py-1.5" />
                  <button onClick={() => setNodes(nodes.filter((_, j) => j !== i))}
                    className="text-slate-300 hover:text-red-400 transition-colors justify-self-center">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Elements */}
          <div className="engineering-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title mb-0 border-0 pb-0 text-xs">ELEMEN (Batang)</h3>
              <button onClick={() => setElements(el => [...el, {
                index: el.length, node_i: 0, node_j: 1,
                material: { E_mpa: 200000 }, section: { A_cm2: 84.12, I_cm4: 23700 }, udl_kn_per_m: 0
              }])} className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-semibold">
                <Plus className="w-3 h-3" /> Tambah
              </button>
            </div>
            <div className="space-y-2">
              <div className="grid grid-cols-7 gap-1 text-xs text-slate-400 font-semibold px-1">
                <span>No.</span><span>i</span><span>j</span>
                <span>E (MPa)</span><span>A (cm²)</span><span>I (cm⁴)</span><span>w (kN/m)</span>
              </div>
              {elements.map((el, i) => (
                <div key={i} className="grid grid-cols-7 gap-1 items-center">
                  <span className="text-xs font-mono text-slate-500 pl-1">{el.index}</span>
                  {[
                    [el.node_i, (v: number) => { const c=[...elements]; c[i]={...el, node_i:v}; setElements(c); }],
                    [el.node_j, (v: number) => { const c=[...elements]; c[i]={...el, node_j:v}; setElements(c); }],
                    [el.material.E_mpa, (v: number) => { const c=[...elements]; c[i]={...el, material:{E_mpa:v}}; setElements(c); }],
                    [el.section.A_cm2, (v: number) => { const c=[...elements]; c[i]={...el, section:{...el.section, A_cm2:v}}; setElements(c); }],
                    [el.section.I_cm4, (v: number) => { const c=[...elements]; c[i]={...el, section:{...el.section, I_cm4:v}}; setElements(c); }],
                    [el.udl_kn_per_m, (v: number) => { const c=[...elements]; c[i]={...el, udl_kn_per_m:v}; setElements(c); }],
                  ].map(([val, onChange], j) => (
                    <input key={j} type="number" step="any" value={val as number}
                      onChange={e => (onChange as Function)(+e.target.value)}
                      className="engineering-input text-xs py-1.5" />
                  ))}
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-400 mt-2">w = beban merata (kN/m, positif = ke bawah)</p>
          </div>

          {/* Supports */}
          <div className="engineering-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title mb-0 border-0 pb-0 text-xs">TUMPUAN</h3>
              <button onClick={() => setSupports(s => [...s, { node_index: 0, fix_ux: true, fix_uy: true, fix_rz: false }])}
                className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-semibold">
                <Plus className="w-3 h-3" /> Tambah
              </button>
            </div>
            <div className="space-y-2">
              <div className="grid grid-cols-5 gap-2 text-xs text-slate-400 font-semibold px-1">
                <span>Node</span><span className="text-center">UX</span><span className="text-center">UY</span><span className="text-center">RZ</span><span></span>
              </div>
              {supports.map((s, i) => (
                <div key={i} className="grid grid-cols-5 gap-2 items-center">
                  <input type="number" value={s.node_index} onChange={e => {
                    const c=[...supports]; c[i]={...s, node_index:+e.target.value}; setSupports(c);
                  }} className="engineering-input text-xs py-1.5" />
                  {(["fix_ux","fix_uy","fix_rz"] as const).map(k => (
                    <label key={k} className="flex items-center justify-center">
                      <input type="checkbox" checked={s[k]} onChange={e => {
                        const c=[...supports]; c[i]={...s, [k]:e.target.checked}; setSupports(c);
                      }} className="w-4 h-4 text-brand-600" />
                    </label>
                  ))}
                  <button onClick={() => setSupports(supports.filter((_,j)=>j!==i))}
                    className="text-slate-300 hover:text-red-400 transition-colors justify-self-center">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Nodal Loads */}
          <div className="engineering-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="section-title mb-0 border-0 pb-0 text-xs">BEBAN SIMPUL</h3>
              <button onClick={() => setLoads(l => [...l, { node_index: 0, fx_kn: 0, fy_kn: 0, mz_knm: 0 }])}
                className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-semibold">
                <Plus className="w-3 h-3" /> Tambah
              </button>
            </div>
            {loads.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-3">Belum ada beban simpul</p>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-5 gap-1 text-xs text-slate-400 font-semibold px-1">
                  <span>Node</span><span>FX (kN)</span><span>FY (kN)</span><span>MZ (kN·m)</span><span></span>
                </div>
                {loads.map((l, i) => (
                  <div key={i} className="grid grid-cols-5 gap-1 items-center">
                    {[
                      [l.node_index, (v:number)=>{const c=[...loads];c[i]={...l,node_index:v};setLoads(c);}],
                      [l.fx_kn, (v:number)=>{const c=[...loads];c[i]={...l,fx_kn:v};setLoads(c);}],
                      [l.fy_kn, (v:number)=>{const c=[...loads];c[i]={...l,fy_kn:v};setLoads(c);}],
                      [l.mz_knm, (v:number)=>{const c=[...loads];c[i]={...l,mz_knm:v};setLoads(c);}],
                    ].map(([val, onChange], j) => (
                      <input key={j} type="number" step="any" value={val as number}
                        onChange={e=>(onChange as Function)(+e.target.value)}
                        className="engineering-input text-xs py-1.5"/>
                    ))}
                    <button onClick={()=>setLoads(loads.filter((_,j)=>j!==i))}
                      className="text-slate-300 hover:text-red-400 transition-colors justify-self-center">
                      <Trash2 className="w-3.5 h-3.5"/>
                    </button>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-slate-400 mt-2">FY positif = ke atas; FX positif = ke kanan</p>
          </div>

          {/* Run Button */}
          <button onClick={handleRun} disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors">
            {loading
              ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>
              : <Play className="w-4 h-4"/>}
            {loading ? "Menghitung..." : "Jalankan Analisis"}
          </button>
        </div>

        {/* ── Result Panel ── */}
        <div className="engineering-card p-6">
          <h3 className="section-title">Hasil Analisis</h3>

          {!result && !error && (
            <div className="flex flex-col items-center justify-center h-64 text-slate-300">
              <Grid3x3 className="w-16 h-16 mb-4 opacity-30"/>
              <p className="text-sm">Isi data struktur lalu klik Jalankan</p>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-4">
              <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5"/>
              <p className="text-sm text-red-700 font-mono whitespace-pre-wrap">{error}</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  ["δ maks", F(result.summary.max_displacement_mm, 4), "mm"],
                  ["M maks", F(result.summary.max_moment_knm, 2), "kN·m"],
                  ["V maks", F(result.summary.max_shear_kn, 2), "kN"],
                ].map(([label, val, unit]) => (
                  <div key={label as string} className="bg-brand-50 border border-brand-200 rounded-lg p-3 text-center">
                    <p className="text-xs text-brand-500 font-semibold">{label}</p>
                    <p className="text-lg font-bold font-mono text-brand-700">{val}</p>
                    <p className="text-xs text-brand-400">{unit}</p>
                  </div>
                ))}
              </div>

              {/* Collapsible sections */}
              {[
                {
                  key: "displacements",
                  label: `Perpindahan Simpul (${result.displacements.length} node)`,
                  content: (
                    <table className="w-full text-xs font-mono">
                      <thead>
                        <tr className="text-slate-400 border-b border-slate-100">
                          <th className="text-left py-1.5 pr-3">Node</th>
                          <th className="text-right pr-3">UX (mm)</th>
                          <th className="text-right pr-3">UY (mm)</th>
                          <th className="text-right">RZ (mrad)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {result.displacements.map(d => (
                          <tr key={d.node}>
                            <td className="py-1.5 pr-3 text-slate-600">{d.node}</td>
                            <td className="text-right pr-3 text-slate-800">{F(d.ux_mm, 5)}</td>
                            <td className="text-right pr-3 text-slate-800">{F(d.uy_mm, 5)}</td>
                            <td className="text-right text-slate-800">{F(d.rz_mrad, 5)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ),
                },
                {
                  key: "reactions",
                  label: `Reaksi Tumpuan (${result.reactions.length} node)`,
                  content: (
                    <table className="w-full text-xs font-mono">
                      <thead>
                        <tr className="text-slate-400 border-b border-slate-100">
                          <th className="text-left py-1.5 pr-3">Node</th>
                          <th className="text-right pr-3">RX (kN)</th>
                          <th className="text-right pr-3">RY (kN)</th>
                          <th className="text-right">MZ (kN·m)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {result.reactions.map(r => (
                          <tr key={r.node}>
                            <td className="py-1.5 pr-3 text-slate-600">{r.node}</td>
                            <td className="text-right pr-3 text-slate-800">{F(r.rx_kn, 3)}</td>
                            <td className="text-right pr-3 text-slate-800">{F(r.ry_kn, 3)}</td>
                            <td className="text-right text-slate-800">{F(r.mz_knm, 3)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ),
                },
                {
                  key: "forces",
                  label: `Gaya Dalam Elemen (${result.element_forces.length} elemen)`,
                  content: (
                    <table className="w-full text-xs font-mono">
                      <thead>
                        <tr className="text-slate-400 border-b border-slate-100">
                          <th className="text-left py-1.5 pr-2">Elem</th>
                          <th className="text-right pr-2">N_i (kN)</th>
                          <th className="text-right pr-2">Vy_i (kN)</th>
                          <th className="text-right pr-2">Mz_i (kN·m)</th>
                          <th className="text-right pr-2">N_j</th>
                          <th className="text-right pr-2">Vy_j</th>
                          <th className="text-right">Mz_j</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {result.element_forces.map(ef => (
                          <tr key={ef.element}>
                            <td className="py-1.5 pr-2 text-slate-600">{ef.element}</td>
                            <td className="text-right pr-2 text-slate-800">{F(ef.N_i_kn, 2)}</td>
                            <td className="text-right pr-2 text-slate-800">{F(ef.Vy_i_kn, 2)}</td>
                            <td className="text-right pr-2 font-bold text-brand-700">{F(ef.Mz_i_knm, 2)}</td>
                            <td className="text-right pr-2 text-slate-800">{F(ef.N_j_kn, 2)}</td>
                            <td className="text-right pr-2 text-slate-800">{F(ef.Vy_j_kn, 2)}</td>
                            <td className="text-right font-bold text-brand-700">{F(ef.Mz_j_knm, 2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ),
                },
              ].map(({ key, label, content }) => (
                <div key={key} className="border border-slate-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setExpandedSection(expandedSection === key ? null : key)}
                    className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
                  >
                    <span className="text-xs font-bold text-slate-600 uppercase tracking-wide">{label}</span>
                    {expandedSection === key
                      ? <ChevronUp className="w-4 h-4 text-slate-400"/>
                      : <ChevronDown className="w-4 h-4 text-slate-400"/>}
                  </button>
                  {expandedSection === key && (
                    <div className="p-4 overflow-x-auto">{content}</div>
                  )}
                </div>
              ))}

              <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3 mt-2">
                <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5"/>
                <p className="text-xs text-amber-700">
                  Solver linear elastik — tidak mencakup non-linearitas geometri atau material.
                  Hasil hanya untuk preliminary design; wajib diverifikasi oleh insinyur berpengalaman.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Diagram Viewer (full width) ── */}
      {result?.diagrams && (
        <div className="mt-6">
          <div className="engineering-card p-5">
            <h2 className="section-title mb-4">Visualisasi Diagram Gaya Dalam & Deformasi</h2>
            <StructureViewer
              nodes={nodes}
              elements={elements}
              supports={supports}
              nodalLoads={loads}
              diagrams={result.diagrams}
            />
          </div>
        </div>
      )}
    </div>
  );
}
