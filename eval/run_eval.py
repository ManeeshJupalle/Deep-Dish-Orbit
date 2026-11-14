"""Score FlameCheck on eval/questions.yaml and write eval/results.md.

Usage:
  uv run python -m eval.run_eval                 # in-process API (no server needed)
  uv run python -m eval.run_eval --url http://localhost:8000
"""
import argparse
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

from api import llm
from api.data import store
from api.retrieve import families
from api.verify import number_ok, numbers, row_numbers

HERE = Path(__file__).resolve().parent
CHECKS = ("status", "citations_real", "required_cited", "no_invented")


def ask_fn(url: str | None):
    if url:
        def call(q: str) -> dict:
            req = urllib.request.Request(f"{url.rstrip('/')}/ask", data=json.dumps({"question": q}).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        return call
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    return lambda q: client.post("/ask", json={"question": q}).json()


def row_matches(row: dict, where: dict) -> bool:
    for k, v in where.items():
        if k == "material":
            if v not in families(row["material"]):
                return False
        elif k == "diluent":
            if not row["diluent"] or v not in row["diluent"].split("+"):
                return False
        elif row.get(k) != v:
            return False
    return True


def score(q: dict, d: dict) -> tuple[dict, list[str]]:
    s = store()
    notes: list[str] = []
    cited = [i for c in d["claims"] for i in c["cites"]]
    cited_tests = [s.by_id[i] for i in cited if i in s.by_id]
    text = (d["summary"] + " " + " ".join(c["text"] for c in d["claims"])).lower()

    status = d["status"] == q["expected_status"]
    if not status:
        notes.append(f"status {d['status']} (expected {q['expected_status']})")

    unknown = [i for i in cited if i not in s.by_id and i not in s.chunk_by_id]
    citations_real = not unknown
    if unknown:
        notes.append(f"unknown citations {unknown}")

    required = True
    missing = [i for i in q.get("must_cite", []) if i not in cited]
    if missing:
        required = False
        notes.append(f"missing citations {missing}")
    if "cite_where" in q:
        bad = [t["test_id"] for t in cited_tests if not row_matches(t, q["cite_where"])]
        if not cited_tests or bad:
            required = False
            notes.append(f"cited tests not matching {q['cite_where']}: {bad or 'none cited'}")
    if q.get("bounds_required") and not (d["bounds"]["microgravity"] and d["bounds"]["earth"]):
        required = False
        notes.append(f"bounds incomplete {d['bounds']}")

    invented = []
    for c in d["claims"]:
        allowed: set[float] = set()
        for i in c["cites"]:
            if i in s.by_id:
                allowed |= row_numbers(s.by_id[i])
            elif i in s.chunk_by_id:
                allowed |= set(numbers(s.chunk_by_id[i]["text"] + " " + s.chunk_by_id[i]["title"]))
        invented += [n for n in numbers(c["text"]) if not number_ok(n, allowed)]
    answer_numbers = numbers(d["summary"] + " " + " ".join(c["text"] for c in d["claims"]))

    def present(m: str) -> bool:
        try:  # numeric values must appear as a whole number, so "2.1" does not match "22.1"
            return any(abs(float(m) - n) < 1e-9 for n in answer_numbers)
        except ValueError:
            return m.lower() in text

    contains = [m for m in q.get("must_contain", []) if not present(m)]
    forbidden = [m for m in q.get("must_not_contain", []) if m.lower() in text]
    no_invented = not (invented or contains or forbidden)
    if invented:
        notes.append(f"numbers not in cited evidence {invented}")
    if contains:
        notes.append(f"missing expected value(s) {contains}")
    if forbidden:
        notes.append(f"contains forbidden text {forbidden}")

    return {"status": status, "citations_real": citations_real, "required_cited": required,
            "no_invented": no_invented}, notes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="score a running API instead of the in-process app")
    args = ap.parse_args()

    questions = yaml.safe_load((HERE / "questions.yaml").read_text(encoding="utf-8"))
    call = ask_fn(args.url)
    rows, times = [], []
    for q in questions:
        t0 = time.perf_counter()
        d = call(q["question"])
        times.append(time.perf_counter() - t0)
        checks, notes = score(q, d)
        rows.append((q, d, checks, notes))

    passed = sum(all(c.values()) for _, _, c, _ in rows)
    per_check = {k: sum(c[k] for _, _, c, _ in rows) for k in CHECKS}
    mode = f"Gemini ({', '.join(llm.CHAT_MODELS)})" if llm.available() else "evidence-only template (no GEMINI_API_KEY)"
    if llm.available() and not args.url:
        from api.answer import STATS
        drafted = STATS["gemini_ok"]
        tried = drafted + STATS["gemini_error"] + STATS["gemini_bad_json"]
        mode += (f"; Gemini drafted {drafted} of {tried} answers it was asked for "
                 f"({STATS['gemini_error']} errors, {STATS['gemini_bad_json']} bad JSON fell back to evidence-only)")
    tick = lambda ok: "✅" if ok else "❌"

    lines = [
        "# FlameCheck eval results", "",
        f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Answer mode: {mode} · "
        f"API: {args.url or 'in-process'} · Median latency: {sorted(times)[len(times) // 2] * 1000:.0f} ms", "",
        f"**Score: {passed} of {len(rows)} questions pass every check.**", "",
        "| Check | Passed |", "| --- | --- |",
        *[f"| {k.replace('_', ' ')} | {per_check[k]} / {len(rows)} |" for k in CHECKS], "",
        "| ID | Kind | Question | Status | Status ok | Citations real | Required cited | No invented values | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for q, d, c, notes in rows:
        lines.append(f"| {q['id']} | {q['kind']} | {q['question']} | {d['status']} | "
                     + " | ".join(tick(c[k]) for k in CHECKS) + f" | {'; '.join(notes)} |")
    lines += ["", "Checks are defined in `eval/questions.yaml`. Expected values come from `data/clean/tests.csv`."]
    (HERE / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Score: {passed}/{len(rows)}  ({mode})")
    for k in CHECKS:
        print(f"  {k}: {per_check[k]}/{len(rows)}")
    worst = sorted(rows, key=lambda r: sum(r[2].values()))[:3]
    print("Worst:")
    for q, d, c, notes in worst:
        print(f"  {q['id']} [{sum(c.values())}/4] {q['question']} -> {'; '.join(notes) or 'ok'}")


if __name__ == "__main__":
    main()
