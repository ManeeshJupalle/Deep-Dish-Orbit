"""SAFFIRE-II (PSI-99) and SAFFIRE-III (PSI-100): large burns in a Cygnus cargo ship.

SAFFIRE-II also reports 1 g burn results for the same samples; those become separate
rows with gravity_g = 1. Mapping in data/clean/MAPPING.md.
"""
import re

from pipeline.schema import RAW, note, num, psi_url, read_raw

S2_FILE = "PSI-99_experimental_table.csv"
S3_FILE = "PSI-100_experimental_table.csv"

# PSI shows "µ-g" as "?-g" in these headers.
UG_LENGTH, UG_SPREAD = "?-g Burn Length", "?-g Spread Length"
G1_LENGTH, G1_SPREAD = "1-g Burn Length", "1-g Spread Rate"

SAMPLE = re.compile(r"^\d+-\d+$")
NOTE_REF = re.compile(r"note (\d)", re.IGNORECASE)


def burn_outcome(length: str) -> str | None:
    """'Complete' or a length -> burned; '~ 0' -> other (no real burn); blank -> unknown."""
    if not length:
        return None
    if length == "Complete":
        return "burned"
    n = num(length)
    if n is None:
        return None
    return "burned" if n > 0 else "other"


def spread(cell: str) -> float | None:
    return num(cell) if cell.endswith("mm/s") else None


def clean_saffire2() -> list[dict]:
    raw = read_raw(RAW / "SAFFIRE-II" / S2_FILE)
    footnotes = {}
    for r in raw:
        m = re.match(r"Note (\d) (.*)", r["Sample Number"])
        if m:
            footnotes[m.group(1)] = m.group(2)

    rows = []
    for r in raw:
        if not SAMPLE.match(r["Sample Number"]):
            continue  # flow-visualisation and footnote rows
        refs = sorted(set(NOTE_REF.findall(" ".join(r.values()))) - {"1"})
        notes_text = [f"Note {n}: {footnotes[n]}" for n in refs if n in footnotes]
        base = {
            "investigation": "SAFFIRE-II",
            "psi_id": "PSI-99",
            "fuel_phase": "solid",
            "material": r["Material"] or None,
            "sample_geometry": note(
                f"thickness {r['Samle Thickness']}" if r["Samle Thickness"] else None,
                f"{r['Sample Length']} x {r['Sample Width (cm)']}",
            ),
            "pressure_kpa": None,
            "diluent": None,
            "source_url": psi_url("PSI-99"),
            "source_file": S2_FILE,
        }
        rows.append({
            **base,
            "test_id": f"SAFFIRE2-{r['Sample Number']}",
            "platform": "Cygnus",
            "o2_pct": num(r["Percent O2 (Note 1)"]),
            "flow_cm_s": num(r["Air Flow (cm/s)"]),
            "gravity_g": 0,
            "outcome": burn_outcome(r[UG_LENGTH]),
            "spread_rate_mm_s": spread(r[UG_SPREAD]),
            "extinction_note": note(
                f"µg burn length: {r[UG_LENGTH]}", f"µg spread: {r[UG_SPREAD]}",
                f"burn time: {r['Burn Time (s)']}", f"flow direction: {r['Flow Direction']}",
                f"O2 as reported: {r['Percent O2 (Note 1)']}", *notes_text,
            ),
        })
        if r[G1_LENGTH] or r[G1_SPREAD]:
            rows.append({
                **base,
                "test_id": f"SAFFIRE2-{r['Sample Number']}-1G",
                "platform": "1 g comparison test",
                "o2_pct": None,
                "flow_cm_s": None,
                "gravity_g": 1,
                "outcome": burn_outcome(r[G1_LENGTH]),
                "spread_rate_mm_s": spread(r[G1_SPREAD]),
                "extinction_note": note(f"1 g burn length: {r[G1_LENGTH]}", f"1 g spread rate: {r[G1_SPREAD]}"),
            })
    return rows


def clean_saffire3() -> list[dict]:
    rows = []
    for r in read_raw(RAW / "SAFFIRE-III" / S3_FILE):
        rows.append({
            "test_id": f"SAFFIRE3-{r['Sample Number']}",
            "investigation": "SAFFIRE-III",
            "psi_id": "PSI-100",
            "platform": "Cygnus",
            "fuel_phase": "solid",
            "material": r["Material"] or None,
            "sample_geometry": note(f"thickness {r['Sample Thickness']}", f"{r['Sample Length']} x {r['Sample Width']}"),
            "o2_pct": None,
            "pressure_kpa": None,
            "diluent": None,
            "flow_cm_s": num(r["Air Flow"]),
            "gravity_g": 0,
            "outcome": None,
            "spread_rate_mm_s": None,
            "extinction_note": f"flow direction: {r['Direction']}",
            "source_url": psi_url("PSI-100"),
            "source_file": S3_FILE,
        })
    return rows


def clean() -> list[dict]:
    return clean_saffire2() + clean_saffire3()
