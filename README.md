# FlameCheck

A fire-safety copilot for spacecraft and habitat engineers. FlameCheck answers questions **only** from NASA microgravity combustion experiments (NASA PSI), cites a NASA test for every claim, and says **"no direct data"** when NASA never tested the conditions you asked about, such as fire at lunar gravity.

NASA Space Apps Challenge 2026, challenge: *Flame in Freefall*.

- **Live site:** _add the Vercel link after deploying_
- **Ask:** "Is cotton safe at 34% oxygen on the Moon?" → *No direct data*. NASA's cotton-fiberglass tests at 0 g (SAFFIRE2-2-5, 22.1% O₂) and 1 g (SAFFIRE2-2-5-1G) only bound the answer, and no cotton test reached 34% O₂.
- **Explore:** a coverage map of every test by oxygen and pressure, with the Moon-base box (≥30% O₂, ≤70.3 kPa) that NASA has not tested.

## How it stays honest

```
question ─► retrieve.py ─► answer.py (Gemini, evidence only) ─► verify.py ─► answer or "no direct data"
              │                                                    │
        tests.csv + NASA text                       drops any claim with an unknown citation,
        (closest tests, 0 g / 1 g bounds,           a number not in the cited row, or a Moon/Mars
         gaps computed from the data)               claim not stated as a 0 g / 1 g bound
```

- Conditions are parsed from the question with plain rules, so a condition can only come from words the user typed.
- Gaps ("No cotton test at or above 34% O2 (highest tested: 22.1%)") are computed from the data, not written by the model.
- If Gemini is unavailable or none of its claims survive, FlameCheck restates the closest evidence rows instead. Those claims go through the same verifier.
- Every dropped claim is logged to `logs/verify.jsonl`.

## Test-set score

`eval/questions.yaml` has 20 questions written from `data/clean/tests.csv`: 6 lookups, 5 comparisons, 4 suppression questions and 5 no-data questions. Each is scored on the right status, real citations, required tests cited, and no invented values.

| Run | Score |
| --- | --- |
| First run (`eval/results_before_fixes.md`) | 17 / 20 |
| After fixing the 3 failures, evidence-only mode (`eval/results.md`) | **20 / 20** |
| Gemini mode | _run `uv run python -m eval.run_eval` with `GEMINI_API_KEY` set_ |

## NASA data used

| Investigation | PSI | Rows in `tests.csv` | Notes |
| --- | --- | --- | --- |
| [BASS-II](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25) | PSI-25 | 129 | ISS solid fuels (PMMA, SIBAL, Nomex, wax); table has no pressure or outcome column |
| [SAFFIRE-II](https://psi.nasa.gov/physci/repo/data/investigations/PSI-99) | PSI-99 | 18 | 9 Cygnus samples, each with its 1 g comparison row |
| [SAFFIRE-III](https://psi.nasa.gov/physci/repo/data/investigations/PSI-100) | PSI-100 | 2 | Large SIBAL burns; no O₂ or outcome in the table |
| [FLEX](https://psi.nasa.gov/physci/repo/data/investigations/PSI-69) | PSI-69 | 274 | Methanol/heptane droplets with N₂, CO₂ or He |

Plus 9 abstracts from the [NASA Technical Reports Server](https://ntrs.nasa.gov). How each raw column maps to the schema, and every value left empty or set aside, is in [`data/clean/MAPPING.md`](data/clean/MAPPING.md). PSI data is CC0-1.0.

**Limits:** PSI has no partial-gravity fire data, so Moon and Mars questions always return "no direct data". BASS-II's table reports no pressure or outcome. Nine FLEX pressures that contradict the documented 0.5–1.5 atm range are left empty. FlameCheck is not an engineering safety review.

## Run it

Needs Python 3.11 with [uv](https://docs.astral.sh/uv/) and Node 20+.

```bash
uv sync
cp .env.example .env   # add GEMINI_API_KEY (optional: without it, answers are evidence-only)
uv run uvicorn api.main:app --reload --port 8000
```

```bash
cd web && npm install
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
npm run dev            # http://localhost:3000
```

Tests and eval:

```bash
uv run pytest
uv run python -m eval.run_eval
```

Rebuild the data:

```bash
uv run python -m pipeline.build_tests && uv run python -m pipeline.build_index && uv run python -m pipeline.check_data
```

## Deploy

- **API (Render):** new Blueprint from this repo (`render.yaml`). Set `GEMINI_API_KEY` and `ALLOWED_ORIGINS` (the Vercel URL).
- **Web (Vercel):** import the repo with root directory `web`, and set `NEXT_PUBLIC_API_URL` to the Render URL.

## Repo layout

```
api/        FastAPI: /ask, /tests, /coverage, /investigations, /chunks; retrieve, answer, verify, trust
pipeline/   cleaners per investigation, text index, data checks
data/       raw PSI tables, clean tests.csv / investigations.json / chunks.jsonl, NASA text
web/        Next.js site: Ask, Explore (coverage map), About
eval/       20-question test set and scorer
tests/      pytest
```

## Credits and AI use

Data: NASA Physical Sciences Informatics and the NASA Technical Reports Server. No NASA logos are used. AI use is described in [AI_USE.md](AI_USE.md).
