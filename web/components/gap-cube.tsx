"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { SERIES } from "@/components/coverage-map";
import type { CubePoint } from "@/components/gap-cube-three";
import type { CoveragePoint } from "@/lib/types";

const MOON_O2 = 30;
const MOON_KPA = 70.3;

// 3D view of the coverage map: oxygen × pressure × gravity. The 2D map and its table stay the accessible view.
export function GapCube({ points }: { points: CoveragePoint[] }) {
  const box = useRef<HTMLDivElement>(null);
  const overlay = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  const plotted = useMemo(
    () => points.filter((p): p is CubePoint => p.o2_pct !== null && p.pressure_kpa !== null && p.gravity_g !== null),
    [points],
  );

  useEffect(() => {
    let stop = () => {};
    let cancelled = false;
    import("@/components/gap-cube-three").then(({ mountGapCube }) => {
      if (cancelled || !box.current || !overlay.current) return;
      try {
        stop = mountGapCube(box.current, overlay.current, plotted, SERIES);
      } catch {
        setFailed(true);
      }
    });
    return () => {
      cancelled = true;
      stop();
    };
  }, [plotted]);

  const missing = points.length - plotted.length;
  const at = (g: number) => plotted.filter((p) => p.gravity_g === g).length;
  const between = plotted.filter((p) => p.gravity_g > 0 && p.gravity_g < 1).length;
  const inZone = plotted.filter((p) => p.o2_pct >= MOON_O2 && p.pressure_kpa <= MOON_KPA).length;
  const present = Object.keys(SERIES).filter((inv) => plotted.some((p) => p.investigation === inv));

  return (
    <figure className="space-y-3">
      {failed ? (
        <p className="text-sm text-muted-foreground">The 3D cube needs WebGL, which this browser does not offer; the map below shows the same data.</p>
      ) : (
        <>
          <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm" aria-label="Legend">
            {present.map((inv) => (
              <li key={inv} className="flex items-center gap-2">
                <span aria-hidden className="size-3 rounded-full" style={{ background: SERIES[inv] }} />
                {inv} ({plotted.filter((p) => p.investigation === inv).length})
              </li>
            ))}
            <li className="flex items-center gap-2">
              <span aria-hidden className="h-3 w-5 rounded-sm border-2 border-dashed border-gap bg-gap/10" />
              Moon and Mars gravity slices (never tested)
            </li>
          </ul>
          <div className="relative h-[380px] w-full cursor-grab overflow-hidden active:cursor-grabbing sm:h-[460px]">
            <div ref={box} aria-hidden className="absolute inset-0" />
            <div ref={overlay} aria-hidden className="pointer-events-none absolute inset-0" />
          </div>
        </>
      )}
      <figcaption className="max-w-prose text-sm text-muted-foreground">
        Each dot is one NASA PSI test that reports oxygen, pressure and gravity: {plotted.length} of {points.length}{" "}
        tests; the other {missing} miss at least one of the three and are not plotted. {at(0)} sit on the 0 g floor and{" "}
        {at(1)} on the 1 g floor;{" "}
        {between === 0 ? "none was run at Moon or Mars gravity" : `${between} lie between 0 g and 1 g`}.{" "}
        {inZone === 0
          ? "No plotted test falls inside the Moon-base box (≥30% O₂ and ≤70.3 kPa) at any gravity."
          : `${inZone} plotted test${inZone === 1 ? "" : "s"} fall inside the Moon-base oxygen and pressure range (≥30% O₂ and ≤70.3 kPa).`}
      </figcaption>
    </figure>
  );
}
