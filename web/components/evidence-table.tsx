import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Evidence } from "@/lib/types";

const OUTCOME: Record<string, string> = {
  burned: "Burned",
  extinguished: "Extinguished",
  no_ignition: "Did not ignite",
  ignited: "Ignited",
  other: "Other (see PSI)",
};

function Missing() {
  return (
    <span className="text-muted-foreground" title="Not reported by NASA">
      —<span className="sr-only">not reported</span>
    </span>
  );
}

export function GravityTag({ g }: { g: number | null }) {
  if (g === null) return <Missing />;
  const zero = g === 0;
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <span aria-hidden className={zero ? "size-2.5 rounded-full bg-zero-g" : "size-2.5 rounded-full bg-one-g"} />
      {zero ? "0 g" : `${g} g`}
    </span>
  );
}

export function EvidenceTable({ evidence }: { evidence: Evidence[] }) {
  if (!evidence.length) return null;
  return (
    <section aria-labelledby="evidence-heading">
      <h3 id="evidence-heading" className="mb-2 text-base font-semibold">
        NASA tests used, closest first
      </h3>
      <div className="overflow-x-auto rounded-lg border border-border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Test</TableHead>
              <TableHead>Investigation</TableHead>
              <TableHead className="text-right">O₂ %</TableHead>
              <TableHead className="text-right">Pressure kPa</TableHead>
              <TableHead>Gravity</TableHead>
              <TableHead>Outcome</TableHead>
              <TableHead className="text-right">Match</TableHead>
              <TableHead>Source</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {evidence.map((e) => (
              <TableRow key={e.test_id} id={`ev-${e.test_id}`} className="scroll-mt-24">
                <TableCell className="font-semibold whitespace-nowrap">{e.test_id}</TableCell>
                <TableCell>{e.investigation}</TableCell>
                <TableCell className="text-right">{e.o2_pct ?? <Missing />}</TableCell>
                <TableCell className="text-right">{e.pressure_kpa ?? <Missing />}</TableCell>
                <TableCell>
                  <GravityTag g={e.gravity_g} />
                </TableCell>
                <TableCell>{e.outcome ? OUTCOME[e.outcome] : <Missing />}</TableCell>
                <TableCell className="text-right">{e.match_score.toFixed(2)}</TableCell>
                <TableCell>
                  <a
                    href={e.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-zero-g underline underline-offset-2 hover:no-underline"
                  >
                    PSI page<span className="sr-only"> for {e.test_id} (opens in a new tab)</span>
                  </a>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
