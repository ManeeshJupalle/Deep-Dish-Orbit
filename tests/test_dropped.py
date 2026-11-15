from fastapi.testclient import TestClient

from api import answer, main


def test_removed_claims_come_back_with_a_reason(monkeypatch):
    """The "Watch the verifier" view needs each removed draft claim and why it was removed."""
    def fake_draft(question, r):
        good = answer.template(r)["claims"][0]
        bad = {"text": "At 0 g, PMMA burned at 304 kPa.", "cites": good["cites"]}
        return {"summary": "x", "claims": [good, bad]}

    monkeypatch.setattr(answer, "draft", fake_draft)
    d = TestClient(main.app).post("/ask", json={"question": "Does PMMA burn at 21% oxygen in microgravity?"}).json()
    assert [x["text"] for x in d["dropped"]] == ["At 0 g, PMMA burned at 304 kPa."]
    assert "304 is not in" in d["dropped"][0]["reason"]
    assert all(c["text"] != "At 0 g, PMMA burned at 304 kPa." for c in d["claims"])


def test_nothing_removed_means_an_empty_list():
    d = TestClient(main.app).post("/ask", json={"question": "How much thrust does a rocket booster make?"}).json()
    assert d["dropped"] == []
