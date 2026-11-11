"""Dish-based weekly meal plan (engines 0.3.0 and 0.4.0), and the cooking
salt that keeps each day under the sodium limit (0.6.0).

Regression coverage for the reported "the food recommendation sucks": the
0.1/0.2 planner filled food-group slots straight from the food table, so
plans read "Rice, bran, raw; Soybean, dried, raw; Frog, legs, raw 280 g" and
the same per-100 g density winner turned up for every patient. Plans are now
composed from household dishes, and these tests pin the rules that keep them
realistic and safe.
"""

from dataclasses import replace

import pytest

from src.diet.food_db import NUTRIENT_COLUMNS, Food
from src.diet.meal_plan import (
    MAX_VIT_A_UG_PER_SERVING,
    MAX_WEEKLY_SERVINGS,
    MEAL_COURSES,
    MIN_DAYS_BETWEEN_REPEATS,
    WEEKDAYS,
    build_meal_plan,
    is_plain_staple,
    ration_salt,
)
from src.diet.recipe import Recipe


def _nutrients(kcal: float, **values) -> dict:
    base = {c: 0.0 for c in NUTRIENT_COLUMNS}
    base["kcal"] = kcal
    base.update(values)
    return base


def _dish(recipe_id: str, category: str, kcal: float, *, meals=("lunch", "dinner"),
          grain: float = 0.0, tags=(), ingredients=(), serving_g: float = 150.0,
          frequency: int = 5, **nutrients) -> Recipe:
    return Recipe(
        recipe_id=recipe_id, name_en=recipe_id, name_bn="", servings=1,
        meal_type=tuple(meals), tags=tuple(tags), source="test",
        ingredients=tuple(ingredients), per_serving=_nutrients(kcal, **nutrients),
        category=category, weekly_frequency_score=frequency,
        serving_size_g=serving_g, group_shares={"grain": grain} if grain else {},
    )


def _fruit(food_id: str, kcal: float, **nutrients) -> Food:
    return Food(food_id=food_id, name_en=f"{food_id}, raw", name_bn="", food_group="fruit",
                nutrients=_nutrients(kcal, **nutrients))


def _kitchen() -> list[Recipe]:
    """A small household repertoire: enough for every course of every meal."""
    return [
        _dish("rice", "Rice & Grain", 275, grain=1.0, serving_g=243, frequency=10, protein_g=6),
        _dish("khichuri", "Rice & Grain", 420, grain=0.46, frequency=9, protein_g=14),
        _dish("ruti", "Bread & Pitha", 267, meals=("breakfast", "dinner"), grain=0.99,
              serving_g=108, frequency=8, protein_g=9, fiber_g=4),
        _dish("dal", "Dal", 169, frequency=9, protein_g=9, fiber_g=3),
        _dish("rohu", "Fish", 277, frequency=6, protein_g=25),
        _dish("chicken", "Meat", 305, frequency=5, protein_g=24),
        _dish("omelette", "Egg", 188, meals=("breakfast",), frequency=6, protein_g=12),
        _dish("shak", "Leafy Green", 94, frequency=6, fiber_g=3, iron_mg=3),
        _dish("bhaji", "Vegetable", 120, meals=("breakfast", "lunch", "dinner"),
              frequency=5, fiber_g=2),
        _dish("payesh", "Sweet", 317, meals=("lunch", "dinner"), frequency=10, protein_g=30),
        _dish("milk_tea", "Beverage", 109, frequency=10, protein_g=30),
    ]


def _plan(recipes=None, fruits=None, target_kcal=1800, **kwargs):
    return build_meal_plan(
        recipes if recipes is not None else _kitchen(),
        fruits if fruits is not None else [_fruit("guava", 68, vit_c_mg=228, fiber_g=5)],
        target_kcal, targets={"protein_g": 50, "fiber_g": 25, "iron_mg": 18}, emphasize=[],
        **kwargs,
    )


def _day(plan, index=0):
    return plan["days"][index]["meals"]


def _all_items(plan):
    return [item for day in plan["days"] for items in day["meals"].values() for item in items]


