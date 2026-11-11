"""The plan the app serves when the trained recommenders are present.

The rest of the suite is pinned to the deterministic scorers (conftest.py), so
this is the one place the two trained models rank a real patient's foods and
dishes end to end. A model may reorder what the gate allows; it must never
bring back what the gate removed or break a rule of the planner, and its
scores must move the way the training constraints say they do.

The models are build artifacts (data/models is not in the repository). Without
them these tests are skipped, not passed: run scripts/train_recommenders.py.
"""

from dataclasses import replace

import numpy as np
import pytest

from src.api.services import build_assessment
from src.db.models import Patient, Visit
from src.diet import matcher, recommender
from src.diet.food_db import NUTRIENT_COLUMNS, food_index, load_foods
from src.diet.meal_plan import MAX_WEEKLY_SERVINGS, plannable
from src.diet.recipe import load_recipes

pytestmark = pytest.mark.skipif(
    not (recommender.MODEL_PATH.exists() and recommender.RECIPE_MODEL_PATH.exists()),
    reason="no trained recommenders in data/models: run scripts/train_recommenders.py",
)

_PATIENTS = {
    "healthy adult": (dict(sex="male", birth_year=1990, height_cm=170), dict(weight_kg=68)),
    "hypertensive, diabetic and anaemic": (
        dict(sex="female", birth_year=1990, height_cm=160),
        dict(weight_kg=70, biomarkers={"fasting_glucose": 130, "systolic_bp": 150,
                                       "diastolic_bp": 95, "hemoglobin": 10.0}),
    ),
    "pregnant vegetarian": (
        dict(sex="female", birth_year=1997, height_cm=158, pregnant=True,
             pregnancy_trimester=2, dietary_restrictions=["vegetarian"]),
        dict(weight_kg=62, biomarkers={"hemoglobin": 10.2}),
    ),
    "older man with kidney disease": (
        dict(sex="male", birth_year=1952, height_cm=166,
             conditions=["hypertension", "chronic_kidney_disease"], activity_level="sedentary"),
        dict(weight_kg=74),
    ),
    "woman with high cholesterol and raised glucose": (
        dict(sex="female", birth_year=1968, height_cm=155, conditions=["high_cholesterol"]),
        dict(weight_kg=66, biomarkers={"fasting_glucose": 112}),
    ),
}


@pytest.fixture(scope="module")
def models():
    food, recipe = recommender._load_model_uncached(), recommender._load_recipe_model_uncached()
    if food is None or recipe is None:
        pytest.skip("the trained recommenders were built for another feature or library version")
    return food, recipe


@pytest.fixture(scope="module")
def tags_by_id():
    foods = load_foods()
    tags = {f.food_id: set(f.tags) for f in foods}
    recipes = load_recipes(food_index(foods))
    tags.update({r.recipe_id: set(r.tags) for r in recipes})
    return tags, {r.recipe_id: r for r in recipes}


def _assess(who: str, models, monkeypatch) -> dict:
    food_model, recipe_model = models
    monkeypatch.setattr(recommender, "load_model", lambda: food_model)
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: recipe_model)
    patient_fields, visit_fields = _PATIENTS[who]
    patient = Patient(**{"name": who, "pregnant": False, "pregnancy_trimester": None,
                         "conditions": [], "dietary_restrictions": [],
                         "fitness_level": "beginner", "activity_level": None, "notes": "",
                         **patient_fields})
    return build_assessment(patient, Visit(**{"biomarkers": {}, **visit_fields}))


@pytest.mark.parametrize("who", _PATIENTS)
def test_a_plan_ranked_by_the_trained_models_keeps_every_rule(who, models, tags_by_id, monkeypatch):
    tags, recipes = tags_by_id
    result = _assess(who, models, monkeypatch)
    nutrition = result["nutrition"]
    assert nutrition["scoring_backend"] == "ml" and nutrition["recipe_scoring_backend"] == "ml"

    excluded = set(result["exclusions"]["food_tags"])
    plan = nutrition["meal_plan"]
    lines = [item for day in plan["days"] for items in day["meals"].values() for item in items]
    ranked = [f["food_id"] for f in nutrition["top_foods"]]
    ranked += [r["recipe_id"] for r in nutrition["top_recipes"]]
    assert nutrition["top_foods"] and nutrition["top_recipes"] and len(plan["days"]) == 7

    # the gate holds: nothing excluded is planned or suggested
    for item_id in ranked + [line.get("recipe_id") or line["food_id"] for line in lines]:
        assert not tags[item_id] & excluded, (item_id, tags[item_id] & excluded)
    # no sweets, drinks or dishes over the vitamin A limit, however they score
    for recipe_id in {line["recipe_id"] for line in lines if line.get("recipe_id")}:
        assert plannable(recipes[recipe_id]), recipe_id

    limit = nutrition["limits"]["sodium_mg"]
    target = plan["target_kcal"]
    served: dict[str, int] = {}
    for day in plan["days"]:
        assert day["totals"]["sodium_mg"] < limit
        assert abs(day["totals"]["kcal"] - target) / target < 0.25
        for meal in ("breakfast", "lunch", "dinner"):
            assert day["meals"][meal], (day["weekday"], meal)
        for line in (item for items in day["meals"].values() for item in items):
            if line.get("course") != "staple":
                key = line.get("recipe_id") or line["food_id"]
                served[key] = served.get(key, 0) + 1
    assert max(served.values()) <= MAX_WEEKLY_SERVINGS


@pytest.mark.parametrize("who", _PATIENTS)
def test_trained_scores_move_the_right_way_with_every_nutrient(who, models, monkeypatch):
    """The monotonic constraints the models are fitted under, checked on the
    real food and recipe tables: a richer copy of an item never scores lower,
    a saltier one never higher. Energy is the one nutrient free to move a
    score either way (it is the denominator of the density score)."""
    nutrition = _assess(who, models, monkeypatch)["nutrition"]
    foods = load_foods()
    recipes = load_recipes(food_index(foods))
    # the patient's full emphasis, and none: where a planned day ends up
    for emphasize in (nutrition["emphasize"], []):
        context = (emphasize, nutrition["targets"], nutrition["findings"], nutrition["limits"])
        for items, field, score in ((foods, "nutrients", matcher.score_foods),
                                    (recipes, "per_serving", matcher.score_recipes)):
            scores = np.array(score(items, *context))
            for nutrient in NUTRIENT_COLUMNS:
                if nutrient == "kcal":
                    continue
                richer = [replace(item, **{field: {**getattr(item, field),
                                                   nutrient: getattr(item, field)[nutrient] * 1.5 + 1.0}})
                          for item in items]
                change = np.array(score(richer, *context)) - scores
                if nutrient == "sodium_mg":
                    assert (change <= 1e-9).all(), (nutrient, emphasize)
                else:
                    assert (change >= -1e-9).all(), (nutrient, emphasize)


def test_a_more_commonly_cooked_dish_never_scores_lower(models, monkeypatch):
    nutrition = _assess("hypertensive, diabetic and anaemic", models, monkeypatch)["nutrition"]
    context = (nutrition["emphasize"], nutrition["targets"], nutrition["findings"], nutrition["limits"])
    recipes = [r for r in load_recipes(food_index(load_foods())) if r.weekly_frequency_score]
    as_cooked = np.array(matcher.score_recipes(recipes, *context))
    as_a_daily_dish = np.array(matcher.score_recipes(
        [replace(r, weekly_frequency_score=10) for r in recipes], *context))
    assert (as_a_daily_dish >= as_cooked).all()
    assert (as_a_daily_dish > as_cooked).any()
