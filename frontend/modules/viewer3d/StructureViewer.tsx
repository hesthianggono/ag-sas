"use client";
import { useRef, useState, useCallback, useMemo } from "react";
import { Canvas, ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Grid, Text, Line } from "@react-three/drei";
import * as THREE from "three";
import type { StructureModel, StructNode, StructElement, Selection } from "./types";

// ── Color palette ───────────────────────────────────────────────────────────
const COLORS = {
  column:      "#1e3a5f",
  beam:        "#3b82f6",
  brace:       "#f59e0b",
  node:        "#ef4444",
  nodeHover:   "#f97316",
  nodeSelect:  "#facc15",
  support:     "#1e3a5f",
  loadArrow:   "#22c55e",
  axisX:       "#ef4444",
  axisY:       "#22c55e",
  axisZ:       "#3b82f6",
  selected:    "#facc15",
};

// ── Node component ──────────────────────────────────────────────────────────

function NodeMesh({
  node,
  selected,
  showLabels,
  onSelect,
}: {
  node: StructNode;
  selected: boolean;
  showLabels: boolean;
  onSelect: (id: string) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const color = selected ? COLORS.nodeSelect : hovered ? COLORS.nodeHover : COLORS.node;

  return (
    <group position={[node.x, node.y, node.z]}>
      <mesh
        onClick={(e: ThreeEvent<MouseEvent>) => { e.stopPropagation(); onSelect(node.id); }}
        onPointerOver={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); setHovered(true); }}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.18, 16, 16]} />
        <meshStandardMaterial color={color} emissive={selected ? "#b45309" : "#000000"} emissiveIntensity={0.3} />
      </mesh>
      {showLabels && (
        <Text
          position={[0.3, 0.3, 0]}
          fontSize={0.22}
          color="#94a3b8"
          anchorX="left"
          anchorY="middle"
          renderOrder={1}
        >
          {node.id}
        </Text>
      )}
    </group>
  );
}

// ── Element (cylinder) component ─────────────────────────────────────────────

