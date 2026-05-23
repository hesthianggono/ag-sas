"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Calculator, CheckCircle, XCircle, FileText, AlertTriangle, Download } from "lucide-react";
import { calcApi, projectsApi } from "@/lib/api";
import { formatNumber, statusBg } from "@/lib/utils";
import type { Project, ConcreteBeamInput } from "@/types";

function ConcreteCalculator() {
  const searchParams = useSearchParams();
  const preProjectId = searchParams.get("project_id");

  const [projects, setProjects] = useState<Project[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [calcId, setCalcId] = useState<number | null>(null);

  const [form, setForm] = useState<ConcreteBeamInput>({
    project_id: preProjectId ? +preProjectId : 0,
    title: "Balok Beton B1",
    width_b_mm: 300, height_h_mm: 600, cover_cc_mm: 40,
    bar_diameter_mm: 19, stirrup_diameter_mm: 10,
    fc_prime_mpa: 25, fy_mpa: 400,
    span_l_m: 6.0, dead_load_w_knm: 20, live_load_w_knm: 15,
    notes: "",
  });

  useEffect(() => {
    projectsApi.list().then(({ data }) => {
      setProjects(data);
      if (!form.project_id && data.length > 0) setForm(f => ({ ...f, project_id: data[0].id }));
    });
  }, []);

  async function handleCalculate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const { data } = await calcApi.concreteBeam(form);
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
          <Calculator className="w-6 h-6" />
          Kalkulator Balok Beton Bertulang
        </h1>
        <p className="text-slate-500 text-sm mt-1">SNI 2847:2019 — Desain lentur, metode kekuatan (LRFD)</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="engineering-card p-6">
          <form onSubmit={handleCalculate} className="space-y-5">
            {/* Meta */}
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

            {/* Dimensi */}
            <div>
              <h3 className="section-title">Dimensi Balok</h3>
              <div className="grid grid-cols-2 gap-4">
                <InputNum label="Lebar b" unit="mm" value={form.width_b_mm}
                  onChange={v => setForm({ ...form, width_b_mm: v })} min={100} max={2000} />
                <InputNum label="Tinggi h" unit="mm" value={form.height_h_mm}
                  onChange={v => setForm({ ...form, height_h_mm: v })} min={100} max={3000} />
                <InputNum label="Selimut Beton cc" unit="mm" value={form.cover_cc_mm}
                  onChange={v => setForm({ ...form, cover_cc_mm: v })} min={20} max={100} />
                <InputNum label="Ø Tulangan Utama" unit="mm" value={form.bar_diameter_mm}
                  onChange={v => setForm({ ...form, bar_diameter_mm: v })} min={8} max={40} />
                <InputNum label="Ø Sengkang" unit="mm" value={form.stirrup_diameter_mm}
                  onChange={v => setForm({ ...form, stirrup_diameter_mm: v })} min={6} max={16} />
              </div>
            </div>

            {/* Material */}
            <div>
              <h3 className="section-title">Material</h3>
              <div className="grid grid-cols-2 gap-4">
                <InputNum label="Mutu Beton fc'" unit="MPa" value={form.fc_prime_mpa}
                  onChange={v => setForm({ ...form, fc_prime_mpa: v })} min={17} max={70} step={1} />
                <InputNum label="Mutu Baja fy" unit="MPa" value={form.fy_mpa}
                  onChange={v => setForm({ ...form, fy_mpa: v })} min={240} max={500} step={10} />
              </div>
            </div>

            {/* Beban */}
            <div>
              <h3 className="section-title">Beban & Geometri</h3>
              <div className="grid grid-cols-2 gap-4">
                <InputNum label="Panjang Bentang L" unit="m" value={form.span_l_m}
                  onChange={v => setForm({ ...form, span_l_m: v })} min={1} max={30} step={0.1} />
                <InputNum label="Beban Mati wD" unit="kN/m" value={form.dead_load_w_knm}
                  onChange={v => setForm({ ...form, dead_load_w_knm: v })} min={0} step={0.5} />
                <InputNum label="Beban Hidup wL" unit="kN/m" value={form.live_load_w_knm}
                  onChange={v => setForm({ ...form, live_load_w_knm: v })} min={0} step={0.5} />
              </div>
            </div>

            <button type="submit" disabled={loading || !form.project_id}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700
                         disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors">
              {loading ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Calculator className="w-4 h-4" />}
              {loading ? "Menghitung..." : "Hitung Sekarang"}
            </button>
          </form>
        </div>

        {/* Results */}
        <div className="engineering-card p-6">
          <h3 className="section-title">Hasil Perhitungan</h3>

          {!result && (
            <div className="flex flex-col items-center justify-center h-64 text-slate-300">
              <Calculator className="w-16 h-16 mb-4 opacity-40" />
              <p className="text-sm">Isi form dan tekan Hitung</p>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Status Banner */}
              <div className={`flex items-center justify-between p-4 rounded-lg border ${statusBg(result.status)}`}>
                <div className="flex items-center gap-2">
                  {result.status === "AMAN"
                    ? <CheckCircle className="w-5 h-5" />
                    : <XCircle className="w-5 h-5" />}
                  <span className="font-bold text-lg">{result.status}</span>
                </div>
                <span className="text-sm font-mono font-semibold">
                  Mu/φMn = {F(result.capacity_ratio)}
                </span>
              </div>

              {/* Beban Terfaktor */}
              <ResultSection title="Beban Terfaktor (SNI 1727:2020)">
                <ResultRow label="wu = 1.2D + 1.6L" value={F(result.wu)} unit="kN/m" formula="Kombinasi LRFD" />
                <ResultRow label="Mu = wu·L²/8" value={F(result.mu_ultimate)} unit="kN·m" formula="Bentang sederhana" />
                <ResultRow label="Vu = wu·L/2" value={F(result.vu_ultimate)} unit="kN" formula="Geser maksimum" />
              </ResultSection>

              {/* Tulangan */}
              <ResultSection title="Kebutuhan Tulangan (SNI 2847:2019)">
                <ResultRow label="d efektif" value={F(result.effective_depth_d)} unit="mm" formula="h - cc - Øs - Ø/2" />
                <ResultRow label="ρ_min" value={F(result.rho_min, 5)} unit="-" formula="max(0.25√fc'/fy, 1.4/fy)" />
                <ResultRow label="ρ_max (0.75ρb)" value={F(result.rho_max, 5)} unit="-" formula="Pasal 9.3" />
                <ResultRow label="As required" value={F(result.as_required, 1)} unit="mm²" formula="ρ·b·d" />
                <ResultRow label="As design" value={F(result.as_design, 1)} unit="mm²"
                  formula={`${result.num_bars} batang Ø${form.bar_diameter_mm}`} highlight />
              </ResultSection>

              {/* Kapasitas */}
              <ResultSection title="Kapasitas Penampang">
                <ResultRow label="φ (lentur)" value={F(result.phi_factor)} unit="-" formula="Tabel 21.2.1" />
                <ResultRow label="φMn" value={F(result.phi_mn)} unit="kN·m" formula="φ·As·fy·(d-a/2)" highlight />
                <ResultRow label="Mu/φMn" value={F(result.capacity_ratio)} unit="-"
                  formula={result.capacity_ratio <= 1 ? "≤ 1.0 ✓" : "> 1.0 ✗"} />
              </ResultSection>

              {/* PDF */}
              {calcId && (
                <button
                  onClick={async () => {
                    setPdfLoading(true);
                    try {
                      await calcApi.downloadPdf(calcId, `AG-SAS_beton_${calcId}.pdf`);
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

              {/* Mini Disclaimer */}
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

export default function ConcretePage() {
  return (
    <Suspense fallback={null}>
      <ConcreteCalculator />
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
          className="engineering-input pr-10"
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
      <div className="border border-slate-200 rounded-lg overflow-hidden divide-y divide-slate-100">
        {children}
      </div>
    </div>
  );
}

function ResultRow({ label, value, unit, formula, highlight }: {
  label: string; value: string; unit: string; formula: string; highlight?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between px-4 py-2.5 ${highlight ? "bg-brand-50" : "bg-white"}`}>
      <div className="flex-1">
        <span className={`text-sm font-mono ${highlight ? "font-bold text-brand-700" : "text-slate-700"}`}>
          {label}
        </span>
        <span className="text-xs text-slate-400 ml-2">— {formula}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className={`text-sm font-bold font-mono ${highlight ? "text-brand-700" : "text-slate-900"}`}>
          {value}
        </span>
        <span className="text-xs text-slate-400 font-mono w-10 text-right">{unit}</span>
      </div>
    </div>
  );
}
