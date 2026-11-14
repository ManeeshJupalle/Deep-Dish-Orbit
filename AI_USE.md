# Use of AI

Space Apps asks every team to say which AI tools they used and how.

## In the product

- **Google Gemini** (Flash model, via the Gemini API) drafts answers from the retrieved NASA evidence only, at temperature 0, as JSON. Gemini embeddings index the NASA text for search.
- Gemini output is never shown as-is. `api/verify.py` drops any claim that cites an unknown id, contains a number that is not in the cited NASA row or document, or describes Moon/Mars behavior without stating it as a 0 g or 1 g bound. The "no direct data" message is fixed text, not model output.
- Without a Gemini key, FlameCheck runs in evidence-only mode: it restates the closest NASA test rows, checked by the same verifier.

## In building it

- **Claude Code** (Anthropic) helped write the code, the data pipeline, the web app, the test set and the documentation, working from our architecture and phase plan.
- The NASA tables were read from the PSI website and saved to `data/raw/`. Each saved file was compared byte for byte (SHA-256) with the copy shown in the browser, so no value was retyped or generated.
- Expected answers in `eval/questions.yaml` were taken from `data/clean/tests.csv`.

## What people checked

_Team: before submitting, list what you reviewed yourselves, e.g. spot-checking rows in `tests.csv` against the PSI pages, reading `data/clean/MAPPING.md`, and trying questions on the live site._

## Images and video

The flame drawing on the site is a hand-written SVG, not AI-generated. If the demo video or slides include AI-generated images or video, they must carry a visible watermark.
