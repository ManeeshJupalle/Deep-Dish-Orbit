# Raw → schema mapping

How each raw PSI table becomes rows in `tests.csv` (schema: ARCHITECTURE.md 5.1). Rule: if the source has no value, the cell stays empty. Nothing is guessed or interpolated.

## How the raw files were captured

PSI pages are rendered in the browser. Each investigation's **Experimental Table** was read from the rendered page (all pages of the table) and saved as `data/raw/<investigation>/PSI-<n>_experimental_table.csv`. Each saved file was checked byte for byte against a SHA-256 of the in-browser copy. The description text of each PSI page is in `data/text/PSI-<n>.txt`, captured and checked the same way.

On the PSI pages, subscripts and the µ sign are lost from headers ("O" = O2, "CO" = CO2, "?-g" = µ-g). Cells shown as `�` are corrupted in the source and are read as empty.

| Investigation | Raw file | Raw rows | `tests.csv` rows |
| --- | --- | --- | --- |
| BASS-II (PSI-25) | `data/raw/BASS-II/PSI-25_experimental_table.csv` | 129 tests | 129 |
| SAFFIRE-II (PSI-99) | `data/raw/SAFFIRE-II/PSI-99_experimental_table.csv` | 9 samples (+ flow-vis and footnote rows, skipped) | 18 (9 at 0 g, 9 at 1 g) |
| SAFFIRE-III (PSI-100) | `data/raw/SAFFIRE-III/PSI-100_experimental_table.csv` | 2 samples | 2 |
| FLEX (PSI-69) | `data/raw/FLEX/PSI-69_experimental_table.csv` | 274 tests | 274 |

## BASS-II (PSI-25) → `pipeline/clean_bass2.py`

| Schema | From | Notes |
| --- | --- | --- |
| `test_id` | `Test #` | `BASS2-<Test #>`, e.g. `BASS2-B1` |
| `platform` | — | `ISS MSG` (PSI-25 hardware: Microgravity Science Glovebox) |
| `fuel_phase` | — | `solid` (all samples are solids; the wax candle is solid fuel) |
| `material` | `Fuel Sample Material` | As NASA wrote it, with spreadsheet quoting undone (`"1/4"" clear rod"` → `1/4" clear rod`) |
| `sample_geometry` | — | Empty. Size and shape are part of the material text |
| `o2_pct` | `Calibrated initial O2 % by vol` | As given |
| `pressure_kpa` | — | Empty: not in the table |
| `diluent` | — | `N2`: the PSI-25 description says O2 was lowered by nitrogen vitiation |
| `flow_cm_s` | — | Empty. `Air display` is not defined in the table, so it is not read as a flow speed |
| `gravity_g` | — | `0` |
| `outcome` | `Fan display` + `Air display` notes | `no ign` → `no_ignition`; `ext`, `blowoff` or `out` → `extinguished`; otherwise empty |
| `extinction_note` | `PI`, `Fan display`, `Air display` | Raw crew notes, kept for context |

Known source issues, left as is: the final O2 column has a few impossible values (e.g. B2 `1.6`, T28b `40.4`). Only the initial O2 is used. Two dates read 2018 (T9, T18).

Material families: NTRS-20150008961 states that the BASS-II rods were cast PMMA. Retrieval may therefore treat `clear rod` / `black rod` as PMMA, while the `material` cell keeps NASA's wording. SIBAL is listed as "Cotton-Fiberglass (SIBAL)" in the SAFFIRE-II table.

## SAFFIRE-II (PSI-99) → `pipeline/clean_saffire.py`

Each sample produces one 0 g row (flight, Cygnus) and, when the table has 1-g columns, one 1 g row from the same table.

