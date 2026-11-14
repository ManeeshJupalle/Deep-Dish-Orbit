import type { AskResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

const STYLE = {
  high: "bg-zero-g text-white border-zero-g",
  medium: "bg-card text-zero-g border-zero-g",
  low: "bg-card text-gap border-gap border-dashed",
};
const LABEL = { high: "High trust", medium: "Medium trust", low: "Low trust" };

export function TrustBadge({ trust }: { trust: AskResponse["trust"] }) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <span className={cn("inline-flex rounded-full border-2 px-3 py-0.5 text-sm font-semibold", STYLE[trust.level])}>
        {LABEL[trust.level]}
      </span>
      <span className="text-sm text-muted-foreground">{trust.reason}</span>
    </div>
  );
}
