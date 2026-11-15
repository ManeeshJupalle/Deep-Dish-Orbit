"""Sanity checks on data/clean. Exits 1 on any problem.

Usage: uv run python -m pipeline.check_data
"""
import csv
import json
import sys
from collections import Counter

from pipeline.schema import CLEAN, COLUMNS, FUEL_PHASES, OUTCOMES

RANGES = {"o2_pct": (0, 100), "pressure_kpa": (0, 350), "flow_cm_s": (0, 1000),
          "gravity_g": (0, 1), "spread_rate_mm_s": (0, 1000)}


def check() -> list[str]:
    errors: list[str] = []
    with open(CLEAN / "tests.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            errors.append(f"tests.csv columns {reader.fieldnames} != schema {COLUMNS}")
        rows = list(reader)

    ids = Counter(r["test_id"] for r in rows)
    errors += [f"duplicate test_id {i} ({n}x)" for i, n in ids.items() if n > 1]

    for r in rows:
        tid = r["test_id"]
        for col in ("test_id", "investigation", "psi_id", "source_url", "source_file"):
            if not r[col]:
                errors.append(f"{tid}: empty {col}")
        if r["source_url"] and not r["source_url"].startswith("https://psi.nasa.gov/"):
            errors.append(f"{tid}: source_url not a PSI page: {r['source_url']}")
        if r["fuel_phase"] not in FUEL_PHASES:
            errors.append(f"{tid}: bad fuel_phase {r['fuel_phase']!r}")
        if r["outcome"] and r["outcome"] not in OUTCOMES:
            errors.append(f"{tid}: bad outcome {r['outcome']!r}")
        for col, (lo, hi) in RANGES.items():
            if not r[col]:
                continue
            try:
                v = float(r[col])
            except ValueError:
                errors.append(f"{tid}: {col} not a number: {r[col]!r}")
                continue
            if not lo <= v <= hi:
                errors.append(f"{tid}: {col}={v} outside {lo}-{hi}")

    investigations = json.loads((CLEAN / "investigations.json").read_text(encoding="utf-8"))
    inv_ids = {i["id"] for i in investigations}
    counts = Counter(r["investigation"] for r in rows)
    for name in counts.keys() - inv_ids:
        errors.append(f"tests.csv investigation {name} missing from investigations.json")
    for inv in investigations:
        if inv["test_count"] != counts.get(inv["id"], 0):
            errors.append(f"{inv['id']}: test_count {inv['test_count']} != {counts.get(inv['id'], 0)} rows")
    if len(counts) < 3:
        errors.append(f"only {len(counts)} investigations in tests.csv (need at least 3)")

    chunks_path = CLEAN / "chunks.jsonl"
    if chunks_path.exists():
        chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line]
        cids = Counter(c["chunk_id"] for c in chunks)
        errors += [f"duplicate chunk_id {i}" for i, n in cids.items() if n > 1]
        errors += [f"chunk_id {i} collides with a test_id" for i in cids.keys() & ids.keys()]
        for c in chunks:
            for key in ("chunk_id", "source_id", "title", "text", "source_url"):
                if not c.get(key):
                    errors.append(f"chunk {c.get('chunk_id')}: empty {key}")
        emb_path = CLEAN / "embeddings.npy"
        if emb_path.exists():
            import numpy as np
            n = np.load(emb_path).shape[0]
            if n != len(chunks):
                errors.append(f"embeddings.npy has {n} rows but chunks.jsonl has {len(chunks)}")
    return errors


def main() -> None:
    errors = check()
    for e in errors:
        print("FAIL", e)
    print("check_data:", "FAILED" if errors else "ok", f"({len(errors)} problems)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
