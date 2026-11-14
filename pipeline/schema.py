"""Shared schema and helpers for the data cleaners (ARCHITECTURE.md section 5)."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
TEXT = ROOT / "data" / "text"

COLUMNS = [
    "test_id", "investigation", "psi_id", "platform", "fuel_phase", "material",
    "sample_geometry", "o2_pct", "pressure_kpa", "diluent", "flow_cm_s", "gravity_g",
    "outcome", "spread_rate_mm_s", "extinction_note", "source_url", "source_file",
]
FUEL_PHASES = {"solid", "liquid", "gas"}
OUTCOMES = {"ignited", "burned", "extinguished", "no_ignition", "other"}

MMHG_TO_KPA = 0.133322
BAD_CELL = "�"  # PSI pages show this replacement character for corrupted cells

_NUM = re.compile(r"^[~\s]*(-?\d*\.?\d+)")


def psi_url(psi_id: str) -> str:
    return f"https://psi.nasa.gov/physci/repo/data/investigations/{psi_id}"


def read_raw(path: Path) -> list[dict]:
    """Read a raw PSI table. Strips cells, blanks corrupted cells, skips empty rows."""
    with open(path, encoding="utf-8", newline="") as f:
        rows = []
        for r in csv.DictReader(f):
            r = {k: ("" if v is None or BAD_CELL in v else v.strip()) for k, v in r.items()}
            if any(r.values()):
                rows.append(r)
        return rows


def num(s: str | None) -> float | None:
    """Leading number in a cell ('~ 22.1' -> 22.1, '20 cm/s' -> 20). None if there is none."""
    if not s:
        return None
    m = _NUM.match(s)
    return float(m.group(1)) if m else None


def note(*parts: str | None) -> str | None:
    """Join non-empty note parts with '; '."""
    text = "; ".join(p for p in parts if p)
    return text or None
