import type { Metadata } from "next";

export const metadata: Metadata = { title: "FlameCheck: how it works" };

const SOURCES = [
  { id: "BASS-II", psi: "PSI-25", what: "129 solid-fuel flame tests on the ISS (PMMA, SIBAL cotton-fiberglass, Nomex, wax)" },
  { id: "SAFFIRE-II", psi: "PSI-99", what: "9 large samples burned in a Cygnus cargo ship, each with its 1 g comparison" },
  { id: "SAFFIRE-III", psi: "PSI-100", what: "2 large SIBAL fabric burns in Cygnus" },
  { id: "FLEX", psi: "PSI-69", what: "274 droplet burns, some put out with CO₂ or helium" },
];

const STEPS = [
  { title: "Find the closest tests", body: "Your material, oxygen, pressure and gravity are matched against 423 NASA test rows. Missing values never earn credit." },
  { title: "Draft from evidence only", body: "GPT-5.6-luna (Azure OpenAI) writes short claims using only those rows and NASA text, each citing a test or document id." },
  { title: "Verify every claim", body: "Any claim with an unknown citation, a number not in the cited row, an outcome (\"burned\") the cited test doesn't record, or a Moon/Mars claim not stated as a 0 g or 1 g bound is dropped before you see it." },
  { title: "Answer, or say no direct data", body: "If nothing survives, or NASA never tested your conditions, FlameCheck says so and shows the tests that bound the answer." },
];

export default function AboutPage() {
  return (
    <main className="mx-auto w-full max-w-3xl space-y-10 px-4 py-8 sm:py-12">
      <section className="space-y-3">
        <h1 className="text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl">How FlameCheck stays honest</h1>
        <p className="text-lg leading-relaxed text-muted-foreground">
          FlameCheck answers fire-safety questions only from NASA microgravity combustion experiments. Nothing the AI
          writes reaches the screen until it has been checked against the data.
        </p>
      </section>

      <section aria-labelledby="method" className="space-y-4">
        <h2 id="method" className="text-xl font-bold tracking-tight">Method</h2>
        <ol className="space-y-3">
          {STEPS.map((s, i) => (
            <li
              key={s.title}
              className={`flex gap-4 rounded-lg bg-card p-4 ${i === 2 ? "border-2 border-zero-g" : "border border-border"}`}
            >
              <span aria-hidden className="text-2xl font-extrabold leading-none text-zero-g">{i + 1}</span>
              <div>
                <h3 className="font-semibold">{s.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{s.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="score" className="space-y-3">
        <h2 id="score" className="text-xl font-bold tracking-tight">Test-set score</h2>
        <p className="leading-relaxed">
          20 questions written from the data: 6 lookups, 5 comparisons, 4 suppression questions and 5 questions NASA has
          no data for. Each is scored on the right status, real citations, the required tests cited, and no invented
          values. The first run scored <strong>17 of 20</strong>. After fixing the three failures, FlameCheck scores{" "}
          <strong>20 of 20</strong> with GPT-5.6-luna drafting the answers, and 20 of 20 without a model. Six models
          all scored 20 of 20 on the same questions, because the verifier removed the drafted claims NASA&apos;s data
          did not back (5 for GPT-5.6-luna, 16 for GPT-4.1-mini); GPT-5.6-luna was about twice as fast as GPT-5-mini
          and the cheapest of the paid models.
        </p>
      </section>

      <section aria-labelledby="data" className="space-y-3">
        <h2 id="data" className="text-xl font-bold tracking-tight">NASA data used</h2>
        <ul className="space-y-2">
          {SOURCES.map((s) => (
            <li key={s.id} className="leading-relaxed">
              <a
                href={`https://psi.nasa.gov/physci/repo/data/investigations/${s.psi}`}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-zero-g underline underline-offset-2 hover:no-underline"
              >
                {s.id} ({s.psi})
              </a>
              : {s.what}
            </li>
          ))}
        </ul>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Experimental tables and descriptions from NASA Physical Sciences Informatics (PSI), plus 9 paper abstracts from
          the NASA Technical Reports Server. When a value is missing from NASA&apos;s table it stays empty; nothing is
          filled in or interpolated. PSI has no partial-gravity fire data, so Moon and Mars questions always get
          &ldquo;no direct data&rdquo; with 0 g and 1 g bounds.
        </p>
      </section>

      <section aria-labelledby="ai" className="space-y-3">
        <h2 id="ai" className="text-xl font-bold tracking-tight">Use of AI</h2>
        <p className="leading-relaxed">
          GPT-5.6-luna on Azure OpenAI drafts the answers. Google Gemini is the fallback drafter and embeds the NASA
          text for search. Claude Code helped write the code, the data pipeline and this site. The data checks, the
          verifier and the test set are there so no model is trusted on its own.
        </p>
      </section>

      <p className="text-sm text-muted-foreground">
        FlameCheck summarizes NASA test data. It is not an engineering safety review.
      </p>
    </main>
  );
}
