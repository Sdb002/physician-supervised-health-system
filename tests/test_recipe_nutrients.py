"""Computed per-serving nutrition vs hand-checked values and the source workbook.

Hand check for BDR-068 (Spinach Stir-fry, serves 4), per-100 g values from
bd_food.csv (spinach minerals from USDA FDC 168462 — see data/food/schema.md,
correction 4); vitamin C x the ingredient's USDA R6 retention factor:
  F216 spinach   450 g → kcal 117,    iron 12.195, vit C 21.2 x 4.5 x 0.85 = 81.09
  F153 onion      60 g → kcal 35.4,   iron 0.54,   vit C 4.5 x 0.6 x 0.85  = 2.295
  F134 garlic     12 g → kcal 17.64,  iron 0.192,  vit C 24.1 x 0.12 x 0.85 = 2.4582
  F287 red chilli  3 g → kcal 9.39,   iron 0.069,  vit C 47.4 x 0.03 x 1.0 = 1.422
  F318 nigella     2 g → kcal 11.38
  F672 oil        20 g → kcal 180
  F697 salt        3 g → kcal 0
  totals: kcal 370.81, iron 12.996, vit C 87.265 → per serving 92.70, 3.249, 21.82
"""

import csv

import pytest

from src.core.config import DATA_DIR
from src.diet.food_db import Food, food_index, load_foods
from src.diet.recipe import (
    _inherited_tags,
    added_salt_per_serving,
    load_recipes,
    per_serving_nutrients,
)

_NUTRIENTS = ("kcal", "protein_g", "carb_g", "fat_g", "fiber_g", "iron_mg",
              "calcium_mg", "zinc_mg", "folate_ug", "vit_a_ug", "vit_c_mg",
              "sodium_mg", "potassium_mg")


def _food(food_id: str, group: str = "other", tags: tuple = (), **nutrients) -> Food:
    base = {c: 0.0 for c in _NUTRIENTS}
    base.update(nutrients)
    return Food(food_id=food_id, name_en=food_id, name_bn="", food_group=group,
                nutrients=base, tags=tags)


@pytest.fixture(scope="module")
def foods():
    return food_index(load_foods())


@pytest.fixture(scope="module")
def recipes(foods):
    return {r.recipe_id: r for r in load_recipes(foods)}


def test_spinach_stirfry_matches_hand_check(recipes):
    r = recipes["BDR-068"]
    assert r.per_serving["kcal"] == pytest.approx(92.70, abs=0.05)
    assert r.per_serving["iron_mg"] == pytest.approx(3.249, abs=0.01)
    assert r.per_serving["vit_c_mg"] == pytest.approx(21.82, abs=0.01)


def test_dal_matches_hand_check(recipes):
    # BDR-021 Thin Red Lentil Soup, serves 4: 150 g dried red lentil (317 kcal,
    # 27.7 g protein /100 g), 15 g mustard oil, onion, garlic, spices, salt
    r = recipes["BDR-021"]
    assert r.per_serving["kcal"] == pytest.approx(674.97 / 4, abs=0.05)
    assert r.per_serving["protein_g"] == pytest.approx(43.871 / 4, abs=0.05)


def test_oil_exclusion_tag_not_inherited_below_weight_share(recipes):
    # oil is 15/250 of BDR-021's weight — high_fat must NOT be inherited
    assert "high_fat" not in recipes["BDR-021"].tags
    assert "vegan" in recipes["BDR-021"].tags


def test_runtime_nutrition_reproduces_the_recipe_workbook(recipes):
    """For every recipe that uses no corrected food, the app's runtime
    calculation must equal the source workbook's own per-serving values —
    same method (FAO/INFOODS, USDA retention factors), same numbers."""
    with open(DATA_DIR / "food" / "corrections_log.csv", encoding="utf-8-sig", newline="") as f:
        corrected = {row["food_id"] for row in csv.DictReader(f)}
    with open(DATA_DIR / "recipe" / "raw" / "bd_recipes_250.csv", encoding="utf-8-sig",
              newline="") as f:
        source = {row["recipe_id"]: row for row in csv.DictReader(f)}
    columns = {"kcal": "energy_kcal_per_serving", "protein_g": "protein_g_per_serving",
               "fat_g": "fat_g_per_serving", "iron_mg": "iron_mg_per_serving",
               "sodium_mg": "sodium_mg_per_serving", "vit_a_ug": "vit_a_ug_rae_per_serving",
               "vit_c_mg": "vit_c_mg_per_serving"}
    checked = 0
    for rid, recipe in recipes.items():
        if {fid for fid, _ in recipe.ingredients} & corrected:
            continue
        checked += 1
        for col, source_col in columns.items():
            assert recipe.per_serving[col] == pytest.approx(
                float(source[rid][source_col]), abs=0.011
            ), f"{rid} {col}"
    assert checked >= 100