def _courses(plan, meal):
    return {item.get("course"): item for item in _day(plan)[meal]}


def test_lunch_is_rice_dal_main_and_vegetable():
    lunch = _courses(_plan(), "lunch")
    assert [c for c, _ in MEAL_COURSES["lunch"]] == list(lunch)
    assert lunch["staple"]["recipe_id"] == "rice"
    assert lunch["dal"]["recipe_id"] == "dal"
    assert lunch["main"]["category"] in ("Fish", "Meat", "Egg")
    assert lunch["vegetable"]["category"] in ("Leafy Green", "Vegetable", "Bhorta")


def test_staple_course_takes_plain_staples_only():
    # khichuri is a whole meal (rice + lentils); beside dal it would double up
    staples = [item for item in _all_items(_plan()) if item.get("course") == "staple"]
    assert staples and all(item["recipe_id"] != "khichuri" for item in staples)
    assert not is_plain_staple(_kitchen()[1])


def test_sweets_and_sugary_drinks_are_never_planned():
    planned = {item.get("recipe_id") for item in _all_items(_plan())}
    assert "payesh" not in planned and "milk_tea" not in planned


def test_high_sugar_dish_is_never_planned():
    kitchen = _kitchen() + [_dish("sweet_dal", "Dal", 150, frequency=10, protein_g=40,
                                  tags=("high_sugar",))]
    planned = {item.get("recipe_id") for item in _all_items(_plan(kitchen))}
    assert "sweet_dal" not in planned


def test_dish_over_the_vitamin_a_upper_limit_is_never_planned():
    # a liver curry: iron-dense enough to win the main course for anemia,
    # but one serving is over the 3000 ug/day preformed vitamin A UL
    liver = _dish("liver", "Meat", 220, frequency=10, iron_mg=30, protein_g=30,
                  vit_a_ug=MAX_VIT_A_UG_PER_SERVING + 300)
    plan = build_meal_plan(_kitchen() + [liver], [_fruit("guava", 68)], 1800,
                           targets={"iron_mg": 27}, emphasize=["iron_mg"])
    planned = {item.get("recipe_id") for item in _all_items(plan)}
    assert "liver" not in planned


def test_main_and_vegetable_dishes_are_not_repeated_within_a_day():
    for day in _plan()["days"]:
        non_staple = [item["recipe_id"] for meal in ("breakfast", "lunch", "dinner")
                      for item in day["meals"][meal] if item["course"] != "staple"]
        assert len(non_staple) == len(set(non_staple))


def test_key_ingredient_is_not_repeated_when_there_is_a_choice():
    potato = Food("potato", "Potato, raw", "", "vegetable", _nutrients(77))
    cabbage = Food("cabbage", "Cabbage, raw", "", "vegetable", _nutrients(25))
    kitchen = _kitchen() + [
        _dish("aloo_bhaji", "Vegetable", 150, meals=("breakfast", "lunch", "dinner"),
              frequency=8, fiber_g=9, ingredients=(("potato", 100),)),
        _dish("aloo_curry", "Vegetable", 150, frequency=8, fiber_g=8,
              ingredients=(("potato", 100),)),
        _dish("cabbage_bhaji", "Vegetable", 140, frequency=5, fiber_g=2,
              ingredients=(("cabbage", 100),)),
    ]
    plan = build_meal_plan(kitchen, [_fruit("guava", 68)], 1800, targets={"fiber_g": 25},
                           emphasize=["fiber_g"],
                           foods_by_id={"potato": potato, "cabbage": cabbage})
    for day in plan["days"]:
        planned = {item.get("recipe_id") for items in day["meals"].values() for item in items}
        assert not {"aloo_bhaji", "aloo_curry"} <= planned  # potato once a day, not twice


def test_eggs_are_served_whole():
    # a low target forces side dishes down to fractional servings
    plan = _plan(target_kcal=1200)
    eggs = [item for item in _all_items(plan) if item.get("category") == "Egg"]
    assert eggs and all(item["servings"] == 1.0 for item in eggs)


