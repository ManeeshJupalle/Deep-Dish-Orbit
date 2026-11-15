import { AskScreen } from "@/components/ask-screen";
import { FlameScene } from "@/components/flame-scene";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 py-8 sm:py-12">
      <section className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-xl space-y-3">
          <h1 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">
            Ask what NASA&apos;s fire tests in space actually show.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Every answer cites a NASA microgravity combustion test. When NASA never tested your conditions,
            FlameCheck says so instead of guessing.
          </p>
        </div>
        <FlameScene className="w-full max-w-[460px] shrink-0 self-center" />
      </section>
      <AskScreen />
    </main>
  );
}
