"""The exercise prescription when the trained exercise model ranks it.

The rest of the suite is pinned to the deterministic formula (conftest.py).
Here the shipped model ranks real patients' prescriptions end to end: it may
reorder what the gate and the plannable rules allow, never bring back what
they removed, and its scores must move the way the training constraints say.

The model is a build artifact (data/models is not in the repository). Without
it these tests are skipped, not passed: run
scripts/train_recommenders.py --only exercise.
"""

from dataclasses import replace

import numpy as np
import pytest

from src.api.services import build_assessment
from src.db.models import Patient, Visit
from src.lifestyle import recommender
from src.lifestyle.exercise_db import PLAN_GROUPS, load_exercises
from src.lifestyle.ranking import context_for, plannable

pytestmark = pytest.mark.skipif(
    not recommender.MODEL_PATH.exists(),
    reason="no trained exercise model in data/models: run scripts/train_recommenders.py",
)

_PATIENTS = {
    "pregnant": dict(sex="female", birth_year=1997, pregnant=True, pregnancy_trimester=2),
    "older man with knee osteoarthritis": dict(sex="male", birth_year=1950,
                                               conditions=["knee_osteoarthritis"],
                                               fitness_level="intermediate"),
    "advanced woman with knee osteoarthritis": dict(sex="female", birth_year=1976,
                                                    conditions=["knee_osteoarthritis"],
                                                    fitness_level="advanced"),
    "hypertensive diabetic beginner": dict(sex="female", birth_year=1980,
                                           conditions=["hypertension", "diabetes"]),
}


@pytest.fixture(scope="module")
def model():
    loaded = recommender._load_model_uncached()
    if loaded is None:
        pytest.skip("the trained exercise model was built for another feature or library version")
    return loaded


@pytest.fixture(scope="module")
def exercises():
    return {e.exercise_id: e for e in load_exercises()}


def _assess(who, model, monkeypatch):
    monkeypatch.setattr(recommender, "load_model", lambda: model)
    fields = {"name": who, "height_cm": 158, "pregnant": False, "pregnancy_trimester": None,
              "conditions": [], "dietary_restrictions": [], "excluded_foods": [],
              "fitness_level": "beginner", **_PATIENTS[who]}
    return build_assessment(Patient(**fields), Visit(weight_kg=66, biomarkers={}))


@pytest.mark.parametrize("who", _PATIENTS)
def test_a_prescription_ranked_by_the_model_keeps_every_rule(who, model, exercises, monkeypatch):
    result = _assess(who, model, monkeypatch)
    plan = result["exercise_plan"]
    assert plan["scoring_backend"] == "ml"
    excluded = set(result["exclusions"]["exercise_tags"])
    ctx = context_for(result["age"], _PATIENTS[who]["sex"], result["conditions"],
                      _PATIENTS[who].get("fitness_level", "beginner"), result["overall_risk"],
                      result["anthropometrics"]["bmi_category"])
    for group, picks in plan["type"].items():
        assert picks, group
        for pick in picks:
            exercise = exercises[pick["exercise_id"]]
            assert exercise.category == group
            assert not set(exercise.tags) & excluded, pick["exercise_id"]
            assert plannable(exercise, ctx), pick["exercise_id"]


def test_the_model_plans_what_the_guidelines_single_out(model, exercises, monkeypatch):
    def strength_traits(who):
        plan = _assess(who, model, monkeypatch)["exercise_plan"]
        return {t for p in plan["type"]["strength"] for t in exercises[p["exercise_id"]].traits}

    # pelvic floor training in pregnancy (2019 Canadian guideline)
    assert "pelvic_floor" in strength_traits("pregnant")
    # quadriceps or hip strengthening with knee osteoarthritis (OARSI 2019),
    # even for an advanced patient whose level the formula would rather match
    assert "knee_oa_strengthening" in strength_traits("advanced woman with knee osteoarthritis")
    assert "knee_oa_strengthening" in strength_traits("older man with knee osteoarthritis")


@pytest.mark.parametrize("who", _PATIENTS)
def test_trained_scores_move_the_right_way(who, model, exercises, monkeypatch):
    """The monotonic constraints the model is fitted under, on the real
    table: needing modification for one of the patient's conditions or
    needing bought equipment never raises a score; a demonstration video
    never lowers one."""
    result = _assess(who, model, monkeypatch)
    ctx = context_for(result["age"], _PATIENTS[who]["sex"], result["conditions"],
                      _PATIENTS[who].get("fitness_level", "beginner"), result["overall_risk"],
                      result["anthropometrics"]["bmi_category"])
    pool = [e for e in exercises.values() if e.category in PLAN_GROUPS and plannable(e, ctx)]
    scores = np.array(recommender.score(pool, ctx))
    for condition in sorted(ctx.conditions):
        flagged = [replace(e, modify_for=tuple({*e.modify_for, condition})) for e in pool]
        assert (np.array(recommender.score(flagged, ctx)) - scores <= 1e-9).all(), condition
    bought = [replace(e, needs_equipment=True) for e in pool]
    assert (np.array(recommender.score(bought, ctx)) - scores <= 1e-9).all()
    unfilmed = [e for e in pool if e.video_match == "none"]
    if unfilmed:
        before = np.array(recommender.score(unfilmed, ctx))
        filmed = [replace(e, video_match="exact") for e in unfilmed]
        assert (np.array(recommender.score(filmed, ctx)) - before >= -1e-9).all()
