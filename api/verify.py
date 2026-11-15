"""Check every drafted claim against the evidence before it reaches the user (ARCHITECTURE.md 7.3).

A claim is dropped when:
  1. it cites nothing, or cites an id that was not in the evidence sent to the model;
  2. any number in it is not in a cited row or chunk (rounding to 1 decimal allowed);
  3. it is about Moon/Mars behavior (the question or the claim says so) and is not phrased as a 0 g / 1 g bound;
  4. it uses an outcome word (burned, extinguished, did not ignite, ...) the cited tests' `outcome` does not record.
Every drop is logged to logs/verify.jsonl.
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from api.answer import ROW_FIELDS
from api.retrieve import PARTIAL_G, Retrieval

LOG = Path(__file__).resolve().parent.parent / "logs" / "verify.jsonl"

# Ids and names such as BASS2-B1, SAFFIRE2-2-5-1G, FLEX-19, PSI-25, NTRS-20210011385-chunk1, BASS-II,
# and NASA's own FLEX identifiers such as 20CAL08 or 256F002.
_ID = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b|\b\d+[A-Za-z]+\d[A-Za-z0-9]*\b")
# Numbers not glued to a preceding letter (so O2, CO2, N2 are not numbers). ".75" counts as 0.75.
_NUM = re.compile(r"(?<![A-Za-z0-9.])(?:\d+(?:\.\d+)?|\.\d+)")
ZERO_G = re.compile(r"\b0\s?g\b|micro-?gravity|[µμ]-?g\b", re.I)
ONE_G = re.compile(r"\b1\s?g\b|1-g\b|normal gravity|earth gravity|\bon earth\b", re.I)
MOON_MARS = re.compile(r"\bmoon\b|lunar|\bmars\b|martian", re.I)

# Outcome words a claim may only use when the cited rows' `outcome` column backs them.
MEASURES = re.compile(r"burn(?:ing)?[- ](?:rate|time|length|duration)|extinction diameter|spread (?:rate|length)", re.I)
OUTCOME_WORDS = [  # order matters: "did not ignite" / "never burned" go before "ignite" / "burn" are looked for
    ("no_ignition", re.compile(r"(?:\bnot|n't|\bnever|\bno|failed to)\s+(?:ignit|burn)\w*", re.I)),
    ("extinguished", re.compile(r"extinguish|extinction|put out|went out|blow-?off|quench", re.I)),
    ("burned", re.compile(r"\bburn(?:ed|t|s|ing)?\b", re.I)),
    ("ignited", re.compile(r"\bignit(?:ed|es|ion)\b", re.I)),
]
ALLOWED = {"no_ignition": {"no_ignition"}, "extinguished": {"extinguished"}, "burned": {"burned"},
           "ignited": {"ignited", "burned", "extinguished"}}
WORDS = {"no_ignition": "did not ignite", "extinguished": "extinguished", "burned": "burned", "ignited": "ignited"}


def _ids(ids: list[str]) -> str:
    return ", ".join(ids[:-1]) + " or " + ids[-1] if len(ids) > 1 else ids[0]


@dataclass
class Verified:
    claims: list[dict]
    dropped: list[dict] = field(default_factory=list)


def numbers(text: str) -> list[float]:
    return [float(n) for n in _NUM.findall(_ID.sub(" ", text))]


def row_numbers(row: dict) -> set[float]:
    """Numbers in the columns the model was shown. File names and PSI ids are not data."""
    out = set()
    for v in (row.get(k) for k in ROW_FIELDS):
        if isinstance(v, (int, float)):
            out.add(float(v))
        elif isinstance(v, str):
            out.update(numbers(v))
    return out


def number_ok(n: float, allowed: set[float]) -> bool:
    return any(abs(n - v) < 1e-9 or round(n, 1) == round(v, 1) for v in allowed)


def outcome_problem(text: str, tests: list[dict]) -> str | None:
    """Outcome words (burned, extinguished, ...) must match the cited tests' recorded outcomes."""
    if not tests:
        return None
    t = MEASURES.sub(" ", text)
    said = []
    for name, rx in OUTCOME_WORDS:
        if rx.search(t):
            said.append(name)
            t = rx.sub(" ", t)
    if not said:
        return None
    for name in said:
        if not any(r["outcome"] in ALLOWED[name] for r in tests):
            return f"says '{WORDS[name]}' but no cited test records that outcome"
    allowed = set().union(*(ALLOWED[n] for n in said))
    wrong = [r["test_id"] for r in tests if r["outcome"] not in allowed]
    if wrong:
        return f"says '{' / '.join(WORDS[n] for n in said)}' but {_ids(wrong)} recorded a different outcome or none"
    return None


