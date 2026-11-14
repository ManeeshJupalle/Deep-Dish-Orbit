"use client";

import {
  CartesianGrid,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { CoveragePoint } from "@/lib/types";

// Categorical slots 1-3 of the validated palette (all-pairs safe for scatter).
// Fixed per investigation, never by rank. Aqua is under 3:1 contrast, so the legend
// and the table view below carry identity too.
export const SERIES: Record<string, string> = {
  FLEX: "#2a78d6",
  "BASS-II": "#eb6834",
  "SAFFIRE-II": "#1baf7a",
};
const MOON_O2 = 30;
const MOON_KPA = 70.3;
const Y_DOMAIN: [number, number] = [10, 40];

type Point = CoveragePoint & { x: number; y: number };

function jitter(id: string) {
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) % 1000;
  return (h / 1000 - 0.5) * 0.6;
}

function Dot(props: { cx?: number; cy?: number; fill?: string }) {
  const { cx = 0, cy = 0, fill } = props;
  return <circle cx={cx} cy={cy} r={4} fill={fill} stroke="#ffffff" strokeWidth={1.5} />;
}

function Tip({ active, payload }: { active?: boolean; payload?: { payload: Point }[] }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-xs shadow-sm">
      <p className="font-semibold">{p.test_id}</p>
      <p className="text-muted-foreground">{p.investigation}</p>
      <p>O₂ {p.o2_pct}%</p>
      <p>{p.pressure_kpa === null ? "Pressure not reported" : `${p.pressure_kpa} kPa`}</p>
      <p>{p.gravity_g === 1 ? "1 g" : "0 g"}</p>
    </div>
  );
}

const axisTick = { fill: "var(--muted-foreground)", fontSize: 12 };

