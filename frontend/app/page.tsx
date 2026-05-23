"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Calculator, FileText, Shield, ChevronRight,
  CheckCircle2, Sun, Moon, Building2,
  BarChart3, Layers, Award,
} from "lucide-react";

const FEATURES = [
  { icon: Calculator,  title: "Balok Beton",      desc: "Desain lentur & geser SNI 2847:2019, tulangan perlu, cek kapasitas φMn dan φVn" },
  { icon: Building2,   title: "Balok Baja",        desc: "Desain LRFD SNI 1729:2020, cek kompaktitas, profil WF/H-Beam" },
  { icon: BarChart3,   title: "Gambar Teknik",     desc: "7 gambar otomatis: model, beban, reaksi, V(x), M(x), deformasi, utilisasi" },
  { icon: FileText,    title: "Laporan PDF",        desc: "10 bab lengkap: pendahuluan, material, analisis, desain, gambar teknik" },
  { icon: Layers,      title: "Multi Proyek",       desc: "Kelola banyak proyek & perhitungan, riwayat tersimpan permanen" },
  { icon: Award,       title: "Standar SNI",        desc: "Mengacu SNI 1727, 1729, 2847, 1726 — referensi pasal tertelusur" },
];

const STANDARDS = [
  { code: "SNI 1727:2020", title: "Beban Desain Minimum",  scope: "Beban mati, hidup, angin" },
  { code: "SNI 1726:2019", title: "Ketahanan Gempa",       scope: "Analisis seismik, respons spektrum" },
  { code: "SNI 2847:2019", title: "Beton Struktural",      scope: "Balok, kolom, pelat beton" },
  { code: "SNI 1729:2020", title: "Baja Struktural",       scope: "Desain elemen baja" },
  { code: "SNI 7860:2020", title: "Seismik Baja",          scope: "Ketentuan seismik baja" },
  { code: "SNI 8369:2020", title: "Praktik Baku Baja",     scope: "Fabrikasi dan ereksi" },
];

