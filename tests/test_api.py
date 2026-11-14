import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import FIXTURES, app
from api.schemas import AskRequest, AskResponse

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


@pytest.mark.parametrize("name", ["answered", "no_direct_data", "out_of_scope"])
def test_fixture_matches_contract(name):
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    resp = AskResponse.model_validate(data)
    assert resp.status == name


def test_contract_example_request_is_valid():
    AskRequest.model_validate({
        "question": "Is cotton safe at 34% oxygen on the Moon?",
        "conditions": {"material": "cotton", "o2_pct": 34, "pressure_kpa": 70.3,
                       "gravity": "moon", "flow_cm_s": None},
    })


def test_ask_returns_valid_response():
    r = client.post("/ask", json={"question": "Does PMMA burn at 21% oxygen?"})
    assert r.status_code == 200
    AskResponse.model_validate(r.json())


def test_ask_rejects_bad_gravity():
    r = client.post("/ask", json={"question": "x", "conditions": {"gravity": "jupiter"}})
    assert r.status_code == 422
