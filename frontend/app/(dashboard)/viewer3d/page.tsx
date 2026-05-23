"use client";
import dynamic from "next/dynamic";
import { Box } from "lucide-react";
import { sampleModel } from "@/modules/viewer3d/sampleModel";

const StructureViewer = dynamic(() => import("@/modules/viewer3d/StructureViewer"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full text-slate-400">
      <span className="w-6 h-6 border-2 border-slate-300 border-t-brand-500 rounded-full animate-spin mr-3" />
      Memuat 3D Viewer...
    </div>
  ),
});

export default function Viewer3DPage() {
  const model = sampleModel;
  const colCount = model.elements.filter((e) => e.type === "column").length;
  const beamCount = model.elements.filter((e) => e.type === "beam").length;

  return (
    <div>
      {/* ── Header ── */}
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy flex items-center gap-3">
            <Box className="w-6 h-6" />
            3D Structural Viewer
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Visualisasi 3D model struktur — klik node atau elemen untuk melihat properti
          </p>
        </div>
        <span className="text-xs font-semibold bg-blue-100 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-full whitespace-nowrap">
          Visualization Only
        </span>
      </div>

      {/* ── Stats ── */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Nodes" value={model.nodes.length} color="text-red-600" />
        <StatCard label="Kolom" value={colCount} color="text-navy" />
        <StatCard label="Balok" value={beamCount} color="text-blue-600" />
        <StatCard label="Perletakan" value={model.supports.length} color="text-slate-600" />
      </div>

      {/* ── Viewer ── */}
      <div className="engineering-card overflow-hidden rounded-xl" style={{ height: "620px" }}>
        <StructureViewer model={model} />
      </div>

      {/* ── Controls guide ── */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-xs text-center text-slate-500">
        <div className="engineering-card p-3">
          <p className="font-bold text-navy mb-1">Kontrol Mouse</p>
          <p>Klik + Drag: Rotate</p>
          <p>Scroll: Zoom</p>
          <p>Klik Kanan + Drag: Pan</p>
        </div>
        <div className="engineering-card p-3">
          <p className="font-bold text-navy mb-1">Interaksi</p>
          <p>Klik node (merah) → info koordinat & beban</p>
          <p>Klik batang → info elemen & penampang</p>
          <p>Klik area kosong → deselect</p>
        </div>
        <div className="engineering-card p-3">
          <p className="font-bold text-navy mb-1">Toggle Tampilan</p>
          <p>Labels: tampilkan ID node</p>
          <p>Beban: tampilkan arrow beban</p>
          <p>Perletakan: tampilkan simbol tumpuan</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="engineering-card p-4 text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
    </div>
  );
}
