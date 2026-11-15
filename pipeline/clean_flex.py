"""FLEX (PSI-69): ISS droplet burns, some with CO2 or He added. Mapping in data/clean/MAPPING.md."""
from pipeline.schema import MMHG_TO_KPA, RAW, note, num, psi_url, read_raw

PSI = "PSI-69"
SOURCE_FILE = "PSI-69_experimental_table.csv"

O2 = "O initial ambient composition; mole fraction"
N2 = "N initial ambient composition; mole fraction"
CO2 = "CO initial ambient composition; mole fraction"  # subscript lost on the PSI page
HE = "He initial ambient composition; mole fraction"

OUTCOME = {"Extinction": "extinguished", "Completion": "burned", "Disruption": "other"}

# Pressures are kept exactly as NASA's table gives them, including nine tests at about 2-3 atm
# that the PSI-69 Approach text (0.5-1.5 atm) does not mention. Only a recorded 0 mmHg
# (FLEX-114) is left empty: it is not a real ambient pressure.


def clean() -> list[dict]:
    rows = []
    for r in read_raw(RAW / "FLEX" / SOURCE_FILE):
        p = num(r["Ambient pressure; mmHg"])
        pressure = round(p * MMHG_TO_KPA, 1) if p else None
        o2 = num(r[O2])
        gases = {"N2": num(r[N2]), "CO2": num(r[CO2]), "He": num(r[HE])}
        d0 = r["Droplet initial diameter; mm"]
        rows.append({
            "test_id": f"FLEX-{r['FLEX Test #']}",
            "investigation": "FLEX",
            "psi_id": PSI,
            "platform": "ISS CIR (MDCA)",
            "fuel_phase": "liquid",
            "material": r["Fuel"] or None,
            "sample_geometry": f"droplet, initial diameter {d0} mm" if d0 else "droplet",
            "o2_pct": round(o2 * 100, 2) if o2 is not None else None,
            "pressure_kpa": pressure,
            "diluent": "+".join(g for g, v in gases.items() if v) or None,
            "flow_cm_s": None,
            "gravity_g": 0,
            "outcome": OUTCOME.get(r["Test end"]),
            "spread_rate_mm_s": None,
            "extinction_note": note(
                f"Test end: {r['Test end']}" if r["Test end"] else None,
                f"FLEX ID {r['FLEX Identifier']}",
                f"ambient pressure {r['Ambient pressure; mmHg']} mmHg" if r["Ambient pressure; mmHg"] else None,
                f"visible flame extinction diameter {r['Visible flame extinction diameter; mm']} mm"
                if r["Visible flame extinction diameter; mm"] else None,
                f"burning rate {r['Burning rate; mm']} (PSI unit label 'mm')" if r["Burning rate; mm"] else None,
                f"burn time {r['Burn time; s']} s" if r["Burn time; s"] else None,
            ),
            "source_url": psi_url(PSI),
            "source_file": SOURCE_FILE,
        })
    return rows
