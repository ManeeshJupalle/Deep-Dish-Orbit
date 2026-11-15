# FlameCheck

A fire-safety copilot for spacecraft and habitat engineers. FlameCheck answers questions **only** from NASA microgravity combustion experiments (NASA PSI), cites a NASA test for every claim, and says **"no direct data"** when NASA never tested the conditions you asked about, such as fire at lunar gravity.

NASA Space Apps Challenge 2026, challenge: *Flame in Freefall*.

- **Live site:** https://thankful-forest-0ab84ba0f.3.azurestaticapps.net
- **Ask:** "Is cotton safe at 34% oxygen on the Moon?" → *No direct data*. NASA's cotton-fiberglass tests at 0 g (SAFFIRE2-2-5, 22.1% O₂) and 1 g (SAFFIRE2-2-5-1G) only bound the answer, and no cotton test reached 34% O₂.
- **Explore:** a coverage map of every test by oxygen and pressure, with the Moon-base box (≥30% O₂, ≤70.3 kPa) that NASA has not tested.

## How it stays honest

```
question ─► retrieve.py ─► answer.py (LLM, evidence only) ─► verify.py ─► answer or "no direct data"
              │                                                    │
        tests.csv + NASA text                       drops any claim with an unknown citation,
        (closest tests, 0 g / 1 g bounds,           a number not in the cited row, or a Moon/Mars
         gaps computed from the data)               claim not stated as a 0 g / 1 g bound, or an
                                                    outcome ("burned") the cited row doesn't record
```

- Conditions are parsed from the question with plain rules, so a condition can only come from words the user typed.
- Gaps ("No cotton test at or above 34% O2 (highest tested: 22.1%)") are computed from the data, not written by the model.
- Answers are drafted by Azure OpenAI GPT-5.6-luna, with Gemini as the fallback. If no model answers, or no surviving claim cites a test at the asked conditions, FlameCheck restates the closest evidence rows. Those claims go through the same verifier. If any drafted claim is dropped, the model's summary is replaced by a plain note saying so.
- Every dropped claim is logged to `logs/verify.jsonl`.

## Test-set score

`eval/questions.yaml` has 20 questions written from `data/clean/tests.csv`: 6 lookups, 5 comparisons, 4 suppression questions and 5 no-data questions. Each is scored on the right status, real citations, required tests cited, and no invented values.

| Run | Score |
| --- | --- |
| First run, evidence-only (`eval/results_before_fixes.md`) | 17 / 20 |
| After fixing the 3 failures, evidence-only (`eval/results_evidence_only.md`) | 20 / 20 |
| **Live model** (Azure OpenAI `gpt-5.6-luna`; it drafted 19 of 19 answers and `verify.py` dropped 5 unsupported claims) (`eval/results.md`) | **20 / 20** |

## Which model and why

We ran the same 20 questions with six models, using the same retrieval and verifier (in-process runs on 2026-11-15). Every model drafted 19 of the 19 answers it was asked for, and every model scored 20/20, because the verifier blocks unsupported claims. What differs is how many drafted claims the verifier had to remove, speed and cost. Results are in `eval/results_<model>.md`.

| Model | Score | Claims the verifier removed | Median time | Approx. cost per answer |
| --- | --- | --- | --- | --- |
| GPT-5.6-luna (live) | 20/20 | 5 and 5 (two runs) | 2.8 s and 3.5 s | about $0.001 |
| GPT-5-mini | 20/20 | 3 and 5 (two runs) | 5.6 s and 5.7 s | about $0.002 |
| Gemini 3.5 Flash-Lite (fallback) | 20/20 | 5 (earlier runs: 6, 4, 1) | 1.1 s | free tier |
| GPT-4.1-mini | 20/20 | 16 | 2.2 s | about $0.0016 |
| GPT-5.4 | 20/20 | 7 | 4.2 s | about $0.014 |
| GPT-5.5 | 20/20 | 7 | 5.7 s | not checked |

GPT-5.6-luna drafted as faithfully as the best model. A difference of a few removed claims is run-to-run noise: Gemini ranged from 1 to 6 over its runs. It was about twice as fast as GPT-5-mini and is the cheapest per answer of the paid models. The larger GPT-5.4 and GPT-5.5 did not draft more faithfully, and they are slower and cost more. GPT-4.1-mini was clearly worse: the verifier removed 16 claims, mostly outcome words the cited test does not record (for example "did not ignite" for a methanol test NASA recorded as a disruption).

