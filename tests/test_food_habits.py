"""Which foods get recommended on their own, and how they're ranked.

Regression coverage for the reported "the food recommendation sucks": per
100 g scoring over the whole food table put rice bran, frog legs, green
chilli, raw-and-boiled duplicates of one leafy green and three sweet-potato
leaf cultivars at the top of "foods that suit your plan".
"""

import pytest

from src.diet.food_db import (
    NUTRIENT_COLUMNS,
    Food,
    display_name,
    eaten_in_portions,
    food_index,
    load_foods,
    recommendable_foods,
)
from src.diet.habits import (
    MAIN_MEALS_PER_WEEK,
    MEALS_PER_WEEK_MIDPOINT,
    FoodHabit,
    familiarity_map,
    food_habits,
    habitual_foods,
    meals_per_week,
    meals_per_week_map,
    median_meals_per_week,
    portion_map,
    variant_key,
)
from src.diet.matcher import meal_frequency_weight, rank_foods
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


def test_ranking_weighs_meals_per_week_and_usual_portion():
    # per 100 g sesame wins on iron; per usual portion (10 g vs 80 g) and
    # how often it is eaten (a festive sweet vs everyday shak) the leafy
    # green does
    foods = [_food("sesame", "other", name_bn="তিল", iron_mg=15),
             _food("shak", "vegetable", name_bn="লাল শাক", iron_mg=5)]
    ranked = rank_foods(foods, ["iron_mg"], {"iron_mg": 18},
                        meals_per_week={"sesame": 0.1, "shak": 2.5},
                        portion_g={"sesame": 10, "shak": 80})
    assert ranked[0]["food_id"] == "shak"


def test_more_frequent_food_scores_more_in_proportion():
    # same nutrients, same portion: the food eaten at twice the meals
    # scores twice as high, and a once-a-week fish loses to daily dal
    foods = [_food("fish", "fish", name_bn="কাতলা", protein_g=20),
             _food("dal", "legume", name_bn="মসুর", protein_g=20)]
    # a large fit, so the 3-decimal rounding of the reported score stays
    # well inside the tolerance
    ranked = rank_foods(foods, ["protein_g"], {"protein_g": 2},
                        meals_per_week={"fish": 1.5, "dal": 13.0})
    assert [f["food_id"] for f in ranked] == ["dal", "fish"]
    assert ranked[0]["score"] / ranked[1]["score"] == pytest.approx(13.0 / 1.5, rel=1e-2)
    assert meal_frequency_weight(21) == 1.0 and meal_frequency_weight(40) == 1.0
    assert meal_frequency_weight(0) == 0.0


def test_meals_per_week_combines_dishes_without_passing_21():
    assert meals_per_week([]) == 0.0
    assert meals_per_week([14.0]) == pytest.approx(14.0)
    # two dishes a week each: almost four meals, a little less because
    # they sometimes fall on the same meal
    assert 3.5 < meals_per_week([2.0, 2.0]) < 4.0
    assert meals_per_week([14.0] * 200) <= MAIN_MEALS_PER_WEEK


def test_habits_count_only_portion_sized_uses_as_meals():
    habits = food_habits([
        _recipe("plain_rice", 10, [("rice", 400)]),  # 100 g a serving
        _recipe("dal", 9, [("lentil", 120)]),  # 30 g a serving
        _recipe("pakora", 3, [("lentil", 20)]),  # 5 g a serving: batter, not dal
    ])
    assert habits["rice"].meals_per_week == pytest.approx(MEALS_PER_WEEK_MIDPOINT[10])
    assert habits["lentil"].meals_per_week == pytest.approx(MEALS_PER_WEEK_MIDPOINT[9])
    # fruit no dish uses takes the median of the foods that have a figure
    foods = [_food("rice", "grain"), _food("lentil", "legume"), _food("guava", "fruit")]
    meals = meals_per_week_map(foods, habits, unknown=median_meals_per_week(habits))
    assert meals["guava"] == pytest.approx((14.0 + 7.0) / 2)


def test_real_dataset_ranks_everyday_foods_first():
    # the reported "rank the foods by how often people eat them": with no
    # nutrient emphasized (nutrient density), the foods of everyday meals
    # lead and foods one weekly dish uses do not
    foods = load_foods()
    habits = food_habits(load_recipes(food_index(foods)))
    pool = habitual_foods(eaten_in_portions(recommendable_foods(foods)), habits)
    names = [display_name(f.name_en) for f in pool]
    assert not any(name.startswith("Onion") for name in names)  # a seasoning
    meals = meals_per_week_map(pool, habits, unknown=median_meals_per_week(habits))
    by_name = {f.name_en: meals[f.food_id] for f in pool}
    assert by_name["Lentil, dried, raw"] > 10 and by_name["Egg, chicken, farmed, raw"] > 10
    assert by_name["Catla, raw"] < 2
    ranked = rank_foods(pool, [], {}, top_n=10, meals_per_week=meals, per_group=3,
                        portion_g=portion_map(pool, habits))
    top = [f["name_en"] for f in ranked]
    for everyday in ("Egg, chicken, farmed", "Lentil, dried"):
        assert everyday in top, top
    for rare in ("Bottle gourd leaves", "Gourd, ash", "Buttermilk, fluid, low fat"):
        assert rare not in top, top


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
