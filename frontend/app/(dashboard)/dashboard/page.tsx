"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderOpen, Calculator, Layers, ChevronRight, TrendingUp, Clock } from "lucide-react";
import { projectsApi } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { formatDate, statusBg } from "@/lib/utils";
import type { Project } from "@/types";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    projectsApi.list().then(({ data }) => setProjects(data)).catch(() => {});
  }, []);

  const recentProjects = projects.slice(0, 5);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy">
          Selamat datang, {user?.full_name?.split(" ")[0]} 👋
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          AG Structural Analysis Suite — Perhitungan struktur berbasis SNI Indonesia
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <StatCard
          icon={FolderOpen}
          label="Total Proyek"
          value={projects.length}
          color="blue"
          href="/projects"
        />
        <StatCard
          icon={Calculator}
          label="Kalkulator Beton"
          value="SNI 2847:2019"
          color="green"
          href="/concrete"
          subtitle="Balok lentur"
        />
        <StatCard
          icon={Layers}
          label="Kalkulator Baja"
          value="SNI 1729:2020"
          color="purple"
          href="/steel"
          subtitle="Balok WF LRFD"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="engineering-card p-6">
          <h2 className="section-title">Aksi Cepat</h2>
          <div className="space-y-3">
            <QuickAction
              href="/projects"
              label="Buat Proyek Baru"
              desc="Mulai proyek perhitungan struktur baru"
              icon={FolderOpen}
            />
            <QuickAction
              href="/concrete"
              label="Hitung Balok Beton"
              desc="Desain lentur SNI 2847:2019"
              icon={Calculator}
            />
            <QuickAction
              href="/steel"
              label="Hitung Balok Baja WF"
              desc="Desain LRFD SNI 1729:2020"
              icon={Layers}
            />
          </div>
        </div>

        <div className="engineering-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0 border-b-0 pb-0">Proyek Terbaru</h2>
            <Link href="/projects" className="text-xs text-brand-600 hover:underline flex items-center gap-1">
              Lihat semua <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          {recentProjects.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              <FolderOpen className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Belum ada proyek</p>
              <Link href="/projects" className="text-xs text-brand-600 hover:underline mt-1 block">
                Buat proyek pertama →
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {recentProjects.map((p) => (
                <Link
                  key={p.id}
                  href={`/projects/${p.id}`}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-all"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">{p.name}</p>
                    <p className="text-xs text-slate-400">{p.location} · {formatDate(p.created_at)}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-300" />
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-xs text-amber-700 font-medium">
          ⚠ DISCLAIMER: Semua hasil perhitungan yang dihasilkan AG-SAS bersifat indikatif dan
          WAJIB diperiksa ulang oleh Engineer Struktur berwenang (Ahli K3 Konstruksi / Insinyur
          Profesional) sebelum digunakan dalam dokumen desain resmi.
        </p>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color, href, subtitle }: {
  icon: any; label: string; value: string | number; color: string;
  href: string; subtitle?: string;
}) {
  const colors: Record<string, string> = {
    blue: "bg-brand-50 text-brand-600",
    green: "bg-green-50 text-green-600",
    purple: "bg-purple-50 text-purple-600",
  };
  return (
    <Link href={href} className="engineering-card p-5 hover:border-brand-300 transition-colors group">
      <div className="flex items-start justify-between">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-brand-400 transition-colors" />
      </div>
      <p className="text-2xl font-bold text-slate-900 mt-3">{value}</p>
      <p className="text-sm font-medium text-slate-600">{label}</p>
      {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
    </Link>
  );
}

function QuickAction({ href, label, desc, icon: Icon }: {
  href: string; label: string; desc: string; icon: any;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-4 p-3 rounded-lg hover:bg-brand-50 border border-transparent hover:border-brand-200 transition-all group"
    >
      <div className="w-8 h-8 bg-slate-100 rounded-md flex items-center justify-center group-hover:bg-brand-100">
        <Icon className="w-4 h-4 text-slate-500 group-hover:text-brand-600" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-semibold text-slate-900">{label}</p>
        <p className="text-xs text-slate-400">{desc}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-brand-400" />
    </Link>
  );
}
