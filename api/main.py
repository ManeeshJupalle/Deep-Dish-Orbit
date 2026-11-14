"""FlameCheck API. Phase 1: /health and a stub /ask that returns a fixture."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.data import store
from api.retrieve import material_rows
from api.schemas import AskRequest, AskResponse

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

FIXTURES = ROOT / "web" / "fixtures"

app = FastAPI(title="FlameCheck API")

origins = os.getenv("ALLOWED_ORIGINS") or "http://localhost:3000"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/investigations")
def investigations() -> list[dict]:
    return store().investigations


@app.get("/tests")
def tests(investigation: str | None = None, material: str | None = None,
          o2_min: float | None = None, o2_max: float | None = None) -> list[dict]:
    rows = store().tests
    if investigation:
        rows = [r for r in rows if r["investigation"].lower() == investigation.lower()]
    if material:
        rows = material_rows(rows, material)
    if o2_min is not None:
        rows = [r for r in rows if r["o2_pct"] is not None and r["o2_pct"] >= o2_min]
    if o2_max is not None:
        rows = [r for r in rows if r["o2_pct"] is not None and r["o2_pct"] <= o2_max]
    return rows


@app.get("/coverage")
def coverage() -> list[dict]:
    keys = ("test_id", "o2_pct", "pressure_kpa", "gravity_g", "investigation")
    return [{k: r[k] for k in keys} for r in store().tests]


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    # Stub until Phase 4: always returns the sample "answered" fixture.
    data = json.loads((FIXTURES / "answered.json").read_text(encoding="utf-8"))
    return AskResponse.model_validate(data)
