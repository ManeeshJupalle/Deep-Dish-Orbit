import type { Metadata } from "next";

import { ExploreScreen } from "@/components/explore-screen";

export const metadata: Metadata = { title: "FlameCheck: explore NASA's fire tests" };

export default function ExplorePage() {
  return (
    <main className="mx-auto w-full max-w-5xl space-y-10 px-4 py-8 sm:py-12">
      <section className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
          What NASA has tested, and what it hasn&apos;t
        </h1>
        <p className="text-lg leading-relaxed text-muted-foreground">
          A Moon base will likely run at 30% oxygen or more and 70.3 kPa (10.2 psi) or less. This map puts every NASA
          PSI fire test FlameCheck uses next to that box.
        </p>
      </section>
      <ExploreScreen />
    </main>
  );
}
