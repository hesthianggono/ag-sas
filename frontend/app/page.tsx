"use client";
import Link from "next/link";
import { Building2, Calculator, FileText, Shield, ChevronRight, CheckCircle2 } from "lucide-react";

const STANDARDS = [
  { code: "SNI 1727:2020", title: "Beban Desain Minimum", scope: "Beban mati, hidup, angin" },
  { code: "SNI 1726:2019", title: "Ketahanan Gempa", scope: "Analisis seismik, respons spektrum" },
  { code: "SNI 2847:2019", title: "Beton Struktural", scope: "Balok, kolom, pelat beton" },
  { code: "SNI 1729:2020", title: "Baja Struktural", scope: "Desain elemen baja" },
  { code: "SNI 7860:2020", title: "Seismik Baja", scope: "Ketentuan seismik baja" },
  { code: "SNI 8369:2020", title: "Praktik Baku Baja", scope: "Fabrikasi dan ereksi" },
];

const FEATURES = [
  { icon: Calculator, title: "Kalkulator Balok Beton", desc: "Desain lentur SNI 2847:2019, tulangan perlu, cek kapasitas" },
  { icon: Building2, title: "Kalkulator Balok Baja", desc: "Desain LRFD SNI 1729:2020, cek kompak, WF/H-Beam" },
  { icon: FileText, title: "Laporan PDF Otomatis", desc: "Cover, data proyek, rumus, hasil, kesimpulan, disclaimer" },
  { icon: Shield, title: "Manajemen Proyek", desc: "CRUD proyek, riwayat perhitungan, export data" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── Navbar ── */}
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-navy rounded-md flex items-center justify-center">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-navy text-sm">AG-SAS</span>
              <span className="text-slate-400 text-xs ml-2 hidden sm:inline">
                AG Structural Analysis Suite
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-navy">
              Masuk
            </Link>
            <Link
              href="/register"
              className="text-sm font-semibold bg-navy text-white px-4 py-2 rounded-md hover:bg-navy-light transition-colors"
            >
              Daftar Gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative bg-navy overflow-hidden">
        <div
          className="absolute inset-0 bg-grid-pattern bg-grid-md opacity-20"
          style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px)" }}
        />
        <div className="relative max-w-7xl mx-auto px-6 py-24 text-center">
          <div className="inline-flex items-center gap-2 bg-brand-600/20 text-brand-200 border border-brand-500/30 rounded-full px-4 py-1.5 text-xs font-semibold mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
            MVP v1.0 — Balok Beton & Baja
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
            AG Structural
            <br />
            <span className="text-brand-400">Analysis Suite</span>
          </h1>
          <p className="text-slate-300 text-lg max-w-2xl mx-auto mb-10 leading-relaxed">
            Platform perhitungan dan pelaporan struktur baja &amp; beton berbasis web
            untuk engineer Indonesia. Mengacu pada standar SNI yang berlaku,
            dilengkapi laporan PDF profesional.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-8 py-3.5 rounded-lg transition-colors"
            >
              Mulai Sekarang
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 border border-slate-500 hover:border-slate-300 text-white font-medium px-8 py-3.5 rounded-lg transition-colors"
            >
              Sudah punya akun? Masuk
            </Link>
          </div>
          <p className="text-slate-500 text-xs mt-8">
            ⚠ Hasil perhitungan wajib diperiksa oleh Engineer Struktur berwenang
          </p>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-navy text-center mb-12">Fitur MVP v1.0</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="engineering-card p-6">
                <div className="w-10 h-10 bg-brand-50 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-brand-600" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-2">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Standards ── */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-navy text-center mb-4">
            Standar SNI yang Didukung
          </h2>
          <p className="text-slate-500 text-center mb-12 text-sm max-w-lg mx-auto">
            Referensi pasal dan rumus diketik manual oleh developer. Teks lengkap SNI tidak disalin.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {STANDARDS.map((s) => (
              <div
                key={s.code}
                className="engineering-card p-5 flex items-start gap-4 hover:border-brand-300 transition-colors"
              >
                <CheckCircle2 className="w-5 h-5 text-brand-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-bold text-navy text-sm">{s.code}</p>
                  <p className="text-slate-700 text-sm font-medium">{s.title}</p>
                  <p className="text-slate-400 text-xs mt-1">{s.scope}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-navy py-16 text-center">
        <h2 className="text-2xl font-bold text-white mb-4">Mulai Perhitungan Pertama Anda</h2>
        <p className="text-slate-400 mb-8 text-sm">Gratis selama masa pengembangan</p>
        <Link
          href="/register"
          className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-10 py-4 rounded-lg transition-colors text-lg"
        >
          Daftar Sekarang
          <ChevronRight className="w-5 h-5" />
        </Link>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-200 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-slate-400 text-xs">
            © 2024 AG Engineering · AG Structural Analysis Suite v1.0
          </p>
          <p className="text-slate-400 text-xs text-center">
            Hak cipta SNI adalah milik BSN. Referensi pasal hanya sebagai indeks.
          </p>
        </div>
      </footer>
    </div>
  );
}
