# FlameCheck — Build Phases

Build one phase at a time. Don't start the next phase until the current phase's **Done when** checks pass.
Each phase has a prompt you can paste into Claude Code. Architecture details are in `ARCHITECTURE.md`.

**Single-track build:** the whole team works through one shared Claude Code chat. Phases run one after another; nothing runs in parallel.

---

## Timeline at a glance

| Phase | When | Output |
| --- | --- | --- |
| 0. Setup | Sat 8:00–9:00 | Accounts, credits, tools |
| 1. Scaffold + contract | Sat 9:00–10:00 | Repo, folders, frozen `/ask` format, fixtures |
| 2. Data | Sat 10:00–13:00 | `tests.csv`, `investigations.json`, `chunks.jsonl` |
| 3. Retrieval | Sat 13:00–15:00 | `/tests`, `/coverage`, ranked evidence |
| 4. Answer + verify | Sat 15:00–18:00 | Working `/ask` with citations and "no direct data" |
| 5. Web app | Sat 18:00–22:00 | Ask screen on the live API (fixtures as fallback) |
| 6. Coverage map + deploy | Sat 22:00–24:00 | Explore screen; v1 live online |
| 7. Eval + fixes | Sun 7:00–11:00 | `eval/results.md` with a score |
| 8. Polish + story | Sun 11:00–15:00 | README, About page, video, slides |
| 9. Submit | Sun 15:00–17:00 | Submitted before the venue closes at 6 PM |

**Checkpoints:** Sat 13:00 data ready · Sat 18:00 `/ask` works end to end · Sat 24:00 deployed · Sun 17:00 submitted.

---

## Phase 0 — Setup (Sat 8:00–9:00)

**Goal:** everyone ready to build at 9:00.

- [ ] Check Space Apps account: in-person or virtual
- [ ] Claim $25 Google credits (8 AM–12 PM only), make a Gemini API key
- [ ] Join Discord; whole team works in one shared Claude Code chat
- [ ] Create the team + project on the Space Apps site, pick Flame in Freefall
- [ ] Installed: Python 3.11+, Node 20+, Git, VS Code + Claude Code

**Done when:** everyone has the repo URL and the Gemini key works.

---

## Phase 1 — Scaffold + contract (Sat 9:00–10:00)

**Goal:** an empty but runnable repo, and a frozen API format the web app can build against.

- [ ] `git init`, public GitHub repo `flamecheck`, push
- [ ] Folders from `ARCHITECTURE.md` section 3
- [ ] `.gitignore` (data/raw, .env, node_modules, .venv), `.env.example`
- [ ] `api/`: FastAPI app with `/health` and a stub `/ask` returning a fixture
- [ ] `api/schemas.py`: Pydantic models exactly matching section 6
- [ ] `web/fixtures/`: 3 sample responses — `answered.json`, `no_direct_data.json`, `out_of_scope.json`
- [ ] `web/`: Next.js + Tailwind + shadcn/ui created, runs locally

**Done when:** `GET /health` returns ok, `POST /ask` returns the fixture, `npm run dev` shows a page.

**Claude Code prompt:**

> Read ARCHITECTURE.md and BUILD_PHASES.md. Do Phase 1 only. Create the repo structure, a FastAPI app in api/ with /health and a stub POST /ask, Pydantic models in api/schemas.py that exactly match the API contract in section 6, three fixture JSON files in web/fixtures/, and a Next.js + Tailwind + shadcn/ui app in web/. Add .gitignore and .env.example. Don't write retrieval or LLM code yet. Tell me the commands to run both apps.

---

## Phase 2 — Data (Sat 10:00–13:00, cap 3 hours)

**Goal:** clean, trustworthy data for the 4 priority-1 investigations.

