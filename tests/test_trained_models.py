"""The plan the app serves when the trained recommenders are present.

The rest of the suite is pinned to the deterministic scorers (conftest.py), so
this is the one place the two trained models rank a real patient's foods and
dishes end to end. A model may reorder what the gate allows; it must never
bring back what the gate removed or break a rule of the planner.

The models are build artifacts (data/models is not in the repository). Without
them these tests are skipped, not passed: run scripts/train_recommenders.py.
"""

import pytest

from src.api.services import build_assessment
from src.db.models import Patient, Visit
from src.diet import recommender
from src.diet.food_db import food_index, load_foods
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


@pytest.mark.parametrize("who", _PATIENTS)
def test_a_plan_ranked_by_the_trained_models_keeps_every_rule(who, models, tags_by_id, monkeypatch):
    food_model, recipe_model = models
    monkeypatch.setattr(recommender, "load_model", lambda: food_model)
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: recipe_model)
    tags, recipes = tags_by_id
    patient_fields, visit_fields = _PATIENTS[who]
    patient = Patient(**{"name": who, "pregnant": False, "pregnancy_trimester": None,
                         "conditions": [], "dietary_restrictions": [],
                         "fitness_level": "beginner", "activity_level": None, "notes": "",
                         **patient_fields})
    visit = Visit(**{"biomarkers": {}, **visit_fields})

    result = build_assessment(patient, visit)
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