function ElementMesh({
  el,
  nodeA,
  nodeB,
  selected,
  onSelect,
}: {
  el: StructElement;
  nodeA: StructNode;
  nodeB: StructNode;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const [hovered, setHovered] = useState(false);

  const { midpoint, length, quaternion } = useMemo(() => {
    const a = new THREE.Vector3(nodeA.x, nodeA.y, nodeA.z);
    const b = new THREE.Vector3(nodeB.x, nodeB.y, nodeB.z);
    const midpoint = new THREE.Vector3().addVectors(a, b).multiplyScalar(0.5);
    const length = a.distanceTo(b);
    const dir = new THREE.Vector3().subVectors(b, a).normalize();
    const quaternion = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir
    );
    return { midpoint, length, quaternion };
  }, [nodeA, nodeB]);

  const baseColor = selected ? COLORS.selected : COLORS[el.type] ?? COLORS.beam;
  const color = hovered ? "#f97316" : baseColor;
  const radius = el.type === "column" ? 0.09 : 0.07;

  return (
    <mesh
      position={midpoint}
      quaternion={quaternion}
      onClick={(e: ThreeEvent<MouseEvent>) => { e.stopPropagation(); onSelect(el.id); }}
      onPointerOver={(e: ThreeEvent<PointerEvent>) => { e.stopPropagation(); setHovered(true); }}
      onPointerOut={() => setHovered(false)}
    >
      <cylinderGeometry args={[radius, radius, length, 8]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

// ── Support symbol ─────────────────────────────────────────────────────────

function SupportSymbol({ x, y, z }: { x: number; y: number; z: number }) {
  return (
    <mesh position={[x, y - 0.35, z]}>
      <coneGeometry args={[0.25, 0.5, 4]} />
      <meshStandardMaterial color={COLORS.support} />
    </mesh>
  );
}

// ── Load arrow ─────────────────────────────────────────────────────────────

function LoadArrow({ x, y, z, fy }: { x: number; y: number; z: number; fy: number }) {
  const dir = fy < 0 ? -1 : 1;
  const arrowLen = 1.2;
  const tip: [number, number, number] = [x, y + dir * arrowLen, z];
  const tail: [number, number, number] = [x, y, z];

  return (
    <group>
      <Line points={[tail, tip]} color={COLORS.loadArrow} lineWidth={2} />
      <mesh position={[x, y + dir * (arrowLen + 0.2), z]} rotation={dir < 0 ? [Math.PI, 0, 0] : [0, 0, 0]}>
        <coneGeometry args={[0.12, 0.3, 6]} />
        <meshStandardMaterial color={COLORS.loadArrow} />
      </mesh>
    </group>
  );
}

// ── Axis helper ──────────────────────────────────────────────────────────────

function AxisHelper({ origin }: { origin: [number, number, number] }) {
  const [ox, oy, oz] = origin;
  const len = 2.5;
  return (
    <group>
      <Line points={[[ox,oy,oz],[ox+len,oy,oz]]} color={COLORS.axisX} lineWidth={3} />
      <Line points={[[ox,oy,oz],[ox,oy+len,oz]]} color={COLORS.axisY} lineWidth={3} />
      <Line points={[[ox,oy,oz],[ox,oy,oz+len]]} color={COLORS.axisZ} lineWidth={3} />
      <Text position={[ox+len+0.4,oy,oz]} fontSize={0.5} color={COLORS.axisX}>X</Text>
      <Text position={[ox,oy+len+0.4,oz]} fontSize={0.5} color={COLORS.axisY}>Y</Text>
      <Text position={[ox,oy,oz+len+0.4]} fontSize={0.5} color={COLORS.axisZ}>Z</Text>
    </group>
  );
}

// ── Scene ──────────────────────────────────────────────────────────────────

function Scene({
  model,
  selection,
  onSelect,
  showLabels,
  showLoads,
  showSupports,
}: {
  model: StructureModel;
  selection: Selection | null;
  onSelect: (sel: Selection | null) => void;
  showLabels: boolean;
  showLoads: boolean;
  showSupports: boolean;
}) {
  const nodeMap = useMemo(() => {
    const m: Record<string, StructNode> = {};
    model.nodes.forEach((n) => (m[n.id] = n));
    return m;
  }, [model.nodes]);

  const supportSet = useMemo(() => new Set(model.supports.map((s) => s.nodeId)), [model.supports]);

  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[20, 30, 20]} intensity={1.2} castShadow />
      <pointLight position={[-15, 15, -15]} intensity={0.4} />

      {/* Elements */}
      {model.elements.map((el) => {
        const a = nodeMap[el.nodeI];
        const b = nodeMap[el.nodeJ];
        if (!a || !b) return null;
        return (
          <ElementMesh
            key={el.id}
            el={el}
            nodeA={a}
            nodeB={b}
            selected={selection?.type === "element" && selection.id === el.id}
            onSelect={(id) => onSelect({ type: "element", id })}
          />
        );
      })}

      {/* Nodes */}
      {model.nodes.map((node) => (
        <NodeMesh
          key={node.id}
          node={node}
          selected={selection?.type === "node" && selection.id === node.id}
          showLabels={showLabels}
          onSelect={(id) => onSelect({ type: "node", id })}
        />
      ))}

      {/* Supports */}
      {showSupports &&
        model.supports.map((s) => {
          const n = nodeMap[s.nodeId];
          if (!n) return null;
          return <SupportSymbol key={s.nodeId} x={n.x} y={n.y} z={n.z} />;
        })}

      {/* Loads */}
      {showLoads &&
        model.loads.map((load, i) => {
          const n = nodeMap[load.nodeId];
          if (!n || load.fy === 0) return null;
          return <LoadArrow key={i} x={n.x} y={n.y} z={n.z} fy={load.fy} />;
        })}

      {/* Lateral load arrows (fx) */}
      {showLoads &&
        model.loads.map((load, i) => {
          const n = nodeMap[load.nodeId];
          if (!n || load.fx === 0) return null;
          const tip: [number, number, number] = [n.x + 1.2, n.y, n.z];
          const tail: [number, number, number] = [n.x, n.y, n.z];
          return (
            <group key={`fx-${i}`}>
              <Line points={[tail, tip]} color="#f59e0b" lineWidth={2} />
              <mesh position={[n.x + 1.5, n.y, n.z]} rotation={[0, 0, -Math.PI / 2]}>
                <coneGeometry args={[0.12, 0.3, 6]} />
                <meshStandardMaterial color="#f59e0b" />
              </mesh>
            </group>
          );
        })}

      {/* Axis */}
      <AxisHelper origin={[-3, -1, -3]} />

      {/* Ground grid */}
      <Grid
        args={[40, 40]}
        position={[7.5, -0.02, 5]}
        cellSize={1}
        cellThickness={0.4}
        cellColor="#1e293b"
        sectionSize={5}
        sectionThickness={0.8}
        sectionColor="#334155"
        fadeDistance={60}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={false}
      />

      {/* Click-away deselect */}
      <mesh
        position={[7.5, -0.1, 5]}
        rotation={[-Math.PI / 2, 0, 0]}
        onClick={() => onSelect(null)}
      >
        <planeGeometry args={[60, 60]} />
        <meshStandardMaterial visible={false} />
      </mesh>
    </>
  );
}

// ── Properties Panel ────────────────────────────────────────────────────────

function PropertiesPanel({
  selection,
  model,
  onClose,
}: {
  selection: Selection;
  model: StructureModel;
  onClose: () => void;
}) {
  if (selection.type === "node") {
    const node = model.nodes.find((n) => n.id === selection.id);
    const support = model.supports.find((s) => s.nodeId === selection.id);
    const loads = model.loads.filter((l) => l.nodeId === selection.id);
    if (!node) return null;

    return (
      <div className="absolute top-4 right-4 z-20 bg-slate-900/95 border border-slate-600 rounded-xl shadow-2xl w-64 text-xs text-slate-300 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
          <span className="font-bold text-white">Node: {node.id}</span>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm leading-none">✕</button>
        </div>
        <div className="p-4 space-y-3">
          <Section title="Koordinat">
            <Row label="X" value={`${node.x.toFixed(2)} m`} />
            <Row label="Y" value={`${node.y.toFixed(2)} m`} />
            <Row label="Z" value={`${node.z.toFixed(2)} m`} />
          </Section>
          {support && (
            <Section title="Perletakan">
              <Row label="Tipe" value={support.type} />
              <Row label="DOF" value={support.dof.map((d) => (d ? "1" : "0")).join(" ")} />
            </Section>
          )}
          {loads.length > 0 && (
            <Section title="Beban Nodal">
              {loads.map((l, i) => (
                <div key={i}>
                  {l.label && <p className="text-slate-400 mb-1">{l.label}</p>}
                  {l.fx !== 0 && <Row label="Fx" value={`${l.fx} kN`} />}
                  {l.fy !== 0 && <Row label="Fy" value={`${l.fy} kN`} />}
                  {l.fz !== 0 && <Row label="Fz" value={`${l.fz} kN`} />}
                </div>
              ))}
            </Section>
          )}
        </div>
      </div>
    );
  }

  if (selection.type === "element") {
    const el = model.elements.find((e) => e.id === selection.id);
    if (!el) return null;
    const sec = model.sections.find((s) => s.id === el.sectionId);
    const mat = model.materials.find((m) => m.id === el.materialId);
    const nodeA = model.nodes.find((n) => n.id === el.nodeI)!;
    const nodeB = model.nodes.find((n) => n.id === el.nodeJ)!;
    const len = nodeA && nodeB
      ? Math.sqrt((nodeB.x-nodeA.x)**2 + (nodeB.y-nodeA.y)**2 + (nodeB.z-nodeA.z)**2)
      : 0;

    return (
      <div className="absolute top-4 right-4 z-20 bg-slate-900/95 border border-slate-600 rounded-xl shadow-2xl w-64 text-xs text-slate-300 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
          <span className="font-bold text-white">Elemen: {el.id}</span>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-sm leading-none">✕</button>
        </div>
        <div className="p-4 space-y-3">
          <Section title="Info Elemen">
            <Row label="Tipe" value={el.type} />
            <Row label="Node I" value={el.nodeI} />
            <Row label="Node J" value={el.nodeJ} />
            <Row label="Panjang" value={`${len.toFixed(2)} m`} />
            {el.label && <Row label="Label" value={el.label} />}
          </Section>
          {sec && (
            <Section title="Penampang">
              <Row label="ID" value={sec.id} />
              <Row label="Nama" value={sec.name} />
              {sec.area_cm2 !== undefined && <Row label="A" value={`${sec.area_cm2} cm²`} />}
              {sec.ix_cm4 !== undefined && <Row label="Ix" value={`${sec.ix_cm4} cm⁴`} />}
            </Section>
          )}
          {mat && (
            <Section title="Material">
              <Row label="Nama" value={mat.name} />
              <Row label="E" value={`${mat.E_gpa} GPa`} />
              {mat.fy_mpa !== undefined && <Row label="fy" value={`${mat.fy_mpa} MPa`} />}
            </Section>
          )}
        </div>
      </div>
    );
  }

  return null;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider mb-1.5">{title}</p>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="text-white font-mono">{value}</span>
    </div>
  );
}

