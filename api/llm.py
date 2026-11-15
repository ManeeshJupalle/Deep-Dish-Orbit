"""Thin model wrapper, server-side only.

Drafting: Azure OpenAI when AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT are set (keyless: the App Service's
managed identity, or `az login` locally), then Gemini (GEMINI_API_KEY) as the fallback.
Search embeddings: Gemini only, because data/clean/embeddings.npy was built with gemini-embedding-001.
"""
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_API_VERSION = "2025-04-01-preview"
# Comma-separated: the first model is used; the next ones are tried if it is overloaded or fails.
# Flash-Lite answers in under a second on the free tier; full Flash models were overloaded (503/504) when tested.
CHAT_MODELS = [m.strip() for m in (os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite,gemini-3.1-flash-lite").split(",")
               if m.strip()]
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL") or "gemini-embedding-001"
TIMEOUT_MS = 20_000  # per request; keeps /ask from hanging on an overloaded model
USAGE: Counter = Counter()  # calls and tokens per provider, read by eval/run_eval.py


def azure_configured() -> bool:
    return bool(AZURE_ENDPOINT and AZURE_DEPLOYMENT)


def gemini_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def available() -> bool:
    """A drafting model is configured."""
    return azure_configured() or gemini_configured()


def describe() -> str:
    """The drafting models in the order they are tried, for the eval report."""
    names = ([f"Azure OpenAI {AZURE_DEPLOYMENT}"] if azure_configured() else []) + \
            ([f"Gemini {', '.join(CHAT_MODELS)}"] if gemini_configured() else [])
    return " then ".join(names) or "evidence-only template (no model configured)"


@lru_cache(maxsize=1)
def _client():
    from google import genai
    from google.genai import types
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=TIMEOUT_MS))


@lru_cache(maxsize=1)
def _azure():
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI
    token = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    return AzureOpenAI(azure_endpoint=AZURE_ENDPOINT, azure_ad_token_provider=token, api_version=AZURE_API_VERSION,
                       timeout=TIMEOUT_MS / 1000, max_retries=0)


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


def _azure_json(system: str, prompt: str) -> str:
    # GPT-5 models reason before answering and accept only the default temperature; low effort keeps them fast.
    reasoning = AZURE_DEPLOYMENT.startswith(("gpt-5", "o"))
    extra = {"reasoning_effort": "low"} if reasoning else {"temperature": 0}
    r = _azure().chat.completions.create(
        model=AZURE_DEPLOYMENT, response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}], **extra)
    USAGE["azure_calls"] += 1
    USAGE["azure_tokens_in"] += r.usage.prompt_tokens
    USAGE["azure_tokens_out"] += r.usage.completion_tokens
    return r.choices[0].message.content or ""


def generate_json(system: str, prompt: str) -> str:
    """One JSON-only completion: Azure OpenAI first if configured, then each Gemini model. Returns the raw text."""
    error: Exception | None = None
    if azure_configured():
        try:
            return _azure_json(system, prompt)
        except Exception as e:  # timed out, throttled or unavailable: fall back to Gemini
            USAGE["azure_errors"] += 1
            error = e
    if gemini_configured():
        from google.genai import types
        config = types.GenerateContentConfig(system_instruction=system, temperature=0,
                                             response_mime_type="application/json")
        for model in CHAT_MODELS:
            try:
                resp = _client().models.generate_content(model=model, contents=prompt, config=config)
                USAGE["gemini_calls"] += 1
                return resp.text or ""
            except Exception as e:  # overloaded, timed out or unavailable: try the next model
                error = e
    raise error  # type: ignore[misc]
