import json

import pytest
from fastapi.testclient import TestClient

from api import answer, verify as verify_mod
from api.data import store
from api.main import app
from api.retrieve import Retrieval, retrieve
from api.schemas import AskResponse, Conditions
from api.verify import check_claim, decide_status, numbers, summary_ok, verify

client = TestClient(app)


@pytest.fixture(autouse=True)
def tmp_log(tmp_path, monkeypatch):
    monkeypatch.setattr(verify_mod, "LOG", tmp_path / "verify.jsonl")
    return tmp_path / "verify.jsonl"


def setup(question):
    r = retrieve(question)
    ev = answer.evidence_rows(r)
    return r, ev, {t["test_id"]: t for t in ev}, {c["chunk_id"]: c for c, _ in r.chunks}


def test_fake_test_id_is_dropped(tmp_log):
    r, ev, _, _ = setup("cotton fabric in a spacecraft")
    v = verify("q", r, ev, [{"text": "At 0 g, the sample burned at 22.1% O2.", "cites": ["BASS2-FAKE99"]}])
    assert v.claims == [] and "unknown citation" in v.dropped[0]["reason"]
    assert "BASS2-FAKE99" in tmp_log.read_text(encoding="utf-8")  # every drop is logged


def test_made_up_number_is_dropped():
    r, ev, _, _ = setup("cotton fabric in a spacecraft")
    real = {"text": "At 0 g, SAFFIRE2-2-5 burned at 22.1% O2 with a spread rate of 2.1 mm/s.", "cites": ["SAFFIRE2-2-5"]}
    fake = {"text": "At 0 g, SAFFIRE2-2-5 burned at 22.1% O2 with a spread rate of 7.4 mm/s.", "cites": ["SAFFIRE2-2-5"]}
    v = verify("q", r, ev, [real, fake])
    assert v.claims == [real]
    assert "7.4" in v.dropped[0]["reason"]


def test_claim_without_citation_is_dropped():
    r, ev, _, _ = setup("cotton fabric in a spacecraft")
    assert verify("q", r, ev, [{"text": "Cotton burns.", "cites": []}]).claims == []


def test_ids_and_formulas_are_not_numbers():
    assert numbers("SAFFIRE2-2-5-1G burned in O2 and CO2 at 21.5% and 0 g (PSI-99, NTRS-20210011385-chunk1)") == [21.5, 0.0]


def test_rounding_to_one_decimal_is_allowed():
    r, ev, rows, chunks = setup("Is cotton safe at 34% oxygen on the Moon at 10.2 psi?")
    # SAFFIRE2-2-5 O2 is 22.1
    assert check_claim({"text": "At 0 g, it burned at 22.10% O2.", "cites": ["SAFFIRE2-2-5"]}, rows, chunks, "micro") is None
    assert check_claim({"text": "At 0 g, it burned at 22% O2.", "cites": ["SAFFIRE2-2-5"]}, rows, chunks, "micro")


def test_moon_claims_must_be_bounds():
    r, ev, rows, chunks = setup("Is cotton safe at 34% oxygen on the Moon?")
    bare = {"text": "Cotton-fiberglass fabric burns on the Moon.", "cites": ["SAFFIRE2-2-5"]}
    bound = {"text": "At 0 g, the cotton-fiberglass sample burned.", "cites": ["SAFFIRE2-2-5"]}
    one_g = {"text": "At 1 g, the same fabric burned completely.", "cites": ["SAFFIRE2-2-5-1G"]}
    wrong = {"text": "At 0 g, the fabric burned.", "cites": ["SAFFIRE2-2-5-1G"]}  # cites 1 g data as 0 g
    assert check_claim(bare, rows, chunks, "moon")
    assert check_claim(bound, rows, chunks, "moon") is None
    assert check_claim(one_g, rows, chunks, "moon") is None
    assert check_claim(wrong, rows, chunks, "moon")


