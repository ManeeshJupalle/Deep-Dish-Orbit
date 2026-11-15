"""Pydantic models for the /ask contract (ARCHITECTURE.md section 6).

Keep these exactly in sync with the doc and web/fixtures/. Extra fields are
rejected so any drift from the contract fails loudly.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict

Gravity = Literal["micro", "moon", "mars", "partial", "earth"]
Status = Literal["answered", "no_direct_data", "out_of_scope"]
Outcome = Literal["ignited", "burned", "extinguished", "no_ignition", "other"]
TrustLevel = Literal["high", "medium", "low"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- request ----

class Conditions(Strict):
    material: str | None = None
    o2_pct: float | None = None
    pressure_kpa: float | None = None
    gravity: Gravity | None = None
    flow_cm_s: float | None = None


class AskRequest(Strict):
    question: str
    conditions: Conditions | None = None


# ---- response ----

class Claim(Strict):
    text: str
    cites: list[str]


class Evidence(Strict):
    test_id: str
    investigation: str
    match_score: float
    o2_pct: float | None
    pressure_kpa: float | None
    gravity_g: float | None
    outcome: Outcome | None
    source_url: str


class Bounds(Strict):
    microgravity: list[str]
    earth: list[str]


class Trust(Strict):
    level: TrustLevel
    reason: str


class AskResponse(Strict):
    status: Status
    summary: str
    claims: list[Claim]
    evidence: list[Evidence]
    bounds: Bounds
    trust: Trust
    gaps: list[str]