- [ ] Download from PSI: BASS-II (PSI-25), Saffire-II (PSI-99), Saffire-III (PSI-100), FLEX (PSI-69). Summary tables only, into `data/raw/<investigation>/`
- [ ] Confirm each PSI ID and URL on the PSI site
- [ ] One cleaner per investigation → rows in `data/clean/tests.csv` (schema in section 5.1)
- [ ] Record raw column → schema mapping in `data/clean/MAPPING.md`
- [ ] `investigations.json` from the PSI description pages (section 5.2)
- [ ] Save each PSI description as text in `data/text/`; add 5–10 NTRS paper abstracts
- [ ] `build_index.py` → `chunks.jsonl` + `embeddings.npy`
- [ ] `pipeline/check_data.py`: no duplicate `test_id`, units in range (O₂ 0–100, pressure 0–200 kPa), every row has `source_url`

**Done when:** `check_data.py` passes and `tests.csv` has rows from at least 3 investigations.

**Fallback at 12:30:** if a dataset won't parse, hand-enter its key tests from the PSI summary page and note it in `MAPPING.md`.

**Claude Code prompt:**

> Do Phase 2 for <INVESTIGATION>. The raw files are in data/raw/<INVESTIGATION>/. First show me the columns and 5 sample rows. Then write pipeline/clean_<name>.py that maps them to the tests.csv schema in ARCHITECTURE.md section 5.1, converts units (pressure to kPa), and leaves cells empty when the source has no value. Never invent or fill values. Append the column mapping to data/clean/MAPPING.md. Run it and show me the row count and 5 output rows.

---

## Phase 3 — Retrieval (Sat 13:00–15:00)

**Goal:** given a question or conditions, return the closest tests and text.

- [ ] `api/data.py`: load CSV, JSON, chunks, embeddings once at startup
- [ ] `GET /investigations`, `GET /tests` (filters), `GET /coverage`
- [ ] `retrieve.py`: condition extraction (small Gemini call when no `conditions`), row scoring (section 7.1), top 8 tests + top 5 chunks
- [ ] Bounding tests: best 0 g and best 1 g matches
- [ ] Unit tests: 5 queries with known best matches

**Done when:** a cotton/PMMA query at a given O₂ returns sensible top tests, and a Moon question returns bounding tests.

**Claude Code prompt:**

> Do Phase 3. Implement api/data.py, api/retrieve.py and the GET endpoints as described in ARCHITECTURE.md sections 6 and 7.1. Scoring must give no credit for missing values. Add pytest tests for 5 queries using real rows from data/clean/tests.csv. Show me the top results for: "PMMA at 21% oxygen", "cotton fabric in a spacecraft", "fire on the Moon at 34% oxygen".

---

## Phase 4 — Answer + verify + trust (Sat 15:00–18:00)

**Goal:** `/ask` returns verified, cited answers, or honestly says "no direct data".

- [ ] `api/prompts/answer.md`: the rules in section 7.2
- [ ] `answer.py`: Gemini call, temperature 0, JSON output, retries once on bad JSON
- [ ] `verify.py`: the 3 checks + status decision (section 7.3), log drops to `logs/verify.jsonl`
- [ ] `trust.py`: levels from section 7.4
- [ ] Wire into `/ask`; return the contract exactly

**Done when (6 PM checkpoint):**

- [ ] A matching-conditions question → `answered`, every claim cited
- [ ] A Moon/Mars question → `no_direct_data` with 0 g/1 g bounds
- [ ] A rocket question → `out_of_scope`
- [ ] A test where you inject a fake citation → `verify.py` drops it

**Claude Code prompt:**

> Do Phase 4. Implement answer.py, verify.py and trust.py following ARCHITECTURE.md sections 7.2–7.4, and wire them into POST /ask. verify.py is the most important file: write pytest tests that inject a fake test id and a made-up number and prove both claims get dropped. Then run /ask on 3 questions (one matching, one Moon, one rocket) and show me the JSON.

---

## Phase 5 — Web app (Sat 18:00–22:00)

**Goal:** a clean, fast Ask screen.

- [ ] Ask page layout, question box, condition fields, sample questions (build on fixtures first)
- [ ] `AnswerCard`, `TrustBadge`, `EvidenceTable`, `GapsList` (section 8)
- [ ] Status banner styles: answered / no direct data / out of scope
- [ ] Citation chips scroll to and highlight the evidence row
- [ ] Switch to the live API with `NEXT_PUBLIC_API_URL`
- [ ] Loading and error states; works on a phone

