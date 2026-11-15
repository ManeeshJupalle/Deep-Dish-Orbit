"""Draft an answer from retrieved evidence only (ARCHITECTURE.md 7.2).

draft() asks the drafting model (Azure OpenAI or Gemini, see llm.py; JSON only, one retry on bad JSON). template() is the
no-LLM fallback: it restates the top evidence rows. Both outputs go through verify.py.
"""
import json
from collections import Counter
from pathlib import Path

from api import llm
from api.retrieve import PARTIAL_G, Retrieval, fmt

SYSTEM = (Path(__file__).parent / "prompts" / "answer.md").read_text(encoding="utf-8")
ROW_FIELDS = ("test_id", "investigation", "material", "sample_geometry", "o2_pct", "pressure_kpa", "diluent",
              "flow_cm_s", "gravity_g", "outcome", "spread_rate_mm_s", "extinction_note")
STATS: Counter = Counter()  # drafted / error / bad_json, read by eval/run_eval.py
OUTCOME_TEXT = {"burned": "burned", "extinguished": "was extinguished", "no_ignition": "did not ignite",
                "ignited": "ignited", "other": "is recorded with outcome 'other'"}


def evidence_rows(r: Retrieval) -> list[dict]:
    """Top tests plus any bounding tests not already among them."""
    from api.data import store
    rows = [t for t, _ in r.tests]
    seen = {t["test_id"] for t in rows}
    for tid in r.bounds["microgravity"] + r.bounds["earth"]:
        if tid not in seen:
            rows.append(store().by_id[tid])
            seen.add(tid)
    return rows


def build_prompt(question: str, r: Retrieval) -> str:
    rows = evidence_rows(r)
    table = [",".join(ROW_FIELDS)] + [
        ",".join(json.dumps(row[k]) if isinstance(row[k], str) else ("" if row[k] is None else fmt(row[k]))
                 for k in ROW_FIELDS) for row in rows]
    chunks = [f"[{c['chunk_id']}] {c['title']}\n{c['text']}" for c, _ in r.chunks]
    return "\n\n".join([
        f"Question: {question}",
        f"Conditions asked: {json.dumps(r.conditions.model_dump(exclude_none=True))}",
        "Test rows (CSV, PSI data; empty = not reported):\n" + "\n".join(table),
        f"Bounding tests: 0 g = {r.bounds['microgravity']}, 1 g = {r.bounds['earth']}",
        "Known gaps in the data: " + ("; ".join(r.gaps) or "none"),
        "Text chunks:\n" + ("\n\n".join(chunks) or "none"),
    ])


def _valid(d) -> bool:
    return (isinstance(d, dict) and isinstance(d.get("summary"), str) and isinstance(d.get("claims"), list)
            and all(isinstance(c, dict) and isinstance(c.get("text"), str) and isinstance(c.get("cites"), list)
                    for c in d["claims"]))


def draft(question: str, r: Retrieval) -> dict | None:
    """Model draft, or None if no model is available or it keeps returning bad JSON."""
    if not llm.available():
        return None
    prompt = build_prompt(question, r)
    for _ in range(2):  # one retry on bad JSON
        try:
            d = json.loads(llm.generate_json(SYSTEM, prompt))
        except json.JSONDecodeError:
            continue
        except Exception:  # network, quota, auth: fall back to the template
            STATS["error"] += 1
            return None
        if _valid(d):
            STATS["drafted"] += 1
            return d
    STATS["bad_json"] += 1
    return None


def template(r: Retrieval) -> dict:
    """Evidence-only answer built straight from the rows (used when the LLM is unavailable)."""
    moon_or_mars = r.conditions.gravity in PARTIAL_G
    from api.data import store
    if moon_or_mars:
        rows = [store().by_id[i] for i in r.bounds["microgravity"][:2] + r.bounds["earth"][:1]]
    else:
        rows = [t for t, _ in r.tests[:3]]
        # Add NASA's closest 1 g comparison when there is one, so both gravities are stated.
        if r.bounds["earth"] and not any(t["gravity_g"] == 1 for t in rows):
            rows.append(store().by_id[r.bounds["earth"][0]])
    claims = []
    for t in rows:
        parts = [f"{t['investigation']} test {t['test_id']} ({t['material'] or 'material not given'})",
                 OUTCOME_TEXT.get(t["outcome"], "has no recorded outcome")]
        conds = []
        if t["o2_pct"] is not None:
            conds.append(f"{fmt(t['o2_pct'])}% O2")
        if t["pressure_kpa"] is not None:
            conds.append(f"{fmt(t['pressure_kpa'])} kPa")
        if t["flow_cm_s"] is not None:
            conds.append(f"{fmt(t['flow_cm_s'])} cm/s flow")
        text = " ".join(parts) + (f" at {', '.join(conds)}" if conds else "")
        if t["spread_rate_mm_s"] is not None:
            text += f", with a flame spread rate of {fmt(t['spread_rate_mm_s'])} mm/s"
        prefix = "At 0 g, " if t["gravity_g"] == 0 else "At 1 g, "
        claims.append({"text": prefix + text + ".", "cites": [t["test_id"]]})
    return {"summary": "", "claims": claims}
