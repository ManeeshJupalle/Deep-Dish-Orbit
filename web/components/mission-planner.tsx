"use client";

import { useEffect, useMemo, useState } from "react";

import { type GravityFilter, OUTCOME_ORDER, type OutcomeKey, plan } from "@/components/mission-planner-logic";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getTests, usingFixtures } from "@/lib/api";
import type { TestRow } from "@/lib/types";

const OUTCOME_LABEL: Record<OutcomeKey, string> = {
  burned: "burned",
  ignited: "ignited",
  extinguished: "extinguished",
  no_ignition: "no ignition",
  other: "other",
  not_recorded: "not recorded",
};

const GRAVITY_OPTIONS: { value: GravityFilter; label: string }[] = [
  { value: "all", label: "All tests" },
  { value: "0", label: "0 g (orbit) only" },
  { value: "1", label: "1 g (Earth) only" },
];

const fmt = (v: number | null, unit: string) => (v === null ? null : `${v}${unit}`);

function GravityTag({ g }: { g: number | null }) {
  if (g === 0) return <span className="rounded border border-zero-g px-1.5 py-0.5 text-xs text-zero-g">0 g</span>;
  if (g === 1) return <span className="rounded border border-one-g px-1.5 py-0.5 text-xs text-one-g">1 g</span>;
  return <span className="rounded border border-dashed border-gap px-1.5 py-0.5 text-xs text-gap">gravity not reported</span>;
}

function NumberField(props: { id: string; label: string; value: string; onChange: (v: string) => void; step?: string }) {
  return (
    <div className="space-y-1">
      <Label htmlFor={props.id}>{props.label}</Label>
      <Input
        id={props.id}
        type="number"
        min={0}
        step={props.step ?? "any"}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
      />
    </div>
  );
}

