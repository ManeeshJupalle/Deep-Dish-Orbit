"use client";

import { useState } from "react";

import { EvidenceTable } from "@/components/evidence-table";
import { GapsList } from "@/components/gaps-list";
import { TrustBadge } from "@/components/trust-badge";
import type { AskResponse, ChunkInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

const BANNER = {
  answered: {
    title: "Answered from NASA test data",
    note: "Every sentence below cites a NASA test or document.",
    box: "border-l-4 border-zero-g",
  },
  no_direct_data: {
    title: "No direct data",
    note: "NASA never tested these exact conditions. Nearby results are shown as bounds, not predictions.",
    box: "border-2 border-dashed border-gap",
  },
  out_of_scope: {
    title: "Outside FlameCheck's data",
    note: "FlameCheck only covers NASA PSI fire-safety experiments.",
    box: "border-l-4 border-gap",
  },
};

function flash(testId: string) {
  const row = document.getElementById(`ev-${testId}`);
  if (!row) return;
  row.scrollIntoView({ behavior: "smooth", block: "center" });
  row.classList.remove("cite-flash");
  void row.offsetWidth; // restart the animation
  row.classList.add("cite-flash");
}

function CitationChip({ id, evidenceIds, chunks }: { id: string; evidenceIds: Set<string>; chunks: Map<string, ChunkInfo> }) {
  const chip = "inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs font-semibold align-baseline";
  if (evidenceIds.has(id)) {
    return (
      <button
        type="button"
        onClick={() => flash(id)}
        className={cn(chip, "border-zero-g/40 bg-accent text-zero-g hover:bg-zero-g hover:text-background focus-visible:outline-2 focus-visible:outline-ring")}
        aria-label={`Show test ${id} in the evidence table`}
      >
        {id}
      </button>
    );
  }
  const chunk = chunks.get(id);
  if (chunk) {
    return (
      <a
        href={chunk.source_url}
        target="_blank"
        rel="noreferrer"
        title={chunk.title}
        className={cn(chip, "border-border bg-muted text-ink hover:bg-secondary")}
      >
        {chunk.source_id}
        <span className="sr-only"> ({chunk.title}, opens in a new tab)</span>
      </a>
    );
  }
  return <span className={cn(chip, "border-border text-muted-foreground")}>{id}</span>;
}

// "Watch the verifier work": the model's drafted claims that verify.py removed, struck through, with the reason.
function VerifierPanel({ dropped, checked }: { dropped: AskResponse["dropped"]; checked: number }) {
  const [open, setOpen] = useState(false);
  if (!dropped?.length) {
    if (!checked) return null;
    return (
      <p className="mt-4 border-t border-border pt-3 text-sm text-muted-foreground">
        <span aria-hidden className="text-zero-g">✓</span> Verifier: every claim above was checked against the NASA
        row or document it cites; nothing had to be removed this time.
      </p>
    );
  }
  const n = dropped.length;
  return (
    <div className="mt-4 border-t border-border pt-3">
      <button
        type="button"
        aria-expanded={open}
        aria-controls="verifier-panel"
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-2 rounded-md border border-border px-2.5 py-1 text-sm font-semibold hover:bg-muted focus-visible:outline-2 focus-visible:outline-ring"
      >
        <span aria-hidden className={cn("inline-block transition-transform", open && "rotate-90")}>▸</span>
        Watch the verifier work: {n} drafted claim{n === 1 ? "" : "s"} removed
      </button>
      {open && (
        <div id="verifier-panel" className="mt-3 space-y-2.5">
          <p className="text-sm text-muted-foreground">
            The AI model drafted these, but NASA&apos;s data does not back them, so they never reach the answer.
          </p>
          <ul className="space-y-2">
            {dropped.map((d, i) => (
              <li
                key={i}
                className="claim-in rounded-md border border-dashed border-destructive/50 bg-destructive/5 p-2.5"
                style={{ animationDelay: `${i * 140}ms` }}
              >
                <p className="text-muted-foreground line-through decoration-destructive/80 decoration-2">
                  {d.text}
                  {d.cites.length > 0 && <span className="ml-1 text-xs">[{d.cites.join(", ")}]</span>}
                </p>
                <p className="mt-1 text-sm font-semibold text-destructive">
                  <span className="sr-only">Removed because: </span>✕ {d.reason}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function BoundsPanel({ bounds }: { bounds: AskResponse["bounds"] }) {
  if (!bounds.microgravity.length && !bounds.earth.length) return null;
  const col = (label: string, ids: string[], dot: string, none: string) => (
    <div className="flex-1 rounded-lg border border-border bg-card p-3">
      <p className="mb-1.5 flex items-center gap-2 text-sm font-semibold">
        <span aria-hidden className={cn("size-2.5 rounded-full", dot)} />
        {label}
      </p>
      {ids.length ? (
        <ul className="flex flex-wrap gap-1.5">
          {ids.map((id) => (
            <li key={id}>
              <button
                type="button"
                onClick={() => flash(id)}
                className="rounded-md border border-border px-1.5 py-0.5 text-xs font-semibold hover:bg-muted focus-visible:outline-2 focus-visible:outline-ring"
              >
                {id}
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">{none}</p>
      )}
    </div>
  );
  return (
    <section aria-labelledby="bounds-heading">
      <h3 id="bounds-heading" className="mb-2 text-base font-semibold">
        The closest NASA tests on either side
      </h3>
      <div className="flex flex-col gap-2 sm:flex-row">
        {col("Microgravity (0 g)", bounds.microgravity, "bg-zero-g", "No matching 0 g test")}
        {col("Earth gravity (1 g)", bounds.earth, "bg-one-g", "No matching 1 g test in PSI")}
      </div>
    </section>
  );
}

export function AnswerCard({ data, chunks }: { data: AskResponse; chunks: Map<string, ChunkInfo> }) {
  const banner = BANNER[data.status];
  const evidenceIds = new Set(data.evidence.map((e) => e.test_id));
  return (
    <article className="space-y-6" aria-live="polite">
      <div className={cn("rounded-lg bg-card p-4 sm:p-5", banner.box)}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold tracking-tight">{banner.title}</h2>
            <p className="text-sm text-muted-foreground">{banner.note}</p>
          </div>
          <TrustBadge trust={data.trust} />
        </div>
        <p className="mt-4 max-w-prose text-[1.05rem] leading-relaxed">{data.summary}</p>
        {data.claims.length > 0 && (
          <ul className="mt-4 space-y-2.5 border-t border-border pt-4">
            {data.claims.map((c, i) => (
              <li key={i} className="claim-in max-w-prose leading-relaxed" style={{ animationDelay: `${150 + i * 140}ms` }}>
                {c.text}{" "}
                <span className="inline-flex flex-wrap gap-1">
                  {c.cites.map((id) => (
                    <CitationChip key={id} id={id} evidenceIds={evidenceIds} chunks={chunks} />
                  ))}
                </span>
              </li>
            ))}
          </ul>
        )}
        <VerifierPanel dropped={data.dropped} checked={data.claims.length} />
      </div>
      {data.status === "no_direct_data" && <BoundsPanel bounds={data.bounds} />}
      <GapsList gaps={data.gaps} />
      <EvidenceTable evidence={data.evidence} />
    </article>
  );
}
