import { AskScreen } from "@/components/ask-screen";
import { FlameFigure } from "@/components/flame-figure";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 py-8 sm:py-12">
      <section className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-xl space-y-3">
          <h1 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
            Ask what NASA&apos;s fire tests in space actually show.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Every answer cites a NASA microgravity combustion test. When NASA never tested your conditions,
            FlameCheck says so instead of guessing.
          </p>
        </div>
        <FlameFigure className="w-full max-w-[300px] shrink-0" />
      </section>
      <AskScreen />
    </main>
  );
}
