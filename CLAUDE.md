# Physician-Supervised Health System

A web app that turns a patient's intake (weight, fasting glucose, blood
pressure, haemoglobin, recorded conditions, foods they do not eat) into a week
of meals, food and recipe rankings and an exercise prescription for
Bangladeshi patients. A physician approves the result before the patient sees
any report. It is a thesis project, and the current goal is a **research paper**
about it.

`README.md` is the source of truth for detail (datasets, models, OCR,
workflow). Read the relevant README section before non-trivial work; this file
is the short version plus the rules.

## Three guarantees: never weaken them

Each is enforced by a test, and each is a central claim of the paper.

1. **Clinical logic never depends on an LLM.** `src/clinical`, `src/diet` and
   `src/lifestyle` must not import `src.llm` (`tests/test_llm_isolation.py`).
2. **Contraindicated items never reach recommendations.** The gate in
   `src/clinical/contraindication.py` runs before any ranking; trained models
   only re-rank what the gate allowed (`tests/test_contraindication.py`).
3. **No report without physician approval.** `GET /report/{visit_id}` is 403
   until an `Approval` row exists (`tests/test_api_gate.py`), and its text is
   the wording the physician previewed and approved, stored with the approval;
   the route writes none and imports no LLM code (`tests/test_report_wording.py`).

The app must also keep working with no `ANTHROPIC_API_KEY`.

## Layout

```
src/clinical   deterministic rules: BMI, risk scoring, targets, contraindication gate
src/diet       food DB, recipe nutrition, matcher, meal plan, recommender (ML backend)
src/lifestyle  exercise DB, ranking, ACSM FITT-VP prescription, weekly schedule
src/ocr        local lab-slip reading (RapidOCR + rule-based parser), prefill only
src/llm        optional Claude OCR and report phrasing
src/api        FastAPI routes; access rule in src/api/access.py; ENGINE_VERSION in services.py
src/db         SQLAlchemy models, Alembic migrations (applied at API startup)
dashboard/     Next.js UI: admin, doctor, patient (has its own CLAUDE.md, read it first)
data/          datasets (schema.md, snapshots, validation reports) and cited reference YAMLs
scripts/       convert_datasets, validate_datasets, seed_db, train_recommenders, refresh_assessments
notebooks/     01 dataset audit, 02 cross-validation, 03 results figures, 04 recommender training
thesis/        diagrams/, figures/, results/ (model comparison CSVs)
tests/         validation tables, gate and isolation tests, synthetic fixtures
```

## Commands (PowerShell, from the project root)

```powershell
.venv\Scripts\python.exe -m pytest                         # engine and API tests
cd dashboard; npm test                                     # dashboard unit tests
.venv\Scripts\python.exe -m uvicorn src.api.main:app --reload   # API on :8000
npm run dev                                                # API + dashboard (may report a failed exit code while both run)
.venv\Scripts\python.exe scripts\seed_db.py                # demo data
.venv\Scripts\python.exe scripts\convert_datasets.py       # regenerate dataset CSVs
.venv\Scripts\python.exe scripts\validate_datasets.py      # validate them
.venv\Scripts\python.exe scripts\train_recommenders.py     # about 110 min (nested CV); run in the background
```

## Data rules

- `data/reference/*.yaml` are real cited clinical constants. Change one only
  with a citation.
- Never hand-edit generated CSVs in `data/food`, `data/recipe` or
  `data/lifestyle`. Fix `scripts/convert_datasets.py`, regenerate, validate.
- Every assessment decision goes to the append-only audit log.
- A change to engine behaviour bumps `ENGINE_VERSION` and updates the README.
- All patients in the repo are synthetic. Never add real patient data.

## Writing the paper

Paper drafts go in `thesis/paper/`; figures in `thesis/figures/`, result tables
in `thesis/results/`, diagrams in `thesis/diagrams/`.

