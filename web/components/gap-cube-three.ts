// The coverage map as a rotatable cube: pressure (x) × oxygen (z) × gravity (y, linear 0-1 g). Each NASA test
// with all three values is one dot. The Moon (0.16 g) and Mars (0.38 g) slices are translucent dashed planes,
// and the Moon-base box (>=30% O2, <=70.3 kPa) is outlined on the Moon slice. Loaded on demand by gap-cube.tsx;
// throws if WebGL is unavailable.
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

import type { CoveragePoint } from "@/lib/types";

export type CubePoint = CoveragePoint & { o2_pct: number; pressure_kpa: number; gravity_g: number };

const KPA: [number, number] = [0, 320];
const O2: [number, number] = [10, 40];
const MOON_G = 0.16;
const MARS_G = 0.38;
const MOON_O2 = 30;
const MOON_KPA = 70.3;
const W = 3; // pressure extent
const D = 2; // oxygen extent
const H = 2; // gravity extent

const X = (kpa: number) => ((kpa - KPA[0]) / (KPA[1] - KPA[0]) - 0.5) * W;
const Z = (o2: number) => (0.5 - (o2 - O2[0]) / (O2[1] - O2[0])) * D; // low O2 at the front
const Y = (g: number) => (g - 0.5) * H;

const DOT_VERT = /* glsl */ `
  attribute vec3 aColor;
  uniform float uSize; uniform int uHover;
  varying vec3 vColor; varying float vHover;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vHover = gl_VertexID == uHover ? 1.0 : 0.0;
    gl_PointSize = uSize * (1.0 + 0.6 * vHover) / -mv.z;
    vColor = aColor;
    gl_Position = projectionMatrix * mv;
  }
`;
const DOT_FRAG = /* glsl */ `
  uniform vec3 uEdge;
  varying vec3 vColor; varying float vHover;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;
    float rim = smoothstep(0.3, 0.36, d);                  // dark outline so dots read on the dark page
    vec3 col = mix(vColor * (1.0 + 0.35 * vHover), uEdge, rim);
    gl_FragColor = vec4(col, 1.0 - smoothstep(0.46, 0.5, d));
  }
`;

function token(name: string, fallback: string) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return /^#[0-9a-f]{3,8}$/i.test(v) ? v : fallback;
}

function rect(x0: number, x1: number, z0: number, z1: number, y: number) {
  return [
    new THREE.Vector3(x0, y, z0), new THREE.Vector3(x1, y, z0), new THREE.Vector3(x1, y, z1),
    new THREE.Vector3(x0, y, z1), new THREE.Vector3(x0, y, z0),
  ];
}

function line(pts: THREE.Vector3[], material: THREE.LineBasicMaterial | THREE.LineDashedMaterial) {
  const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), material);
  if (material instanceof THREE.LineDashedMaterial) l.computeLineDistances();
  return l;
}

function plane(x0: number, x1: number, z0: number, z1: number, y: number, color: string, opacity: number) {
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(x1 - x0, z1 - z0),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity, side: THREE.DoubleSide, depthWrite: false }),
  );
  m.rotation.x = -Math.PI / 2;
  m.position.set((x0 + x1) / 2, y, (z0 + z1) / 2);
  return m;
}