// ── Main export ──────────────────────────────────────────────────────────────

export default function StructureViewer({ model }: { model: StructureModel }) {
  const [selection, setSelection] = useState<Selection | null>(null);
  const [showLabels, setShowLabels] = useState(false);
  const [showLoads, setShowLoads] = useState(true);
  const [showSupports, setShowSupports] = useState(true);

  const handleSelect = useCallback((sel: Selection | null) => setSelection(sel), []);

  const nodeCount = model.nodes.length;
  const elemCount = model.elements.length;
  const colCount = model.elements.filter((e) => e.type === "column").length;
  const beamCount = model.elements.filter((e) => e.type === "beam").length;

  return (
    <div className="w-full h-full bg-slate-900 relative select-none">
      {/* ── Info overlay ── */}
      <div className="absolute top-4 left-4 z-10 bg-black/60 text-white text-xs px-3 py-2 rounded-lg font-mono pointer-events-none">
        <p className="font-bold text-brand-400 mb-1">AG-SAS 3D Viewer</p>
        <p className="text-slate-300">{model.name}</p>
        <p className="text-slate-400 mt-1">
          Nodes: {nodeCount} · Kolom: {colCount} · Balok: {beamCount}
        </p>
      </div>

      {/* ── Toolbar toggles ── */}
      <div className="absolute bottom-4 left-4 z-10 flex gap-2">
        <ToggleBtn active={showLabels} onClick={() => setShowLabels((v) => !v)} label="Labels" />
        <ToggleBtn active={showLoads} onClick={() => setShowLoads((v) => !v)} label="Beban" />
        <ToggleBtn active={showSupports} onClick={() => setShowSupports((v) => !v)} label="Perletakan" />
      </div>

      {/* ── Legend ── */}
      <div className="absolute bottom-4 right-4 z-10 bg-black/60 text-xs text-slate-300 px-3 py-2 rounded-lg space-y-1">
        <LegendItem color={COLORS.column} label="Kolom" />
        <LegendItem color={COLORS.beam} label="Balok" />
        <LegendItem color={COLORS.node} label="Node" />
        <LegendItem color={COLORS.loadArrow} label="Beban" />
      </div>

      {/* ── Properties panel ── */}
      {selection && (
        <PropertiesPanel
          selection={selection}
          model={model}
          onClose={() => setSelection(null)}
        />
      )}

      <Canvas
        camera={{ position: [22, 14, 22], fov: 50 }}
        gl={{ antialias: true, alpha: false }}
        style={{ background: "#0f172a" }}
      >
        <Scene
          model={model}
          selection={selection}
          onSelect={handleSelect}
          showLabels={showLabels}
          showLoads={showLoads}
          showSupports={showSupports}
        />
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          minDistance={5}
          maxDistance={80}
        />
      </Canvas>
    </div>
  );
}

function ToggleBtn({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
        active
          ? "bg-brand-600 text-white"
          : "bg-slate-700/80 text-slate-300 hover:bg-slate-600"
      }`}
    >
      {label}
    </button>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
      <span>{label}</span>
    </div>
  );
}
