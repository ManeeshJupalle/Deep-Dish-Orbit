"""Find the tests and text closest to a question (ARCHITECTURE.md 7.1).

Conditions are parsed from the question with plain rules (no LLM), so a condition can
only come from words the user actually typed.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from api import llm
from api.data import store
from api.schemas import Conditions

TOP_TESTS, TOP_CHUNKS, TOP_BOUNDS = 8, 5, 3
O2_NEAR = 3.0          # points of O2 that count as "matching"
PRESSURE_NEAR = 10.0   # kPa

# Material families. Patterns match both questions and NASA's material text.
# BASS-II "rods" are cast PMMA (NTRS-20150008961), hence \brods?\b.
FAMILIES = {
    "PMMA": r"pmma|acrylic|plexiglas|\brods?\b",
    "cotton": r"cotton|sibal",
    "Nomex": r"nomex",
    "silicone": r"silicone",
    "wax": r"\bwax\b|candle",
    "methanol": r"methanol",
    "heptane": r"heptane",
}
_FAMILY_RE = {k: re.compile(v, re.I) for k, v in FAMILIES.items()}

INVESTIGATIONS = {"BASS-II": r"bass", "SAFFIRE-II": r"saffire[- ]?(ii|2)\b", "SAFFIRE-III": r"saffire[- ]?(iii|3)\b",
                  "FLEX": r"\bflex\b"}
DILUENTS = {"He": r"helium|\bhe\b", "CO2": r"\bco2\b|carbon dioxide", "N2": r"nitrogen|\bn2\b"}
GRAVITY = [("moon", r"\bmoon\b|lunar|artemis"), ("mars", r"\bmars\b|martian"),
           ("micro", r"micro-?gravity|\b0\s*g\b|zero[- ]g|weightless|\biss\b|space station|spacecraft|orbit"),
           ("earth", r"\bearth\b|\b1\s*g\b|normal gravity|on the ground")]
OUT_OF_SCOPE = re.compile(r"rocket|propellant|thruster|\bengines?\b|launch vehicle|hydrazine|\bmotor\b", re.I)

TO_KPA = {"kpa": 1.0, "psi": 6.89476, "psia": 6.89476, "atm": 101.325, "mmhg": 0.133322, "torr": 0.133322, "bar": 100.0}
_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_PRESSURE = re.compile(r"(\d+(?:\.\d+)?)\s*(kpa|psia|psi|atm|mmhg|torr|bar)\b", re.I)
_FLOW = re.compile(r"(\d+(?:\.\d+)?)\s*cm\s*/\s*s", re.I)
_OXYGEN = re.compile(r"oxygen|\bo2\b|o₂", re.I)
_OTHER_GAS = re.compile(r"co2|carbon dioxide|helium|nitrogen|\bhe\b|\bn2\b", re.I)

W = {"material": 0.5, "o2_pct": 0.25, "pressure_kpa": 0.15, "flow_cm_s": 0.1, "gravity": 0.15, "diluent": 0.3}
SPAN = {"o2_pct": 10.0, "pressure_kpa": 50.0, "flow_cm_s": 20.0}


@dataclass
class Retrieval:
    conditions: Conditions
    tests: list[tuple[dict, float]]
    chunks: list[tuple[dict, float]]
    bounds: dict[str, list[str]]
    gaps: list[str]
    out_of_scope: bool


def families(text: str | None) -> set[str]:
    return {k for k, rx in _FAMILY_RE.items() if text and rx.search(text)}


def fmt(x: float) -> str:
    return f"{x:g}"


# ---------- parsing ----------

def _o2(question: str) -> float | None:
    hits = []
    for m in _PCT.finditer(question):
        after = question[m.end(): m.end() + 15].strip()
        before = question[max(0, m.start() - 20): m.start()]
        if _OTHER_GAS.match(after):
            continue  # e.g. "20% helium"
        hits.append((bool(_OXYGEN.match(after) or _OXYGEN.search(before)), float(m.group(1))))
    near_oxygen = [v for ok, v in hits if ok]
    if near_oxygen:
        return near_oxygen[0]
    return hits[0][1] if len(hits) == 1 and _OXYGEN.search(question) else None


def parse_conditions(question: str) -> Conditions:
    fams = families(question)
    p = _PRESSURE.search(question)
    f = _FLOW.search(question)
    gravity = next((g for g, rx in GRAVITY if re.search(rx, question, re.I)), None)
    return Conditions(
        material=", ".join(sorted(fams)) or None,
        o2_pct=_o2(question),
        pressure_kpa=round(float(p.group(1)) * TO_KPA[p.group(2).lower()], 1) if p else None,
        gravity=gravity,
        flow_cm_s=float(f.group(1)) if f else None,
    )


def merge(explicit: Conditions | None, parsed: Conditions) -> Conditions:
    """Conditions typed in the form win; the question fills the rest."""
    if explicit is None:
        return parsed
    data = parsed.model_dump()
    data.update({k: v for k, v in explicit.model_dump().items() if v not in (None, "")})
    return Conditions(**data)


# ---------- structured lane ----------

def material_rows(rows: list[dict], material: str) -> list[dict]:
    fams = families(material)
    if fams:
        return [r for r in rows if families(r["material"]) & fams]
    m = material.lower()
    return [r for r in rows if r["material"] and m in r["material"].lower()]


def score(row: dict, c: Conditions, gravity_g: float | None, diluents: set[str], mat_ok: bool) -> float:
    total = got = 0.0
    if c.material:
        total += W["material"]
        got += W["material"] if mat_ok else 0.0
    for k, span in SPAN.items():
        q = getattr(c, k)
        if q is None:
            continue
        total += W[k]
        if row[k] is not None:  # missing values get no credit
            got += W[k] * max(0.0, 1 - abs(row[k] - q) / span)
    if gravity_g is not None:
        total += W["gravity"]
        got += W["gravity"] if row["gravity_g"] == gravity_g else 0.0
    if diluents:
        total += W["diluent"]
        got += W["diluent"] if row["diluent"] and diluents & set(row["diluent"].split("+")) else 0.0
    return got / total if total else 0.0


def _rank(scored: list[tuple[dict, float]], c: Conditions) -> list[tuple[dict, float]]:
    def key(item):
        row, s = item
        o2_gap = abs(row["o2_pct"] - c.o2_pct) if c.o2_pct is not None and row["o2_pct"] is not None else math.inf
        return (-s, row["outcome"] is None, o2_gap)
    return sorted([x for x in scored if x[1] > 0], key=key)


def _gaps(c: Conditions, pool: list[dict], label: str) -> list[str]:
    gaps = []
    if c.gravity == "moon":
        gaps.append("No PSI data at lunar gravity")
    if c.gravity == "mars":
        gaps.append("No PSI data at Martian gravity")
    if c.material and not pool:
        return gaps + [f"No PSI test for {c.material}"]
    what = f"{label} test" if label else "test"
    if c.o2_pct is not None:
        o2s = [r["o2_pct"] for r in pool if r["o2_pct"] is not None]
        if not o2s:
            gaps.append(f"No {what} reports an oxygen level")
        elif max(o2s) < c.o2_pct - O2_NEAR:
            gaps.append(f"No {what} at or above {fmt(c.o2_pct)}% O2 (highest tested: {fmt(max(o2s))}%)")
        elif min(o2s) > c.o2_pct + O2_NEAR:
            gaps.append(f"No {what} at or below {fmt(c.o2_pct)}% O2 (lowest tested: {fmt(min(o2s))}%)")
    if c.pressure_kpa is not None:
        ps = [r["pressure_kpa"] for r in pool if r["pressure_kpa"] is not None]
        if not ps:
            gaps.append(f"No {what} reports a pressure")
        elif min(abs(p - c.pressure_kpa) for p in ps) > PRESSURE_NEAR:
            gaps.append(f"No {what} within {fmt(PRESSURE_NEAR)} kPa of {fmt(c.pressure_kpa)} kPa")
    if c.gravity in ("moon", "mars", "earth") and not any(r["gravity_g"] == 1 for r in pool):
        gaps.append(f"No 1 g comparison {what}")
    return gaps


# ---------- text lane ----------

_WORD = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
STOP = {"the", "a", "an", "of", "in", "on", "at", "is", "are", "was", "were", "and", "or", "to", "for", "with",
        "how", "what", "which", "does", "do", "did", "it", "be", "by", "as", "this", "that", "from", "if", "can"}


def tokens(text: str) -> list[str]:
    return [t for t in _WORD.findall(text.lower()) if t not in STOP]


@lru_cache(maxsize=1)
def _chunk_index():
    docs = [Counter(tokens(c["title"] + " " + c["text"])) for c in store().chunks]
    return docs, Counter(t for d in docs for t in d)


def rank_chunks(question: str) -> list[tuple[dict, float]]:
    chunks, emb = store().chunks, store().embeddings
    if emb is not None and llm.available():
        try:
            sims = emb @ llm.embed([question], "RETRIEVAL_QUERY")[0]
            order = sims.argsort()[::-1][:TOP_CHUNKS]
            return [(chunks[i], round(float(sims[i]), 3)) for i in order]
        except Exception:  # network or quota trouble: fall back to keywords
            pass
    docs, df = _chunk_index()
    q = set(tokens(question))
    scores = [sum(math.log(1 + len(docs) / df[t]) for t in q if t in d) for d in docs]
    order = sorted(range(len(docs)), key=lambda i: -scores[i])[:TOP_CHUNKS]
    return [(chunks[i], round(scores[i], 3)) for i in order if scores[i] > 0]


# ---------- entry point ----------

def retrieve(question: str, conditions: Conditions | None = None) -> Retrieval:
    c = merge(conditions, parse_conditions(question))
    rows = store().tests
    named = {k for k, rx in INVESTIGATIONS.items() if re.search(rx, question, re.I)}
    if named:
        rows = [r for r in rows if r["investigation"] in named]
    diluents = {k for k, rx in DILUENTS.items() if re.search(rx, question, re.I)}

    mat = material_rows(rows, c.material) if c.material else []
    candidates = mat or rows
    mat_ids = {r["test_id"] for r in mat}
    gravity_g = {"micro": 0.0, "earth": 1.0}.get(c.gravity or "")

    has_signal = any([c.material, c.o2_pct is not None, c.pressure_kpa is not None, c.flow_cm_s is not None,
                      diluents, named])
    tests: list[tuple[dict, float]] = []
    bounds = {"microgravity": [], "earth": []}
    def scored(g: float | None) -> list[tuple[dict, float]]:
        out = [(r, score(r, c, g, diluents, r["test_id"] in mat_ids)) for r in candidates]
        if named and not any(s for _, s in out):  # only an investigation was named
            out = [(r, 1.0) for r, _ in out]
        return _rank(out, c)

    if has_signal:
        tests = [(r, round(s, 2)) for r, s in scored(gravity_g)[:TOP_TESTS]]
        ranked = scored(None)  # bounds ignore gravity: best 0 g and best 1 g matches
        bounds = {"microgravity": [r["test_id"] for r, _ in ranked if r["gravity_g"] == 0][:TOP_BOUNDS],
                  "earth": [r["test_id"] for r, _ in ranked if r["gravity_g"] == 1][:TOP_BOUNDS]}

    label = c.material or ""
    return Retrieval(
        conditions=c,
        tests=tests,
        chunks=rank_chunks(question),
        bounds=bounds,
        gaps=_gaps(c, mat if c.material else rows, label),
        out_of_scope=bool(OUT_OF_SCOPE.search(question)),
    )