**Done when:** all 3 fixtures look right, and a live question shows a real answer in under 5 seconds.

**Claude Code prompt:**

> Do Phase 5. Build the Ask screen in web/ per ARCHITECTURE.md section 8, using the fixtures in web/fixtures/ through a small api client that switches to NEXT_PUBLIC_API_URL when set. Components: AnswerCard, TrustBadge, EvidenceTable, GapsList. Use shadcn/ui. Make the "no direct data" state look deliberate and clear, not like an error.

---

## Phase 6 — Coverage map + deploy (Sat 22:00–24:00)

**Goal:** the "NASA's data gap" picture, and a live link.

- [ ] Explore page: `CoverageMap` from `/coverage` (x = pressure kPa, y = O₂ %, colour = investigation)
- [ ] Shade the Moon-base zone: O₂ ≥ 30%, pressure ≤ 70.3 kPa
- [ ] `InvestigationCompare` table from `/investigations`
- [ ] Deploy API (Cloud Run or Render) and web (Vercel); set env vars; check CORS
- [ ] Open the live site signed out, ask 3 questions

**Done when:** the live URL works on your phone.

**Fallback:** if deploy fails by 23:30, stop and sleep. Record the demo locally on Sunday.

---

## Phase 7 — Eval + fixes (Sun 7:00–11:00)

**Goal:** a real accuracy number to show judges.

- [ ] `eval/questions.yaml`: 20 questions (6 lookup, 5 compare, 4 suppression, 5 no-data), expected answers taken from `tests.csv`
- [ ] `run_eval.py` → `eval/results.md`
- [ ] Fix the 3 worst failures (usually retrieval, not the prompt)
- [ ] Re-run, keep the final table
- [ ] If time allows: add priority-2 data (ACME CFI-G for high oxygen)

**Done when:** `results.md` exists with a score, and no answer contains an invented number.

**Cut line:** at 10:00, if fewer than 20 questions are written, ship 10.

**Claude Code prompt:**

> Do Phase 7. Write eval/run_eval.py per ARCHITECTURE.md section 10. It reads eval/questions.yaml, calls /ask, and scores status, real citations, required citations, and invented numbers. Write a markdown table to eval/results.md with totals. Then show me the 3 worst failures and why they failed.

---

## Phase 8 — Polish + story (Sun 11:00–15:00)

- [ ] About page: data sources, method diagram, eval score, AI use
- [ ] README: what it is, live link, screenshots, how to run, data credits, eval score
- [ ] `AI_USE.md`: Claude Code (coding help), Gemini (answers + embeddings), what humans checked
- [ ] Remove any NASA logos; credit NASA PSI as the data source
- [ ] 30-second video with English subtitles (script below)
- [ ] Backup: 7-slide deck (title, problem, solution, demo, how it stays honest, results, team)

**Video script (≤ 30 s):**

1. 0–3 s — "I'm Maneesh, team FlameCheck, Chicago."
2. 3–8 s — "A Moon base will run at 30%+ oxygen. NASA has no lunar-gravity fire data."
3. 8–20 s — Ask a question → cited answer → click a source → ask a Moon question → "no direct data" with bounds.
4. 20–26 s — Coverage map: "Here's what NASA has tested, and the Moon-base gap."
5. 26–30 s — "Scored X of 20 on our test set. Every claim traces to NASA."

---

## Phase 9 — Submit (Sun 15:00–17:00)

- [ ] Fill every required field (summary, description, NASA data, other data, AI use)
- [ ] Demo link (video or slides) public, no login
- [ ] Final project link (repo or site) public, no login
- [ ] Open every link in a private window
- [ ] Tick both verification boxes, click **Submit for Judging** by 17:00

---

## Definition of done (whole project)

- [ ] Live site answers questions with citations to real PSI tests
- [ ] Moon/Mars questions return "no direct data" with bounds, never a guess
- [ ] Coverage map shows the Moon-base gap
- [ ] Eval score published in README and About page
- [ ] Repo public, AI use disclosed, demo ≤ 30 s or ≤ 7 slides
