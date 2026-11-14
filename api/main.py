"""FlameCheck API (ARCHITECTURE.md section 6)."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import answer
from api.data import store
from api.retrieve import Retrieval, material_rows, retrieve
from api.schemas import AskRequest, AskResponse
from api.trust import trust
from api.verify import decide_status, summary_ok, verify

app = FastAPI(title="FlameCheck API")

origins = os.getenv("ALLOWED_ORIGINS") or "http://localhost:3000"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

OUT_OF_SCOPE_SUMMARY = ("FlameCheck answers from NASA PSI fire-safety experiments on materials and fuels in "
                        "spacecraft. Rockets and propellants are outside that data.")


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


@app.get("/chunks")
def chunks() -> list[dict]:
    """Text sources that claims may cite by chunk_id (title and link for citation chips)."""
    keys = ("chunk_id", "source_id", "title", "source_url")
    return [{k: c[k] for k in keys} for c in store().chunks]


def _summary(status: str, r: Retrieval, llm_summary: str | None, claims: list[dict]) -> str:
    if status == "out_of_scope":
        return OUT_OF_SCOPE_SUMMARY
    if status == "no_direct_data":
        if r.conditions.gravity in ("moon", "mars"):
            where = "lunar" if r.conditions.gravity == "moon" else "Martian"
            return (f"NASA PSI has no fire tests at {where} gravity. The 0 g and 1 g tests below only bound "
                    "the answer; they do not predict it.")
        if claims:
            return ("NASA PSI has no test at the conditions you asked about. The closest tests below do not "
                    "answer the question directly.")
        return "NASA PSI has no test that matches this question."
    if llm_summary:
        return llm_summary
    n = len({i for c in claims for i in c["cites"]})
    return f"Showing NASA PSI evidence only: {n} cited source{'s' if n != 1 else ''} below."


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    r = retrieve(req.question, req.conditions)
    evidence = answer.evidence_rows(r)
    claims: list[dict] = []
    llm_summary = None
    if not r.out_of_scope:
        draft = answer.draft(req.question, r)
        if draft:
            claims = verify(req.question, r, evidence, draft["claims"]).claims
            if claims and draft["summary"].strip() and summary_ok(draft["summary"], r, evidence, req.question):
                llm_summary = draft["summary"].strip()
        if not claims:  # no LLM, or nothing it wrote survived: restate the evidence instead
            claims = verify(req.question, r, evidence, answer.template(r)["claims"]).claims
    status = decide_status(r, claims)
    rows = {t["test_id"]: t for t in evidence}
    return AskResponse.model_validate({
        "status": status,
        "summary": _summary(status, r, llm_summary, claims),
        "claims": claims,
        "evidence": [] if status == "out_of_scope" else [
            {"test_id": t["test_id"], "investigation": t["investigation"],
             "match_score": r.scores.get(t["test_id"], 0.0), "o2_pct": t["o2_pct"],
             "pressure_kpa": t["pressure_kpa"], "gravity_g": t["gravity_g"], "outcome": t["outcome"],
             "source_url": t["source_url"]} for t in evidence],
        "bounds": r.bounds if status != "out_of_scope" else {"microgravity": [], "earth": []},
        "trust": trust(r, claims, status, rows),
        "gaps": r.gaps if status != "out_of_scope" else ["PSI does not cover rockets or propellants"],
    })