def test_portions_track_the_energy_target():
    for target in (1300, 1800, 2400):
        plan = _plan(target_kcal=target)
        assert abs(plan["totals"]["kcal"] - target) / target < 0.2  # the average day
        for day in plan["days"]:
            assert abs(day["totals"]["kcal"] - target) / target < 0.25


def test_fruit_snack_is_a_realistic_portion():
    snack = _day(_plan(fruits=[_fruit("papaya", 32)]))["snack"]
    assert len(snack) == 1
    assert 80 <= snack[0]["qty_g"] <= 200
    assert snack[0]["name_en"] == "papaya"  # shown without the table's ", raw"


def test_untracked_nutrient_is_reported_instead_of_zero_coverage():
    plan = build_meal_plan(_kitchen(), [_fruit("guava", 68)], 1800,
                           targets={"protein_g": 50, "folate_ug": 400}, emphasize=[],
                           untracked=frozenset({"folate_ug"}))
    assert "folate_ug" not in plan["coverage"]
    assert plan["untracked"] == ["folate_ug"]


def test_an_untracked_nutrient_never_leaves_the_recipe_id_to_pick_the_dish():
    # reported: an anaemic man has his iron by dinner, which left folate - a
    # nutrient no food has a value for - as the only thing emphasized. Every
    # dish scored 0 on it, so the first recipe id won the course and the
    # week's snacks came out in alphabetical order.
    kitchen = [
        _dish("rice", "Rice & Grain", 275, grain=1.0, serving_g=243, frequency=10),
        _dish("ruti", "Bread & Pitha", 267, meals=("breakfast",), grain=0.99, serving_g=108),
        _dish("omelette", "Egg", 188, meals=("breakfast",), protein_g=12),
        _dish("dal", "Dal", 169, meals=("lunch",), protein_g=9),
        _dish("beef", "Meat", 300, meals=("lunch",), iron_mg=40, protein_g=24),
        _dish("shak", "Leafy Green", 94, meals=("lunch",), iron_mg=3),
        _dish("a_thin_fish_broth", "Fish", 260, meals=("dinner",), protein_g=4),
        _dish("b_fish_curry", "Fish", 260, meals=("dinner",), protein_g=26),
        _dish("bhaji", "Vegetable", 120, meals=("dinner",), fiber_g=2),
    ]
    fruits = [_fruit("apple", 60, fiber_g=1), _fruit("guava", 68, fiber_g=5)]
    plan = build_meal_plan(kitchen, fruits, 1800, targets={"iron_mg": 8, "folate_ug": 400},
                           emphasize=["iron_mg", "folate_ug"],
                           untracked=frozenset({"folate_ug"}))
    # lunch's beef alone is over the iron the day needs...
    assert plan["days"][0]["totals"]["iron_mg"] >= 1.5 * 8
    # ...so dinner and the snack go to the nutrient-dense choice, not the first id
    assert _courses(plan, "dinner")["main"]["recipe_id"] == "b_fish_curry"
    assert _day(plan)["snack"][0]["food_id"] == "guava"


def test_the_plan_covers_a_week_starting_saturday():
    plan = _plan()
    assert [day["weekday"] for day in plan["days"]] == list(WEEKDAYS)
    assert WEEKDAYS[0] == "saturday" and len(plan["days"]) == 7
    assert [day["day"] for day in plan["days"]] == list(range(1, 8))


def _big_kitchen() -> list[Recipe]:
    """Enough choice per course for the weekly variety rules to bite."""
    kitchen = [
        _dish("rice", "Rice & Grain", 275, grain=1.0, serving_g=243, frequency=10, protein_g=6),
        _dish("ruti", "Bread & Pitha", 267, meals=("breakfast", "dinner"), grain=0.99,
              serving_g=108, frequency=8, protein_g=9),
    ]
    for i in range(8):
        kitchen += [
            _dish(f"dal{i}", "Dal", 170, frequency=9 - i % 3, protein_g=9 - i * 0.5),
            _dish(f"fish{i}", "Fish", 260, frequency=6, protein_g=25 - i),
            _dish(f"meat{i}", "Meat", 300, frequency=5, protein_g=24 - i),
            _dish(f"shak{i}", "Leafy Green", 95, frequency=6, protein_g=3 - i * 0.2),
            _dish(f"veg{i}", "Vegetable", 120, frequency=5, protein_g=2 - i * 0.1),
            _dish(f"egg{i}", "Egg", 180, meals=("breakfast",), frequency=6, protein_g=12 - i),
        ]
    return kitchen


