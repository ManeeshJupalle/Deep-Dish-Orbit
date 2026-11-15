import pytest
from fastapi.testclient import TestClient

from api.data import store
from api.main import app
from api.retrieve import families, parse_conditions, retrieve, score
from api.schemas import Conditions

client = TestClient(app)


def test_pmma_at_21_percent():
    r = retrieve("PMMA at 21% oxygen")
    assert r.conditions.material == "PMMA" and r.conditions.o2_pct == 21
    assert len(r.tests) == 8
    for row, _ in r.tests:
        assert "PMMA" in families(row["material"])
        assert abs(row["o2_pct"] - 21) <= 3


def test_cotton_in_a_spacecraft():
    r = retrieve("cotton fabric in a spacecraft")
    ids = [row["test_id"] for row, _ in r.tests]
    assert "SAFFIRE2-2-5" in ids  # Cotton-Fiberglass (SIBAL) on Cygnus
    assert all("cotton" in families(row["material"]) and row["gravity_g"] == 0 for row, _ in r.tests)


def test_moon_question_returns_bounds_and_gaps():
    r = retrieve("Is cotton safe at 34% oxygen on the Moon at 10.2 psi?")
    c = r.conditions
    assert (c.material, c.o2_pct, c.pressure_kpa, c.gravity) == ("cotton", 34, 70.3, "moon")
    assert r.bounds["earth"] == ["SAFFIRE2-2-5-1G"]
    assert r.bounds["microgravity"] and all(store().by_id[i]["gravity_g"] == 0 for i in r.bounds["microgravity"])
    assert "No PSI data at lunar gravity" in r.gaps
    assert "No cotton test at or above 34% O2 (highest tested: 22.1%)" in r.gaps


def test_fire_on_the_moon_at_34_percent():
    r = retrieve("fire on the Moon at 34% oxygen")
    assert r.tests[0][0]["o2_pct"] == 34
    assert r.bounds["microgravity"]


def test_flex_helium_tests():
    r = retrieve("Which FLEX tests used helium to put out the flame?")
    for row, _ in r.tests:
        assert row["investigation"] == "FLEX" and "He" in row["diluent"]
    assert all("He" in store().by_id[i]["diluent"] for i in r.bounds["microgravity"])


def test_rockets_are_out_of_scope():
    assert retrieve("How do rockets burn propellant?").out_of_scope


def test_missing_values_get_no_credit():
    c = Conditions(o2_pct=21)
    with_o2 = {"o2_pct": 21.0, "pressure_kpa": None, "flow_cm_s": None, "gravity_g": 0.0, "diluent": None}
    without = {**with_o2, "o2_pct": None}
    assert score(with_o2, c, None, set(), False) == 1.0
    assert score(without, c, None, set(), False) == 0.0


def test_parse_ignores_diluent_percentages():
    c = parse_conditions("heptane with 20% helium at 21% oxygen and 760 mmHg")
    assert c.o2_pct == 21 and c.material == "heptane" and c.pressure_kpa == 101.3


def test_get_endpoints():
    assert len(client.get("/investigations").json()) == 4
    cotton = client.get("/tests", params={"material": "cotton"}).json()
    assert cotton and all("cotton" in families(r["material"]) for r in cotton)
    hi = client.get("/tests", params={"o2_min": 30}).json()
    assert hi and all(r["o2_pct"] >= 30 for r in hi)
    points = client.get("/coverage").json()
    assert len(points) == len(store().tests)
    assert set(points[0]) == {"test_id", "o2_pct", "pressure_kpa", "gravity_g", "investigation"}


def test_named_test_id_comes_first():
    r = retrieve("What oxygen level was BASS-II test BASS2-T28a run at?")
    assert r.tests[0][0]["test_id"] == "BASS2-T28a"


def test_untested_material_is_a_gap_not_another_material():
    r = retrieve("Does Kapton burn at 21% oxygen in microgravity?")
    assert r.conditions.material == "kapton"
    assert "No PSI test for kapton" in r.gaps


# ---- regressions from the code review ----

@pytest.mark.parametrize("question,gravity", [
    ("Does PMMA burn at 21% oxygen in partial gravity?", "partial"),
    ("Does PMMA burn at 21% oxygen at 0.38 g?", "mars"),
    ("Does PMMA burn at 21% oxygen at 1/6 g?", "moon"),
    ("Does PMMA burn at 21% oxygen in a moonbase?", "moon"),
    ("Does PMMA burn at 21% oxygen at 0.1 g?", "partial"),
    ("Does PMMA burn at 21% oxygen at 0.5 g?", "partial"),
    ("Does PMMA burn at 21% oxygen at 1 g?", "earth"),
    ("Does PMMA burn at 21% oxygen at 0 g?", "micro"),
    ("Does PMMA burn at 21% oxygen?", None),
])
def test_gravity_words(question, gravity):
    assert parse_conditions(question).gravity == gravity


@pytest.mark.parametrize("question", [
    "Does wood burn at 21% oxygen in microgravity?",           # material NASA PSI did not test
    "Does PMMA burn at 21% oxygen on Earth?",                  # no 1 g PMMA row reports oxygen
    "Was PMMA tested with helium in microgravity?",            # PMMA rows are N2 only
    "Does PMMA burn at 21% oxygen in partial gravity?",
    "Does PMMA burn at 21% oxygen at 0.38 g?",
    "What did FLEX-2 find about heptane droplets?",            # FLEX-2 is a different investigation
    "Did FLEX test cotton fabric?",
])
def test_untested_conditions_are_no_direct_data(question):
    d = client.post("/ask", json={"question": question}).json()
    assert d["status"] == "no_direct_data", (d["status"], d["gaps"])
    assert d["gaps"] and d["trust"]["level"] != "high"


@pytest.mark.parametrize("question", ["How does fire behave on the Moon?", "fire on the Moon at 34% oxygen"])
def test_moon_questions_always_get_both_bounds(question):
    r = retrieve(question)
    assert r.bounds["microgravity"] and r.bounds["earth"]
    assert all(store().by_id[i]["gravity_g"] == 1 for i in r.bounds["earth"])


def test_gap_names_the_investigation_asked_about():
    r = retrieve("Did FLEX test cotton fabric?")
    assert r.tests == []  # FLEX methanol rows are not evidence for a cotton question
    assert r.gaps == ["No FLEX test for cotton (tested in BASS-II, SAFFIRE-II, SAFFIRE-III)"]


def test_flex_2_the_investigation_is_not_flex_test_2():
    r = retrieve("What did FLEX-2 find about heptane droplets?")
    assert all(t["test_id"] != "FLEX-2" for t, _ in r.tests)
    assert any("FLEX-2" in g for g in r.gaps)
    assert retrieve("What happened in test FLEX-2?").tests[0][0]["test_id"] == "FLEX-2"


def test_trust_is_not_high_when_no_material_is_recognised():
    d = client.post("/ask", json={"question": "Does spandex burn at 21% oxygen in microgravity?"}).json()
    assert d["trust"]["level"] != "high"


def test_flex_tests_at_3_atm_are_found():
    # NASA's FLEX table has methanol droplets at about 2319 mmHg (309 kPa); 3 atm is 304 kPa.
    r = retrieve("Did FLEX test methanol at 3 atm?")
    assert r.conditions.pressure_kpa == 304.0 and r.gaps == []
    top = r.tests[0][0]
    assert top["material"] == "Methanol" and abs(top["pressure_kpa"] - 304.0) <= 10
    d = client.post("/ask", json={"question": "Did FLEX test methanol at 3 atm?"}).json()
    assert d["status"] == "answered"
