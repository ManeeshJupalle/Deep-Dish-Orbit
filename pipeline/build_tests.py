"""Run every cleaner and write data/clean/tests.csv and data/clean/investigations.json.

Usage: uv run python -m pipeline.build_tests
"""
import csv
import json
from collections import Counter

from pipeline import clean_bass2, clean_flex, clean_saffire
from pipeline.investigations import INVESTIGATIONS
from pipeline.schema import CLEAN, COLUMNS


def main() -> None:
    rows = clean_bass2.clean() + clean_saffire.clean() + clean_flex.clean()

    CLEAN.mkdir(parents=True, exist_ok=True)
    with open(CLEAN / "tests.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: "" if r[k] is None else r[k] for k in COLUMNS})

    counts = Counter(r["investigation"] for r in rows)
    records = [{**inv, "test_count": counts.get(inv["id"], 0)} for inv in INVESTIGATIONS]
    (CLEAN / "investigations.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"tests.csv: {len(rows)} rows")
    for name, n in counts.items():
        print(f"  {name}: {n}")


if __name__ == "__main__":
    main()