| Schema | 0 g row | 1 g row |
| --- | --- | --- |
| `test_id` | `SAFFIRE2-<Sample Number>` | `SAFFIRE2-<Sample Number>-1G` |
| `platform` | `Cygnus` | `1 g comparison test` |
| `material` | `Material` (blank for 2-6 and 2-9 → empty) | same |
| `sample_geometry` | `thickness <Samle Thickness>; <Length> x <Width>` (as written, e.g. `037 mm`) | same |
| `o2_pct` | `Percent O2 (Note 1)`: leading number (`~ 22.1` → 22.1; `22.1 to 22.0` → 22.1, the start value) | Empty: not given for 1 g |
| `flow_cm_s` | `Air Flow (cm/s)` → 20 | Empty |
| `gravity_g` | 0 | 1 |
| `outcome` | `µ-g Burn Length`: a length → `burned`, `~ 0` → `other` | `1-g Burn Length`: `Complete` or a length → `burned`, `~ 0` → `other` |
| `spread_rate_mm_s` | `µ-g Spread Length` when it is in mm/s | `1-g Spread Rate` when in mm/s (`Acceleratory` → empty) |
| `extinction_note` | burn length, spread, burn time, flow direction, O2 as reported, referenced footnotes | 1 g burn length and spread rate |

Note 1 (O2 derived from CO2 production) applies to every O2 value.

## SAFFIRE-III (PSI-100) → `pipeline/clean_saffire.py`

| Schema | From | Notes |
| --- | --- | --- |
| `test_id` | `Sample Number` | `SAFFIRE3-S1`, `SAFFIRE3-S2` |
| `platform` | — | `Cygnus` (hardware: "Saffire III enclosure in Cygnus") |
| `material` | `Material` | `SIBAL Fabric` |
| `sample_geometry` | thickness, length, width | As written (`.33 cm`) |
| `flow_cm_s` | `Air Flow` | 30 |
| `o2_pct`, `pressure_kpa`, `outcome` | — | Empty: not in the table |
| `extinction_note` | `Direction` | Concurrent / opposed |

## FLEX (PSI-69) → `pipeline/clean_flex.py`

| Schema | From | Notes |
| --- | --- | --- |
| `test_id` | `FLEX Test #` | `FLEX-<n>`. `FLEX Identifier` is not unique (193F001 appears twice), so it goes in the note |
| `platform` | — | `ISS CIR (MDCA)` (PSI-69 hardware) |
| `fuel_phase` | — | `liquid` |
| `material` | `Fuel` | `Methanol` / `Heptane` |
| `sample_geometry` | `Droplet initial diameter; mm` | `droplet, initial diameter <d> mm` |
| `o2_pct` | `O initial ambient composition; mole fraction` | × 100 |
| `pressure_kpa` | `Ambient pressure; mmHg` | × 0.133322, 1 decimal. Every value is kept as NASA's table gives it, including 9 tests at 1545–2320 mmHg (FLEX-10 to FLEX-18, 206–309 kPa, about 2–3 atm) that the PSI-69 Approach text (0.5–1.5 atm) does not mention. Only one value is left empty: FLEX-114 is recorded as `0` mmHg, which is not a real ambient pressure. The raw value stays in the note |
| `diluent` | N2 / CO2 / He mole fractions | Gases with a non-zero fraction, joined with `+` (e.g. `N2+CO2`) |
| `flow_cm_s` | — | Empty: not in the table |
| `gravity_g` | — | `0` |
| `outcome` | `Test end` | `Extinction` → `extinguished`, `Completion` → `burned`, `Disruption` → `other` |
| `spread_rate_mm_s` | — | Empty. `Burning rate` is a droplet burning rate, not a flame spread rate |
| `extinction_note` | test end, FLEX ID, raw pressure, extinction diameter, burning rate, burn time | Burning rate unit is shown as PSI labels it (`mm`) |

## Text sources (`data/text/`)

- `PSI-25.txt`, `PSI-69.txt`, `PSI-99.txt`, `PSI-100.txt`: PSI description pages.
- `NTRS-*.txt`: NASA Technical Reports Server abstracts, fetched with `pipeline/fetch_ntrs.py` from `https://ntrs.nasa.gov/api/citations/<id>`.
