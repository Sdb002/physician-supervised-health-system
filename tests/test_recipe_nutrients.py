"""Computed per-serving nutrition vs hand-checked values.

Hand check for R002 (Spinach stir-fry, serves 2), FCT-BD dataset (iron_mg
corrected to USDA FoodData Central's ~2.7 mg/100g — see data/food/schema.md):
  F081 spinach 300 g  → kcal 26×3 = 78, iron 2.7×3 = 8.1, sodium 0.9×3 = 2.7
  F235 oil      10 g  → kcal 900×0.1 = 90, iron 0.1×0.1 = 0.01, sodium 0
  totals: kcal 168, iron 8.11, sodium 2.7  → per serving: 84, 4.055, 1.35
"""

import pytest

from src.diet.food_db import Food, food_index, load_foods
from src.diet.recipe import (
    _inherited_tags,
    load_recipes,
    per_serving_nutrients,
)


@pytest.fixture(scope="module")
def recipes():
    foods = food_index(load_foods())
    return {r.recipe_id: r for r in load_recipes(foods)}


def test_spinach_stirfry_matches_hand_check(recipes):
    r = recipes["R002"]
    assert r.per_serving["kcal"] == pytest.approx(84.0, abs=0.05)
    assert r.per_serving["iron_mg"] == pytest.approx(4.055, abs=0.05)
    assert r.per_serving["sodium_mg"] == pytest.approx(1.35, abs=0.05)


def test_dal_matches_hand_check(recipes):
    # R001: boiled lentils 400 g + oil 10 g, serves 4
    r = recipes["R001"]
    assert r.per_serving["kcal"] == pytest.approx((155 * 4 + 90) / 4, abs=0.05)
    assert r.per_serving["protein_g"] == pytest.approx(13.6, abs=0.05)


def test_oil_exclusion_tag_not_inherited_below_weight_share(recipes):
    # oil is 10/410 of R001's weight — high_fat must NOT be inherited
    assert "high_fat" not in recipes["R001"].tags
    assert "vegetarian" in recipes["R001"].tags


def test_sodium_cap_inherits_high_sodium_tag():
    shutki = Food(
        food_id="FX", name_en="Dried fish", name_bn="", food_group="fish",
        nutrients={"kcal": 270, "protein_g": 55, "carb_g": 0, "fat_g": 4,
                   "fiber_g": 0, "iron_mg": 4.5, "calcium_mg": 1500, "zinc_mg": 3,
                   "folate_ug": 20, "vit_a_ug": 25, "vit_c_mg": 0,
                   "sodium_mg": 3500, "potassium_mg": 900},
        tags=("high_protein", "high_sodium"),
    )
    ingredients = [("FX", 50.0)]
    per_serving = per_serving_nutrients(ingredients, 1, {"FX": shutki})
    assert per_serving["sodium_mg"] == pytest.approx(1750)
    tags = _inherited_tags(ingredients, per_serving, {"FX": shutki})
    assert "high_sodium" in tags


def test_recipe_with_missing_ingredient_is_skipped(tmp_path):
    foods = food_index(load_foods())
    recipes_csv = tmp_path / "recipes.csv"
    ingredients_csv = tmp_path / "ingredients.csv"
    recipes_csv.write_text(
        "recipe_id,name_en,name_bn,servings,meal_type,tags,source\n"
        "R900,Ghost recipe,,2,lunch,,DEMO\n",
        encoding="utf-8",
    )
    ingredients_csv.write_text(
        "recipe_id,food_id,qty_g\nR900,F999,100\n", encoding="utf-8"
    )
    loaded = load_recipes(foods, recipes_csv, ingredients_csv)
    assert loaded == []
