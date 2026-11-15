// The product's idea as a live 3D scene: a round blue flame around a fuel droplet (0 g: no buoyancy, so heat
// spreads evenly), an amber teardrop candle flame (1 g: hot gas rises), and the Moon inside an empty dashed
// shell (lunar gravity: never tested). Loaded on demand by flame-scene.tsx; throws if WebGL is unavailable.
import * as THREE from "three";

const NOISE = /* glsl */ `
  float hash(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
  float noise(vec3 x) {
    vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
               mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
  }
`;

const ZERO_G_VERT = /* glsl */ `
  uniform float uTime; uniform float uIgnite;
  varying vec3 vN; varying vec3 vView; varying vec3 vPos;
  ${NOISE}
  void main() {
    vec3 p = position * (0.94 + 0.08 * noise(position * 2.5 + uTime * 0.35)) * uIgnite;  // breathes, never rises
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    vN = normalize(normalMatrix * normal); vView = normalize(-mv.xyz); vPos = position;
    gl_Position = projectionMatrix * mv;
  }
`;
const ZERO_G_FRAG = /* glsl */ `
  uniform float uTime; uniform float uIgnite;
  varying vec3 vN; varying vec3 vView; varying vec3 vPos;
  ${NOISE}
  void main() {
    float shell = pow(1.0 - max(dot(vN, vView), 0.0), 1.6);  // the thin flame sheet glows where seen edge-on
    float flick = 0.85 + 0.15 * noise(vPos * 4.0 + uTime * 0.8);
    vec3 col = mix(vec3(0.16, 0.27, 0.95), vec3(0.66, 0.77, 1.0), shell) * (0.25 + 1.4 * shell) * flick;
    gl_FragColor = vec4(col, (0.12 + 0.88 * shell) * uIgnite);
  }
`;

const ONE_G_VERT = /* glsl */ `
  uniform float uTime; uniform float uIgnite;
  varying vec3 vN; varying vec3 vView; varying float vH;
  ${NOISE}
  void main() {
    vec3 p = position;
    float h = clamp((p.y + 0.55) / 1.5, 0.0, 1.0);
    p.x += (noise(vec3(uTime * 1.6, h * 2.0, 0.0)) - 0.5) * 0.24 * h * h;   // the tip licks sideways
    p.z += (noise(vec3(0.0, h * 2.0, uTime * 1.3)) - 0.5) * 0.12 * h * h;
    p.y += h * 0.07 * sin(uTime * 7.0 + noise(vec3(uTime)) * 6.0);           // and stretches upward
    p.y = -0.55 + (p.y + 0.55) * uIgnite;
    p.xz *= mix(0.3, 1.0, uIgnite);
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    vN = normalize(normalMatrix * normal); vView = normalize(-mv.xyz); vH = h;
    gl_Position = projectionMatrix * mv;
  }
`;
const ONE_G_FRAG = /* glsl */ `
  uniform float uIgnite;
  varying vec3 vN; varying vec3 vView; varying float vH;
  void main() {
    vec3 col = mix(vec3(0.25, 0.4, 1.0), vec3(1.0, 0.86, 0.55), smoothstep(0.04, 0.22, vH));  // blue base
    col = mix(col, vec3(1.0, 0.55, 0.15), smoothstep(0.45, 0.95, vH));                       // amber tip
    float core = pow(max(dot(vN, vView), 0.0), 1.5);
    float a = (0.3 + 0.7 * core) * (1.0 - 0.6 * smoothstep(0.8, 1.0, vH)) * uIgnite;
    gl_FragColor = vec4(col * (0.6 + 0.9 * core), a);
  }
`;

const MOON_VERT = /* glsl */ `
  varying vec3 vN; varying vec3 vP;
  void main() { vN = normalize(normalMatrix * normal); vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
`;
const MOON_FRAG = /* glsl */ `
  uniform float uIgnite; uniform vec3 uLight;
  varying vec3 vN; varying vec3 vP;
  ${NOISE}
  void main() {
    float n = noise(vP * 3.0) * 0.5 + noise(vP * 7.0) * 0.3 + noise(vP * 15.0) * 0.2;
    vec3 base = mix(vec3(0.74, 0.74, 0.72), vec3(0.42, 0.43, 0.46), smoothstep(0.45, 0.6, noise(vP * 1.6)));  // maria
    float light = max(dot(normalize(vN), normalize(uLight)), 0.0);
    gl_FragColor = vec4(base * (0.75 + 0.35 * n) * (0.07 + 0.95 * light), uIgnite);
  }
`;

const ease = (t: number) => 1 - Math.pow(1 - Math.min(Math.max(t, 0), 1), 3);

function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d")!;
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.35, "rgba(255,255,255,0.35)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}

function dashedRing(radius: number, color: string) {
  const pts = new THREE.EllipseCurve(0, 0, radius, radius, 0, Math.PI * 2).getPoints(160);
  const geo = new THREE.BufferGeometry().setFromPoints(pts.map((p) => new THREE.Vector3(p.x, p.y, 0)));
  const ring = new THREE.Line(geo, new THREE.LineDashedMaterial({ color, dashSize: 0.09, gapSize: 0.07, transparent: true }));
  ring.computeLineDistances();
  return ring;
}

