"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  Eye, EyeOff, LogIn, UserPlus,
  CheckCircle2, Sun, Moon,
  Calculator, FileText, Building2, BarChart3, Layers,
} from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { authApi } from "@/lib/api";

const HIGHLIGHTS = [
  { icon: Calculator,   text: "Balok Beton SNI 2847:2019" },
  { icon: Building2,    text: "Balok Baja SNI 1729:2020"  },
  { icon: BarChart3,    text: "7 Gambar Teknik Otomatis"  },
  { icon: FileText,     text: "Laporan PDF 10 Bab"        },
  { icon: Layers,       text: "Multi Proyek & Riwayat"    },
  { icon: CheckCircle2, text: "Referensi Pasal SNI"       },
];

// ── Login Form ────────────────────────────────────────────────────────────────
function LoginForm({ onSwitch }: { onSwitch: () => void }) {
  const router   = useRouter();
  const setAuth  = useAuthStore((s) => s.setAuth);
  const [form,   setForm]   = useState({ email: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [error,  setError]  = useState("");
  const [loading,setLoading]= useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const { data } = await authApi.login(form);
      setAuth({ id: data.user_id, email: data.email, full_name: data.full_name }, data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login gagal. Periksa email dan password.");
    } finally { setLoading(false); }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700
                        text-red-700 dark:text-red-300 text-xs px-3 py-2.5 rounded-lg">
          {error}
        </div>
      )}
      <div>
        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Email</label>
        <input
          type="email" required
          placeholder="engineer@example.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-600
                     bg-white dark:bg-slate-700/60 text-slate-800 dark:text-white
                     placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#2563eb]/40
                     focus:border-[#2563eb] transition"
        />
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Password</label>
        <div className="relative">
          <input
            type={showPw ? "text" : "password"} required
            placeholder="••••••••"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full px-3 py-2.5 pr-10 text-sm rounded-lg border border-slate-200 dark:border-slate-600
                       bg-white dark:bg-slate-700/60 text-slate-800 dark:text-white
                       placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#2563eb]/40
                       focus:border-[#2563eb] transition"
          />
          <button type="button" onClick={() => setShowPw(!showPw)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
            {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>
      <button type="submit" disabled={loading}
        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-semibold text-sm
                   bg-[#1e3a5f] dark:bg-[#2563eb] hover:bg-[#2563eb] text-white
                   disabled:opacity-50 transition-colors shadow">
        {loading
          ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          : <LogIn className="w-4 h-4" />}
        {loading ? "Memproses..." : "Masuk"}
      </button>
      <p className="text-center text-xs text-slate-500 dark:text-slate-400 pt-1">
        Belum punya akun?{" "}
        <button type="button" onClick={onSwitch}
          className="text-[#2563eb] font-semibold hover:underline">
          Daftar sekarang
        </button>
      </p>
    </form>
  );
}

// ── Register Form ─────────────────────────────────────────────────────────────
function RegisterForm({ onSwitch }: { onSwitch: () => void }) {
  const router   = useRouter();
  const setAuth  = useAuthStore((s) => s.setAuth);
  const [form,   setForm]   = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [error,  setError]  = useState("");
  const [loading,setLoading]= useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) { setError("Password tidak cocok"); return; }
    if (form.password.length < 8)       { setError("Password minimal 8 karakter"); return; }
    setLoading(true);
    try {
      const { data } = await authApi.register({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
      });
      setAuth({ id: data.user_id, email: data.email, full_name: data.full_name }, data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Pendaftaran gagal.");
    } finally { setLoading(false); }
  }

  const inp = "w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-600 " +
              "bg-white dark:bg-slate-700/60 text-slate-800 dark:text-white " +
              "placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#2563eb]/40 " +
              "focus:border-[#2563eb] transition";

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700
                        text-red-700 dark:text-red-300 text-xs px-3 py-2 rounded-lg">
          {error}
        </div>
      )}
      <div>
        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Nama Lengkap</label>
        <input type="text" required placeholder="Ir. Budi Santoso, M.T."
          value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          className={inp} />
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Email</label>
        <input type="email" required placeholder="engineer@example.com"
          value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
          className={inp} />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Password</label>
          <input type="password" required placeholder="Min. 8 karakter"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
            className={inp} />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Konfirmasi</label>
          <input type="password" required placeholder="Ulangi password"
            value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })}
            className={inp} />
        </div>
      </div>
      <button type="submit" disabled={loading}
        className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-semibold text-sm
                   bg-[#1e3a5f] dark:bg-[#2563eb] hover:bg-[#2563eb] text-white
                   disabled:opacity-50 transition-colors shadow mt-1">
        {loading
          ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          : <UserPlus className="w-4 h-4" />}
        {loading ? "Mendaftar..." : "Buat Akun — Gratis"}
      </button>
      <p className="text-center text-xs text-slate-500 dark:text-slate-400">
        Sudah punya akun?{" "}
        <button type="button" onClick={onSwitch}
          className="text-[#2563eb] font-semibold hover:underline">
          Masuk
        </button>
      </p>
    </form>
  );
}

