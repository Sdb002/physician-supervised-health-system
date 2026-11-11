"""The exercise prescription built from the exercise safety dataset: what the
gate removes for each condition, age and sex, which exercises the plan may
pick, the order it picks them in, and what each pick carries.

The suite runs on the deterministic formula (conftest.py); the trained
exercise model is exercised in tests/test_trained_models.py.
"""

import csv
import importlib.util
from pathlib import Path

import pytest

from src.api.services import build_assessment
from src.clinical.contraindication import excluded_tags, filter_items
from src.core.config import DATA_DIR
from src.db.models import Patient, Visit
from src.lifestyle import recommender
from src.lifestyle.exercise_db import PLAN_GROUPS, RATED_CONDITIONS, load_exercises
from src.lifestyle.fitt_vp import PICKS
from src.lifestyle.ranking import baseline_score, context_for, plannable

RAW = DATA_DIR / "lifestyle" / "raw" / "exercise_safety_dataset.csv"
RAW_RATING = {"pregnancy": "cond_pregnancy", "hypertension": "cond_hypertension",
              "diabetes": "cond_diabetes", "anemia": "cond_anemia",
              "knee_osteoarthritis": "cond_knee_oa"}


@pytest.fixture(scope="module")
def exercises():
    return load_exercises()


@pytest.fixture(scope="module")
def raw_rows():
    with open(RAW, encoding="utf-8-sig", newline="") as f:
        return {r["exercise_id"]: r for r in csv.DictReader(f)}


def _plan(sex="female", birth_year=1985, conditions=(), pregnant=False, fitness="beginner",
          biomarkers=None, weight_kg=62, height_cm=158):
    patient = Patient(name="Exercise Case", sex=sex, birth_year=birth_year, height_cm=height_cm,
                      conditions=list(conditions), dietary_restrictions=[], excluded_foods=[],
                      pregnant=pregnant, pregnancy_trimester=2 if pregnant else None,
                      fitness_level=fitness)
    result = build_assessment(patient, Visit(weight_kg=weight_kg, biomarkers=biomarkers or {}))
    return result, result["exercise_plan"]


def _picks(plan):
    return [e for group in plan["type"].values() for e in group]


# --- the dataset ------------------------------------------------------------

def test_every_source_row_is_in_the_table(exercises, raw_rows):
    assert [e.exercise_id for e in exercises] == list(raw_rows)
    assert len(exercises) == 408
    assert {e.category for e in exercises} == {"aerobic", "strength", "flexibility",
                                               "balance", "breathing"}


