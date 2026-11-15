"use client";

import { useEffect, useState } from "react";

import { CoverageMap } from "@/components/coverage-map";
import { GapCube } from "@/components/gap-cube";
import { InvestigationCompare } from "@/components/investigation-compare";
import { Skeleton } from "@/components/ui/skeleton";
import { getCoverage, getInvestigations, usingFixtures } from "@/lib/api";
import type { CoveragePoint, Investigation } from "@/lib/types";

export function ExploreScreen() {
  const [points, setPoints] = useState<CoveragePoint[] | null>(null);
  const [investigations, setInvestigations] = useState<Investigation[] | null>(null);
  const [error, setError] = useState<string | null>(
    usingFixtures ? "The Explore page reads live data. Set NEXT_PUBLIC_API_URL to the FlameCheck API and reload." : null,
  );

  useEffect(() => {
    if (usingFixtures) return;
    Promise.all([getCoverage(), getInvestigations()])
      .then(([p, i]) => {
        setPoints(p);
        setInvestigations(i);
      })
      .catch((e: Error) => setError(`${e.message} Check that the API is running, then reload.`));
  }, []);

  if (error) {
    return (
      <p role="alert" className="rounded-lg border-l-4 border-destructive bg-card p-4 text-sm">
        {error}
      </p>
    );
  }
  if (!points || !investigations) {
    return <Skeleton className="h-96 w-full" aria-label="Loading the coverage map" />;
  }
  return (
    <div className="space-y-10">
      <section aria-labelledby="cube-heading" className="space-y-3">
        <h2 id="cube-heading" className="text-xl font-bold tracking-tight">
          Gap cube: oxygen × pressure × gravity
        </h2>
        <p className="text-sm text-muted-foreground">
          Drag to turn it. NASA&apos;s tests can only sit on the 0 g and 1 g floors; the Moon and Mars slices are empty.
        </p>
        <GapCube points={points} />
      </section>
      <section aria-labelledby="map-heading" className="space-y-3">
        <h2 id="map-heading" className="text-xl font-bold tracking-tight">
          Coverage map: oxygen vs pressure
        </h2>
        <CoverageMap points={points} />
      </section>
      <section aria-labelledby="compare-heading" className="space-y-3">
        <h2 id="compare-heading" className="text-xl font-bold tracking-tight">
          The investigations behind the data
        </h2>
        <InvestigationCompare investigations={investigations} />
      </section>
    </div>
  );
}