def test_a_week_varies_its_dishes_and_spaces_any_repeat():
    fruits = [_fruit(f"fruit{i}", 60, vit_c_mg=50 - i) for i in range(5)]
    plan = build_meal_plan(_big_kitchen(), fruits, 1800, targets={"protein_g": 50},
                           emphasize=[])
    served: dict[str, list[int]] = {}
    for index, day in enumerate(plan["days"]):
        for items in day["meals"].values():
            for item in items:
                if item.get("course") != "staple":
                    served.setdefault(item.get("recipe_id") or item["food_id"], []).append(index)
    for days in served.values():
        assert len(days) <= MAX_WEEKLY_SERVINGS
        assert all(b - a >= MIN_DAYS_BETWEEN_REPEATS for a, b in zip(days, days[1:]))
    # with eight choices per course, no dal is repeated at all
    dals = [item["recipe_id"] for day in plan["days"] for item in day["meals"]["lunch"]
            if item["course"] == "dal"]
    assert len(set(dals)) == 7


def test_the_staple_may_repeat_every_day():
    plan = build_meal_plan(_big_kitchen(), [_fruit("guava", 68)], 1800,
                           targets={"protein_g": 50}, emphasize=[])
    lunch_staples = {item["recipe_id"] for day in plan["days"]
                     for item in day["meals"]["lunch"] if item["course"] == "staple"}
    assert lunch_staples == {"rice"}


def test_plan_lines_report_carbohydrate_fat_and_sodium():
    # reviewers could not check carbohydrate per meal, or the fat and sodium
    # of a dish, from weights and energy alone
    kitchen = [
        _dish("rice", "Rice & Grain", 275, grain=1.0, serving_g=243, frequency=10,
              carb_g=61, fat_g=0.5, sodium_mg=2),
        _dish("ruti", "Bread & Pitha", 267, meals=("breakfast", "dinner"), grain=0.99,
              serving_g=108, frequency=8, carb_g=50, fat_g=4, sodium_mg=210),
        _dish("dal", "Dal", 169, frequency=9, carb_g=22, fat_g=5, sodium_mg=400),
        _dish("rohu", "Fish", 277, frequency=6, carb_g=8, fat_g=16, sodium_mg=520),
        _dish("omelette", "Egg", 188, meals=("breakfast",), frequency=6,
              carb_g=3, fat_g=14, sodium_mg=495),
        _dish("shak", "Leafy Green", 94, frequency=6, carb_g=6, fat_g=6, sodium_mg=360),
    ]
    plan = _plan(recipes=kitchen, fruits=[_fruit("guava", 68, carb_g=14, sodium_mg=2)])
    for day in plan["days"]:
        lines = [item for items in day["meals"].values() for item in items]
        for nutrient in ("carb_g", "fat_g", "sodium_mg"):
            assert all(nutrient in item for item in lines)
            # the lines add up to the day's total, within their rounding
            assert abs(sum(item[nutrient] for item in lines) - day["totals"][nutrient]) <= 1.0
    breakfast = _courses(plan, "breakfast")
    assert breakfast["staple"]["carb_g"] == 50 * breakfast["staple"]["servings"]


def test_a_dish_reports_the_fat_it_is_cooked_in():
    korma = Recipe(
        recipe_id="korma", name_en="korma", name_bn="", servings=1, meal_type=("lunch",),
        tags=(), source="test", ingredients=(), per_serving=_nutrients(300, fat_g=22),
        category="Meat", serving_size_g=200, cooking_fat_g=12.0,
    )
    plan = _plan(recipes=[*_kitchen(), korma])
    served = [item for item in _all_items(plan) if item.get("recipe_id") == "korma"]
    assert served
    assert all(item["cooking_fat_g"] == round(12.0 * item["servings"], 1) for item in served)
    # a single food has no recipe, so no cooking fat to report
    assert all("cooking_fat_g" not in item for item in _all_items(plan) if "food_id" in item)


