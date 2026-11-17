# Related work: index

This folder holds the literature search for the project's research paper. Start with
the report, then open the notes for whichever topic you are writing.

- **Report:** `Related work for physician diet app.md`, the synthesis (written 16 November 2026).
- **Notes:** `notes/`, six files with the full per-topic findings, one per topic.
- **Sources:** `sources/`, official reports and a few papers downloaded during the search (not in git).

## The question

Searched and verified 15–16 November 2026:

> Which published papers are most similar to this project, a physician-supervised diet
> and lifestyle recommendation web app for patients in Bangladesh? How does the project
> compare with them? What does that mean for writing the project's research paper: its
> related-work section, its novelty claim, the limitations it must state, and the
> evaluation reviewers will expect?

The searches were given this description of the project:

> A deterministic, guideline-cited rule engine; a contraindication gate that runs before
> any ranking; food (672 items from FCTB 2013, IFCT 2017 and USDA), recipe (250
> Bangladeshi home dishes) and exercise (408 items) rankers, which are monotonic
> HistGradientBoosting models trained on synthetic archetypes with labels from a
> hand-written function; a weekly meal plan under 2000 mg sodium; local OCR of lab slips;
> an LLM used only to phrase the report; physician approval before any report; an audit
> log; a daily checklist with a streak; a Bangla interface. No real patients have used it
> yet.

Each notes file opens with the version of this brief it worked from.

## What is in `notes/`

Every file is organised by key question. Each question has a takeaway, cited findings,
inferences and gaps, and the file ends with a synthesis and a list of venues. The
"in all" counts are approximate: they were made by counting distinct DOIs, PMIDs and
arXiv IDs, and companion papers or co-publications can share one entry.

| File | Covers | Papers |
|---|---|---|
| `food_diet_recommenders.md` | Health-aware food, recipe and meal-plan recommenders; condition coverage; gates before ranking; diet optimisation (LP/IP); composition tables and recipe nutrition; evaluation | 25 ranked (18 systems, 7 surveys), five in depth; about 75 in all |
| `safety_oversight_llms.md` | Clinician-in-the-loop review of AI output; rule-based and hybrid CDSS; LLM diet-advice studies; LLM phrasing and Bengali; WHO, FDA and EU AI Act oversight rules | 25 ranked, five in depth; about 70 in all, plus the WHO, FDA and EU documents |
| `bangladesh_south_asia.md` | South Asian diet recommenders and datasets; Bangladeshi digital-health trials; Bangla apps, literacy and the gender gap in phone access; disease burden; doctors per population | 20 ranked; about 65 in all, plus national surveys and data sources |
| `exercise_lifestyle_recommenders.md` | Automated FITT/FITT-VP prescription; exercise safety rules; combined diet-and-exercise systems; checklists, streaks and gamification | 17 ranked; about 50 in all |
| `lab_report_ocr.md` | OCR and extraction of lab values from photos and scans; engine comparisons; human confirmation; LMIC and Bangla OCR; multimodal LLMs on lab reports | 13 ranked entries (14 papers) plus 14 supporting; 28 in all |
| `methods_evaluation.md` | Training on rule-generated labels; synthetic patients; monotonic constraints; recommender evaluation and grouped CV; reporting guidelines (TRIPOD+AI, DECIDE-AI); the staged path to clinical evaluation | 25 ranked; about 85 in all, including guidelines and scikit-learn docs |

## How papers were checked, and what is still uncertain

Every paper was checked on 15–16 November 2026 against at least one primary record:
Crossref, PubMed, Europe PMC, arXiv, OpenAlex, the publisher page or an official
proceedings page. A number appears in the notes only if it was read in the abstract or
the full text. Each notes file starts with its own verification statement.

Caveats that remain:

- **Abstract only.** Many entries rely on abstracts. The safety notes read full text only
  for Hoang 2023 and Chen 2024. Full texts were not read for, among others, DIETOS (the
  CMPB paper), PREFer, Iwendi 2020, EXPERT, Ferretto 2020, Sun 2021, HeNuALs, Kairat 2025,
  Diet-Right, Bondevik 2024, Min 2020 and Tran 2018.
- **Preprints.** FITTER (posted 2026-11-02; its numbers may change), NutriOrion,
  MedRepBench (its ECCV 2026 acceptance is unconfirmed), OBESEYE, Trattner & Elsweiler
  2017, bbOCR, the PP-OCR technical reports, NutriBench, Abrar 2025, RecSim, Krauth 2020,
  Winecoff 2021 and Hinton 2015.
- **Partial full text.** FITTER and P3-EX were read through a summarising fetch. Recheck
  their numbers against the PDFs.
- **Marked TODO(verify) or flagged in the notes:** the volume, pages and given names for
  Lee, Wang & Hagras 2010; the band-to-diet mapping in DIETOS Fig. 2; the odd confidence
  intervals in Wang LC 2024 and Billah 2022; the BBS ICT and HIES figures, which come from
  newspaper reports; the WHO 2024 publication date; the provenance of the RJUA-MedDQA data.
