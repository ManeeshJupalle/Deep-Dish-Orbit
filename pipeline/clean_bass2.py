"""BASS-II (PSI-25): ISS solid-fuel flame tests in a small wind tunnel. Mapping in data/clean/MAPPING.md."""
import re

from pipeline.schema import RAW, note, num, psi_url, read_raw

PSI = "PSI-25"
SOURCE_FILE = "PSI-25_experimental_table.csv"

# The table has no outcome column. The crew notes in "Fan display" / "Air display"
# say when a flame went out ("ext", "blowoff", "out") or never lit ("no ign").
NO_IGNITION = re.compile(r"no ign")
EXTINGUISHED = re.compile(r"ext|blowoff|\bout\b")


def material(raw: str) -> str | None:
    """Undo the spreadsheet quoting on rod sizes: '"1/4"" clear rod"' -> '1/4" clear rod'."""
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1].replace('""', '"')
    return raw.strip() or None


def outcome(notes: str) -> str | None:
    if NO_IGNITION.search(notes):
        return "no_ignition"
    if EXTINGUISHED.search(notes):
        return "extinguished"
    return None


def clean() -> list[dict]:
    rows = []
    for r in read_raw(RAW / "BASS-II" / SOURCE_FILE):
        fan, air = r["Fan display"], r["Air display"]
        rows.append({
            "test_id": f"BASS2-{r['Test #']}",
            "investigation": "BASS-II",
            "psi_id": PSI,
            "platform": "ISS MSG",
            "fuel_phase": "solid",
            "material": material(r["Fuel Sample Material"]),
            "sample_geometry": None,
            "o2_pct": num(r["Calibrated initial O2 % by vol"]),
            "pressure_kpa": None,
            "diluent": "N2",  # PSI-25 description: O2 lowered by nitrogen vitiation
            "flow_cm_s": None,
            "gravity_g": 0,
            "outcome": outcome(f"{fan} {air}".lower()),
            "spread_rate_mm_s": None,
            "extinction_note": note(
                f"PI {r['PI']}",
                f"fan display: {fan}" if fan else None,
                f"air display: {air}" if air else None,
            ),
            "source_url": psi_url(PSI),
            "source_file": SOURCE_FILE,
        })
    return rows
