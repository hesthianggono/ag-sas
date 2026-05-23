"use client";
import { useState } from "react";
import {
  Eye, EyeOff, Edit3, Trash2, Download, GripVertical,
  CheckCircle2, AlertTriangle, Image as ImageIcon,
} from "lucide-react";
import type { FigureSnapshot } from "@/lib/figuresApi";
import { pngBase64ToDataUrl, downloadFigureAsPng } from "@/lib/figuresApi";

interface FigureCardProps {
  figure: FigureSnapshot;
  index: number;
  onToggleVisible: (id: number, visible: boolean) => void;
  onEditCaption: (figure: FigureSnapshot) => void;
  onDelete: (id: number) => void;
  isDragging?: boolean;
}

export default function FigureCard({
  figure,
  index,
  onToggleVisible,
  onEditCaption,
  onDelete,
  isDragging = false,
}: FigureCardProps) {
  const [lightbox, setLightbox] = useState(false);
  const dataUrl = pngBase64ToDataUrl(figure.png_base64);

  const sourceBadge =
    figure.source === "frontend"
      ? { label: "Frontend", cls: "bg-purple-100 text-purple-700" }
      : { label: "Backend", cls: "bg-blue-100 text-blue-700" };

  return (
    <>
      <div
        className={`engineering-card overflow-hidden transition-shadow ${
          isDragging ? "shadow-xl ring-2 ring-brand-500" : ""
        } ${!figure.is_visible ? "opacity-50" : ""}`}
      >
        {/* ── Header ── */}
        <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border-b border-slate-100">
          <GripVertical className="w-3.5 h-3.5 text-slate-300 cursor-grab flex-shrink-0" />
          <span className="text-xs font-bold text-navy font-mono min-w-[2.5rem]">
            {figure.figure_number}
          </span>
          <span className="flex-1 text-xs font-semibold text-slate-700 truncate">
            {figure.title}
          </span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${sourceBadge.cls}`}>
            {sourceBadge.label}
          </span>
          {!figure.is_visible && (
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-500">
              Disembunyikan
            </span>
          )}
        </div>

        {/* ── Preview gambar ── */}
        <div
          className="relative bg-slate-100 cursor-zoom-in"
          style={{ minHeight: "120px" }}
          onClick={() => setLightbox(true)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={dataUrl}
            alt={figure.caption}
            className="w-full h-auto object-contain"
            style={{ maxHeight: "220px" }}
          />
          <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 bg-black/10 transition-opacity">
            <Eye className="w-6 h-6 text-white drop-shadow" />
          </div>
        </div>

        {/* ── Caption ── */}
        <div className="px-3 py-2 bg-white">
          <p className="text-xs text-slate-600 italic leading-relaxed line-clamp-2">
            {figure.caption}
          </p>
          {/* Metadata chips */}
          <div className="flex flex-wrap gap-1 mt-1.5">
            {figure.load_combination && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                {figure.load_combination}
              </span>
            )}
            {figure.scale_factor && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                Skala ×{figure.scale_factor}
              </span>
            )}
            {figure.unit && figure.unit !== "—" && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                {figure.unit}
              </span>
            )}
          </div>
        </div>

        {/* ── Actions ── */}
        <div className="flex items-center gap-1 px-3 py-2 bg-slate-50 border-t border-slate-100">
          <button
            onClick={() => onToggleVisible(figure.id, !figure.is_visible)}
            title={figure.is_visible ? "Sembunyikan dari laporan" : "Tampilkan di laporan"}
            className="p-1.5 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-700 transition-colors"
          >
            {figure.is_visible ? (
              <Eye className="w-3.5 h-3.5" />
            ) : (
              <EyeOff className="w-3.5 h-3.5" />
            )}
          </button>
          <button
            onClick={() => onEditCaption(figure)}
            title="Edit caption"
            className="p-1.5 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-700 transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => downloadFigureAsPng(figure)}
            title="Download PNG"
            className="p-1.5 rounded hover:bg-slate-200 text-slate-500 hover:text-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <div className="flex-1" />
          <button
            onClick={() => onDelete(figure.id)}
            title="Hapus gambar"
            className="p-1.5 rounded hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Lightbox ── */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
          onClick={() => setLightbox(false)}
        >
          <div className="max-w-5xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="bg-white rounded-xl overflow-hidden shadow-2xl">
              <div className="flex items-center justify-between px-4 py-2 bg-navy text-white text-sm">
                <span className="font-mono font-bold">{figure.figure_number}</span>
                <span className="flex-1 mx-3 truncate">{figure.title}</span>
                <button onClick={() => setLightbox(false)} className="text-slate-300 hover:text-white">✕</button>
              </div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={dataUrl} alt={figure.caption} className="w-full h-auto" />
              <div className="px-4 py-2 bg-slate-50 text-xs text-slate-600 italic">
                {figure.caption}
                {figure.load_combination && ` — Kombinasi: ${figure.load_combination}`}
                {figure.unit && figure.unit !== "—" && ` — Satuan: ${figure.unit}`}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