Related work lives in `thesis/related_work/`: start from its `README.md`, which
says what was searched and how, then the synthesized report, then `notes/` for
the full per-topic notes (diet recommenders, safety and LLMs, Bangladesh
context, exercise recommenders, lab-report OCR, evaluation methods). Each paper
there was checked against its source page in November 2026. Recheck a
citation's details against the source before submission, and take references
for the paper from these notes rather than from memory.

### What the paper can claim, and where the evidence is

| Claim | Evidence |
|---|---|
| The three guarantees hold | The three tests named above |
| Thresholds follow cited guidelines (ADA 2024, ACC/AHA 2017, WHO 2011, NIH/IOM, ACSM) | `data/reference/*.yaml`; `tests/test_risk_scoring.py` is the validation table, exported by `notebooks/03_results_figures.ipynb` |
| Trained recommenders recover the labelling function better than the formula on held-out patient types (nested cross-validation: no held-out archetype took part in tuning) | `thesis/results/*_recommender_comparison.csv`, `thesis/results/*_recommender_nested_cv.csv`, `data/models/*_metrics.json`, `notebooks/04_recommender_training.ipynb`, README tables, `tests/test_nested_cv.py` |
| Monotonic behaviour of the models | `tests/test_trained_models.py`, `tests/test_trained_exercise_model.py` |
| Dataset provenance and corrections | `data/*/schema.md`, `data/food/corrections_log.csv`, validation reports, `notebooks/01_dataset_audit.ipynb` |
| Lab-slip reader accuracy (73.8% to 99.7% of 351 fields) | README "Lab-slip reading"; synthetic slips only |
| Recipe nutrition reproduces the source workbook | `tests/test_recipe_nutrients.py` |

### Limitations that must be stated, never hidden

- **No real patients and no clinical evaluation.** Nothing here shows a health
  outcome, physician agreement or patient preference.
- **Model labels are synthetic.** The models learn a hand-written suitability
  function built from cited guidance. The Spearman figures say how faithfully
  it is recovered, not that the rankings are good.
- **OCR was measured on made-up slips.** It is untested on real phone photos,
  Bangla text and handwriting.
- **No saturated fat or cholesterol values** in the food table, so the high
  cholesterol plan excludes solid-fat dishes instead of counting them.
- Exercise injury ratings are carried but unused; exercises have no Bangla
  names; the Bangla interface wording has not been reviewed by a clinician.
- Physician approval is a workflow gate, not a validation of the engine.

### Rules when writing

- Every number in the paper traces to a file in this repo or a rerun of a
  script or notebook. Do not quote a figure from memory; open the file. If a
  number cannot be traced, write `TODO(verify)` instead.
- Never invent a citation, author, year, DOI or page. Take references from
  `data/reference/*.yaml` and the dataset `schema.md` files, or look them up
  and give the link. Mark anything unchecked `TODO(cite)`.
- Say "synthetic" wherever patients, labels or OCR slips are synthetic.
- Do not use outcome words (effective, improves health, clinically validated,
  accurate diagnosis). The system produces recommendations for physician
  review; it does not diagnose or treat.
- Do not compare against other systems' published numbers unless the task and
  data match; say when they do not.
- If results change (retrain, new dataset), regenerate the tables and figures
  from the notebooks; never edit a number in the text alone.
- Plain academic English, past tense for what was done, no promotional
  wording.

### Suggested structure

1. Introduction: diet-related disease in Bangladesh, the gap (local foods,
   physician oversight, safe use of LLMs)
2. Related work: diet recommender systems, clinical decision support, LLMs in
   health
3. System design: architecture, the three guarantees, workflow
4. Datasets: foods, recipes, exercises, corrections, validation
5. Methods: rule engine, contraindication gate, meal planner, recommenders,
   OCR
6. Evaluation: threshold validation, model comparison, OCR benchmark,
   guarantee tests
7. Limitations and ethics
8. Future work: physician study, labels from real review decisions, real
   lab-slip photos

Still to settle with the author: target venue and its format and page limit,
citation style, and the co-authors or supervisor to name.