def test_the_table_validates():
    spec = importlib.util.spec_from_file_location(
        "validate_datasets", Path(__file__).resolve().parents[1] / "scripts" / "validate_datasets.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    errors, _, count = validator.validate_exercises()
    assert errors == [] and count == 408
    assert validator.cross_check_contraindications() == []


def test_avoid_tags_are_the_source_ratings(exercises, raw_rows):
    for e in exercises:
        raw = raw_rows[e.exercise_id]
        for condition, column in RAW_RATING.items():
            assert (f"avoid_{condition}" in e.tags) == (raw[column] == "avoid"), e.exercise_id
            assert (condition in e.modify_for) == (raw[column] == "modify"), e.exercise_id
        assert ("not_for_older_adults" in e.tags) == (raw["older_adult_suitable"] == "no")


def test_lying_on_the_back_is_read_off_the_pregnancy_note(exercises):
    by_id = {e.exercise_id: e for e in exercises}
    assert "supine_position" in by_id["EX026"].tags      # supine hamstring stretch
    assert "supine_position" in by_id["EX084"].tags      # hip bridge
    # "the inclined position avoids lying flat"
    assert "supine_position" not in by_id["EX359"].tags
    assert "supine_position" not in by_id["EX006"].tags  # wall press-up


def test_aerobic_mets_are_the_compendium_values(exercises):
    by_id = {e.exercise_id: e for e in exercises}
    assert by_id["EX049"].met_value == 4.8 and by_id["EX049"].intensity_level == "moderate"
    assert by_id["EX050"].met_value == 7.5 and by_id["EX050"].intensity_level == "vigorous"
    assert by_id["EX317"].intensity_level == "light"
    # a warm-up drill the Compendium has no code for
    assert by_id["EX124"].met_value is None and by_id["EX124"].intensity_level == ""


# --- the gate -----------------------------------------------------------------

@pytest.mark.parametrize("condition", RATED_CONDITIONS)
def test_each_condition_removes_what_the_dataset_says_to_avoid(condition, exercises, raw_rows):
    allowed = {e.exercise_id for e in filter_items(exercises, excluded_tags([condition]).exercise_tags)}
    avoided = {i for i, r in raw_rows.items() if r[RAW_RATING[condition]] == "avoid"}
    assert not allowed & avoided
    removed = {e.exercise_id for e in exercises} - allowed
    if condition == "pregnancy":
        # ...and, as before the dataset, what is done lying on the back
        supine = {e.exercise_id for e in exercises if "supine_position" in e.tags}
        assert removed == avoided | supine
    else:
        assert removed == avoided


def test_age_and_sex_rules(exercises):
    older = excluded_tags([], age=70, sex="male")
    assert older.applied_populations == ("older_adult", "male")
    assert {"not_for_older_adults", "female_only"} == set(older.exercise_tags)
    younger = excluded_tags([], age=64, sex="female")
    assert younger.applied_populations == ("female",)
    assert younger.exercise_tags == {"male_only"}
    allowed = {e.exercise_id for e in filter_items(exercises, older.exercise_tags)}
    assert "EX146" not in allowed  # barbell back squat
    assert "EX283" not in allowed  # deep abdominal contraction after childbirth
    assert "EX357" in allowed      # pelvic floor exercises for men


# --- the prescription ---------------------------------------------------------

def test_nothing_the_gate_removed_is_planned():
    cases = [
        dict(pregnant=True, birth_year=1997),
        dict(conditions=["knee_osteoarthritis"], sex="male", birth_year=1950, fitness="advanced"),
        dict(biomarkers={"systolic_bp": 160, "diastolic_bp": 100, "hemoglobin": 9.5,
                         "fasting_glucose": 140}, fitness="intermediate"),
    ]
    by_id = {e.exercise_id: e for e in load_exercises()}
    for case in cases:
        result, plan = _plan(**case)
        excluded = set(result["exclusions"]["exercise_tags"])
        for pick in _picks(plan):
            assert not set(by_id[pick["exercise_id"]].tags) & excluded, (case, pick["exercise_id"])


def test_every_pick_is_plannable_for_the_patient():
    result, plan = _plan(conditions=["knee_osteoarthritis"], birth_year=1950, fitness="intermediate")
    ctx = context_for(result["age"], "female", result["conditions"], "intermediate",
                      result["overall_risk"], result["anthropometrics"]["bmi_category"])
    by_id = {e.exercise_id: e for e in load_exercises()}
    for pick in _picks(plan):
        exercise = by_id[pick["exercise_id"]]
        assert plannable(exercise, ctx)
        assert exercise.home_feasible  # no gym-only exercise
    for exercise in (by_id[p["exercise_id"]] for p in plan["type"]["aerobic"]):
        assert exercise.met_value is not None and exercise.intensity_level != "vigorous"


def test_groups_and_frequencies_by_age():
    _, younger = _plan(birth_year=1985)
    assert set(younger["type"]) == {"aerobic", "strength", "flexibility"}
    assert "balance_days" not in younger["frequency"]
    _, older = _plan(birth_year=1950)
    assert set(older["type"]) == set(PLAN_GROUPS)
    assert older["frequency"]["balance_days"] == 3
    for group, items in older["type"].items():
        assert len(items) == PICKS[group]
        assert len({e["exercise_id"] for e in items}) == len(items)


def test_a_beginner_or_a_high_risk_patient_starts_on_beginner_exercises():
    by_id = {e.exercise_id: e for e in load_exercises()}
    for kwargs in (dict(fitness="beginner"),
                   dict(fitness="advanced", biomarkers={"systolic_bp": 182, "diastolic_bp": 112})):
        _, plan = _plan(**kwargs)
        assert plan["intensity"]["level"] == "light"
        assert {by_id[p["exercise_id"]].fitness_level for p in _picks(plan)} == {"beginner"}


def test_strength_picks_spread_over_the_body():
    by_id = {e.exercise_id: e for e in load_exercises()}
    _, plan = _plan(fitness="intermediate")
    regions = [by_id[p["exercise_id"]].body_region for p in plan["type"]["strength"]]
    assert len(set(regions)) == len(regions) == PICKS["strength"]
    areas = {"lower": {"thigh", "hip/glutes", "calf", "ankle/foot"},
             "trunk": {"core/abdomen/waist", "lower back"}}
    assert set(regions) & areas["lower"] and set(regions) & areas["trunk"]


def test_a_pick_carries_how_to_do_it_and_the_notes_for_the_patient():
    result, plan = _plan(biomarkers={"systolic_bp": 150, "diastolic_bp": 95})
    assert "hypertension" in result["conditions"]
    picks = _picks(plan)
    for pick in picks:
        assert pick["how_to"] and pick["source"]["name"]
        assert {n["condition"] for n in pick["condition_notes"]} <= {"hypertension"}
    by_id = {e.exercise_id: e for e in load_exercises()}
    for pick in picks:
        exercise = by_id[pick["exercise_id"]]
        notes = {n["condition"]: n for n in pick["condition_notes"]}
        if "hypertension" in exercise.modify_for:
            assert notes["hypertension"]["modify"] is True
            assert notes["hypertension"]["note"] == exercise.notes["hypertension"]


def test_a_patient_reads_the_dose_without_the_curators_notes():
    from src.lifestyle.fitt_vp import patient_dose

    by_id = {e.exercise_id: e for e in load_exercises()}
    assert patient_dose(by_id["EX447"]) == "10-15 reps"                       # "[CCG]"
    assert patient_dose(by_id["EX020"]) == ("hold 5 s each leg; reps and frequency set by "
                                            "the clinician")                 # "(source leaves them blank)"
    assert patient_dose(by_id["EX164"]) == ("1 set of 8-12 (2-3 sets may be more effective), "
                                            "at least 2 non-consecutive days/wk")
    assert patient_dose(by_id["EX049"]) == ""  # an aerobic activity: the plan sets its minutes
    for exercise in by_id.values():
        dose = patient_dose(exercise)
        assert not any(word in dose for word in ("source", "[", "Compendium", ">=")), exercise.exercise_id
    _, plan = _plan(birth_year=1950)
    for pick in _picks(plan):
        assert pick["dose_source"] == by_id[pick["exercise_id"]].dose


def test_older_patients_are_pointed_to_the_easier_version():
    by_id = {e.exercise_id: e for e in load_exercises()}
    _, plan = _plan(birth_year=1950, fitness="intermediate")
    for pick in _picks(plan):
        assert pick["use_easier_version"] == (by_id[pick["exercise_id"]].older_adult == "modify")


def test_without_a_model_the_formula_ranks():
    exercises = load_exercises()
    ctx = context_for(40, "female", [], "beginner", "low", "normal")
    assert recommender.active_backend() == "linear"
    assert recommender.score(exercises[:5], ctx) == [baseline_score(e, ctx) for e in exercises[:5]]
    assert recommender.featurize(exercises[0], ctx).shape == (recommender.FEATURE_DIM,)


def test_the_formula_prefers_what_needs_no_modification():
    by_id = {e.exercise_id: e for e in load_exercises()}
    plain = context_for(40, "female", [], "beginner", "low", "normal")
    hypertensive = context_for(40, "female", ["hypertension"], "beginner", "low", "normal")
    bracing = by_id["EX047"]  # rated "modify" for hypertension (15-s hold)
    assert "hypertension" in bracing.modify_for
    assert baseline_score(bracing, hypertensive) < baseline_score(bracing, plain)


def test_the_written_report_lists_each_exercise_with_its_dose():
    from src.api.report_template import template_report

    result, plan = _plan(birth_year=1950, fitness="intermediate",
                         biomarkers={"systolic_bp": 150, "diastolic_bp": 95})
    text = template_report("Older Case", result, "en")
    assert "Balance: 3 days a week" in text
    for pick in _picks(plan):
        assert pick["name_en"] in text
        if pick["dose"]:
            assert f"{pick['name_en']}: {pick['dose']}" in text
        if pick["use_easier_version"] and pick["easier_version"]:
            assert f"Start with the easier version: {pick['easier_version']}" in text
        for note in pick["condition_notes"]:
            if note["modify"]:
                assert f"With your high blood pressure: {note['note']}" in text
    # Bangla: the headings translate, the dataset's instructions stay English
    assert "ভারসাম্যের ব্যায়াম: সপ্তাহে 3 দিন" in template_report("Older Case", result, "bn")


# --- the physician's plan editor ----------------------------------------------

def test_the_editor_keeps_balance_and_rejects_what_the_gate_removed(client):
    patient = {"name": "Older Case", "sex": "male", "birth_year": 1950, "height_cm": 165,
               "conditions": ["knee_osteoarthritis"]}
    patient_id = client.post("/patients", json=patient).json()["id"]
    assessment = client.post(f"/patients/{patient_id}/visits", json={"weight_kg": 70}).json()
    plan = assessment["result"]["exercise_plan"]
    kept = {group: [e["exercise_id"] for e in items] for group, items in plan["type"].items()}
    kept["strength"] = kept["strength"][:2]
    def ref(item):
        key = "recipe_id" if item.get("recipe_id") else "food_id"
        return {key: item[key], "qty_g": item["qty_g"]}

    edit = {"exercise": {"aerobic_days": 4, "strength_days": 2, "flexibility_days": 3,
                         "balance_days": 2, "aerobic_min_per_session": 20, "type": kept},
            "days": [{meal: [ref(i) for i in items] for meal, items in day["meals"].items()}
                     for day in assessment["result"]["nutrition"]["meal_plan"]["days"]]}
    response = client.post(f"/review/{assessment['id']}/recompute", json=edit)
    assert response.status_code == 200
    edited = response.json()["exercise_plan"]
    assert edited["frequency"]["balance_days"] == 2
    assert [e["exercise_id"] for e in edited["type"]["strength"]] == kept["strength"]
    assert edited["type"]["balance"] == plan["type"]["balance"]

    # jogging is "avoid" with knee osteoarthritis
    edit["exercise"]["type"] = {**kept, "aerobic": ["EX050"]}
    response = client.post(f"/review/{assessment['id']}/recompute", json=edit)
    assert response.status_code == 422
    assert "not allowed for this patient" in response.json()["detail"]
