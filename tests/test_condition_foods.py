"""What to eat and what to avoid, per condition (src.diet.condition_foods).

The eat lists must stay inside the patient's whole safety gate and hold only
real sources of the condition's nutrients; the avoid lists must be exactly
what that condition's rule removes, most commonly eaten first.
"""

from src.clinical.contraindication import excluded_tags, filter_items
from src.clinical.deficiency import finding_nutrients, nutrient_targets
from src.diet.condition_foods import condition_food_guide, is_source
from src.diet.food_db import (
    NUTRIENT_COLUMNS,
    eaten_in_portions,
    food_index,
    load_foods,
    recommendable_foods,
    untracked_nutrients,
)
from src.diet.habits import (
    food_habits,
    habitual_foods,
    meals_per_week_map,
    median_meals_per_week,
    portion_map,
)
from src.diet.recipe import load_recipes


def _nutrients(**values) -> dict:
    base = {c: 0.0 for c in NUTRIENT_COLUMNS}
    base.update(values)
    return base


def test_source_thresholds_follow_the_eu_claim_rules():
    # 15% of the iron NRV (14 mg) per 100 g
    assert is_source(_nutrients(kcal=100, iron_mg=2.1), "iron_mg")
    assert not is_source(_nutrients(kcal=60, iron_mg=0.1), "iron_mg")  # milk
    # fibre: 3 g per 100 g, or 1.5 g per 100 kcal for a watery vegetable
    assert is_source(_nutrients(kcal=344, fiber_g=3.4), "fiber_g")
    assert is_source(_nutrients(kcal=20, fiber_g=1.2), "fiber_g")
    assert not is_source(_nutrients(kcal=97, fiber_g=0.0), "fiber_g")  # fish
    # no threshold for a nutrient means never a source
    assert not is_source(_nutrients(kcal=100, sodium_mg=900), "sodium_mg")


def test_kidney_disease_takes_potassium_out_of_the_blood_pressure_list():
    assert finding_nutrients("hypertension") == ["potassium_mg", "fiber_g"]
    assert finding_nutrients("hypertension", ["hypertension", "chronic_kidney_disease"]) == ["fiber_g"]
    assert finding_nutrients("knee_osteoarthritis") == []


def _guide(conditions: list[str], sex: str = "female"):
    foods = load_foods()
    recipes = load_recipes(food_index(foods))
    habits = food_habits(recipes)
    exclusions = excluded_tags(conditions, age=45, sex=sex)
    allowed = habitual_foods(
        eaten_in_portions(recommendable_foods(filter_items(foods, exclusions.food_tags))), habits)
    nutrition = nutrient_targets(sex, "pregnancy" in conditions, [], conditions=conditions, age=45)
    guide = condition_food_guide(
        conditions, foods=foods, recipes=recipes, allowed_foods=allowed, habits=habits,
        meals_per_week=meals_per_week_map(allowed, habits, unknown=median_meals_per_week(habits)),
        portion_g=portion_map(allowed, habits), targets=nutrition["targets"],
        untracked=untracked_nutrients(foods), findings=nutrition["findings"],
        limits=nutrition["limits"])
    return {entry["condition"]: entry for entry in guide}, foods, exclusions


def test_each_condition_gets_its_own_eat_and_avoid_lists():
    guide, foods, exclusions = _guide(["hypertension", "diabetes", "high_cholesterol", "anemia",
                                       "knee_osteoarthritis"])
    by_id = food_index(foods)
    # knee osteoarthritis changes no food, so it gets no entry
    assert set(guide) == {"hypertension", "diabetes", "high_cholesterol", "anemia"}

    for condition, entry in guide.items():
        for food in entry["eat"]:
            # inside the patient's whole gate: nothing any condition excludes
            assert not set(food["tags"]) & exclusions.food_tags, (condition, food["name_en"])
            # and a real source of one of the condition's nutrients
            assert any(is_source(by_id[food["food_id"]].nutrients, n) for n in entry["nutrients"])
        for item in entry["avoid_foods"] + entry["avoid_dishes"]:
            assert set(item["reasons"]) <= set(entry["avoid_tags"]) and item["reasons"]

    assert guide["hypertension"]["avoid_tags"] == ["high_sodium"]
    assert guide["diabetes"]["avoid_foods"][0]["name_en"] == "Sugar, white"  # most used
    assert {"Milk Tea", "Black Tea"} <= {d["name_en"] for d in guide["diabetes"]["avoid_dishes"]}
    assert "Ghee, cow" in {f["name_en"] for f in guide["high_cholesterol"]["avoid_foods"]}
    # anaemia excludes nothing, and milk (0.1 mg iron) is no iron source
    assert guide["anemia"]["avoid_foods"] == [] and guide["anemia"]["avoid_dishes"] == []
    assert not any(f["name_en"].startswith("Milk") for f in guide["anemia"]["eat"])
    # without saturated fat data, fatty foods (coconut kernel) are offered
    # for no condition
    for entry in guide.values():
        assert not any("high_fat" in f["tags"] for f in entry["eat"])


def test_pregnancy_lists_what_to_avoid_even_with_nothing_to_add():
    guide, _, _ = _guide(["pregnancy"])
    entry = guide["pregnancy"]
    assert entry["eat"] == []
    assert {"Beef liver", "Chicken liver"} <= {f["name_en"] for f in entry["avoid_foods"]}
    assert "Spiced Beef Liver" in {d["name_en"] for d in entry["avoid_dishes"]}


def test_assessment_carries_the_guide(client):
    patient_id = client.post("/patients", json={
        "name": "Guide Patient", "sex": "female", "birth_year": 1980, "height_cm": 155,
    }).json()["id"]
    response = client.post(f"/patients/{patient_id}/visits", json={
        "weight_kg": 68,
        "biomarkers": {"fasting_glucose": 130, "systolic_bp": 150, "diastolic_bp": 95,
                       "hemoglobin": 10.0},
    })
    assert response.status_code == 201
    result = response.json()["result"]
    guide = {e["condition"]: e for e in result["nutrition"]["condition_foods"]}
    assert {"hypertension", "diabetes", "anemia"} <= set(guide)
    excluded = set(result["exclusions"]["food_tags"])
    for entry in guide.values():
        assert all(not set(f["tags"]) & excluded for f in entry["eat"])