export function mountGapCube(box: HTMLElement, overlay: HTMLElement, points: CubePoint[], series: Record<string, string>) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); // throws without WebGL
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(dpr);
  renderer.domElement.style.display = "block";
  box.appendChild(renderer.domElement);

  const c = {
    zeroG: token("--zero-g", "#7d98ff"),
    oneG: token("--one-g", "#f2a541"),
    gap: token("--gap", "#8e98ae"),
    border: token("--border", "#243152"),
    card: token("--card", "#0c1226"),
    ink: token("--ink", "#e8edf7"),
  };

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50);
  camera.position.set(3.9, 2.2, 4.8);

  const xL = X(KPA[0]), xR = X(KPA[1]), zF = Z(O2[0]), zB = Z(O2[1]);
  const edge = new THREE.LineBasicMaterial({ color: c.border, transparent: true, opacity: 0.9 });
  const grid = new THREE.LineBasicMaterial({ color: c.border, transparent: true, opacity: 0.45 });

  // Cube frame: the 0 g and 1 g floors plus the four vertical edges.
  const cube = new THREE.Group();
  cube.add(line(rect(xL, xR, zF, zB, Y(0)), new THREE.LineBasicMaterial({ color: c.zeroG, transparent: true, opacity: 0.7 })));
  cube.add(line(rect(xL, xR, zF, zB, Y(1)), new THREE.LineBasicMaterial({ color: c.oneG, transparent: true, opacity: 0.7 })));
  for (const [x, z] of [[xL, zF], [xR, zF], [xR, zB], [xL, zB]]) {
    cube.add(line([new THREE.Vector3(x, Y(0), z), new THREE.Vector3(x, Y(1), z)], edge));
  }
  // Floor grids at the tick values, so a dot's position on the 0 g / 1 g floor can be read.
  for (const g of [0, 1]) {
    for (const k of [100, 200, 300]) cube.add(line([new THREE.Vector3(X(k), Y(g), zF), new THREE.Vector3(X(k), Y(g), zB)], grid));
    for (const o of [20, 30]) cube.add(line([new THREE.Vector3(xL, Y(g), Z(o)), new THREE.Vector3(xR, Y(g), Z(o))], grid));
  }
  cube.add(plane(xL, xR, zF, zB, Y(0), c.zeroG, 0.05), plane(xL, xR, zF, zB, Y(1), c.oneG, 0.05));

  // Moon and Mars slices: translucent, dashed, and (per the data) empty.
  const dashed = new THREE.LineDashedMaterial({ color: c.gap, dashSize: 0.08, gapSize: 0.06, transparent: true, opacity: 0.95 });
  for (const g of [MOON_G, MARS_G]) {
    cube.add(plane(xL, xR, zF, zB, Y(g), c.gap, 0.09));
    cube.add(line(rect(xL, xR, zF, zB, Y(g)), dashed));
  }
  // Moon-base box on the lunar slice.
  const mb = { x0: X(0), x1: X(MOON_KPA), z0: Z(MOON_O2), z1: Z(O2[1]) };
  cube.add(plane(mb.x0, mb.x1, mb.z0, mb.z1, Y(MOON_G), c.ink, 0.12));
  cube.add(line(rect(mb.x0, mb.x1, mb.z0, mb.z1, Y(MOON_G)),
    new THREE.LineDashedMaterial({ color: c.ink, dashSize: 0.06, gapSize: 0.04 })));
  scene.add(cube);

  // Dots: one Points object, colored per investigation.
  const pos = new Float32Array(points.length * 3);
  const col = new Float32Array(points.length * 3);
  const tmp = new THREE.Color();
  points.forEach((p, i) => {
    pos.set([X(p.pressure_kpa), Y(p.gravity_g), Z(p.o2_pct)], i * 3);
    tmp.set(series[p.investigation] ?? c.gap);
    col.set([tmp.r, tmp.g, tmp.b], i * 3);
  });
  const dotGeo = new THREE.BufferGeometry();
  dotGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  dotGeo.setAttribute("aColor", new THREE.BufferAttribute(col, 3));
  const dotU = { uSize: { value: 0 }, uHover: { value: -1 }, uEdge: { value: new THREE.Color(c.card) } };
  const dots = new THREE.Points(dotGeo, new THREE.ShaderMaterial({
    vertexShader: DOT_VERT, fragmentShader: DOT_FRAG, uniforms: dotU, transparent: true, depthWrite: false,
  }));
  scene.add(dots);

  // HTML labels, projected from 3D anchors each frame. Text uses theme text colors only.
  const count = (g: number) => points.filter((p) => p.gravity_g === g).length;
  const slice = (name: string, g: number) => {
    const n = count(g);
    return `${name} ${g} g: ${n === 0 ? "no tests" : `${n} test${n === 1 ? "" : "s"}`}`;
  };
  const plotted = (n: number) => `${n} test${n === 1 ? "" : "s"} plotted`;
  type Label = { el: HTMLElement; at: THREE.Vector3; anchor: "left" | "center" | "right" };
  const labels: Label[] = [];
  const addLabel = (text: string, at: THREE.Vector3, opts: { strong?: boolean; anchor?: Label["anchor"]; size?: number } = {}) => {
    const el = document.createElement("span");
    el.textContent = text;
    Object.assign(el.style, {
      position: "absolute", left: "0", top: "0", whiteSpace: "nowrap", pointerEvents: "none",
      fontSize: `${opts.size ?? 11}px`, lineHeight: "1.2",
      color: opts.strong ? "var(--ink)" : "var(--muted-foreground)", fontWeight: opts.strong ? "600" : "400",
      textShadow: "0 0 3px var(--background), 0 0 6px var(--background)",
    });
    overlay.appendChild(el);
    labels.push({ el, at, anchor: opts.anchor ?? "center" });
  };
  const pad = 0.14;
  for (const k of [0, 100, 200, 300]) addLabel(String(k), new THREE.Vector3(X(k), Y(0), zF + pad));
  addLabel("Pressure (kPa)", new THREE.Vector3(0, Y(0) - 0.08, zF + 0.42), { size: 12 });
  for (const o of [10, 20, 30, 40]) addLabel(`${o}%`, new THREE.Vector3(xR + pad, Y(0), Z(o)), { anchor: "left" });
  addLabel("O₂ %", new THREE.Vector3(xR + 0.5, Y(0) - 0.08, 0), { anchor: "left", size: 12 });
  addLabel(`0 g orbit: ${plotted(count(0))}`, new THREE.Vector3(xL - pad, Y(0), zF), { anchor: "right", strong: true });
  addLabel(slice("Moon", MOON_G), new THREE.Vector3(xL - pad, Y(MOON_G), zF), { anchor: "right", strong: true });
  addLabel(slice("Mars", MARS_G), new THREE.Vector3(xL - pad, Y(MARS_G), zF), { anchor: "right", strong: true });
  addLabel(`1 g Earth: ${plotted(count(1))}`, new THREE.Vector3(xL - pad, Y(1), zF), { anchor: "right", strong: true });
  addLabel("Moon base: ≥30% O₂, ≤70.3 kPa", new THREE.Vector3((mb.x0 + mb.x1) / 2, Y(MOON_G) + 0.06, (mb.z0 + mb.z1) / 2), { strong: true, size: 10 });

  const tip = document.createElement("div");
  Object.assign(tip.style, {
    position: "absolute", left: "0", top: "0", display: "none", pointerEvents: "none", fontSize: "12px",
    lineHeight: "1.35", padding: "6px 10px", borderRadius: "6px", border: "1px solid var(--border)",
    background: "var(--card)", color: "var(--ink)", whiteSpace: "nowrap",
  });
  overlay.appendChild(tip);

  const controls = new OrbitControls(camera, renderer.domElement);
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  controls.enablePan = false;
  controls.enableDamping = !still;
  controls.minDistance = 3.5;
  controls.maxDistance = 11;
  controls.autoRotate = !still;
  controls.autoRotateSpeed = 0.6;
  controls.target.set(0, -0.2, 0);
  controls.addEventListener("start", () => { controls.autoRotate = false; });

  let w = 1, h = 1;
  const v = new THREE.Vector3();
  const toScreen = (p: THREE.Vector3) => {
    v.copy(p).project(camera);
    return { x: (v.x * 0.5 + 0.5) * w, y: (-v.y * 0.5 + 0.5) * h, behind: v.z > 1 };
  };

  const resize = () => {
    w = box.clientWidth || 1;
    h = box.clientHeight || 1;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    dotU.uSize.value = (w < 500 ? 7 : 9) * 7 * dpr; // 7-9 px dots at the default camera distance (~7)
  };

  const render = () => {
    controls.update();
    renderer.render(scene, camera);
    for (const l of labels) {
      const s = toScreen(l.at);
      const shift = l.anchor === "left" ? "0%" : l.anchor === "right" ? "-100%" : "-50%";
      l.el.style.display = s.behind ? "none" : "";
      l.el.style.transform = `translate(${s.x}px, ${s.y}px) translate(${shift}, -50%)`;
    }
  };

  // Hover: nearest dot on screen within 10 px.
  const p3 = new THREE.Vector3();
  const onMove = (e: PointerEvent) => {
    const r = renderer.domElement.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    let best = -1, bestD = 100;
    for (let i = 0; i < points.length; i++) {
      p3.fromArray(pos, i * 3);
      const s = toScreen(p3);
      const d = (s.x - mx) ** 2 + (s.y - my) ** 2;
      if (!s.behind && d < bestD) { bestD = d; best = i; }
    }
    dotU.uHover.value = best;
    if (best < 0) { tip.style.display = "none"; return; }
    const p = points[best];
    tip.replaceChildren();
    const rows: [string, boolean][] = [
      [p.test_id, true], [p.investigation, false], [`O₂ ${p.o2_pct}%`, false],
      [`${p.pressure_kpa} kPa`, false], [`${p.gravity_g} g`, false],
    ];
    for (const [text, strong] of rows) {
      const row = document.createElement("div");
      row.textContent = text;
      if (strong) row.style.fontWeight = "600";
      else if (text === p.investigation) row.style.color = "var(--muted-foreground)";
      tip.appendChild(row);
    }
    tip.style.display = "block";
    const left = mx + 14 + 150 > w ? mx - 14 : mx + 14;
    tip.style.transform = `translate(${left}px, ${my + 10}px)${left < mx ? " translateX(-100%)" : ""}`;
    if (still) render();
  };
  const onLeave = () => { tip.style.display = "none"; dotU.uHover.value = -1; if (still) render(); };

  let frame = 0;
  let visible = true;
  const loop = () => {
    render();
    if (visible) frame = requestAnimationFrame(loop);
  };

  const ro = new ResizeObserver(() => { resize(); render(); });
  const io = new IntersectionObserver(([entry]) => {
    const was = visible;
    visible = entry.isIntersecting;
    if (visible && !was) frame = requestAnimationFrame(loop);
  });

  resize();
  ro.observe(box);
  io.observe(box);
  renderer.domElement.addEventListener("pointermove", onMove);
  renderer.domElement.addEventListener("pointerleave", onLeave);
  frame = requestAnimationFrame(loop);

  return () => {
    cancelAnimationFrame(frame);
    visible = false;
    renderer.domElement.removeEventListener("pointermove", onMove);
    renderer.domElement.removeEventListener("pointerleave", onLeave);
    ro.disconnect();
    io.disconnect();
    controls.dispose();
    scene.traverse((o) => {
      const m = o as THREE.Mesh;
      m.geometry?.dispose();
      (m.material as THREE.Material | undefined)?.dispose();
    });
    renderer.dispose();
    renderer.domElement.remove();
    overlay.replaceChildren();
  };
}
