"""Fetch NASA NTRS paper abstracts into data/text/NTRS-<id>.txt (text lane for retrieval).

Usage: uv run python -m pipeline.fetch_ntrs
"""
import json
import urllib.request

from pipeline.schema import TEXT

# NTRS id -> investigation it is about (None = general background)
PAPERS = {
    "20210011385": "BASS-II",      # BASS-II Summary Report
    "20160000593": "BASS-II",      # Combustion of Solids in Microgravity: Results from BASS-II
    "20150008961": "BASS-II",      # Microgravity Flammability of PMMA Rods in Concurrent Flow
    "20160012691": "BASS-II",      # Normal gravity vs microgravity blowoff limits
    "20170008805": "SAFFIRE-II",   # Results of Large-Scale Spacecraft Flammability Tests
    "20180005168": "SAFFIRE-II",   # Saffire presentation (2017)
    "20150023456": "FLEX",         # Detailed results from FLEX, March 2009 - December 2011
    "20010073996": None,           # Solid Inflammability Boundary at Low-Speed (SIBAL)
    "20040142368": None,           # Organizing Questions for Reduced-Gravity Flammability
}


def fetch(ntrs_id: str) -> dict:
    req = urllib.request.Request(f"https://ntrs.nasa.gov/api/citations/{ntrs_id}", headers={"User-Agent": "flamecheck"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main() -> None:
    TEXT.mkdir(parents=True, exist_ok=True)
    for ntrs_id, investigation in PAPERS.items():
        d = fetch(ntrs_id)
        abstract = " ".join((d.get("abstract") or "").split())
        if not abstract:
            print(f"skip {ntrs_id}: no abstract")
            continue
        title = " ".join(d["title"].split())
        header = [f"Source: https://ntrs.nasa.gov/citations/{ntrs_id}", f"Title: {title}"]
        if investigation:
            header.append(f"Related investigation: {investigation}")
        (TEXT / f"NTRS-{ntrs_id}.txt").write_text("\n".join(header) + "\n\n" + abstract + "\n", encoding="utf-8")
        print(f"NTRS-{ntrs_id}: {len(abstract.split())} words  {title[:70]}")


if __name__ == "__main__":
    main()
