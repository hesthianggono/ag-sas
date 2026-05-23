"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Calculator, FileText, ChevronRight,
  Sun, Moon, Building2, BarChart3, Layers,
  CheckCircle2,
} from "lucide-react";

const FEATURES = [
  { icon: Calculator,  title: "Balok Beton",   desc: "Desain lentur & geser SNI 2847:2019, φMn & φVn" },
  { icon: Building2,   title: "Balok Baja",    desc: "Desain LRFD SNI 1729:2020, profil WF/H-Beam" },
  { icon: BarChart3,   title: "Gambar Teknik", desc: "7 diagram otomatis: M(x), V(x), deformasi, utilisasi" },
  { icon: FileText,    title: "Laporan PDF",   desc: "10 bab lengkap, cover proyek, daftar isi otomatis" },
  { icon: Layers,      title: "Multi Proyek",  desc: "Kelola banyak proyek & perhitungan sekaligus" },
  { icon: CheckCircle2,title: "Standar SNI",   desc: "SNI 1727, 1729, 2847, 1726 — pasal tertelusur" },
];

export default function LandingPage() {
  const [dark, setDark] = useState(false);

  return (
    <div className={dark ? "dark" : ""}>
      {/* Satu viewport penuh, tidak scroll */}
      <div className="h-screen flex flex-col overflow-hidden
                      bg-gradient-to-br from-[#dbeafe] via-[#e8f4fd] to-[#fef9c3]
                      dark:from-[#0c1426] dark:via-[#0f1f3d] dark:to-[#0c1426]
                      transition-colors duration-300">

        {/* ── NAVBAR ───────────────────────────────────────────────── */}
        <nav className="flex-none h-16 flex items-center px-8
                        bg-white/60 dark:bg-slate-900/60 backdrop-blur-md
                        border-b border-white/40 dark:border-slate-700/40">

          {/* Logo AG-SAS kiri atas */}
          <div className="flex items-center">
            <div className="relative h-10 w-40">
              <Image
                src="/logo-agsas.png"
                alt="AG-SAS"
                fill
                priority
                className="object-contain object-left"
              />
            </div>
          </div>

          <div className="flex-1" />

          {/* Kanan: toggle + auth */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDark(!dark)}
              className="p-2 rounded-full bg-slate-100 dark:bg-slate-700
                         hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              title={dark ? "Mode Terang" : "Mode Gelap"}
            >
              {dark
                ? <Sun  className="w-4 h-4 text-yellow-400" />
                : <Moon className="w-4 h-4 text-slate-500"  />}
            </button>
            <Link
              href="/login"
              className="text-sm font-medium text-slate-600 dark:text-slate-300
                         hover:text-[#1e3a5f] dark:hover:text-white px-4 py-2"
            >
              Masuk
            </Link>
            <Link
              href="/register"
              className="text-sm font-semibold bg-[#1e3a5f] dark:bg-[#2563eb]
                         text-white px-5 py-2 rounded-lg
                         hover:bg-[#2563eb] transition-colors shadow"
            >
              Daftar Gratis
            </Link>
          </div>
        </nav>

        {/* ── HERO (mengisi sisa tinggi) ───────────────────────────── */}
        <main className="flex-1 flex items-center overflow-hidden relative">

          {/* Blob dekorasi */}
          <div className="absolute top-0 right-0 w-[500px] h-[500px]
                          bg-[#2563eb]/15 dark:bg-[#2563eb]/10 rounded-full blur-3xl -translate-y-1/4 translate-x-1/4" />
          <div className="absolute bottom-0 left-0 w-[380px] h-[380px]
                          bg-[#fbbf24]/20 dark:bg-[#fbbf24]/5 rounded-full blur-3xl translate-y-1/4 -translate-x-1/4" />

          <div className="relative w-full max-w-7xl mx-auto px-8
                          grid grid-cols-1 lg:grid-cols-5 gap-10 items-center">

            {/* ── KOLOM KIRI (3/5) ─────────────────────────────────── */}
            <div className="lg:col-span-3 flex flex-col gap-5">

              {/* Badge versi */}
              <div className="inline-flex w-fit items-center gap-2
                              bg-[#2563eb]/10 dark:bg-[#2563eb]/20
                              text-[#2563eb] dark:text-[#93c5fd]
                              border border-[#2563eb]/20 rounded-full
                              px-4 py-1.5 text-xs font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2563eb] animate-pulse" />
                MVP v1.0 — Balok Beton &amp; Baja
              </div>

              {/* Heading */}
              <h1 className="text-4xl xl:text-5xl font-bold
                             text-[#1e3a5f] dark:text-white leading-tight">
                Hitung Struktur
                <br />
                <span className="text-[#2563eb]">Lebih Cepat,</span>
                <br />
                Lebih Tepat
              </h1>

              {/* Deskripsi singkat */}
              <p className="text-slate-600 dark:text-slate-300 text-sm max-w-xl leading-relaxed">
                Platform perhitungan &amp; pelaporan struktur baja dan beton berbasis web
                untuk engineer Indonesia. Mengacu standar SNI, laporan PDF profesional
                siap dalam hitungan detik.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-wrap gap-3">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2
                             bg-[#1e3a5f] dark:bg-[#2563eb] hover:bg-[#2563eb]
                             text-white font-semibold px-7 py-3 rounded-xl
                             transition-colors shadow-lg shadow-[#1e3a5f]/20"
                >
                  Mulai Sekarang
                  <ChevronRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2
                             border-2 border-[#1e3a5f]/25 dark:border-slate-600
                             hover:border-[#2563eb] text-[#1e3a5f] dark:text-white
                             font-medium px-7 py-3 rounded-xl transition-colors"
                >
                  Sudah punya akun?
                </Link>
              </div>

              {/* Fitur grid kecil */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-1">
                {FEATURES.map(({ icon: Icon, title, desc }) => (
                  <div
                    key={title}
                    className="flex items-start gap-2 bg-white/60 dark:bg-slate-800/60
                               backdrop-blur rounded-xl p-3
                               border border-white/60 dark:border-slate-700/40
                               hover:border-[#2563eb]/40 transition-colors"
                  >
                    <div className="w-7 h-7 rounded-lg bg-[#dbeafe] dark:bg-[#1e3a5f]
                                    flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Icon className="w-3.5 h-3.5 text-[#2563eb] dark:text-[#93c5fd]" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-[#1e3a5f] dark:text-white">{title}</p>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-snug mt-0.5">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-slate-400 dark:text-slate-500 text-[10px]">
                ⚠ Hasil perhitungan wajib diperiksa oleh Engineer Struktur berwenang
              </p>
            </div>

            {/* ── KOLOM KANAN (2/5): Card preview ─────────────────── */}
            <div className="hidden lg:block lg:col-span-2">
              <div className="relative">
                {/* Badge atas */}
                <div className="absolute -top-4 -right-4 z-10
                                bg-[#fbbf24] text-[#1e3a5f] text-xs font-bold
                                px-3 py-1.5 rounded-full shadow-lg">
                  PDF Otomatis ✨
                </div>

                {/* Card utama */}
                <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md
                                rounded-2xl shadow-2xl p-6
                                border border-white/60 dark:border-slate-700">

                  <div className="flex items-center gap-3 mb-5">
                    <div className="w-9 h-9 bg-[#1e3a5f] dark:bg-[#2563eb]
                                    rounded-xl flex items-center justify-center">
                      <Calculator className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-[#1e3a5f] dark:text-white text-sm">
                        Balok B-1 — Lantai 3
                      </p>
                      <p className="text-xs text-slate-400">SNI 2847:2019 · LRFD</p>
                    </div>
                    <span className="ml-auto text-xs font-bold text-green-600
                                     bg-green-50 dark:bg-green-900/30
                                     px-2 py-1 rounded-full">
                      ✓ OK
                    </span>
                  </div>

                  {[
                    { label: "Mu",   val: "97.2 kN·m",  cap: "φMn = 110.5 kN·m" },
                    { label: "Vu",   val: "64.8 kN",    cap: "φVn = 84.0 kN"    },
                    { label: "δmax", val: "12.5 mm",    cap: "δizin = 16.7 mm"  },
                  ].map((r) => (
                    <div
                      key={r.label}
                      className="flex items-center justify-between py-2.5
                                 border-b border-slate-100 dark:border-slate-700 last:border-0"
                    >
                      <span className="text-xs font-mono text-[#2563eb] font-bold w-10">{r.label}</span>
                      <span className="text-sm font-semibold text-slate-800 dark:text-white">{r.val}</span>
                      <span className="text-xs text-slate-400">{r.cap}</span>
                    </div>
                  ))}

                  <button className="mt-5 w-full bg-[#1e3a5f] dark:bg-[#2563eb] text-white
                                     text-sm font-semibold py-2.5 rounded-xl
                                     hover:bg-[#2563eb] transition-colors">
                    Download Laporan PDF
                  </button>
                </div>

                {/* Badge bawah */}
                <div className="absolute -bottom-4 -left-4
                                bg-white dark:bg-slate-800
                                border border-slate-200 dark:border-slate-700
                                text-xs font-medium px-3 py-1.5 rounded-full
                                shadow-lg text-slate-600 dark:text-slate-300">
                  🏗 7 Gambar Teknik
                </div>
              </div>
            </div>

          </div>
        </main>

        {/* ── FOOTER ───────────────────────────────────────────────── */}
        <footer className="flex-none h-12 flex items-center px-8
                           bg-white/50 dark:bg-slate-900/50 backdrop-blur-md
                           border-t border-white/40 dark:border-slate-700/40">

          {/* Logo Anggono Group kiri bawah */}
          <div className="flex items-center gap-2">
            <div className="relative h-7 w-28">
              <Image
                src="/logo-anggono.png"
                alt="Anggono Group"
                fill
                className="object-contain object-left"
              />
            </div>
            <span className="text-slate-400 dark:text-slate-500 text-xs hidden sm:inline">
              © 2025 Anggono Group
            </span>
          </div>

          <div className="flex-1" />

          <p className="text-slate-400 dark:text-slate-500 text-xs text-center hidden md:block">
            Hak cipta SNI adalah milik BSN · Referensi pasal hanya sebagai indeks
          </p>

          <div className="flex-1" />

          <p className="text-slate-400 dark:text-slate-500 text-xs">AG-SAS v1.0</p>
        </footer>

      </div>
    </div>
  );
}