def check_claim(claim: dict, rows: dict[str, dict], chunks: dict[str, dict], gravity: str | None) -> str | None:
    """Reason the claim must be dropped, or None if it passes."""
    cites = claim.get("cites") or []
    if not cites:
        return "cites no NASA test or document"
    unknown = [c for c in cites if c not in rows and c not in chunks]
    if unknown:
        return f"unknown citation: {_ids(unknown)} was not in the evidence sent to the model"

    allowed: set[float] = set()
    for c in cites:
        allowed |= row_numbers(rows[c]) if c in rows else set(numbers(chunks[c]["text"] + " " + chunks[c]["title"]))
    bad = [n for n in numbers(claim["text"]) if not number_ok(n, allowed)]
    if bad:
        return f"{_ids([f'{n:g}' for n in bad])} is not in {_ids(cites)}"

    problem = outcome_problem(claim["text"], [rows[c] for c in cites if c in rows])
    if problem:
        return problem

    # Rule 3 applies when the question is about partial gravity, or the claim itself talks about the Moon or Mars.
    text = claim["text"]
    levels = {rows[c]["gravity_g"] for c in cites if c in rows}
    says_moon_mars = bool(MOON_MARS.search(text))
    if gravity in PARTIAL_G or says_moon_mars:
        if 0.0 in levels and not ZERO_G.search(text):
            return "Moon/Mars claim cites 0 g data but is not phrased as a 0 g bound"
        if 1.0 in levels and not ONE_G.search(text):
            return "Moon/Mars claim cites 1 g data but is not phrased as a 1 g bound"
    if gravity in PARTIAL_G and not levels and says_moon_mars and not (ZERO_G.search(text) or ONE_G.search(text)):
        return "claim about Moon/Mars behavior without a 0 g / 1 g bound"
    return None


def verify(question: str, r: Retrieval, evidence: list[dict], draft_claims: list[dict]) -> Verified:
    rows = {t["test_id"]: t for t in evidence}
    chunks = {c["chunk_id"]: c for c, _ in r.chunks}
    result = Verified(claims=[])
    for claim in draft_claims:
        reason = check_claim(claim, rows, chunks, r.conditions.gravity)
        if reason:
            result.dropped.append({"claim": claim, "reason": reason})
        else:
            result.claims.append({"text": claim["text"], "cites": list(dict.fromkeys(claim["cites"]))})
    if result.dropped:
        _log(question, result.dropped)
    return result


def summary_ok(summary: str, r: Retrieval, evidence: list[dict], question: str, claims: list[dict]) -> bool:
    """Numbers must come from the evidence, gaps or question; outcome words must match the cited tests."""
    allowed = set(numbers(question)) | {n for g in r.gaps for n in numbers(g)}
    for t in evidence:
        allowed |= row_numbers(t)
    for c, _ in r.chunks:
        allowed |= set(numbers(c["text"]))
    if not all(number_ok(n, allowed) for n in numbers(summary)):
        return False
    rows = {t["test_id"]: t for t in evidence}
    cited = list({i: rows[i] for c in claims for i in c["cites"] if i in rows}.values())
    return outcome_problem(summary, cited) is None


def decide_status(r: Retrieval, claims: list[dict]) -> str:
    if r.out_of_scope:
        return "out_of_scope"
    if r.conditions.gravity in PARTIAL_G or r.gaps or not claims:
        return "no_direct_data"
    return "answered"


def _log(question: str, dropped: list[dict]) -> None:
    LOG.parent.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(LOG, "a", encoding="utf-8") as f:
        for d in dropped:
            f.write(json.dumps({"ts": ts, "question": question, **d}, ensure_ascii=False) + "\n")