export default function LandingPage() {
  const [dark, setDark] = useState(false);

  return (
    <div className={dark ? "dark" : ""}>
      <div className="min-h-screen bg-white dark:bg-slate-900 transition-colors duration-300">

        {/* ── NAVBAR ─────────────────────────────────────────────────────── */}
        <nav className="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-700">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

            {/* Logo kiri */}
            <div className="flex items-center gap-3">
              <div className="relative w-36 h-10">
                <Image
                  src="/logo-agsas.png"
                  alt="AG-SAS"
                  fill
                  className="object-contain object-left"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
              {/* Fallback teks jika logo belum ada */}
              <span className="font-bold text-[#1e3a5f] dark:text-white text-lg tracking-tight select-none">
                AG<span className="text-[#2563eb]">SAS</span>
              </span>
            </div>

            {/* Kanan: dark toggle + auth */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setDark(!dark)}
                className="p-2 rounded-full bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                title={dark ? "Mode Terang" : "Mode Gelap"}
              >
                {dark
                  ? <Sun  className="w-4 h-4 text-yellow-400" />
                  : <Moon className="w-4 h-4 text-slate-600"  />
                }
              </button>
              <Link
                href="/login"
                className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-[#1e3a5f] dark:hover:text-white px-3 py-2"
              >
                Masuk
              </Link>
              <Link
                href="/register"
                className="text-sm font-semibold bg-[#1e3a5f] dark:bg-[#2563eb] text-white px-5 py-2 rounded-lg hover:bg-[#2563eb] transition-colors"
              >
                Daftar Gratis
              </Link>
            </div>
          </div>
        </nav>

        {/* ── HERO ───────────────────────────────────────────────────────── */}
        <section className="relative min-h-[88vh] flex items-center overflow-hidden">

          {/* Gradient background mirip Growin */}
          <div className="absolute inset-0 bg-gradient-to-br from-[#dbeafe] via-[#e0f2fe] to-[#fef9c3] dark:from-[#0f172a] dark:via-[#1e3a5f] dark:to-[#0f172a]" />

          {/* Grid pattern tipis */}
          <div
            className="absolute inset-0 opacity-20 dark:opacity-10"
            style={{
              backgroundImage: "linear-gradient(rgba(30,58,95,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(30,58,95,0.15) 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />

          {/* Blob dekorasi */}
          <div className="absolute top-20 right-10 w-96 h-96 bg-[#2563eb]/20 dark:bg-[#2563eb]/10 rounded-full blur-3xl" />
          <div className="absolute bottom-10 left-20 w-72 h-72 bg-[#fbbf24]/20 dark:bg-[#fbbf24]/5 rounded-full blur-3xl" />

          <div className="relative max-w-7xl mx-auto px-6 py-20 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center w-full">

            {/* Kiri: teks */}
            <div>
              <div className="inline-flex items-center gap-2 bg-[#2563eb]/10 dark:bg-[#2563eb]/20 text-[#2563eb] dark:text-[#93c5fd] border border-[#2563eb]/20 rounded-full px-4 py-1.5 text-xs font-semibold mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2563eb] animate-pulse" />
                MVP v1.0 — Balok Beton &amp; Baja
              </div>

              <h1 className="text-4xl sm:text-5xl font-bold text-[#1e3a5f] dark:text-white leading-tight mb-6">
                Hitung Struktur
                <br />
                <span className="text-[#2563eb]">Lebih Cepat,</span>
                <br />
                Lebih Tepat
              </h1>

              <p className="text-slate-600 dark:text-slate-300 text-base max-w-lg mb-8 leading-relaxed">
                Platform perhitungan dan pelaporan struktur baja &amp; beton berbasis web
                untuk engineer Indonesia. Mengacu standar SNI, laporan PDF profesional
                siap dalam hitungan detik.
              </p>

              <div className="flex flex-col sm:flex-row gap-3 mb-8">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center gap-2 bg-[#1e3a5f] dark:bg-[#2563eb] hover:bg-[#2563eb] text-white font-semibold px-8 py-3.5 rounded-xl transition-colors shadow-lg shadow-[#1e3a5f]/20"
                >
                  Mulai Sekarang
                  <ChevronRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center gap-2 border-2 border-[#1e3a5f]/20 dark:border-slate-600 hover:border-[#2563eb] text-[#1e3a5f] dark:text-white font-medium px-8 py-3.5 rounded-xl transition-colors"
                >
                  Sudah punya akun? Masuk
                </Link>
              </div>

              <p className="text-slate-400 dark:text-slate-500 text-xs">
                ⚠ Hasil perhitungan wajib diperiksa oleh Engineer Struktur berwenang
              </p>
            </div>

            {/* Kanan: card preview */}
            <div className="hidden lg:flex justify-center">
              <div className="relative w-full max-w-md">
                {/* Card utama */}
                <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-2xl shadow-2xl p-6 border border-white/60 dark:border-slate-700">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-10 h-10 bg-[#1e3a5f] dark:bg-[#2563eb] rounded-xl flex items-center justify-center">
                      <Calculator className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-[#1e3a5f] dark:text-white text-sm">Balok B-1 — Lantai 3</p>
                      <p className="text-xs text-slate-400">SNI 2847:2019 · LRFD</p>
                    </div>
                    <span className="ml-auto text-xs font-bold text-green-600 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded-full">✓ OK</span>
                  </div>
                  {[
                    { label: "Mu",   val: "97.2 kN·m",  cap: "φMn = 110.5 kN·m" },
                    { label: "Vu",   val: "64.8 kN",    cap: "φVn = 84.0 kN"    },
                    { label: "δmax", val: "12.5 mm",    cap: "δizin = 16.7 mm"  },
                  ].map((r) => (
                    <div key={r.label} className="flex items-center justify-between py-2.5 border-b border-slate-100 dark:border-slate-700 last:border-0">
                      <span className="text-xs font-mono text-[#2563eb] font-bold w-10">{r.label}</span>
                      <span className="text-sm font-semibold text-slate-800 dark:text-white">{r.val}</span>
                      <span className="text-xs text-slate-400">{r.cap}</span>
                    </div>
                  ))}
                  <button className="mt-5 w-full bg-[#1e3a5f] dark:bg-[#2563eb] text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-[#2563eb] transition-colors">
                    Download Laporan PDF
                  </button>
                </div>

                {/* Badge mengambang */}
                <div className="absolute -top-4 -right-4 bg-[#fbbf24] text-[#1e3a5f] text-xs font-bold px-3 py-1.5 rounded-full shadow-lg">
                  PDF Otomatis ✨
                </div>
                <div className="absolute -bottom-4 -left-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium px-3 py-1.5 rounded-full shadow-lg text-slate-600 dark:text-slate-300">
                  🏗 7 Gambar Teknik
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── FEATURES ───────────────────────────────────────────────────── */}
        <section className="py-20 bg-slate-50 dark:bg-slate-800/50">
          <div className="max-w-7xl mx-auto px-6">
            <h2 className="text-2xl font-bold text-[#1e3a5f] dark:text-white text-center mb-3">Fitur Unggulan</h2>
            <p className="text-slate-500 dark:text-slate-400 text-center text-sm mb-12">Semua yang dibutuhkan engineer struktur dalam satu platform</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {FEATURES.map(({ icon: Icon, title, desc }) => (
                <div
                  key={title}
                  className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700 hover:border-[#2563eb]/40 hover:shadow-md transition-all"
                >
                  <div className="w-10 h-10 bg-[#dbeafe] dark:bg-[#1e3a5f] rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-[#2563eb] dark:text-[#93c5fd]" />
                  </div>
                  <h3 className="font-semibold text-[#1e3a5f] dark:text-white mb-2">{title}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── STANDARDS ──────────────────────────────────────────────────── */}
        <section className="py-20 bg-white dark:bg-slate-900">
          <div className="max-w-7xl mx-auto px-6">
            <h2 className="text-2xl font-bold text-[#1e3a5f] dark:text-white text-center mb-3">Standar SNI yang Didukung</h2>
            <p className="text-slate-500 dark:text-slate-400 text-center text-sm mb-12 max-w-lg mx-auto">
              Referensi pasal dan rumus diketik manual oleh developer. Teks lengkap SNI tidak disalin.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {STANDARDS.map((s) => (
                <div key={s.code} className="flex items-start gap-4 p-5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-[#2563eb]/40 transition-colors bg-white dark:bg-slate-800">
                  <CheckCircle2 className="w-5 h-5 text-[#2563eb] mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-bold text-[#1e3a5f] dark:text-white text-sm">{s.code}</p>
                    <p className="text-slate-700 dark:text-slate-300 text-sm font-medium">{s.title}</p>
                    <p className="text-slate-400 text-xs mt-1">{s.scope}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ────────────────────────────────────────────────────────── */}
        <section className="bg-gradient-to-r from-[#1e3a5f] to-[#2563eb] py-20 text-center relative overflow-hidden">
          <div className="absolute inset-0 opacity-10"
            style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)", backgroundSize: "40px 40px" }}
          />
          <div className="relative">
            <h2 className="text-3xl font-bold text-white mb-3">Mulai Perhitungan Pertama Anda</h2>
            <p className="text-blue-200 mb-8 text-sm">Gratis selama masa pengembangan · Tanpa kartu kredit</p>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 bg-white hover:bg-slate-50 text-[#1e3a5f] font-bold px-10 py-4 rounded-xl transition-colors text-base shadow-lg"
            >
              Daftar Sekarang
              <ChevronRight className="w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* ── FOOTER ─────────────────────────────────────────────────────── */}
        <footer className="border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 py-8">
          <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">

            {/* Logo Anggono Group kiri bawah */}
            <div className="flex items-center gap-3">
              <div className="relative w-32 h-10">
                <Image
                  src="/logo-anggono.png"
                  alt="Anggono Group"
                  fill
                  className="object-contain object-left"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
              <span className="text-slate-400 dark:text-slate-500 text-xs">
                © 2025 Anggono Group
              </span>
            </div>

            <p className="text-slate-400 dark:text-slate-500 text-xs text-center">
              Hak cipta SNI adalah milik BSN · Referensi pasal hanya sebagai indeks
            </p>

            {/* Versi kanan */}
            <p className="text-slate-400 dark:text-slate-500 text-xs">
              AG-SAS v1.0
            </p>
          </div>
        </footer>

      </div>
    </div>
  );
}