export function MissionPlanner() {
  const [rows, setRows] = useState<TestRow[] | null>(null);
  const [error, setError] = useState<string | null>(
    usingFixtures ? "The Mission planner reads live data. Set NEXT_PUBLIC_API_URL to the FlameCheck API and reload." : null,
  );
  const [o2, setO2] = useState("34");
  const [pressure, setPressure] = useState("70.3");
  const [o2Window, setO2Window] = useState("3");
  const [pressureWindow, setPressureWindow] = useState("15");
  const [gravity, setGravity] = useState<GravityFilter>("all");

  useEffect(() => {
    if (usingFixtures) return;
    getTests()
      .then(setRows)
      .catch((e: Error) => setError(`${e.message} Check that the API is running, then reload.`));
  }, []);

  const input = useMemo(() => {
    const vals = [o2, pressure, o2Window, pressureWindow].map((v) => (v.trim() === "" ? NaN : Number(v)));
    if (vals.some((v) => !Number.isFinite(v) || v < 0)) return null;
    const [a, b, c, d] = vals;
    return { o2: a, pressure: b, o2Window: c, pressureWindow: d, gravity };
  }, [o2, pressure, o2Window, pressureWindow, gravity]);

  const result = useMemo(() => (rows && input ? plan(rows, input) : null), [rows, input]);

  if (error) {
    return (
      <p role="alert" className="rounded-lg border-l-4 border-destructive bg-card p-4 text-sm">
        {error}
      </p>
    );
  }

  return (
    <div className="space-y-10">
      <form className="space-y-4 rounded-xl border border-border bg-card p-4 sm:p-5" onSubmit={(e) => e.preventDefault()}>
        <fieldset className="space-y-2">
          <legend className="text-sm font-semibold">Habitat atmosphere</legend>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <NumberField id="plan-o2" label="Oxygen %" value={o2} onChange={setO2} />
            <NumberField id="plan-pressure" label="Pressure kPa" value={pressure} onChange={setPressure} />
            <div className="space-y-1">
              <Label htmlFor="plan-gravity">Gravity of tests</Label>
              <select
                id="plan-gravity"
                value={gravity}
                onChange={(e) => setGravity(e.target.value as GravityFilter)}
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2 text-sm focus-visible:outline-2 focus-visible:outline-ring"
              >
                {GRAVITY_OPTIONS.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </fieldset>
        <fieldset className="space-y-2">
          <legend className="text-sm font-semibold">How near counts as &quot;near&quot;</legend>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <NumberField id="plan-o2-window" label="Oxygen ± percentage points" value={o2Window} onChange={setO2Window} />
            <NumberField id="plan-p-window" label="Pressure ± kPa" value={pressureWindow} onChange={setPressureWindow} />
          </div>
          <p className="text-sm text-muted-foreground">
            A test is near when its oxygen is within the oxygen window <strong>and</strong> its pressure is within the
            pressure window. If NASA did not report the pressure, the test counts as near on oxygen alone and is marked
            &quot;pressure not reported&quot;. Tests with no reported oxygen are never near.
          </p>
        </fieldset>
        {!input && (
          <p role="alert" className="text-sm text-destructive">
            Enter a number of 0 or more in every field.
          </p>
        )}
      </form>

      <p className="rounded-lg border-2 border-dashed border-gap bg-card p-4 text-sm">
        <strong>No NASA PSI test was run at lunar or Martian gravity.</strong> Every test here is either 0 g (orbit) or 1 g
        (Earth). Results below bound what a Moon or Mars habitat might see; they are not predictions for it.
      </p>

      {!rows ? (
        <Skeleton className="h-96 w-full" aria-label="Loading NASA tests" />
      ) : result ? (
        <>
          <section aria-labelledby="near-heading" className="space-y-3">
            <h2 id="near-heading" className="text-xl font-bold tracking-tight">
              Materials NASA tested near these conditions
            </h2>
            <p className="text-sm text-muted-foreground" aria-live="polite">
              {result.nearCount} near {result.nearCount === 1 ? "test" : "tests"} across {result.near.length}{" "}
              {result.near.length === 1 ? "material" : "materials"}. Sorted: any burned first, then ignited, then
              extinguished or no ignition, then other, then outcome not recorded.
            </p>
            {result.near.length === 0 ? (
              <p className="rounded-lg border-2 border-dashed border-gap bg-card p-4 text-sm">
                <strong>No direct data.</strong> No NASA PSI test falls inside these windows. See the closest tests per
                material below.
              </p>
            ) : (
              <div className="rounded-xl border border-border bg-card">
                <Table>
                  <TableCaption className="sr-only">Materials with NASA tests near the habitat atmosphere</TableCaption>
                  <TableHeader>
                    <TableRow>
                      <TableHead scope="col">Material</TableHead>
                      <TableHead scope="col">Near tests</TableHead>
                      <TableHead scope="col">Outcomes</TableHead>
                      <TableHead scope="col">Gravity</TableHead>
                      <TableHead scope="col">Closest tests</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.near.map((m) => (
                      <TableRow key={m.key} className="align-top">
                        <TableCell className="font-medium whitespace-normal">{m.label}</TableCell>
                        <TableCell>{m.tests.length}</TableCell>
                        <TableCell className="whitespace-normal">
                          <ul className="space-y-0.5">
                            {OUTCOME_ORDER.filter((k) => m.outcomes[k] > 0).map((k) => (
                              <li key={k} className={k === "not_recorded" ? "text-gap" : undefined}>
                                {OUTCOME_LABEL[k]}: {m.outcomes[k]}
                              </li>
                            ))}
                          </ul>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {m.gravities.map((g) => (
                              <GravityTag key={String(g)} g={g} />
                            ))}
                          </div>
                        </TableCell>
                        <TableCell className="whitespace-normal">
                          <ul className="space-y-1">
                            {m.tests.slice(0, 3).map((t) => (
                              <li key={t.row.test_id}>
                                <a
                                  href={t.row.source_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="font-mono text-zero-g underline underline-offset-2"
                                >
                                  {t.row.test_id}
                                </a>{" "}
                                <span className="text-muted-foreground">
                                  {fmt(t.row.o2_pct, "% O₂")},{" "}
                                  {t.pressureMissing ? (
                                    <span className="text-gap">pressure not reported</span>
                                  ) : (
                                    fmt(t.row.pressure_kpa, " kPa")
                                  )}
                                  , {OUTCOME_LABEL[t.row.outcome ?? "not_recorded"]}
                                </span>
                              </li>
                            ))}
                          </ul>
                          {m.tests.length > 3 && (
                            <p className="mt-1 text-xs text-muted-foreground">+{m.tests.length - 3} more near {m.tests.length === 4 ? "test" : "tests"}</p>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </section>

          <section aria-labelledby="untested-heading" className="space-y-3 rounded-xl border-2 border-dashed border-gap bg-card p-4 sm:p-5">
            <h2 id="untested-heading" className="text-xl font-bold tracking-tight">
              Not tested near these conditions ({result.untested.length})
            </h2>
            <p className="text-sm text-muted-foreground">
              NASA has data on these materials{gravity === "all" ? "" : " at this gravity"}, but none inside the windows
              above. The closest test is shown so you can see how far off it is. Sorted closest first.
            </p>
            <ul className="divide-y divide-border text-sm">
              {result.untested.map((u) => (
                <li key={u.key} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-2">
                  <span className="font-medium">
                    <span className="sr-only">Not tested near: </span>
                    {u.label}
                  </span>
                  <span className="text-muted-foreground">
                    {u.closest ? (
                      <>
                        closest test:{" "}
                        <a
                          href={u.closest.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-mono text-zero-g underline underline-offset-2"
                        >
                          {u.closest.test_id}
                        </a>{" "}
                        {fmt(u.closest.o2_pct, "% O₂")},{" "}
                        {u.closest.pressure_kpa === null ? (
                          <span className="text-gap">pressure not reported</span>
                        ) : (
                          fmt(u.closest.pressure_kpa, " kPa")
                        )}
                        , {u.closest.gravity_g === null ? "gravity not reported" : `${u.closest.gravity_g} g`}
                      </>
                    ) : (
                      <span className="text-gap">oxygen not reported in any of its {u.testCount} tests</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </>
      ) : null}
    </div>
  );
}
