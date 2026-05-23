"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, FolderOpen, MapPin, User, ChevronRight, Trash2, Edit } from "lucide-react";
import { projectsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Project, ProjectCreate } from "@/types";

const DEFAULTS: ProjectCreate = {
  name: "", location: "", client_name: "", consultant_name: "",
  building_type: "Gedung Kantor", num_floors: 3,
  structural_system: "Rangka Momen Biasa", primary_material: "Beton Bertulang",
  applicable_standards: "SNI 1727:2020,SNI 1726:2019,SNI 2847:2019,SNI 1729:2020",
  description: "",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ProjectCreate>(DEFAULTS);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const { data } = await projectsApi.list();
    setProjects(data);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await projectsApi.create(form);
      setForm(DEFAULTS);
      setShowForm(false);
      load();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Hapus proyek ini?")) return;
    await projectsApi.delete(id);
    load();
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-navy">Proyek Struktur</h1>
          <p className="text-slate-500 text-sm">{projects.length} proyek aktif</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-navy hover:bg-navy-light text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" /> Proyek Baru
        </button>
      </div>

      {/* Project List */}
      {projects.length === 0 ? (
        <div className="engineering-card p-16 text-center">
          <FolderOpen className="w-14 h-14 text-slate-200 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-700 mb-2">Belum ada proyek</h3>
          <p className="text-slate-400 text-sm mb-6">Mulai dengan membuat proyek perhitungan struktur baru</p>
          <button onClick={() => setShowForm(true)} className="bg-navy text-white px-5 py-2.5 rounded-lg text-sm font-semibold">
            Buat Proyek Pertama
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {projects.map((p) => (
            <div key={p.id} className="engineering-card p-5 hover:border-brand-300 transition-colors group">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <Link href={`/projects/${p.id}`} className="font-bold text-navy hover:text-brand-600 transition-colors">
                    {p.name}
                  </Link>
                  <p className="text-xs text-slate-400 mt-0.5">{formatDate(p.created_at)}</p>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Link href={`/projects/${p.id}`} className="p-1.5 hover:bg-slate-100 rounded text-slate-400 hover:text-brand-600">
                    <Edit className="w-3.5 h-3.5" />
                  </Link>
                  <button onClick={() => handleDelete(p.id)} className="p-1.5 hover:bg-red-50 rounded text-slate-400 hover:text-red-500">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <InfoItem icon={MapPin} label={p.location} />
                <InfoItem icon={User} label={p.client_name} />
              </div>

              <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                <div className="flex gap-1.5">
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{p.building_type}</span>
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{p.num_floors} Lantai</span>
                </div>
                <Link href={`/projects/${p.id}`} className="flex items-center gap-1 text-xs text-brand-600 hover:underline">
                  Detail <ChevronRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Form */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-bold text-navy">Proyek Baru</h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Nama Proyek" required>
                <input className="engineering-input" value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </Field>
              <Field label="Lokasi" required>
                <input className="engineering-input" value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })} required />
              </Field>
              <Field label="Pemberi Tugas" required>
                <input className="engineering-input" value={form.client_name}
                  onChange={(e) => setForm({ ...form, client_name: e.target.value })} required />
              </Field>
              <Field label="Konsultan">
                <input className="engineering-input" value={form.consultant_name ?? ""}
                  onChange={(e) => setForm({ ...form, consultant_name: e.target.value })} />
              </Field>
              <Field label="Jenis Bangunan" required>
                <select className="engineering-input" value={form.building_type}
                  onChange={(e) => setForm({ ...form, building_type: e.target.value })}>
                  {["Gedung Kantor","Rumah Tinggal","Ruko","Gudang","Jembatan","Menara","Fasilitas Publik"].map(v => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </Field>
              <Field label="Jumlah Lantai" required>
                <input type="number" min={1} className="engineering-input" value={form.num_floors}
                  onChange={(e) => setForm({ ...form, num_floors: +e.target.value })} required />
              </Field>
              <Field label="Sistem Struktur" required>
                <select className="engineering-input" value={form.structural_system}
                  onChange={(e) => setForm({ ...form, structural_system: e.target.value })}>
                  {["Rangka Momen Biasa","Rangka Momen Menengah","Rangka Momen Khusus",
                    "Dinding Geser","Rangka Bracing","Sistem Ganda"].map(v => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </Field>
              <Field label="Material Utama" required>
                <select className="engineering-input" value={form.primary_material}
                  onChange={(e) => setForm({ ...form, primary_material: e.target.value })}>
                  {["Beton Bertulang","Baja Struktural","Komposit","Kayu"].map(v => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </Field>
              <Field label="Deskripsi" className="sm:col-span-2">
                <textarea className="engineering-input" rows={3} value={form.description ?? ""}
                  onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </Field>

              <div className="sm:col-span-2 flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">
                  Batal
                </button>
                <button type="submit" disabled={saving}
                  className="px-5 py-2 text-sm font-semibold bg-navy text-white rounded-lg hover:bg-navy-light disabled:opacity-50">
                  {saving ? "Menyimpan..." : "Simpan Proyek"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoItem({ icon: Icon, label }: { icon: any; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-slate-500">
      <Icon className="w-3 h-3 flex-shrink-0" />
      <span className="truncate">{label}</span>
    </div>
  );
}

function Field({ label, children, required, className }: {
  label: string; children: React.ReactNode; required?: boolean; className?: string;
}) {
  return (
    <div className={className}>
      <label className="engineering-label">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
    </div>
  );
}