def test_recipe_metadata_steps_and_ingredient_lines(recipes):
    rice = recipes["BDR-001"]
    assert rice.weekly_frequency_score == 10
    assert rice.frequency_tier == "Daily staple"
    assert rice.category == "Rice & Grain"
    assert rice.serving_size_g == pytest.approx(243)
    assert rice.steps and rice.steps[0].startswith("Wash the rice")
    assert rice.ingredient_lines[0]["household_measure"] == "1.6 cups raw parboiled rice"
    assert rice.group_shares == {"grain": 1.0}


def test_added_sugar_energy_share_inherits_high_sugar(recipes):
    # BDR-133 rice pudding (payesh): sugar is 120 of 1758 g — far below the
    # 25% weight rule — but supplies ~25% of the energy (WHO: >10%)
    assert "high_sugar" in recipes["BDR-133"].tags


def test_added_sugar_rule_on_synthetic_recipe():
    foods = {
        "MILK": _food("MILK", "dairy", kcal=63),
        "SUGAR": _food("SUGAR", "sweet", ("high_sugar", "added_sugar"), kcal=398),
    }
    sweet = [("MILK", 1000.0), ("SUGAR", 30.0)]    # 119 of 749 kcal = 16%
    plain = [("MILK", 1000.0), ("SUGAR", 10.0)]    # 40 of 670 kcal = 6%
    assert "high_sugar" in _inherited_tags(sweet, per_serving_nutrients(sweet, 4, foods), foods)
    assert "high_sugar" not in _inherited_tags(plain, per_serving_nutrients(plain, 4, foods), foods)


def test_retention_factor_applies_to_vitamins_only():
    foods = {"VEG": _food("VEG", "vegetable", kcal=30, vit_c_mg=100, vit_a_ug=200, iron_mg=2)}
    per_serving = per_serving_nutrients(
        [("VEG", 100.0)], 1, foods, retention=[{"vit_c_mg": 0.5, "vit_a_ug": 0.9}]
    )
    assert per_serving["vit_c_mg"] == pytest.approx(50)
    assert per_serving["vit_a_ug"] == pytest.approx(180)
    assert per_serving["iron_mg"] == pytest.approx(2)  # minerals are not lost
    assert per_serving["kcal"] == pytest.approx(30)


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


def test_recipe_reports_the_salt_it_adds(recipes):
    # BDR-068 Spinach Stir-fry: 3 g salt (39340 mg sodium per 100 g) in 4 servings
    spinach = recipes["BDR-068"]
    assert spinach.salt_g == pytest.approx(0.75)
    assert spinach.salt_sodium_mg == pytest.approx(295.05)
    assert spinach.salt_sodium_mg < spinach.per_serving["sodium_mg"]
    # plain boiled rice is cooked without any
    assert recipes["BDR-001"].salt_g == 0 and recipes["BDR-001"].salt_sodium_mg == 0


def test_only_salt_counts_as_added_salt():
    foods = {
        "SALT": _food("SALT", sodium_mg=39340),
        "BAKING": _food("BAKING", sodium_mg=11800),      # baking powder: salty, not salt
        "SHUTKI": _food("SHUTKI", "fish", sodium_mg=3500),  # salted dried fish
    }
    grams, sodium_mg = added_salt_per_serving(
        [("SALT", 4.0), ("BAKING", 5.0), ("SHUTKI", 50.0)], 2, foods)
    assert grams == pytest.approx(2.0)
    assert sodium_mg == pytest.approx(786.8)


def test_recipe_with_missing_ingredient_is_skipped(foods, tmp_path):
    recipes_csv = tmp_path / "recipes.csv"
    ingredients_csv = tmp_path / "ingredients.csv"
    recipes_csv.write_text(
        "recipe_id,name_en,name_bn,servings,meal_type,tags,source\n"
        "BDR-900,Ghost recipe,,2,lunch,,TEST\n",
        encoding="utf-8",
    )
    ingredients_csv.write_text(
        "recipe_id,food_id,qty_g\nBDR-900,F999,100\n", encoding="utf-8"
    )
    loaded = load_recipes(foods, recipes_csv, ingredients_csv)
    assert loaded == []


def test_minimal_recipe_files_still_load(foods, tmp_path):
    """Optional columns (frequency, retention factors, steps) may be absent."""
    recipes_csv = tmp_path / "recipes.csv"
    ingredients_csv = tmp_path / "ingredients.csv"
    recipes_csv.write_text(
        "recipe_id,name_en,name_bn,servings,meal_type,tags,source\n"
        "BDR-901,Plain spinach,,2,lunch,,TEST\n",
        encoding="utf-8",
    )
    ingredients_csv.write_text("recipe_id,food_id,qty_g\nBDR-901,F216,200\n", encoding="utf-8")
    [recipe] = load_recipes(foods, recipes_csv, ingredients_csv)
    assert recipe.weekly_frequency_score is None
    assert recipe.steps == ()
    assert recipe.per_serving["iron_mg"] == pytest.approx(2.71)