export function CoverageMap({ points }: { points: CoveragePoint[] }) {
  const both = points.filter((p) => p.o2_pct !== null && p.pressure_kpa !== null);
  const o2Only = points.filter((p) => p.o2_pct !== null && p.pressure_kpa === null);
  const neither = points.length - both.length - o2Only.length;
  const inZone = both.filter((p) => p.o2_pct! >= MOON_O2 && p.pressure_kpa! <= MOON_KPA);
  const stripGroups = [...new Set(o2Only.map((p) => p.investigation))];

  const main = Object.keys(SERIES).map((inv) => ({
    inv,
    data: both.filter((p) => p.investigation === inv).map((p) => ({ ...p, x: p.pressure_kpa!, y: p.o2_pct! })),
  }));
  const strip = Object.keys(SERIES).map((inv) => ({
    inv,
    data: o2Only
      .filter((p) => p.investigation === inv)
      .map((p) => ({ ...p, x: stripGroups.indexOf(inv) + 0.5 + jitter(p.test_id), y: p.o2_pct! })),
  }));
  const present = Object.keys(SERIES).filter((inv) => points.some((p) => p.investigation === inv && p.o2_pct !== null));

  return (
    <figure className="space-y-3">
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm" aria-label="Legend">
        {present.map((inv) => (
          <li key={inv} className="flex items-center gap-2">
            <span aria-hidden className="size-3 rounded-full" style={{ background: SERIES[inv] }} />
            {inv} ({points.filter((p) => p.investigation === inv && p.o2_pct !== null).length})
          </li>
        ))}
        <li className="flex items-center gap-2">
          <span aria-hidden className="h-3 w-5 rounded-sm border-2 border-dashed border-gap bg-gap/10" />
          Moon base: ≥30% O₂ and ≤70.3 kPa (never tested)
        </li>
      </ul>

      <div className="flex rounded-lg border border-border bg-card p-2">
        <div className="w-28 shrink-0 sm:w-36" aria-label="Tests with oxygen but no reported pressure">
          <ResponsiveContainer width="100%" height={360}>
            <ScatterChart margin={{ top: 10, right: 4, bottom: 30, left: 0 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis
                type="number"
                dataKey="x"
                domain={[0, Math.max(1, stripGroups.length)]}
                ticks={stripGroups.map((_, i) => i + 0.5)}
                tickFormatter={(v: number) => stripGroups[Math.round(v - 0.5)] ?? ""}
                tick={{ ...axisTick, fontSize: 10 }}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                label={{ value: "Pressure not reported", position: "bottom", offset: 12, ...axisTick, fontSize: 11 }}
              />
              <YAxis
                type="number"
                dataKey="y"
                domain={Y_DOMAIN}
                tick={axisTick}
                tickLine={false}
                axisLine={false}
                width={36}
                label={{ value: "O₂ %", angle: -90, position: "insideLeft", offset: 8, ...axisTick }}
              />
              <Tooltip content={<Tip />} cursor={false} />
              {strip.map((s) =>
                s.data.length ? (
                  <Scatter key={s.inv} name={s.inv} data={s.data} fill={SERIES[s.inv]} shape={<Dot />} isAnimationActive={false} />
                ) : null,
              )}
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="min-w-0 flex-1" aria-label="Tests by oxygen and pressure">
          <ResponsiveContainer width="100%" height={360}>
            <ScatterChart margin={{ top: 10, right: 16, bottom: 30, left: 0 }}>
              <CartesianGrid stroke="var(--border)" />
              <ReferenceArea
                x1={0}
                x2={MOON_KPA}
                y1={MOON_O2}
                y2={Y_DOMAIN[1]}
                fill="var(--gap)"
                fillOpacity={0.08}
                stroke="var(--gap)"
                strokeDasharray="6 5"
                strokeWidth={1.5}
                label={{ value: "Moon base", position: "insideTopLeft", fill: "var(--ink)", fontSize: 12 }}
              />
              <ReferenceLine
                x={101.3}
                stroke="var(--muted-foreground)"
                strokeDasharray="2 4"
                label={{ value: "1 atm", position: "insideTopRight", fill: "var(--muted-foreground)", fontSize: 11 }}
              />
              <XAxis
                type="number"
                dataKey="x"
                domain={[0, 120]}
                ticks={[0, 20, 40, 60, 80, 100, 120]}
                tick={axisTick}
                tickLine={false}
                axisLine={{ stroke: "var(--border)" }}
                label={{ value: "Pressure (kPa)", position: "bottom", offset: 12, ...axisTick }}
              />
              <YAxis type="number" dataKey="y" domain={Y_DOMAIN} tick={axisTick} tickLine={false} axisLine={false} width={28} />
              <Tooltip content={<Tip />} cursor={{ strokeDasharray: "3 3" }} />
              {main.map((s) =>
                s.data.length ? (
                  <Scatter key={s.inv} name={s.inv} data={s.data} fill={SERIES[s.inv]} shape={<Dot />} isAnimationActive={false} />
                ) : null,
              )}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <figcaption className="max-w-prose text-sm text-muted-foreground">
        Each dot is one NASA PSI test. {both.length} of {points.length} tests report both oxygen and pressure;{" "}
        {o2Only.length} report oxygen only (left strip); {neither} report neither.{" "}
        {inZone.length === 0
          ? "No test falls inside the Moon-base box"
          : `${inZone.length} test${inZone.length === 1 ? "" : "s"} fall inside the Moon-base box`}
        , and none was run at lunar gravity.
      </figcaption>

      <details className="text-sm">
        <summary className="cursor-pointer text-zero-g underline underline-offset-2">Show the plotted tests as a table</summary>
        <div className="mt-2 max-h-80 overflow-auto rounded-lg border border-border bg-card">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-muted">
              <tr>
                <th className="px-3 py-1.5">Test</th>
                <th className="px-3 py-1.5">Investigation</th>
                <th className="px-3 py-1.5 text-right">O₂ %</th>
                <th className="px-3 py-1.5 text-right">Pressure kPa</th>
              </tr>
            </thead>
            <tbody>
              {[...both, ...o2Only].map((p) => (
                <tr key={p.test_id} className="border-t border-border">
                  <td className="px-3 py-1">{p.test_id}</td>
                  <td className="px-3 py-1">{p.investigation}</td>
                  <td className="px-3 py-1 text-right">{p.o2_pct}</td>
                  <td className="px-3 py-1 text-right">{p.pressure_kpa ?? "not reported"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </figure>
  );
}
