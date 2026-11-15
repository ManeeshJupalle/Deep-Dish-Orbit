// Pure filtering logic for the Mission planner. No guessing: null values stay null and are labelled in the UI.
import type { Outcome, TestRow } from "@/lib/types";

export type OutcomeKey = Outcome | "not_recorded";
export type GravityFilter = "all" | "0" | "1";

export interface PlanInput {
  o2: number;
  pressure: number;
  o2Window: number;
  pressureWindow: number;
  gravity: GravityFilter;
}

export interface NearTest {
  row: TestRow;
  pressureMissing: boolean;
  distance: number;
}

export interface NearMaterial {
  key: string;
  label: string;
  tests: NearTest[]; // sorted closest first
  outcomes: Record<OutcomeKey, number>;
  gravities: (number | null)[];
  rank: number;
}

export interface UntestedMaterial {
  key: string;
  label: string;
  closest: TestRow | null; // null: no test of this material has an oxygen value (in the gravity filter)
  testCount: number;
}

export const OUTCOME_ORDER: OutcomeKey[] = ["burned", "ignited", "extinguished", "no_ignition", "other", "not_recorded"];

export const normaliseMaterial = (m: string | null) => (m ?? "").trim().toLowerCase() || "material not reported";

// Scaled distance: each axis divided by its window. A missing pressure adds nothing (it is labelled instead).
function distance(r: TestRow, p: PlanInput): number {
  const dO2 = r.o2_pct === null ? Infinity : (r.o2_pct - p.o2) / p.o2Window;
  const dP = r.pressure_kpa === null ? 0 : (r.pressure_kpa - p.pressure) / p.pressureWindow;
  return Math.hypot(dO2, dP);
}

// Near = O2 within the window AND (pressure within the window OR pressure not reported).
export function isNear(r: TestRow, p: PlanInput): boolean {
  if (r.o2_pct === null || Math.abs(r.o2_pct - p.o2) > p.o2Window) return false;
  return r.pressure_kpa === null || Math.abs(r.pressure_kpa - p.pressure) <= p.pressureWindow;
}

function rankOf(o: Record<OutcomeKey, number>): number {
  if (o.burned) return 0;
  if (o.ignited) return 1;
  if (o.extinguished || o.no_ignition) return 2;
  if (o.other) return 3;
  return 4;
}

export function plan(rows: TestRow[], p: PlanInput): { near: NearMaterial[]; untested: UntestedMaterial[]; nearCount: number } {
  const inGravity = rows.filter((r) => p.gravity === "all" || r.gravity_g === Number(p.gravity));
  const groups = new Map<string, { label: string; rows: TestRow[] }>();
  for (const r of inGravity) {
    const key = normaliseMaterial(r.material);
    const g = groups.get(key) ?? { label: r.material?.trim() || "Material not reported", rows: [] };
    g.rows.push(r);
    groups.set(key, g);
  }

  const near: NearMaterial[] = [];
  const untested: UntestedMaterial[] = [];
  let nearCount = 0;
  for (const [key, g] of groups) {
    const tests = g.rows
      .filter((r) => isNear(r, p))
      .map((row) => ({ row, pressureMissing: row.pressure_kpa === null, distance: distance(row, p) }))
      .sort((a, b) => a.distance - b.distance);
    if (tests.length === 0) {
      const withO2 = g.rows.filter((r) => r.o2_pct !== null).sort((a, b) => distance(a, p) - distance(b, p));
      untested.push({ key, label: g.label, closest: withO2[0] ?? null, testCount: g.rows.length });
      continue;
    }
    nearCount += tests.length;
    const outcomes = Object.fromEntries(OUTCOME_ORDER.map((k) => [k, 0])) as Record<OutcomeKey, number>;
    for (const t of tests) outcomes[t.row.outcome ?? "not_recorded"] += 1;
    const gravities = [...new Set(tests.map((t) => t.row.gravity_g))].sort((a, b) => (a ?? 9) - (b ?? 9));
    near.push({ key, label: g.label, tests, outcomes, gravities, rank: rankOf(outcomes) });
  }
  near.sort((a, b) => a.rank - b.rank || b.tests.length - a.tests.length || a.key.localeCompare(b.key));
  untested.sort((a, b) => (a.closest ? distance(a.closest, p) : Infinity) - (b.closest ? distance(b.closest, p) : Infinity) || a.key.localeCompare(b.key));
  return { near, untested, nearCount };
}
