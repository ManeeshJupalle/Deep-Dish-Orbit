"""Load the clean data once (tests.csv, investigations.json, chunks.jsonl, embeddings.npy)."""
import csv
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"
NUMERIC = ("o2_pct", "pressure_kpa", "flow_cm_s", "gravity_g", "spread_rate_mm_s")


@dataclass(frozen=True)
class Store:
    tests: list[dict]
    by_id: dict[str, dict]
    investigations: list[dict]
    chunks: list[dict]
    chunk_by_id: dict[str, dict]
    embeddings: np.ndarray | None


def _row(r: dict) -> dict:
    out = {k: (v if v != "" else None) for k, v in r.items()}
    for k in NUMERIC:
        if out[k] is not None:
            out[k] = float(out[k])
    return out


@lru_cache(maxsize=1)
def store() -> Store:
    with open(CLEAN / "tests.csv", encoding="utf-8", newline="") as f:
        tests = [_row(r) for r in csv.DictReader(f)]
    investigations = json.loads((CLEAN / "investigations.json").read_text(encoding="utf-8"))
    chunks = [json.loads(line) for line in (CLEAN / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line]
    emb_path = CLEAN / "embeddings.npy"
    embeddings = np.load(emb_path) if emb_path.exists() else None
    if embeddings is not None and len(embeddings) != len(chunks):
        embeddings = None  # out of step with chunks: ignore rather than mis-rank
    return Store(tests, {t["test_id"]: t for t in tests}, investigations, chunks,
                 {c["chunk_id"]: c for c in chunks}, embeddings)
