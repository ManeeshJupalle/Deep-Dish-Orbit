# Live demo script (4 minutes, local judging)

Open https://thankful-forest-0ab84ba0f.3.azurestaticapps.net before the judge arrives and ask one question
so everything is warm. Answers take 3-8 s; talk while they load.

| Time | Do | Say |
| --- | --- | --- |
| 0:00-0:30 | Home page, point at the 3D hero | "We're Deep Dish Orbit. A Moon base will likely run at 30% oxygen or more. In orbit a flame is a round blue ball (left); on Earth it's a teardrop (middle). On the Moon, nobody knows (right): NASA has never tested fire at lunar gravity." |
| 0:30-1:15 | Ask **"Does PMMA burn at 21% oxygen in microgravity?"**, click a blue citation chip | "Every sentence cites a real NASA test. Click a citation and the exact row lights up, with a link to NASA's page." |
| 1:15-2:00 | Ask **"Is cotton safe at 34% oxygen on the Moon?"** | "Here it refuses to guess. It says *no direct data*, shows the closest 0 g and 1 g tests on either side as bounds, and lists exactly what NASA never tested." |
| 2:00-2:30 | Ask **"How does wood burn on the space station?"** | "NASA never tested wood in these experiments, so again: no direct data, not an invented answer." |
| 2:30-3:00 | Explore page, coverage map | "Every NASA test we use, by oxygen and pressure. The dashed box is Moon-base conditions: almost nothing there." |
| 3:00-3:40 | About page | "How it stays honest: an AI model (GPT-5.6-luna on Azure) drafts the answer, then our verifier deletes any claim whose test ID, number or outcome isn't in NASA's data. We tested six models on 20 questions; all scored 20/20 because the verifier caught every bad claim. We picked Luna by measurement: as faithful as the best, twice as fast, cheapest." |
| 3:40-4:00 | Back to home | "FlameCheck: answers only from NASA data, every claim cited, and an honest 'we don't know' where NASA never looked." |

## Spare questions (if a judge asks for more)

- **"Which FLEX tests used helium to put out the flame?"**: answered, High trust, lists the FLEX tests.
- **"How much thrust does a solid rocket booster make?"**: out of scope instantly; shows it knows its limits.
- **"Did FLEX test methanol at 3 atm?"**: answered from FLEX-10/11 (309 kPa). Sometimes the verifier removes the model's "304 kPa" conversion and shows NASA's rows directly: a live example of the verifier at work.

## Likely judge questions

- *Why not just ask ChatGPT?* It would answer the Moon question confidently. NASA has no data there; we say so and show the bounds.
- *What if the AI is wrong?* It can't reach the screen: every claim is checked against the cited NASA row, and dropped if it doesn't match.
- *Why Azure / this model?* API, website and model all run on Azure; the model signs in with the app's Azure identity, so no keys are stored. Model chosen by a 20-question test, not by size.
- *Data?* 423 tests from four NASA PSI investigations (BASS-II, SAFFIRE-II/III, FLEX), plus 9 NASA technical report abstracts. Missing values stay empty; we never fill them in.
