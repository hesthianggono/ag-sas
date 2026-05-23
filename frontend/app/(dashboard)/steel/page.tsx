"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Layers, CheckCircle, XCircle, FileText, AlertTriangle, Download } from "lucide-react";
import { calcApi, projectsApi, steelProfilesApi } from "@/lib/api";
import { formatNumber, statusBg } from "@/lib/utils";
import type { Project, SteelProfile, SteelBeamInput } from "@/types";

function SteelCalculator() {
  const searchParams = useSearchParams();
  const preProjectId = searchParams.get("project_id");

  const [projects, setProjects] = useState<Project[]>([]);
  const [profiles, setProfiles] = useState<SteelProfile[]>([]);
  const [category, setCategory] = useState("WF");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [calcId, setCalcId] = useState<number | null>(null);

  const [form, setForm] = useState<SteelBeamInput>({
    project_id: preProjectId ? +preProjectId : 0,
    title: "Balok Baja B1",
    profile_id: 0,
    fy_mpa: 250,
    span_l_m: 6.0, dead_load_w_knm: 15, live_load_w_knm: 12,
    notes: "",
  });

  useEffect(() => {
    projectsApi.list().then(({ data }) => {
      setProjects(data);
      if (!form.project_id && data.length > 0) setForm(f => ({ ...f, project_id: data[0].id }));
    });
  }, []);

  useEffect(() => {
    steelProfilesApi.list(category).then(({ data }) => {
      setProfiles(data);
      if (data.length > 0) setForm(f => ({ ...f, profile_id: data[0].id }));
    });
  }, [category]);

  async function handleCalculate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const { data } = await calcApi.steelBeam(form);
      setResult(data.output_data);
      setCalcId(data.id);
    } finally {
      setLoading(false);
    }
  }

  const F = (v: any, d = 3) => typeof v === "number" ? formatNumber(v, d) : String(v ?? "-");

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy flex items-center gap-3">
          <Layers className="w-6 h-6" />
          Kalkulator Balok Baja WF
        </h1>
        <p className="text-slate-500 text-sm mt-1">SNI 1729:2020 — Desain lentur LRFD, penampang kompak</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Form */}
        <div className="engineering-card p-6">
          <form onSubmit={handleCalculate} className="space-y-5">
            <div>
              <h3 className="section-title">Informasi Perhitungan</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="engineering-label">Proyek <span className="text-red-500">*</span></label>
                  <select className="engineering-input" value={form.project_id}
                    onChange={(e) => setForm({ ...form, project_id: +e.target.value })} required>
                    <option value={0} disabled>Pilih proyek...</option>
                    {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="engineering-label">Judul Perhitungan</label>
                  <input className="engineering-input" value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })} />
                </div>
              </div>
            </div>

            {/* Profil */}
            <div>
              <h3 className="section-title">Profil Baja</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="engineering-label">Kategori</label>
                  <select className="engineering-input" value={category}
                    onChange={(e) => setCategory(e.target.value)}>
                    {["WF", "H-Beam", "CNP", "UNP"].map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="engineering-label">Profil <span className="text-red-500">*</span></label>
                  <select className="engineering-input" value={form.profile_id}
                    onChange={(e) => setForm({ ...form, profile_id: +e.target.value })} required>
                    {profiles.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.designation} — Zx={p.zx} cm³, W={p.weight_per_m} kg/m
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Profile Summary */}
              {form.profile_id > 0 && (() => {
                const p = profiles.find(x => x.id === form.profile_id);
                if (!p) return null;
                return (
                  <div className="mt-3 bg-slate-50 rounded-lg p-3 font-mono text-xs grid grid-cols-4 gap-2">
                    {[["H", `${p.height_h} mm`], ["B", `${p.flange_width_b} mm`],
                      ["Ix", `${p.ix} cm⁴`], ["Zx", `${p.zx} cm³`]].map(([k, v]) => (
                      <div key={k}>
                        <p className="text-slate-400">{k}</p>
                        <p className="font-bold text-slate-700">{v}</p>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>

            {/* Material */}
            <div>
              <h3 className="section-title">Material & Beban</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="engineering-label">Mutu Baja fy</label>
                  <select className="engineering-input" value={form.fy_mpa}
                    onChange={(e) => setForm({ ...form, fy_mpa: +e.target.value })}>
                    <option value={210}>210 MPa (BJ-34)</option>
                    <option value={240}>240 MPa (BJ-37)</option>
                    <option value={250}>250 MPa (BJ-41)</option>
                    <option value={290}>290 MPa (BJ-50)</option>
                    <option value={360}>360 MPa (BJ-55)</option>
                  </select>
                </div>
                <InputNum label="Panjang Bentang L" unit="m" value={form.span_l_m}
                  onChange={v => setForm({ ...form, span_l_m: v })} min={1} max={30} step={0.1} />
                <InputNum label="Beban Mati wD" unit="kN/m" value={form.dead_load_w_knm}
                  onChange={v => setForm({ ...form, dead_load_w_knm: v })} min={0} step={0.5} />
                <InputNum label="Beban Hidup wL" unit="kN/m" value={form.live_load_w_knm}
                  onChange={v => setForm({ ...form, live_load_w_knm: v })} min={0} step={0.5} />
              </div>
            </div>

            <button type="submit" disabled={loading || !form.project_id || !form.profile_id}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700
                         disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors">
              {loading ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Layers className="w-4 h-4" />}
              {loading ? "Menghitung..." : "Hitung Sekarang"}
            </button>
          </form>
        </div>

        {/* Results */}
        <div className="engineering-card p-6">
          <h3 className="section-title">Hasil Perhitungan</h3>

          {!result && (
            <div className="flex flex-col items-center justify-center h-64 text-slate-300">
              <Layers className="w-16 h-16 mb-4 opacity-40" />
              <p className="text-sm">Isi form dan tekan Hitung</p>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Status */}
              <div className={`flex items-center justify-between p-4 rounded-lg border ${statusBg(result.status)}`}>
                <div className="flex items-center gap-2">
                  {result.status === "AMAN" ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
                  <span className="font-bold text-lg">{result.status}</span>
                </div>
                <span className="text-sm font-mono font-semibold">Mu/φMn = {F(result.capacity_ratio)}</span>
              </div>

              <ResultSection title="Profil yang Digunakan">
                <ResultRow label="Profil" value={result.profile_designation} unit="-" formula="Dari database" />
                <ResultRow label="Zx" value={F(result.zx, 1)} unit="cm³" formula="Plastic section modulus" />
                <ResultRow label="Berat" value={F(result.weight_per_m, 1)} unit="kg/m" formula="Unit weight" />
              </ResultSection>

              <ResultSection title="Beban (SNI 1727:2020)">
                <ResultRow label="wu = 1.2(D+SW)+1.6L" value={F(result.wu)} unit="kN/m" formula="Termasuk berat sendiri" />
                <ResultRow label="Mu = wu·L²/8" value={F(result.mu_ultimate)} unit="kN·m" formula="Bentang sederhana" />
              </ResultSection>

              <ResultSection title="Cek Kelangsingan (SNI 1729:2020 Tabel B4.1b)">
                <ResultRow label="λ_f = (b/2)/tf" value={F(result.lambda_f)} unit="-" formula="Sayap" />
                <ResultRow label="λ_pf = 0.38√(E/Fy)" value={F(result.lambda_pf)} unit="-" formula="Batas kompak" />
                <ResultRow label="Penampang" value={result.is_compact ? "KOMPAK" : "TIDAK KOMPAK"} unit="-"
                  formula={result.is_compact ? "λ_f ≤ λ_pf ✓" : "λ_f > λ_pf ✗"} highlight={result.is_compact} />
              </ResultSection>

              <ResultSection title="Kapasitas Lentur (SNI 1729:2020 Pasal F2)">
                <ResultRow label="Mp = Fy·Zx" value={F(result.mp)} unit="kN·m" formula="Momen plastis" />
                <ResultRow label="φMn = φ·Mp" value={F(result.phi_mn)} unit="kN·m" formula="φ = 0.90, Lb ≤ Lp" highlight />
                <ResultRow label="Mu/φMn" value={F(result.capacity_ratio)}
                  unit="-" formula={result.capacity_ratio <= 1 ? "≤ 1.0 ✓" : "> 1.0 ✗"} />
              </ResultSection>

              {calcId && (
                <button
                  onClick={async () => {
                    setPdfLoading(true);
                    try {
                      await calcApi.downloadPdf(calcId, `AG-SAS_baja_${calcId}.pdf`);
                    } finally {
                      setPdfLoading(false);
                    }
                  }}
                  disabled={pdfLoading}
                  className="flex items-center justify-center gap-2 w-full border border-brand-300 text-brand-600 hover:bg-brand-50 disabled:opacity-50 font-semibold py-2.5 rounded-lg transition-colors text-sm"
                >
                  {pdfLoading
                    ? <span className="w-4 h-4 border-2 border-brand-400/30 border-t-brand-600 rounded-full animate-spin" />
                    : <Download className="w-4 h-4" />}
                  {pdfLoading ? "Menyiapkan PDF..." : "Download Laporan PDF"}
                </button>
              )}

              <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
                <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-700">{result.disclaimer}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SteelPage() {
  return (
    <Suspense fallback={null}>
      <SteelCalculator />
    </Suspense>
  );
}

function InputNum({ label, unit, value, onChange, min, max, step = 1 }: {
  label: string; unit: string; value: number;
  onChange: (v: number) => void; min?: number; max?: number; step?: number;
}) {
  return (
    <div>
      <label className="engineering-label">{label}</label>
      <div className="relative">
        <input type="number" step={step} min={min} max={max}
          className="engineering-input pr-12"
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)} />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs font-mono">{unit}</span>
      </div>
    </div>
  );
}

function ResultSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">{title}</p>
      <div className="border border-slate-200 rounded-lg overflow-hidden divide-y divide-slate-100">{children}</div>
    </div>
  );
}

function ResultRow({ label, value, unit, formula, highlight }: {
  label: string; value: string; unit: string; formula: string; highlight?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between px-4 py-2.5 ${highlight ? "bg-brand-50" : "bg-white"}`}>
      <div className="flex-1">
        <span className={`text-sm font-mono ${highlight ? "font-bold text-brand-700" : "text-slate-700"}`}>{label}</span>
        <span className="text-xs text-slate-400 ml-2">— {formula}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className={`text-sm font-bold font-mono ${highlight ? "text-brand-700" : "text-slate-900"}`}>{value}</span>
        <span className="text-xs text-slate-400 font-mono w-12 text-right">{unit}</span>
      </div>
    </div>
  );
}