def test_chunk_citations_check_numbers_in_the_chunk():
    r, ev, rows, chunks = setup("BASS-II wind tunnel airflow speed")
    cid = next(c for c in chunks if c.startswith("BASS-II-chunk"))
    assert "40 cm/s" in chunks[cid]["text"]
    assert check_claim({"text": "The duct could impose airflow speeds up to 40 cm/s.", "cites": [cid]}, rows, chunks, None) is None
    assert check_claim({"text": "The duct could impose airflow speeds up to 90 cm/s.", "cites": [cid]}, rows, chunks, None)


def test_status_rules():
    assert decide_status(retrieve("How do rockets burn propellant?"), []) == "out_of_scope"
    assert decide_status(retrieve("Is cotton safe on the Moon?"), [{"text": "x", "cites": ["a"]}]) == "no_direct_data"
    assert decide_status(retrieve("PMMA at 21% oxygen"), []) == "no_direct_data"
    assert decide_status(retrieve("PMMA at 21% oxygen"), [{"text": "x", "cites": ["a"]}]) == "answered"


def test_summary_with_invented_number_is_rejected():
    r, ev, _, _ = setup("cotton fabric in a spacecraft")
    claims = [{"text": "x", "cites": ["SAFFIRE2-2-5"]}]
    assert summary_ok("The cotton-fiberglass fabric burned at 22.1% oxygen.", r, ev, "q", claims)
    assert not summary_ok("The fabric burned at 31.7% oxygen.", r, ev, "q", claims)


def test_outcome_words_must_match_recorded_outcomes():
    r, ev, rows, chunks = setup("PMMA at 21% oxygen")
    assert rows["BASS2-B6"]["outcome"] is None
    # BASS-II table has no outcome for B6: "burned" is not backed by the data
    assert check_claim({"text": "At 0 g, the PMMA film burned at 21% O2.", "cites": ["BASS2-B6"]}, rows, chunks, None)
    assert check_claim({"text": "At 0 g, the PMMA film was tested at 21% O2.", "cites": ["BASS2-B6"]}, rows, chunks, None) is None


def test_outcome_rule_on_flex_rows():
    r, ev, rows, chunks = setup("Which FLEX tests used helium to put out the flame?")
    ext = next(t for t in ev if t["outcome"] == "extinguished")
    other = {"test_id": "FLEX-1", "outcome": "other", "gravity_g": 0.0, "o2_pct": 21.0}
    rows = {**rows, ext["test_id"]: ext, "FLEX-1": other}
    assert check_claim({"text": "At 0 g, the droplet flame was extinguished.", "cites": [ext["test_id"]]}, rows, chunks, None) is None
    assert check_claim({"text": "At 0 g, the droplet burned.", "cites": [ext["test_id"]]}, rows, chunks, None)
    assert check_claim({"text": "At 0 g, the droplet burned.", "cites": ["FLEX-1"]}, rows, chunks, None)
    # measurements are not outcomes
    assert check_claim({"text": "At 0 g, the burning rate was recorded.", "cites": ["FLEX-1"]}, rows, chunks, None) is None


def test_ask_drops_injected_fake_claims(monkeypatch, tmp_log):
    def fake_draft(question, r):
        return {"summary": "Cotton-fiberglass burned at 99.9% oxygen.",  # invented number -> summary replaced
                "claims": [
                    {"text": "At 0 g, the cotton-fiberglass sample burned at 22.1% O2.", "cites": ["SAFFIRE2-2-5"]},
                    {"text": "At 0 g, cotton burned at 22.1% O2.", "cites": ["SAFFIRE9-X1"]},
                    {"text": "At 0 g, cotton spread at 5.5 mm/s.", "cites": ["SAFFIRE2-2-5"]},
                ]}
    monkeypatch.setattr(answer, "draft", fake_draft)
    d = client.post("/ask", json={"question": "Does cotton fabric burn in a spacecraft?"}).json()
    AskResponse.model_validate(d)
    assert [c["cites"] for c in d["claims"]] == [["SAFFIRE2-2-5"]]
    assert "99.9" not in d["summary"]
    logged = [json.loads(line) for line in tmp_log.read_text(encoding="utf-8").splitlines()]
    assert len(logged) == 2


