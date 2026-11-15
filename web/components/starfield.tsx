"use client";

import { useEffect, useRef } from "react";

// Three depth layers drifting at different speeds, like the view from orbit. Decorative only.
const LAYERS = [
  { count: 140, speed: 0.004, size: 0.6, alpha: 0.45 },
  { count: 70, speed: 0.009, size: 0.9, alpha: 0.7 },
  { count: 25, speed: 0.018, size: 1.3, alpha: 0.95 },
];

type Star = { x: number; y: number; layer: number; phase: number };

export function Starfield() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const stars: Star[] = LAYERS.flatMap((l, layer) =>
      Array.from({ length: l.count }, () => ({ x: Math.random(), y: Math.random(), layer, phase: Math.random() * 6.3 })),
    );
    let w = 0, h = 0, frame = 0, last = performance.now();

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (t: number) => {
      const dt = Math.min(t - last, 50) / 1000;
      last = t;
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        const l = LAYERS[s.layer];
        if (!still) s.x = (s.x - l.speed * dt + 1) % 1;
        const twinkle = still ? 1 : 0.75 + 0.25 * Math.sin(t / 900 + s.phase);
        ctx.globalAlpha = l.alpha * twinkle;
        ctx.fillStyle = s.layer === 2 && s.phase < 1 ? "#cdd8ff" : "#ffffff";
        ctx.beginPath();
        ctx.arc(s.x * w, s.y * h, l.size, 0, Math.PI * 2);
        ctx.fill();
      }
      if (!still) frame = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    frame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={ref} aria-hidden className="pointer-events-none fixed inset-0 -z-10 h-full w-full" />;
}
