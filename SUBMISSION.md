# Space Apps submission (draft fields)

Paste these into the Space Apps project page. Replace every _italic placeholder_ first.

## Project name

FlameCheck

## Summary

FlameCheck is a fire-safety copilot that answers questions only from NASA's microgravity combustion experiments. Every claim cites a NASA PSI test, and when NASA never tested the conditions asked about, such as fire at lunar gravity, it says "no direct data" and shows the 0 g and 1 g tests that bound the answer. A coverage map shows what NASA has tested and the Moon-base conditions it hasn't.

## Demo link

_Video (≤30 s, English subtitles) or slides (≤7), public, no login_

## Final project link

_Public GitHub repo or live site, no login_

## Detailed description

Engineers designing Artemis and Mars habitats need to know how materials burn at the oxygen and pressure those habitats will use (likely ≥30% O₂ and ≤70.3 kPa). NASA's Physical Sciences Informatics (PSI) system holds the answers that exist, spread across investigations and tables. It has no data at partial gravity.

FlameCheck turns four PSI investigations (BASS-II, SAFFIRE-II, SAFFIRE-III, FLEX) into one clean table of 423 tests. A user asks a question in plain English, optionally with material, oxygen, pressure and gravity. FlameCheck:

1. finds the closest NASA tests (missing values never earn credit) and the best 0 g and 1 g bounding tests;
2. asks Gemini to draft short claims from that evidence only, each citing a test or NASA document;
3. runs every claim through a verifier that drops unknown citations, numbers not in the cited row, outcomes ("burned") the cited test doesn't record, and Moon/Mars claims not stated as 0 g or 1 g bounds;
4. returns a cited answer with a High/Medium/Low trust badge, the ranked evidence with links to each PSI page, and the gaps computed from the data. If nothing matches, it says "no direct data".

On a 20-question test set written from the data (lookups, comparisons, suppression, no-data), the first run scored 17/20. The current version scores 20/20 with Gemini drafting the answers, and the verifier removed 6 drafted claims the data did not back. Built with Python, FastAPI, Next.js and Gemini.

## NASA data used

- NASA Physical Sciences Informatics: BASS-II (PSI-25), SAFFIRE-II (PSI-99), SAFFIRE-III (PSI-100), FLEX (PSI-69). Experimental tables and investigation descriptions.
- NASA Technical Reports Server: 9 abstracts on BASS-II, Saffire, FLEX, SIBAL and reduced-gravity flammability.

## Other data used

None.

## Use of AI

Google Gemini drafts answers from retrieved NASA evidence and embeds NASA text for search. All of its output is checked by a verifier before display. Claude Code (Anthropic) helped write the code, data pipeline, web app, test set and documentation. Details are in AI_USE.md. No AI-generated images or video are used _(if the video uses any, they carry a visible watermark)_.

## Before you click Submit

- [x] Gemini key in `.env` (local); embeddings built
- [x] Eval re-run in Gemini mode (20/20); score updated in README, About page, video and this file
- [ ] Gemini key added on Render
- [ ] Repo public on GitHub; `.env` not committed
- [ ] API deployed (Render) and web deployed (Vercel), `ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_URL` set
- [ ] Live link opened in a private window on a phone; 3 questions asked
- [ ] "What people checked" filled in AI_USE.md
- [ ] Demo video ≤30 s with subtitles, or ≤7 slides, public, no login
- [ ] No NASA logos anywhere
- [ ] Both verification boxes ticked, submitted before 5 PM
