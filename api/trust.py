"""High / Medium / Low trust badge with a reason (ARCHITECTURE.md 7.4)."""
from api.retrieve import O2_NEAR, PARTIAL_G, Retrieval, fmt, matches


def trust(r: Retrieval, claims: list[dict], status: str, rows: dict[str, dict]) -> dict:
    c = r.conditions
    if status == "out_of_scope":
        return {"level": "low", "reason": "Question is outside the PSI fire-safety data"}
    if c.gravity in PARTIAL_G:
        return {"level": "low",
                "reason": f"Only 0 g and 1 g bounding tests; no PSI data at {PARTIAL_G[c.gravity]} gravity"}
    if not claims:
        return {"level": "low", "reason": "No verified claim"}

    cited = [rows[i] for cl in claims for i in cl["cites"] if i in rows]
    cited = list({t["test_id"]: t for t in cited}.values())
    if not cited:
        return {"level": "low", "reason": "Only text evidence, no test rows"}

    matching = [] if r.gaps else [t for t in cited if matches(t, c, r.diluents)]  # a gap means nothing matches
    n = len(matching)
    with_outcome = sum(t["outcome"] is not None for t in matching)
    if with_outcome >= 3 and not r.gaps and not r.any_material:
        return {"level": "high", "reason": f"{with_outcome} verified tests at matching conditions"}
    reason = f"{n} matching test{'s' if n != 1 else ''}" if n else "Tests near but not at the asked conditions"
    if n and with_outcome < n:
        reason += f", but NASA recorded no outcome for {n - with_outcome}"
    if c.o2_pct is not None:
        o2s = [t["o2_pct"] for t in cited if t["o2_pct"] is not None]
        if o2s:
            gap = min(o2s, key=lambda v: abs(v - c.o2_pct)) - c.o2_pct
            if abs(gap) > O2_NEAR:
                reason += f", oxygen {fmt(round(abs(gap), 1))} points {'lower' if gap < 0 else 'higher'} than asked"
        else:
            reason += ", oxygen not reported for the cited tests"
    if r.any_material:  # "same material family" cannot hold when the question names none we recognise
        reason += "; the question names no material FlameCheck recognises, so tests of any material are shown"
    return {"level": "medium", "reason": reason}
