"use client";

import { useEffect, useRef, useState } from "react";

import { FlameFigure } from "@/components/flame-figure";

const CASES = [
  { g: "0 g", note: "tested in orbit", tone: "text-zero-g" },
  { g: "1 g", note: "tested on Earth", tone: "text-one-g" },
  { g: "Moon", note: "never tested", tone: "text-gap" },
];

// Live 3D version of FlameFigure. Falls back to the SVG if WebGL is unavailable.
export function FlameScene({ className = "" }: { className?: string }) {
  const box = useRef<HTMLDivElement>(null);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    let stop = () => {};
    let cancelled = false;
    import("@/components/flame-scene-three").then(({ mountFlameScene }) => {
      if (cancelled || !box.current) return;
      try {
        stop = mountFlameScene(box.current);
      } catch {
        setFallback(true);
      }
    });
    return () => {
      cancelled = true;
      stop();
    };
  }, []);

  if (fallback) return <FlameFigure className={className} />;
  return (
    <figure className={className} aria-label="Flames NASA tested at 0 g and 1 g, and the untested Moon case">
      <div ref={box} aria-hidden className="aspect-[2/1] w-full" />
      <figcaption className="grid grid-cols-3 text-center">
        {CASES.map((c) => (
          <p key={c.g} className="leading-tight">
            <span className={`block text-sm font-bold ${c.tone}`}>{c.g}</span>
            <span className="text-xs text-muted-foreground">{c.note}</span>
          </p>
        ))}
      </figcaption>
    </figure>
  );
}