# sodium in a gram of table salt (food table: 39340 mg per 100 g)
_SODIUM_MG_PER_G_SALT = 393.4


def _salted(recipe_id: str, category: str, kcal: float, salt_g: float, *,
            own_sodium_mg: float = 20.0, **kwargs) -> Recipe:
    """A dish cooked with `salt_g` of salt a serving, on top of the sodium
    its ingredients carry themselves."""
    salt_sodium_mg = salt_g * _SODIUM_MG_PER_G_SALT
    dish = _dish(recipe_id, category, kcal, sodium_mg=own_sodium_mg + salt_sodium_mg, **kwargs)
    return replace(dish, salt_g=salt_g, salt_sodium_mg=salt_sodium_mg)


def _salted_kitchen(own_sodium_mg: float | None = None) -> list[Recipe]:
    """The household repertoire salted the way the recipe dataset salts it:
    about a gram a serving, none in the rice. `own_sodium_mg` overrides the
    sodium every salted dish's ingredients carry."""
    def own(default: float) -> float:
        return default if own_sodium_mg is None else own_sodium_mg

    return [
        _dish("rice", "Rice & Grain", 275, grain=1.0, serving_g=243, frequency=10, sodium_mg=2),
        _salted("ruti", "Bread & Pitha", 267, 0.5, own_sodium_mg=own(10),
                meals=("breakfast", "dinner"), grain=0.99, serving_g=108, frequency=8),
        _salted("dal", "Dal", 169, 1.0, own_sodium_mg=own(20), frequency=9),
        _salted("rohu", "Fish", 277, 1.0, own_sodium_mg=own(75), frequency=6),
        _salted("chicken", "Meat", 305, 1.25, own_sodium_mg=own(100), frequency=5),
        _salted("omelette", "Egg", 188, 1.0, own_sodium_mg=own(95), meals=("breakfast",),
                frequency=6),
        _salted("shak", "Leafy Green", 94, 0.75, own_sodium_mg=own(60), frequency=6),
        _salted("bhaji", "Vegetable", 120, 1.0, own_sodium_mg=own(40),
                meals=("breakfast", "lunch", "dinner"), frequency=5),
    ]


def _lines(day: dict) -> list[dict]:
    return [item for items in day["meals"].values() for item in items]


def test_ration_salt_matches_hand_check():
    # dal: 1 g salt (393.4 mg) + 20 mg of its own; fish: 1.5 g salt (590.1 mg)
    # + 80 mg; a fruit brings 10 mg. As written 1093.5 mg, against a limit of
    # 800: 800 - 110 = 690 mg of room = 1.754 g of salt, stated as 1.7 g,
    # which is 68% of the recipes' 2.5 g.
    dal = _salted("dal", "Dal", 169, 1.0)
    fish = _salted("fish", "Fish", 277, 1.5, own_sodium_mg=80)
    dal_line, fish_line = {"sodium_mg": 413, "salt_g": 1.0}, {"sodium_mg": 670, "salt_g": 1.5}
    totals = {"sodium_mg": 413.4 + 670.1 + 10}
    salt = ration_salt([(dal_line, dal, 1.0), (fish_line, fish, 1.0)], totals, 800)
    assert salt == {"salt_g": 1.7, "recipe_salt_g": 2.5}
    assert dal_line == {"sodium_mg": 288, "salt_g": 0.68}    # 20 + 0.68 x 393.4
    assert fish_line == {"sodium_mg": 481, "salt_g": 1.02}   # 80 + 0.68 x 590.1
    assert totals["sodium_mg"] == pytest.approx(110 + 1.7 * 393.4)


