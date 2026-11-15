# Use of AI

Space Apps asks every team to say which AI tools they used and how.

## In the product

- **Azure OpenAI GPT-5.6-luna** drafts the live answers from the retrieved NASA evidence only, as JSON. It runs keyless: the API's Azure managed identity has access to the model, so no model key is stored. We picked it after running the 20-question test set with six models (see the README, "Which model and why").
- **Google Gemini** (`gemini-3.5-flash-lite`, then `gemini-3.1-flash-lite`, via the Gemini API free tier) is the fallback drafter, used if Azure OpenAI fails and a Gemini key is set. `gemini-embedding-001` embeds the NASA text for search. Without a Gemini key, search uses keywords instead.
- Model output is never shown as-is. `api/verify.py` drops any claim that cites an unknown id, contains a number that is not in the cited NASA row or document, states an outcome ("burned", "extinguished") the cited test doesn't record, or describes Moon/Mars behavior without stating it as a 0 g or 1 g bound. If any claim is dropped, the model's summary is replaced by a plain note. The "no direct data" message is fixed text, not model output.
- With no drafting model available, FlameCheck runs in evidence-only mode: it restates the closest NASA test rows, checked by the same verifier.

## In building it

- **Claude Code** (Anthropic) helped write the code, the data pipeline, the web app, the test set and the documentation, working from our architecture and phase plan.
- The NASA tables were read from the PSI website and saved to `data/raw/`. Each saved file was compared byte for byte (SHA-256) with the copy shown in the browser, so no value was retyped or generated.
- Expected answers in `eval/questions.yaml` were taken from `data/clean/tests.csv`.

## What people checked

_Team: before submitting, list what you reviewed yourselves, e.g. spot-checking rows in `tests.csv` against the PSI pages, reading `data/clean/MAPPING.md`, and trying questions on the live site._

## Images and video

The flame drawing on the site is a hand-written SVG, not AI-generated. If the demo video or slides include AI-generated images or video, they must carry a visible watermark.
