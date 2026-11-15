import csv

from pipeline.check_data import check
from pipeline.schema import CLEAN


def rows():
    with open(CLEAN / "tests.csv", encoding="utf-8", newline="") as f:
        return {r["test_id"]: r for r in csv.DictReader(f)}


def test_clean_data_passes_checks():
    assert check() == []


def test_known_rows_match_source():
    t = rows()
    # BASS-II B1: 100 micron PMMA film, initial O2 22.2 %
    assert t["BASS2-B1"]["o2_pct"] == "22.2"
    assert "PMMA" in t["BASS2-B1"]["material"]
    # Rod quoting is undone
    assert t["BASS2-O1"]["material"] == '1/4" clear rod'
    # FLEX-1: 757.7 mmHg -> 101.0 kPa, O2 0.21 -> 21 %, Disruption -> other
    assert t["FLEX-1"]["pressure_kpa"] == "101.0"
    assert float(t["FLEX-1"]["o2_pct"]) == 21.0
    assert t["FLEX-1"]["outcome"] == "other"
    # FLEX-10: NASA's table says 2319.7 mmHg (about 3 atm); kept as recorded -> 309.3 kPa
    assert t["FLEX-10"]["pressure_kpa"] == "309.3"
    # FLEX-114 is recorded as 0 mmHg, which is not a real ambient pressure -> empty, not guessed
    assert t["FLEX-114"]["pressure_kpa"] == ""
    # SAFFIRE-II cotton-fiberglass sample has both a 0 g and a 1 g row
    assert t["SAFFIRE2-2-5"]["gravity_g"] == "0"
    assert t["SAFFIRE2-2-5"]["spread_rate_mm_s"] == "2.1"
    assert t["SAFFIRE2-2-5-1G"]["gravity_g"] == "1"
    # Missing material stays empty
    assert t["SAFFIRE2-2-6"]["material"] == ""
