import type { Metadata } from "next";

import { MissionPlanner } from "@/components/mission-planner";

export const metadata: Metadata = { title: "FlameCheck: mission planner" };

export default function PlanPage() {
  return (
    <main className="mx-auto w-full max-w-5xl space-y-10 px-4 py-8 sm:py-12">
      <section className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
          Mission planner: which materials has NASA burned at your atmosphere?
        </h1>
        <p className="text-lg leading-relaxed text-muted-foreground">
          Enter the oxygen and pressure your habitat will run at. FlameCheck lists every material NASA PSI tested near
          those conditions, with outcomes, and flags the materials NASA never tested there.
        </p>
      </section>
      <MissionPlanner />
    </main>
  );
}
