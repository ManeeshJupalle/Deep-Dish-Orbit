# FlameCheck — notes for Claude Code

NASA Space Apps 2026, challenge "Flame in Freefall". A fire-safety copilot that answers only from NASA PSI microgravity combustion data, cites every claim, and says "no direct data" when NASA never tested the conditions.

## Read first

- `ARCHITECTURE.md` — system design, data schema, API contract, retrieval/verify rules
- `BUILD_PHASES.md` — the phase plan. Work on **one phase at a time**, only the phase the user names.

## Rules

- Never invent data. If a value isn't in the NASA source, leave it empty (null). Don't fill, guess or interpolate.
- Every answer claim must cite a `test_id` or `chunk_id` that exists. `verify.py` must stay strict.
- No partial-gravity (Moon/Mars) data exists in PSI. Those questions return `no_direct_data` with 0 g and 1 g bounds.
- Keep the `/ask` response exactly as in ARCHITECTURE.md section 6. If it must change, update the doc and `web/fixtures/` in the same change.
- Secrets only in `.env` (git-ignored). Never put the Gemini key in `web/`.
- Pressure is stored in kPa. Oxygen in %. Flow in cm/s. Gravity in g.
- Keep code simple: hackathon, 2 days. No new services or databases without asking.
- Commit after each phase's "Done when" checks pass.
- The whole team works in one shared chat: treat it as a single-person, single-track build.
- Python is 3.11, installed with uv (no plain `python` on PATH). Use `uv` for venvs and runs.

## Commands

Run from the repo root unless noted.

- Install: `uv sync` (Python) and `cd web && npm install` (web)
- API: `uv run uvicorn api.main:app --reload --port 8000` (docs at http://localhost:8000/docs)
- Web: `cd web && npm run dev` (http://localhost:3000)
- Tests: `uv run pytest`
- Eval: `uv run python -m eval.run_eval` (in-process) or `uv run python -m eval.run_eval --url http://localhost:8000` → `eval/results.md`
- Data: `uv run python -m pipeline.build_tests`, `uv run python -m pipeline.build_index`, `uv run python -m pipeline.check_data`
