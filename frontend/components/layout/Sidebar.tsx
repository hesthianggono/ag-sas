"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Building2, LayoutDashboard, FolderOpen,
  Columns, Layers, FileText, Box, LogOut, FlaskConical, Grid3x3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store";

const NAV = [
  { href: "/dashboard",     label: "Dashboard",    icon: LayoutDashboard },
  { href: "/projects",      label: "Proyek",       icon: FolderOpen },
  { href: "/concrete",      label: "Balok Beton",  icon: Columns },
  { href: "/steel",         label: "Balok Baja",   icon: Layers },
  { href: "/report",        label: "Laporan",      icon: FileText },
  { href: "/viewer3d",      label: "3D Viewer",    icon: Box,          badge: "Beta" },
  { href: "/frame2d",       label: "Portal 2D",    icon: Grid3x3,      badge: "FEM" },
  { href: "/verification",  label: "Verifikasi",   icon: FlaskConical, badge: "V&V" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-navy flex flex-col z-40">
      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-navy-light/30">
        <div className="w-8 h-8 bg-brand-600 rounded-md flex items-center justify-center">
          <Building2 className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-tight">AG-SAS</p>
          <p className="text-slate-400 text-xs">v1.0</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active
                  ? "bg-brand-600 text-white"
                  : "text-slate-300 hover:bg-navy-light/50 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {badge && (
                <span className="text-[10px] font-bold bg-brand-500/20 text-brand-300 px-1.5 py-0.5 rounded">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-navy-light/30">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-brand-600/20 rounded-full flex items-center justify-center text-brand-300 text-sm font-bold">
            {user?.full_name?.[0]?.toUpperCase() ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-xs font-semibold truncate">{user?.full_name}</p>
            <p className="text-slate-400 text-xs truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 text-slate-400 hover:text-white text-xs px-2 py-1.5 rounded hover:bg-navy-light/30 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Keluar
        </button>
      </div>
    </aside>
  );
}
