# Live demo script (4 minutes: 2 min slides, 2 min demo)

Before the judge arrives: open https://thankful-forest-0ab84ba0f.3.azurestaticapps.net and ask one question so
everything is warm. Answers take 3-8 s; talk while they load.

## Slides (about 2:00)

Title (0:10) → Problem (0:25) → Solution (0:25) → How it stays honest (0:30) → Results (0:30).
The speaker notes in the deck carry the words.

## Demo (about 1:50)

| Time | Do | Say |
| --- | --- | --- |
| 2:00-2:15 | Home page, point at the 3D flames | "In orbit a flame is a round blue ball, on Earth a teardrop. On the Moon nobody knows: NASA never tested fire at lunar gravity." |
All four questions are one-click buttons under "Try one of these" on the Ask page.

| Time | Do | Say |
| --- | --- | --- |
| 2:15-2:35 | Ask **"Does PMMA burn at 21% oxygen in microgravity?"**, click a blue citation chip | "Every sentence cites a real NASA test. Click one and the exact evidence row lights up, with a link to NASA's page." |
| 2:35-2:55 | Open **Watch the verifier work** under the answer | "This is what the AI drafted and our verifier removed, with the reason. If nothing was removed, it says every claim was checked." (Either result makes the point.) |
| 2:55-3:15 | Ask **"Is cotton safe at 34% oxygen on the Moon?"** | "It refuses to guess. *No direct data*, the closest 0 g and 1 g tests as bounds, and exactly what NASA never tested: no cotton test above 22% oxygen." |
| 3:15-3:30 | Ask **"Which FLEX tests used helium to put out the flame?"** | "It finds the exact FLEX tests that used helium as the diluent, with High trust because every cited test matches." |
| 3:30-3:45 | Ask **"Does cotton-fiberglass fabric burn in a spacecraft?"** | "Yes: it burned at 0 g in SAFFIRE-II at 2.1 mm/s, and it cites the NASA report on the large-scale fabric fire flown on a spacecraft." |
| (only if ahead of time) | Click **Plan**, then **Explore** and drag the gap cube | "Habitat designers can enter their cabin atmosphere here. And in the cube, every test sits on the 0 g floor; the Moon and Mars slices are empty." |
| 3:45-3:55 | **Why it matters** slide | Impact, creativity, validity, relevance: one line each (see the slide notes). |
| 3:55-4:00 | **Thank you / Questions?** slide | "Answers only from NASA data, every claim cited, and an honest 'we don't know' where NASA never looked. Thank you." |

If behind: skip the helium question first, then cotton-fiberglass. Never skip the Moon question.

For global submission upload `FlameCheck_Slides_global.pdf` (7 slides, the limit). The 8-slide deck with the Thank-you slide is for presenting.

## If a judge wants more

- **Plan page** (34% O₂, 70.3 kPa defaults): only methanol and heptane were tested near a Moon-base atmosphere, all in orbit; 55 materials never were.
- **"How much thrust does a solid rocket booster make?"**: out of scope instantly.

## Likely judge questions

- *Why not just ask ChatGPT?* It would answer the Moon question confidently. NASA has no data there; we say so.
- *What if the AI is wrong?* It can't reach the screen: each claim is checked against the NASA row it cites, and you can watch the removed ones.
- *Why Azure / this model?* Site, API and model all on Azure; the model signs in with the app's identity, no keys stored. GPT-5.6-luna chosen by testing six models: as faithful as the best, twice as fast, cheapest.
- *Data?* 423 tests from four NASA PSI investigations (BASS-II, SAFFIRE-II/III, FLEX) plus 9 NASA report abstracts. Missing values stay empty; nothing is filled in.