In FlameCheck the verifier, not the model, decides what reaches the user. The model was chosen by measurement. Live on Azure, an answer takes about 6–8 s (network plus model).

Costs: the GPT-5.6-luna price is from Azure's retail price list ($0.20 per 1M input tokens, $1.20 per 1M output, global standard). The other Azure prices are approximate list prices from a third-party tracker (GPT-4.1-mini $0.40/$1.60, GPT-5-mini $0.25/$2.00, GPT-5.4 $2.50/$15 per 1M). Each answer sends about 3,100 input tokens.

## NASA data used

| Investigation | PSI | Rows in `tests.csv` | Notes |
| --- | --- | --- | --- |
| [BASS-II](https://psi.nasa.gov/physci/repo/data/investigations/PSI-25) | PSI-25 | 129 | ISS solid fuels (PMMA, SIBAL, Nomex, wax); table has no pressure or outcome column |
| [SAFFIRE-II](https://psi.nasa.gov/physci/repo/data/investigations/PSI-99) | PSI-99 | 18 | 9 Cygnus samples, each with its 1 g comparison row |
| [SAFFIRE-III](https://psi.nasa.gov/physci/repo/data/investigations/PSI-100) | PSI-100 | 2 | Large SIBAL burns; no O₂ or outcome in the table |
| [FLEX](https://psi.nasa.gov/physci/repo/data/investigations/PSI-69) | PSI-69 | 274 | Methanol/heptane droplets with N₂, CO₂ or He |

Plus 9 abstracts from the [NASA Technical Reports Server](https://ntrs.nasa.gov). How each raw column maps to the schema, and every value left empty or set aside, is in [`data/clean/MAPPING.md`](data/clean/MAPPING.md). PSI data is CC0-1.0.

**Limits:** PSI has no partial-gravity fire data, so Moon and Mars questions always return "no direct data". BASS-II's table reports no pressure or outcome. One FLEX pressure recorded as 0 mmHg is left empty; nine FLEX tests at about 2–3 atm are kept as NASA's table gives them, although the PSI description of FLEX only mentions 0.5–1.5 atm. FlameCheck is not an engineering safety review.

## Run it

Needs Python 3.11 with [uv](https://docs.astral.sh/uv/) and Node 20+.

```bash
uv sync
cp .env.example .env   # model settings are optional, see below
uv run uvicorn api.main:app --reload --port 8000
```

Model settings in `.env`, all optional: `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT` for Azure OpenAI drafting (sign in with `az login`; no key is needed), and `GEMINI_API_KEY` for the Gemini fallback and the search embeddings. Without any of them, answers are evidence-only and NASA-text search uses keywords.

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

Both parts run on Microsoft Azure.

- **Web:** Azure Static Web Apps (Free tier) at https://thankful-forest-0ab84ba0f.3.azurestaticapps.net. `web/next.config.ts` sets `output: "export"`, so `npm run build` writes plain files to `web/out`. Set `NEXT_PUBLIC_API_URL` to the API URL before building.
- **API:** Azure App Service (Linux, Python 3.11, plan B1 with Always On, East US) at https://flamecheck-api.azurewebsites.net. It is deployed as a zip of `api/`, `data/clean/` (`tests.csv`, `chunks.jsonl`, `embeddings.npy`, `investigations.json`) and a `requirements.txt` made with `uv export --no-dev --no-hashes --no-emit-project --format requirements-txt`. The app setting `SCM_DO_BUILD_DURING_DEPLOYMENT=true` makes Azure install the requirements. Start command: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`.
- **App settings:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, and `ALLOWED_ORIGINS` (the Static Web Apps URL plus http://localhost:3000). `GEMINI_API_KEY` is optional and not set on Azure right now, so NASA-text search uses keywords there.
- **No model key:** Azure OpenAI (resource `flamecheck-ai`, East US) is keyless. The App Service's system-assigned managed identity has the "Cognitive Services OpenAI User" role.

`render.yaml` is left from the earlier Render plan and is not used.

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
