"""Which foods get recommended on their own, and how they're ranked.

Regression coverage for the reported "the food recommendation sucks": per
100 g scoring over the whole food table put rice bran, frog legs, green
chilli, raw-and-boiled duplicates of one leafy green and three sweet-potato
leaf cultivars at the top of "foods that suit your plan".
"""

from src.diet.food_db import NUTRIENT_COLUMNS, Food, display_name, food_index, load_foods
from src.diet.habits import (
    FoodHabit,
    familiarity_map,
    food_habits,
    habitual_foods,
    variant_key,
)
from src.diet.matcher import rank_foods
from src.diet.recipe import Recipe, load_recipes


def _food(food_id: str, group: str, kcal: float = 50, name_bn: str = "", name_en: str = "",
          **nutrients) -> Food:
    values = {c: 0.0 for c in NUTRIENT_COLUMNS}
    values["kcal"] = kcal
    values.update(nutrients)
    return Food(food_id=food_id, name_en=name_en or food_id, name_bn=name_bn,
                food_group=group, nutrients=values)


def _recipe(recipe_id: str, frequency: int, ingredients, servings: int = 4) -> Recipe:
    return Recipe(recipe_id=recipe_id, name_en=recipe_id, name_bn="", servings=servings,
                  meal_type=("lunch",), tags=(), source="test",
                  ingredients=tuple(ingredients), per_serving={},
                  weekly_frequency_score=frequency)


def test_habits_read_familiarity_and_portion_off_the_dishes():
    habits = food_habits([
        _recipe("plain_rice", 10, [("rice", 400)]),
        _recipe("khichuri", 4, [("rice", 200), ("lentil", 120), ("chilli", 8)]),
    ])
    assert habits["rice"].familiarity == 10  # the most common dish using it
    assert habits["rice"].typical_g == 75  # median of 100 g and 50 g per serving
    assert habits["chilli"].typical_g == 2


def test_only_foods_eaten_in_portions_are_recommended():
    habits = {
        "lentil": FoodHabit(familiarity=9, typical_g=30, dish_count=12),
        "chilli": FoodHabit(familiarity=10, typical_g=3, dish_count=80),
        "lemon": FoodHabit(familiarity=5, typical_g=4, dish_count=6),
    }
    foods = [
        _food("lentil", "legume"),
        _food("chilli", "vegetable"),  # a seasoning, used by the gram
        _food("rice_bran", "grain"),  # in the table, in no dish
        _food("guava", "fruit", kcal=68),  # whole fruit, eaten as is
        _food("lemon", "fruit", kcal=30),  # fruit used as a sour seasoning
        _food("orange_juice", "fruit", kcal=45, name_en="Orange juice, raw"),
        _food("dates_dried", "fruit", kcal=280),  # not fresh fruit
    ]
    kept = {f.food_id for f in habitual_foods(foods, habits)}
    assert kept == {"lentil", "guava"}


def test_variants_of_one_food_share_a_key():
    raw = _food("a", "vegetable", name_bn="নটে শাক")
    boiled = _food("b", "vegetable", name_bn="নটে শাক (সিদ্ধ)")
    cultivar = _food("c", "vegetable", name_bn="মিষ্টি আলু শাক (এসপি-৪)")
    plain = _food("d", "vegetable", name_bn="মিষ্টি আলু শাক")
    assert variant_key(raw) == variant_key(boiled)
    assert variant_key(cultivar) == variant_key(plain)
    assert variant_key(raw) != variant_key(plain)


def test_ranking_lists_each_everyday_food_once():
    foods = [
        _food("raw", "vegetable", name_bn="নটে শাক", iron_mg=8),
        _food("boiled", "vegetable", name_bn="নটে শাক (সিদ্ধ)", iron_mg=7),
        _food("other", "vegetable", name_bn="লাল শাক", iron_mg=5),
    ]
    ranked = rank_foods(foods, ["iron_mg"], {"iron_mg": 18})
    assert [f["food_id"] for f in ranked] == ["raw", "other"]


def test_ranking_caps_entries_per_food_group():
    foods = [_food(f"veg{i}", "vegetable", name_bn=f"শাক {i}", iron_mg=10 - i) for i in range(5)]
    foods.append(_food("lentil", "legume", name_bn="মসুর", iron_mg=1))
    ranked = rank_foods(foods, ["iron_mg"], {"iron_mg": 18}, per_group=2)
    groups = [f["food_group"] for f in ranked]
    assert groups.count("vegetable") == 2 and "legume" in groups


def test_ranking_weighs_familiarity_and_usual_portion():
    # per 100 g sesame wins on iron; per usual portion (10 g vs 80 g) and
    # familiarity (a festive sweet vs everyday shak) the leafy green does
    foods = [_food("sesame", "other", name_bn="তিল", iron_mg=15),
             _food("shak", "vegetable", name_bn="লাল শাক", iron_mg=5)]
    ranked = rank_foods(foods, ["iron_mg"], {"iron_mg": 18},
                        familiarity={"sesame": 2, "shak": 6},
                        portion_g={"sesame": 10, "shak": 80})
    assert ranked[0]["food_id"] == "shak"


def test_display_name_drops_table_noise():
    assert display_name("Guava, green, raw") == "Guava, green"
    assert display_name("Milk, cow, whole fat (pasteurized, UTH)") == "Milk, cow, whole fat"


def test_real_dataset_never_suggests_unused_foods_or_seasonings():
    foods = load_foods()
    habits = food_habits(load_recipes(food_index(foods)))
    kept = {f.name_en for f in habitual_foods(foods, habits)}
    for name in ("Rice, bran, raw", "Frog, legs, raw", "Chilli, green, with seeds, raw",
                 "Orange juice, raw (unsweetened)", "Dates, dried"):
        assert name not in kept, name
    for name in ("Lentil, dried, raw", "Guava, green, raw"):
        assert name in kept, name
    # every kept non-fruit food is cooked with by households
    assert all(f.food_id in habits for f in habitual_foods(foods, habits)
               if f.food_group != "fruit")
    assert familiarity_map(foods[:1], habits, unknown=5)
