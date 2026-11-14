import pytest

from api import llm


@pytest.fixture(autouse=True)
def no_network_llm(monkeypatch):
    """Tests never call Gemini: answers use the evidence-only template, text search uses keywords."""
    monkeypatch.setattr(llm, "available", lambda: False)
