"""Thin Gemini wrapper. The key is read from .env (GEMINI_API_KEY) and only used server-side."""
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CHAT_MODEL = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL") or "gemini-embedding-001"


def available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


@lru_cache(maxsize=1)
def _client():
    from google import genai
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


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
    """One deterministic JSON-only completion. Returns the raw text."""
    from google.genai import types
    resp = _client().models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0, response_mime_type="application/json"),
    )
    return resp.text or ""
