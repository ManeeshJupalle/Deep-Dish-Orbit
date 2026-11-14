"""FlameCheck API. Phase 1: /health and a stub /ask that returns a fixture."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    # Stub until Phase 4: always returns the sample "answered" fixture.
    data = json.loads((FIXTURES / "answered.json").read_text(encoding="utf-8"))
    return AskResponse.model_validate(data)