- **Metadata only.** Some records were confirmed only bibliographically (for example
  DiabChatbot, Seljak 2009, Mahajan & Kaur 2024, Koo & Li 2016 and MI-CLAIM). No content
  claims are made about them.
- **Bounded search.** IEEE Xplore and DBLP could not be searched directly, and the
  searches were not systematic. Every "we found no system that ..." is a negative result
  from this search, not proof of absence.
- **Different data.** Numbers from other papers come from different tasks and data. Do not
  set them against the project's own numbers.

## What is in `sources/`

These files are not in git: `sources/.gitignore` contains `*.pdf`. Files present on
16 November 2026:

| File | What it is |
|---|---|
| `BDHS_2017-18_final_report_FR344.pdf` | Bangladesh Demographic and Health Survey 2017–18, final report (NIPORT & ICF) |
| `BDHS_2022_final_report_FR386.pdf` | Bangladesh Demographic and Health Survey 2022, final report (NIPORT & ICF) |
| `WHO_STEPS_Bangladesh_2018_fact_sheet.pdf` | WHO STEPS 2018 Bangladesh fact sheet |
| `IDF_Diabetes_Atlas_South_East_Asia.pdf` | IDF Diabetes Atlas, 11th edition, South-East Asia factsheet |
| `GSMA_Mobile_Gender_Gap_Report_2025.pdf` | GSMA Mobile Gender Gap Report 2025 |
| `ITU_report.pdf` | An ITU report. **The download is incomplete** (1,260,955 of a declared 1,274,606 bytes) and the file does not open. The notes do not cite it. Download it again if it is needed. |
| `FDA_Clinical_Decision_Support_Software_guidance.pdf` | FDA, Clinical Decision Support Software guidance (issued 29 January 2026) |
| `Caruana_2015_intelligible_models_healthcare.pdf` | Caruana et al., KDD 2015 (the asthma/pneumonia example) |
| `Joachims_clickthrough_bias.pdf` | Joachims et al., SIGIR 2005, on interpreting clickthrough data as implicit feedback |
| `CEUR-WS_vol1953_paper13_HealthRecSys2017.pdf` | The DIETOS paper at the HealthRecSys 2017 workshop (CEUR-WS Vol-1953) |
| `Starke_2021.pdf` | Starke et al. 2021, "The Cholesterol Factor" (MORS workshop at RecSys) |
| `Yera_Toledo_2019_IEEE_Access.pdf` | Yera Toledo, Alzahrani & Martínez, IEEE Access 2019 |

## Three findings in the code (checked by the coordinator on 2026-11-16)

These change what the paper can claim. The report explains each one in context.

1. **The LLM phrases the report after approval.** `src/api/routes/report.py` lines 60–68
   call the LLM every time the report is requested, after the `Approval` row exists. The
   physician approves the structured result, not the wording. The patient can therefore
   read wording the physician never saw, and it can differ from one request to the next.
   The safety notes (Zaretsky 2024, Woo 2024, Luo 2026, Brewster 2024) show why this
   matters. The paper must disclose it, or the design should change so that the physician
   approves the final text.
   *Status 2026-11-17: fixed.* The wording is now written before approval
   (`POST /review/{id}/wording`, `src/api/report_wording.py`), shown to the physician,
   and stored with the approval; the report route serves that text and imports no LLM
   code (`tests/test_report_wording.py`). The line numbers above refer to the old code.
2. **Tuning leaks into the model evaluation.** `scripts/train_recommenders.py` line 843
   tunes hyperparameters with `GroupKFold` over all archetypes, and line 861 evaluates
   with `GroupKFold` over the same archetypes. The "held-out" archetypes were seen during
   tuning, so the reported Spearman figures may be slightly optimistic. Nested
   cross-validation fixes this (Varma & Simon 2006, in the methods notes).
   *Status 2026-11-17: fixed.* The evaluation is now nested (the search reruns inside
   each outer fold; `tests/test_nested_cv.py`). The optimism did not show at three
   decimals: food 0.9987 nested against 0.9987 before, recipes 0.9981 against 0.9981,
   exercises 0.9865 against 0.9836. Figures: `thesis/results/*_recommender_nested_cv.csv`
   and the README tables.
3. **The live app ranks with the trained model.** It uses the shipped model when the model
   file exists, and the deterministic formula otherwise. The hand-written label function
   is used only to make training labels. The paper must therefore explain why the model
   is used rather than the label function, and report where the model departs from it.

## Rules for using these notes in the paper

From `CLAUDE.md` ("Writing the paper"):

- Take references for the paper from these notes, not from memory. Recheck each
  citation's details against its source page before submission.
- Never invent a citation, author, year, DOI or page. Mark anything unchecked
  `TODO(cite)`.
- Every number in the paper must trace to a file in the repo or a rerun. Mark a number
  that cannot be traced `TODO(verify)`.
- Say "synthetic" wherever patients, labels or OCR slips are synthetic. Do not use outcome
  words. Do not compare against other systems' published numbers unless the task and data
  match.

Still to settle with the author: the target venue and its format, the citation style, and
the co-authors.
