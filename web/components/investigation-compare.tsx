import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Investigation } from "@/lib/types";

export function InvestigationCompare({ investigations }: { investigations: Investigation[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Investigation</TableHead>
            <TableHead>Fire-safety area</TableHead>
            <TableHead>Fuel</TableHead>
            <TableHead>Hardware</TableHead>
            <TableHead>Measurements</TableHead>
            <TableHead className="text-right">Tests</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {investigations.map((inv) => (
            <TableRow key={inv.id} className="align-top">
              <TableCell className="min-w-56 whitespace-normal">
                <a href={inv.source_url} target="_blank" rel="noreferrer" className="font-semibold text-zero-g underline underline-offset-2 hover:no-underline">
                  {inv.id}
                </a>{" "}
                <span className="text-muted-foreground">({inv.psi_id})</span>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{inv.objective}</p>
              </TableCell>
              <TableCell className="capitalize">{inv.area.join(", ")}</TableCell>
              <TableCell className="capitalize">{inv.fuels.join(", ")}</TableCell>
              <TableCell className="min-w-40 whitespace-normal">{inv.hardware}</TableCell>
              <TableCell className="min-w-40 whitespace-normal">
                {inv.sensors.length ? inv.sensors.join(", ") : <span className="text-muted-foreground">Not listed on PSI</span>}
              </TableCell>
              <TableCell className="text-right font-semibold">{inv.test_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
