export function GapsList({ gaps }: { gaps: string[] }) {
  if (!gaps.length) return null;
  return (
    <section aria-labelledby="gaps-heading">
      <h3 id="gaps-heading" className="mb-2 text-base font-semibold">
        What NASA hasn&apos;t tested
      </h3>
      <ul className="space-y-1.5">
        {gaps.map((g) => (
          <li key={g} className="flex items-start gap-2.5 text-sm">
            <span aria-hidden className="mt-1 size-3 shrink-0 rounded-full border-2 border-dashed border-gap" />
            {g}
          </li>
        ))}
      </ul>
    </section>
  );
}
