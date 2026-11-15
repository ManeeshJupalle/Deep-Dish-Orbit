# Space Apps submission (draft fields)

Paste these into the Space Apps project page. Replace every _italic placeholder_ first.

## Project name

FlameCheck

## Summary

FlameCheck is a fire-safety copilot that answers questions only from NASA's microgravity combustion experiments. Every claim cites a NASA PSI test, and when NASA never tested the conditions asked about, such as fire at lunar gravity, it says "no direct data" and shows the 0 g and 1 g tests that bound the answer. A coverage map shows what NASA has tested and the Moon-base conditions it hasn't.

## Demo link

_Video (≤30 s, English subtitles) or slides (≤7), public, no login_

## Final project link

_Suggested: the live site, https://thankful-forest-0ab84ba0f.3.azurestaticapps.net (or the public GitHub repo), no login_

## Detailed description

Engineers designing Artemis and Mars habitats need to know how materials burn at the oxygen and pressure those habitats will use (likely ≥30% O₂ and ≤70.3 kPa). NASA's Physical Sciences Informatics (PSI) system holds the answers that exist, spread across investigations and tables. It has no data at partial gravity.

FlameCheck turns four PSI investigations (BASS-II, SAFFIRE-II, SAFFIRE-III, FLEX) into one clean table of 423 tests. A user asks a question in plain English, optionally with material, oxygen, pressure and gravity. FlameCheck:

1. finds the closest NASA tests (missing values never earn credit) and the best 0 g and 1 g bounding tests;
2. asks a language model (Azure OpenAI GPT-5.6-luna, with Gemini as fallback) to draft short claims from that evidence only, each citing a test or NASA document;
3. runs every claim through a verifier that drops unknown citations, numbers not in the cited row, outcomes ("burned") the cited test doesn't record, and Moon/Mars claims not stated as 0 g or 1 g bounds;
4. returns a cited answer with a High/Medium/Low trust badge, the ranked evidence with links to each PSI page, and the gaps computed from the data. If nothing matches, it says "no direct data".

On a 20-question test set written from the data (lookups, comparisons, suppression, no-data), the first run scored 17/20. The current version scores 20/20 with GPT-5.6-luna drafting the answers. We ran the same test set with six models. All scored 20/20, because the verifier blocks unsupported claims; they differed in how many drafted claims the verifier removed (5 for GPT-5.6-luna, 16 for GPT-4.1-mini), speed and cost. GPT-5.6-luna drafted as faithfully as the best, was about twice as fast as GPT-5-mini, and was the cheapest of the paid models. Built with Python, FastAPI, Next.js, Azure OpenAI and Gemini, hosted on Microsoft Azure.

## NASA data used

- NASA Physical Sciences Informatics: BASS-II (PSI-25), SAFFIRE-II (PSI-99), SAFFIRE-III (PSI-100), FLEX (PSI-69). Experimental tables and investigation descriptions.
- NASA Technical Reports Server: 9 abstracts on BASS-II, Saffire, FLEX, SIBAL and reduced-gravity flammability.

## Other data used

None.

## Use of AI

Azure OpenAI GPT-5.6-luna drafts answers from retrieved NASA evidence. Google Gemini is the fallback drafter and embeds NASA text for search. All model output is checked by a verifier before display. Claude Code (Anthropic) helped write the code, data pipeline, web app, test set and documentation. Details are in AI_USE.md. No AI-generated images or video are used _(if the video uses any, they carry a visible watermark)_.

## Before you click Submit

- [x] Gemini key in `.env` (local); embeddings built
- [x] Eval re-run with the live model, GPT-5.6-luna (20/20), and five other models; score updated in README, About page, video and this file
- [ ] Optional: Gemini key added on Azure App Service (embedding search and fallback drafting)
- [ ] Repo public on GitHub; `.env` not committed
- [x] API deployed (Azure App Service) and web deployed (Azure Static Web Apps), `ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_URL` set
- [ ] Live link opened in a private window on a phone; 3 questions asked
- [ ] "What people checked" filled in AI_USE.md
- [ ] Demo video ≤30 s with subtitles, or ≤7 slides, public, no login
- [ ] No NASA logos anywhere
- [ ] Both verification boxes ticked, submitted before 5 PM