@pytest.mark.parametrize("question,status", [
    ("Does PMMA burn at 21% oxygen in microgravity?", "answered"),
    ("Is cotton safe at 34% oxygen on the Moon?", "no_direct_data"),
    ("How do rockets burn solid propellant?", "out_of_scope"),
])
def test_ask_end_to_end_without_llm(monkeypatch, question, status):
    monkeypatch.setattr(answer, "draft", lambda q, r: None)  # template path, no network
    d = client.post("/ask", json={"question": question}).json()
    AskResponse.model_validate(d)
    assert d["status"] == status
    cited = {i for c in d["claims"] for i in c["cites"]}
    assert cited <= {e["test_id"] for e in d["evidence"]}
    if status == "no_direct_data":
        assert d["bounds"]["microgravity"] and d["bounds"]["earth"]


# ---- regressions from the code review ----

def test_numbers_must_come_from_data_columns_not_file_names_or_ids():
    rows = {i: store().by_id[i] for i in ("BASS2-B1", "SAFFIRE3-S1", "FLEX-1")}
    # 25 and 100 appear only in source_file (PSI-25_..., PSI-100_...); 20 only inside the id "20CAL08".
    assert check_claim({"text": "At 0 g, BASS2-B1 was run at 25% O2.", "cites": ["BASS2-B1"]}, rows, {}, None)
    assert check_claim({"text": "At 0 g, SAFFIRE3-S1 was run at 100 kPa.", "cites": ["SAFFIRE3-S1"]}, rows, {}, None)
    assert check_claim({"text": "At 0 g, FLEX-1 was run at 20% O2.", "cites": ["FLEX-1"]}, rows, {}, None)
    assert check_claim({"text": "At 0 g, BASS2-B1 was run at 22.2% O2.", "cites": ["BASS2-B1"]}, rows, {}, None) is None


def test_leading_dot_numbers_are_checked():
    rows = {"SAFFIRE3-S1": store().by_id["SAFFIRE3-S1"]}  # geometry says "thickness .33 cm"
    assert numbers("spread at .75 mm/s") == [0.75]
    assert check_claim({"text": "At 0 g, the sample spread at .75 mm/s.", "cites": ["SAFFIRE3-S1"]}, rows, {}, None)
    assert check_claim({"text": "At 0 g, the sample was 0.33 cm thick.", "cites": ["SAFFIRE3-S1"]}, rows, {}, None) is None


@pytest.mark.parametrize("text", [
    "At 0 g, the sample did not burn.",
    "At 0 g, the sample didn't ignite.",
    "At 0 g, the sample never burned.",
])
def test_negated_outcome_is_not_backed_by_a_burned_row(text):
    rows = {"SAFFIRE2-2-5": store().by_id["SAFFIRE2-2-5"]}
    assert rows["SAFFIRE2-2-5"]["outcome"] == "burned"
    assert check_claim({"text": text, "cites": ["SAFFIRE2-2-5"]}, rows, {}, None)


def test_moon_wording_needs_a_bound_in_any_question():
    rows = {"SAFFIRE2-2-5": store().by_id["SAFFIRE2-2-5"]}
    bare = {"text": "Cotton-fiberglass fabric burns on the Moon.", "cites": ["SAFFIRE2-2-5"]}
    bound = {"text": "At 0 g, which only bounds the Moon, the cotton-fiberglass fabric burned.", "cites": ["SAFFIRE2-2-5"]}
    assert check_claim(bare, rows, {}, "micro")  # the question itself was not about the Moon
    assert check_claim(bound, rows, {}, "micro") is None


def test_every_row_restated_by_the_template_passes():
    """Guards against over-strictness: a plain restatement of any NASA row must survive."""
    for t in store().tests:
        r = Retrieval(conditions=Conditions(), tests=[(t, 1.0)], chunks=[], bounds={"microgravity": [], "earth": []},
                      gaps=[], out_of_scope=False, scores={})
        (claim,) = answer.template(r)["claims"]
        assert check_claim(claim, {t["test_id"]: t}, {}, None) is None, claim
