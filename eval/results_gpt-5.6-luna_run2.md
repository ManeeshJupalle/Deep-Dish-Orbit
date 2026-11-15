# FlameCheck eval results

Run: 2026-11-15 12:01 · Answer mode: Azure OpenAI gpt-5.6-luna then Gemini gemini-3.5-flash-lite, gemini-3.1-flash-lite; the model drafted 19 of 19 answers it was asked for (0 errors, 0 bad JSON fell back to evidence-only); the verifier dropped 5 drafted claims; usage {'azure_calls': 19, 'azure_tokens_in': 58980, 'azure_tokens_out': 7148} · API: in-process · Median latency: 3520 ms

**Score: 20 of 20 questions pass every check.**

| Check | Passed |
| --- | --- |
| status | 20 / 20 |
| citations real | 20 / 20 |
| required cited | 20 / 20 |
| no invented | 20 / 20 |

| ID | Kind | Question | Status | Status ok | Citations real | Required cited | No invented values | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | lookup | Which SAFFIRE-II sample was cotton-fiberglass (SIBAL) fabric? | answered | ✅ | ✅ | ✅ | ✅ |  |
| L2 | lookup | What was the microgravity flame spread rate of the cotton-fiberglass sample in SAFFIRE-II? | answered | ✅ | ✅ | ✅ | ✅ |  |
| L3 | lookup | What oxygen level was BASS-II test BASS2-B1 run at? | answered | ✅ | ✅ | ✅ | ✅ |  |
| L4 | lookup | Which FLEX tests burned methanol at 34% oxygen? | answered | ✅ | ✅ | ✅ | ✅ |  |
| L5 | lookup | Which BASS-II tests used Nomex fabric? | answered | ✅ | ✅ | ✅ | ✅ |  |
| L6 | lookup | What happened to the silicone samples in SAFFIRE-II? | answered | ✅ | ✅ | ✅ | ✅ |  |
| C1 | compare | How did the SAFFIRE-II cotton-fiberglass sample burn in microgravity compared with 1 g? | answered | ✅ | ✅ | ✅ | ✅ |  |
| C2 | compare | How did heptane and methanol droplets compare at 21% oxygen in FLEX? | answered | ✅ | ✅ | ✅ | ✅ |  |
| C3 | compare | How did PMMA rods compare with PMMA films in BASS-II at 17% oxygen? | answered | ✅ | ✅ | ✅ | ✅ |  |
| C4 | compare | How did methanol droplets in FLEX behave at 21% versus 34% oxygen? | answered | ✅ | ✅ | ✅ | ✅ |  |
| C5 | compare | How did SIBAL fabric burn in BASS-II at 18% compared with 21% oxygen? | answered | ✅ | ✅ | ✅ | ✅ |  |
| S1 | suppression | Which FLEX tests used helium to put out the flame? | answered | ✅ | ✅ | ✅ | ✅ |  |
| S2 | suppression | Which FLEX methanol tests with carbon dioxide were extinguished? | answered | ✅ | ✅ | ✅ | ✅ |  |
| S3 | suppression | Which FLEX heptane tests used helium? | answered | ✅ | ✅ | ✅ | ✅ |  |
| S4 | suppression | Did carbon dioxide put out heptane droplets at 18% oxygen in FLEX? | answered | ✅ | ✅ | ✅ | ✅ |  |
| N1 | no-data | How does cotton burn in lunar gravity? | no_direct_data | ✅ | ✅ | ✅ | ✅ |  |
| N2 | no-data | Is Nomex safe at 34% oxygen on the Moon? | no_direct_data | ✅ | ✅ | ✅ | ✅ |  |
| N3 | no-data | Will PMMA burn on Mars at 30% oxygen? | no_direct_data | ✅ | ✅ | ✅ | ✅ |  |
| N4 | no-data | Does Kapton burn at 21% oxygen in microgravity? | no_direct_data | ✅ | ✅ | ✅ | ✅ |  |
| N5 | no-data | How do rockets burn solid propellant? | out_of_scope | ✅ | ✅ | ✅ | ✅ |  |

Checks are defined in `eval/questions.yaml`. Expected values come from `data/clean/tests.csv`.
