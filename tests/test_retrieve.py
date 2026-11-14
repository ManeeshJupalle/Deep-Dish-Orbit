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
