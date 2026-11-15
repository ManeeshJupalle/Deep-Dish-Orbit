# PSI source notes (pre-download recon, 2026-11-14)

Read from psi.nasa.gov pages (logged out). Facts about file contents are from the page previews; confirm against the downloaded files before relying on them.

Page URL pattern: `https://psi.nasa.gov/physci/repo/data/investigations/PSI-<n>`. Pages are rendered by JavaScript, so plain curl gets an empty shell. No login prompt was seen. Zips over 1 GB are emailed, so fetch small files only.

## Investigations (IDs confirmed)

| PSI | Investigation | Total size | Notes |
| --- | --- | --- | --- |
| PSI-25 | BASS-II | 256 GB | Table: 130 rows. Small files: `BASS-II_Test.Matrices.xlsx`, `Fan calibration data.xlsx`, `ReadMe.docx`, `SRD.pdf`; `BASS-II Summary Report.pdf` 46.7 MB |
| PSI-99 | SAFFIRE-II | 16 GB | Table: 9 samples + notes rows. Has µg **and 1 g** burn length / spread rate columns |
| PSI-100 | SAFFIRE-III | 33 GB | Table: 2 rows (S1 concurrent, S2 opposed), SIBAL, 30 cm/s. No O2 or outcome columns |
| PSI-69 | FLEX | 860 GB | Table: 275 rows (methanol 157, heptane 117). Pressure in mmHg; O2/N2/CO2/He as mole fractions |
| PSI-10 | ACME Flame Design | 1.98 TB | Table: 121 rows (priority 2) |
| PSI-159 | ACME CFI-G | 1.90 TB | Table: 1016 rows, O2 mole fraction 0.12–0.85, pressure 0.50–3.31 bar; Fuel blank on 862 rows (priority 2) |
| PSI-101 | SAME-R | 5.9 GB | 110 rows of smoke/aerosol tests, not flames (priority 2) |
| PSI-98 | SAFFIRE-I | — | 5 rows, SIBAL (priority 3) |

## What each table gives (and lacks)

- **BASS-II:** test number, sample, fuel material, flow restrictor, fan display, air display, initial/final calibrated O2 %, CO2, CO. No flow speed, pressure, outcome or spread rate in the table. Flow may come from `Test.Matrices.xlsx` + `Fan calibration data.xlsx`.
- **SAFFIRE-II:** material, thickness, size, air flow (20 cm/s), %O2 (~21.5–22.1, derived from CO2), ignition, burn time, flow direction, µg burn length and spread rate, 1 g burn length and spread rate. Messy: blank material on 2 samples, "µ-g" shows as "?-g", thickness like "037 mm".
- **SAFFIRE-III:** sample, flow direction, SIBAL, 30 cm/s, thickness ".33 cm" (suspect units).
- **FLEX:** fuel, pressure (mmHg, 526–2320; 9 values > 1500 are above the 0.5–1.5 atm in the Approach text and are kept as the table gives them), O2/N2/CO2/He mole fractions, droplet and extinction diameter, burning rate, burn time, outcome (Extinction 186, Disruption 61, Completion 27).

## Cotton and 1 g

- Cotton: SIBAL = "Cotton-Fiberglass" fabric. Appears in BASS-II (~27 rows), SAFFIRE-I, -II, -III.
- 1 g data: only the SAFFIRE-II table has 1 g columns. Other tables are microgravity only.

## Secondary sources (text lane, NTRS)

- BASS-II Summary Report TM (2021): https://ntrs.nasa.gov/citations/20210011385
- FLEX detailed results, NASA/TP-2015-216046: https://ntrs.nasa.gov/citations/20150023456
- Saffire presentation (2017): https://ntrs.nasa.gov/citations/20180005168
- Challenge page: https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/

Other teams' GitHub repos hold copies of PSI CSVs, but at least one mixes in modeled (non-NASA) rows. Do not use them as a data source.