def test_each_day_is_cooked_with_the_salt_that_keeps_it_under_the_sodium_limit():
    # reported: sodium over the 2000 mg limit on all seven days of a plan.
    # Every dish takes about a gram of salt, so the dishes stay and the salt
    # in them comes down.
    as_written = _plan(recipes=_salted_kitchen())
    plan = _plan(recipes=_salted_kitchen(), sodium_limit_mg=2000)
    for written, day in zip(as_written["days"], plan["days"]):
        assert written["totals"]["sodium_mg"] > 2000
        assert day["totals"]["sodium_mg"] < 2000
        assert day["salt_g"] < day["recipe_salt_g"] == written["salt_g"]
        # nothing but the salt changed: same dishes, portions and energy
        assert ([(i.get("recipe_id"), i["qty_g"], i["kcal"]) for i in _lines(day)]
                == [(i.get("recipe_id"), i["qty_g"], i["kcal"]) for i in _lines(written)])
        # the lines carry the day's salt and add up to its sodium
        assert sum(i.get("salt_g", 0.0) for i in _lines(day)) == pytest.approx(day["salt_g"], abs=0.05)
        assert abs(sum(i["sodium_mg"] for i in _lines(day)) - day["totals"]["sodium_mg"]) <= 5
        # every dish gives up the same share of its recipe's salt
        shares = [now["salt_g"] / was["salt_g"]
                  for now, was in zip(_lines(day), _lines(written)) if was.get("salt_g")]
        assert max(shares) - min(shares) < 0.05
    assert plan["salt_g"] < plan["recipe_salt_g"]
    assert plan["totals"]["sodium_mg"] < 2000


def test_a_day_under_the_sodium_limit_keeps_its_recipes_salt():
    as_written = _plan(recipes=_salted_kitchen())
    assert _plan(recipes=_salted_kitchen(), sodium_limit_mg=6000) == as_written
    for day in as_written["days"]:
        assert day["salt_g"] == day["recipe_salt_g"] > 0


def test_salt_cannot_take_out_the_sodium_in_the_food_itself():
    # dishes built on salty ingredients: cooked with no salt at all the day
    # is still over, and its total says so
    plan = _plan(recipes=_salted_kitchen(own_sodium_mg=600), sodium_limit_mg=2000)
    for day in plan["days"]:
        assert day["salt_g"] == 0 and day["recipe_salt_g"] > 0
        assert day["totals"]["sodium_mg"] > 2000
        assert all(item["salt_g"] == 0 for item in _lines(day) if "recipe_id" in item)


def test_a_dish_reports_the_salt_it_is_cooked_with():
    plan = _plan(recipes=_salted_kitchen())
    dal = [item for item in _all_items(plan) if item.get("recipe_id") == "dal"]
    assert dal and all(item["salt_g"] == round(1.0 * item["servings"], 2) for item in dal)
    # a single food has no recipe, so no cooking salt to report
    assert all("salt_g" not in item for item in _all_items(plan) if "food_id" in item)


def test_a_patient_who_eats_no_fish_or_meat_gets_egg_or_dal_as_the_main_dish():
    meatless = [r for r in _big_kitchen() if r.category not in ("Fish", "Meat")]
    meatless += [_dish(f"egg_curry{i}", "Egg", 200, frequency=6, protein_g=13) for i in range(8)]
    plan = build_meal_plan(meatless, [_fruit("guava", 68)], 1800, targets={"protein_g": 50},
                           emphasize=[])
    mains = [item["category"] for day in plan["days"] for meal in ("lunch", "dinner")
             for item in day["meals"][meal] if item["course"] == "main"]
    # every lunch and dinner has a main dish, and dal takes its turn with egg
    assert len(mains) == 14 and set(mains) == {"Egg", "Dal"}
    # with fish and meat on offer, dal stays in its own course
    usual = build_meal_plan(_big_kitchen(), [_fruit("guava", 68)], 1800,
                            targets={"protein_g": 50}, emphasize=[])
    assert all(item["category"] in ("Fish", "Meat", "Egg")
               for item in _all_items(usual) if item.get("course") == "main")