export function mountFlameScene(box: HTMLElement): () => void {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });  // throws without WebGL
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  box.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 2, 0.1, 50);
  const glow = glowTexture();
  const additive = { transparent: true, depthWrite: false, blending: THREE.AdditiveBlending };
  const u = { uTime: { value: 0 }, uIgnite: { value: 0 } };

  // 0 g: spherical flame around a fuel droplet (as in NASA's FLEX droplet tests).
  const zeroU = { uTime: u.uTime, uIgnite: { value: 0 } };
  const zero = new THREE.Group();
  zero.position.set(-2.2, 0, 0);
  zero.add(new THREE.Mesh(new THREE.SphereGeometry(0.62, 64, 48),
    new THREE.ShaderMaterial({ vertexShader: ZERO_G_VERT, fragmentShader: ZERO_G_FRAG, uniforms: zeroU, ...additive })));
  const droplet = new THREE.Mesh(new THREE.SphereGeometry(0.07, 24, 16), new THREE.MeshBasicMaterial({ color: "#dfe6ff", transparent: true }));
  const zeroHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow, color: "#4f6fff", ...additive }));
  zeroHalo.scale.setScalar(2.8);
  zero.add(droplet, zeroHalo);

  // 1 g: teardrop candle flame on a wick, pulled upward by buoyancy.
  const oneU = { uTime: u.uTime, uIgnite: { value: 0 } };
  const profile = Array.from({ length: 41 }, (_, i) => {
    const t = i / 40;
    return new THREE.Vector2(0.38 * Math.pow(Math.sin(Math.PI * Math.pow(t, 0.75)), 0.9) * (1 - 0.35 * t), -0.55 + 1.5 * t);
  });
  const one = new THREE.Group();
  one.position.set(0, -0.1, 0);
  one.add(new THREE.Mesh(new THREE.LatheGeometry(profile, 64),
    new THREE.ShaderMaterial({ vertexShader: ONE_G_VERT, fragmentShader: ONE_G_FRAG, uniforms: oneU, ...additive })));
  const wick = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.03, 0.22, 12), new THREE.MeshBasicMaterial({ color: "#2a2d36" }));
  wick.position.y = -0.62;
  const oneHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow, color: "#ff9a3c", ...additive }));
  oneHalo.scale.set(2.2, 3.0, 1);
  oneHalo.position.y = 0.25;
  one.add(wick, oneHalo);

  // Moon: never tested, so its flame is an empty dashed shell.
  const moonU = { uIgnite: { value: 0 }, uLight: { value: new THREE.Vector3(-1, 0.4, 0.8) } };
  const moon = new THREE.Group();
  moon.position.set(2.2, 0, 0);
  const moonBall = new THREE.Mesh(new THREE.SphereGeometry(0.42, 64, 48),
    new THREE.ShaderMaterial({ vertexShader: MOON_VERT, fragmentShader: MOON_FRAG, uniforms: moonU, transparent: true }));
  const ringFront = dashedRing(0.78, "#8e98ae");
  const ringTilt = dashedRing(0.78, "#8e98ae");
  ringTilt.rotation.x = Math.PI * 0.42;
  moon.add(moonBall, ringFront, ringTilt);
  const ringPoints = 161;

  scene.add(zero, one, moon);

  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pointer = { x: 0, y: 0 };
  const cam = { x: 0, y: 0 };
  const start = performance.now();
  let frame = 0;
  let visible = true;

  const resize = () => {
    const w = box.clientWidth, h = box.clientHeight || w / 2;
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    camera.aspect = w / h;
    // Fit 6.6 units across so the three objects sit at the centres of the label columns below.
    camera.position.z = 6.6 / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect);
    camera.updateProjectionMatrix();
  };

  const render = (now: number) => {
    const t = still ? 10 : (now - start) / 1000;
    u.uTime.value = t;
    zeroU.uIgnite.value = ease((t - 0.2) / 1.0);
    oneU.uIgnite.value = ease((t - 0.9) / 1.0);
    moonU.uIgnite.value = ease((t - 1.5) / 0.8);
    const draw = Math.round(ringPoints * ease((t - 1.9) / 1.0));
    ringFront.geometry.setDrawRange(0, draw);
    ringTilt.geometry.setDrawRange(0, draw);
    (droplet.material as THREE.MeshBasicMaterial).opacity = zeroU.uIgnite.value;
    zeroHalo.material.opacity = 0.55 * zeroU.uIgnite.value;
    oneHalo.material.opacity = (0.45 + 0.05 * Math.sin(t * 9)) * oneU.uIgnite.value;
    moonBall.rotation.y = t * 0.15;
    ringFront.rotation.z = t * 0.12;
    ringTilt.rotation.z = -t * 0.08;

    cam.x += (pointer.x * 0.35 - cam.x) * 0.05;
    cam.y += (pointer.y * 0.2 - cam.y) * 0.05;
    camera.position.x = cam.x;
    camera.position.y = cam.y;
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  };

  const loop = (now: number) => {
    render(now);
    if (visible) frame = requestAnimationFrame(loop);
  };

  const onPointer = (e: PointerEvent) => {
    pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -((e.clientY / window.innerHeight) * 2 - 1);
  };
  const ro = new ResizeObserver(() => { resize(); if (still) render(performance.now()); });
  const io = new IntersectionObserver(([entry]) => {
    const was = visible;
    visible = entry.isIntersecting;
    if (visible && !was && !still) frame = requestAnimationFrame(loop);
  });

  resize();
  ro.observe(box);
  if (still) {
    render(performance.now());
  } else {
    io.observe(box);
    window.addEventListener("pointermove", onPointer);
    frame = requestAnimationFrame(loop);
  }

  return () => {
    cancelAnimationFrame(frame);
    window.removeEventListener("pointermove", onPointer);
    ro.disconnect();
    io.disconnect();
    scene.traverse((o) => {
      const m = o as THREE.Mesh;
      m.geometry?.dispose();
      const mat = m.material as THREE.Material | undefined;
      mat?.dispose();
    });
    glow.dispose();
    renderer.dispose();
    renderer.domElement.remove();
  };
}
