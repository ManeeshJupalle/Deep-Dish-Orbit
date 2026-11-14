"""Thin Gemini wrapper. The key is read from .env (GEMINI_API_KEY) and only used server-side."""
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Comma-separated: the first model is used; the next ones are tried if it is overloaded or fails.
# Flash-Lite answers in under a second on the free tier; full Flash models were overloaded (503/504) when tested.
CHAT_MODELS = [m.strip() for m in (os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite,gemini-3.1-flash-lite").split(",")
               if m.strip()]
CHAT_MODEL = CHAT_MODELS[0]
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL") or "gemini-embedding-001"
TIMEOUT_MS = 20_000  # per request; keeps /ask from hanging on an overloaded model


def available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


@lru_cache(maxsize=1)
def _client():
    from google import genai
    from google.genai import types
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=TIMEOUT_MS))


def embed(texts: list[str], task_type: str) -> np.ndarray:
    """Unit-length embeddings, one row per text. task_type: RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY."""
    from google.genai import types
    rows = []
    for i in range(0, len(texts), 100):
        resp = _client().models.embed_content(
            model=EMBED_MODEL, contents=texts[i:i + 100], config=types.EmbedContentConfig(task_type=task_type))
        rows += [e.values for e in resp.embeddings]
    m = np.asarray(rows, dtype=np.float32)
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def generate_json(system: str, prompt: str) -> str:
    """One deterministic JSON-only completion, trying each model in CHAT_MODELS. Returns the raw text."""
    from google.genai import types
    config = types.GenerateContentConfig(system_instruction=system, temperature=0, response_mime_type="application/json")
    error: Exception | None = None
    for model in CHAT_MODELS:
        try:
            return _client().models.generate_content(model=model, contents=prompt, config=config).text or ""
        except Exception as e:  # overloaded, timed out or unavailable: try the next model
            error = e
    raise error  # type: ignore[misc]
