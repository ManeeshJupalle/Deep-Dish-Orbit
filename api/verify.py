"""Check every drafted claim against the evidence before it reaches the user (ARCHITECTURE.md 7.3).

A claim is dropped when:
  1. it cites nothing, or cites an id that was not in the evidence sent to the model;
  2. any number in it is not in a cited row or chunk (rounding to 1 decimal allowed);
  3. the question is about Moon/Mars gravity and the claim is not phrased as a 0 g / 1 g bound.
Every drop is logged to logs/verify.jsonl.
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from api.retrieve import Retrieval

LOG = Path(__file__).resolve().parent.parent / "logs" / "verify.jsonl"

# Ids and names such as BASS2-B1, SAFFIRE2-2-5-1G, FLEX-19, PSI-25, NTRS-20210011385-chunk1, BASS-II.
_ID = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b")
# Numbers not glued to a preceding letter (so O2, CO2, N2 are not numbers).
_NUM = re.compile(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?")
ZERO_G = re.compile(r"\b0\s?g\b|micro-?gravity|[µμ]-?g\b", re.I)
ONE_G = re.compile(r"\b1\s?g\b|1-g\b|normal gravity|earth gravity|\bon earth\b", re.I)
MOON_MARS = re.compile(r"\bmoon\b|lunar|\bmars\b|martian", re.I)


@dataclass
class Verified:
    claims: list[dict]
    dropped: list[dict] = field(default_factory=list)


def numbers(text: str) -> list[float]:
    return [float(n) for n in _NUM.findall(_ID.sub(" ", text))]


def row_numbers(row: dict) -> set[float]:
    out = set()
    for v in row.values():
        if isinstance(v, (int, float)):
            out.add(float(v))
        elif isinstance(v, str):
            out.update(numbers(v))
    return out


def number_ok(n: float, allowed: set[float]) -> bool:
    return any(abs(n - v) < 1e-9 or round(n, 1) == round(v, 1) for v in allowed)


def check_claim(claim: dict, rows: dict[str, dict], chunks: dict[str, dict], gravity: str | None) -> str | None:
    """Reason the claim must be dropped, or None if it passes."""
    cites = claim.get("cites") or []
    if not cites:
        return "no citation"
    unknown = [c for c in cites if c not in rows and c not in chunks]
    if unknown:
        return f"unknown citation {unknown}"

    allowed: set[float] = set()
    for c in cites:
        allowed |= row_numbers(rows[c]) if c in rows else set(numbers(chunks[c]["text"] + " " + chunks[c]["title"]))
    bad = [n for n in numbers(claim["text"]) if not number_ok(n, allowed)]
    if bad:
        return f"number(s) {bad} not in cited evidence"

    if gravity in ("moon", "mars"):
        levels = {rows[c]["gravity_g"] for c in cites if c in rows}
        text = claim["text"]
        if 0.0 in levels and not ZERO_G.search(text):
            return "Moon/Mars claim cites 0 g data but is not phrased as a 0 g bound"
        if 1.0 in levels and not ONE_G.search(text):
            return "Moon/Mars claim cites 1 g data but is not phrased as a 1 g bound"
        if not levels and MOON_MARS.search(text) and not (ZERO_G.search(text) or ONE_G.search(text)):
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


def summary_ok(summary: str, r: Retrieval, evidence: list[dict], question: str) -> bool:
    """Every number in the summary must come from the evidence, the gaps or the question."""
    allowed = set(numbers(question)) | {n for g in r.gaps for n in numbers(g)}
    for t in evidence:
        allowed |= row_numbers(t)
    for c, _ in r.chunks:
        allowed |= set(numbers(c["text"]))
    return all(number_ok(n, allowed) for n in numbers(summary))


def decide_status(r: Retrieval, claims: list[dict]) -> str:
    if r.out_of_scope:
        return "out_of_scope"
    if r.conditions.gravity in ("moon", "mars") or r.gaps or not claims:
        return "no_direct_data"
    return "answered"


def _log(question: str, dropped: list[dict]) -> None:
    LOG.parent.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(LOG, "a", encoding="utf-8") as f:
        for d in dropped:
            f.write(json.dumps({"ts": ts, "question": question, **d}, ensure_ascii=False) + "\n")