// ── Main Landing Page ─────────────────────────────────────────────────────────
export default function LandingPage() {
  const [dark,    setDark]  = useState(false);
  const [tab,     setTab]   = useState<"login" | "register">("login");

  return (
    <div className={dark ? "dark" : ""}>
      <div className="h-screen flex flex-col overflow-hidden
                      bg-gradient-to-br from-[#dbeafe] via-[#e4f0fd] to-[#fef9c3]
                      dark:from-[#0c1426] dark:via-[#0f1f3d] dark:to-[#0c1426]
                      transition-colors duration-300">

        {/* ── NAVBAR ─────────────────────────────────────────────────── */}
        <nav className="flex-none h-14 flex items-center px-8
                        bg-white/50 dark:bg-slate-900/50 backdrop-blur-md
                        border-b border-white/40 dark:border-slate-700/40">
          <div className="relative h-9 w-36">
            <Image src="/logo-agsas.png" alt="AG-SAS" fill priority
              className="object-contain object-left" />
          </div>
          <div className="flex-1" />
          <button onClick={() => setDark(!dark)}
            className="p-2 rounded-full bg-slate-100 dark:bg-slate-700
                       hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            title={dark ? "Mode Terang" : "Mode Gelap"}>
            {dark ? <Sun className="w-4 h-4 text-yellow-400" /> : <Moon className="w-4 h-4 text-slate-500" />}
          </button>
        </nav>

        {/* ── BODY ───────────────────────────────────────────────────── */}
        <main className="flex-1 flex items-center overflow-hidden relative">

          {/* Blob dekorasi */}
          <div className="absolute top-0 right-0 w-[600px] h-[600px]
                          bg-[#2563eb]/15 dark:bg-[#2563eb]/8 rounded-full blur-3xl
                          -translate-y-1/3 translate-x-1/4 pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px]
                          bg-[#fbbf24]/20 dark:bg-[#fbbf24]/5 rounded-full blur-3xl
                          translate-y-1/3 -translate-x-1/4 pointer-events-none" />

          <div className="relative w-full max-w-6xl mx-auto px-8
                          grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

            {/* ── KIRI: Branding ──────────────────────────────────────── */}
            <div className="flex flex-col gap-5">
              {/* Badge */}
              <div className="inline-flex w-fit items-center gap-2
                              bg-[#2563eb]/10 dark:bg-[#2563eb]/20
                              text-[#2563eb] dark:text-[#93c5fd]
                              border border-[#2563eb]/20 rounded-full px-4 py-1.5 text-xs font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2563eb] animate-pulse" />
                MVP v1.0 — Balok Beton &amp; Baja
              </div>

              {/* Heading */}
              <div>
                <h1 className="text-4xl xl:text-5xl font-bold text-[#1e3a5f] dark:text-white leading-tight">
                  Hitung Struktur<br />
                  <span className="text-[#2563eb]">Lebih Cepat,</span><br />
                  Lebih Tepat
                </h1>
                <p className="mt-4 text-slate-600 dark:text-slate-300 text-sm leading-relaxed max-w-md">
                  Platform perhitungan &amp; pelaporan struktur baja dan beton berbasis web
                  untuk engineer Indonesia. Laporan PDF profesional siap dalam hitungan detik.
                </p>
              </div>

              {/* Fitur highlight grid */}
              <div className="grid grid-cols-2 gap-2">
                {HIGHLIGHTS.map(({ icon: Icon, text }) => (
                  <div key={text}
                    className="flex items-center gap-2.5 bg-white/60 dark:bg-slate-800/50
                               backdrop-blur rounded-lg px-3 py-2
                               border border-white/60 dark:border-slate-700/40">
                    <Icon className="w-3.5 h-3.5 text-[#2563eb] dark:text-[#93c5fd] flex-shrink-0" />
                    <span className="text-xs font-medium text-slate-700 dark:text-slate-200">{text}</span>
                  </div>
                ))}
              </div>

              <p className="text-slate-400 dark:text-slate-500 text-[10px]">
                ⚠ Hasil perhitungan wajib diperiksa oleh Engineer Struktur berwenang
              </p>
            </div>

            {/* ── KANAN: Auth Card ─────────────────────────────────────── */}
            <div className="w-full max-w-sm mx-auto lg:ml-auto">
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl
                              rounded-2xl shadow-2xl border border-white/60 dark:border-slate-700
                              overflow-hidden">

                {/* Tab switcher */}
                <div className="grid grid-cols-2 border-b border-slate-200 dark:border-slate-700">
                  {(["login", "register"] as const).map((t) => (
                    <button key={t} onClick={() => setTab(t)}
                      className={`py-3 text-sm font-semibold transition-colors
                        ${tab === t
                          ? "text-[#1e3a5f] dark:text-white border-b-2 border-[#2563eb] bg-white/60 dark:bg-slate-700/40"
                          : "text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
                        }`}>
                      {t === "login" ? "Masuk" : "Daftar Gratis"}
                    </button>
                  ))}
                </div>

                {/* Form body */}
                <div className="p-6">
                  {tab === "login"
                    ? <LoginForm    onSwitch={() => setTab("register")} />
                    : <RegisterForm onSwitch={() => setTab("login")}    />}
                </div>
              </div>

              <p className="text-center text-[10px] text-slate-400 dark:text-slate-500 mt-3">
                Gratis selama masa pengembangan · Tanpa kartu kredit
              </p>
            </div>

          </div>
        </main>

        {/* ── FOOTER ─────────────────────────────────────────────────── */}
        <footer className="flex-none h-11 flex items-center px-8
                           bg-white/40 dark:bg-slate-900/40 backdrop-blur-md
                           border-t border-white/40 dark:border-slate-700/40">
          <div className="flex items-center gap-2">
            <div className="relative h-6 w-24">
              <Image src="/logo-anggono.png" alt="Anggono Group" fill
                className="object-contain object-left" />
            </div>
            <span className="text-slate-400 dark:text-slate-500 text-xs hidden sm:inline">
              © 2025 Anggono Group
            </span>
          </div>
          <div className="flex-1" />
          <p className="text-slate-400 dark:text-slate-500 text-[10px] hidden md:block">
            Hak cipta SNI adalah milik BSN · Referensi pasal hanya sebagai indeks
          </p>
          <div className="flex-1" />
          <p className="text-slate-400 dark:text-slate-500 text-xs">AG-SAS v1.0</p>
        </footer>

      </div>
    </div>
  );
}
