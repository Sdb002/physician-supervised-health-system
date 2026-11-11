"""The hard safety gate: condition → excluded tags → filtered items."""

from src.clinical.contraindication import (
    excluded_tags,
    filter_items,
    is_allowed,
    known_conditions,
    known_restrictions,
)
from src.diet.food_db import load_foods
from src.lifestyle.exercise_db import load_exercises


def test_hypertension_exclusions():
    ex = excluded_tags(["hypertension"])
    assert "high_sodium" in ex.food_tags
    assert "avoid_hypertension" in ex.exercise_tags
    assert ex.applied_conditions == ("hypertension",)


def test_unknown_condition_is_ignored():
    ex = excluded_tags(["hypertension", "no_such_condition"])
    assert ex.applied_conditions == ("hypertension",)


def test_exclusions_are_a_union():
    ex = excluded_tags(["hypertension", "diabetes", "knee_osteoarthritis"])
    assert {"high_sodium", "high_sugar"} <= set(ex.food_tags)
    assert {"avoid_hypertension", "avoid_diabetes",
            "avoid_knee_osteoarthritis"} == set(ex.exercise_tags)


def test_gate_removes_high_sodium_foods():
    foods = load_foods()
    salty = [f for f in foods if "high_sodium" in f.tags]
    assert salty  # dataset must contain high-sodium foods (salted/dried items)
    ex = excluded_tags(["hypertension"])
    allowed = filter_items(foods, ex.food_tags)
    assert len(allowed) == len(foods) - len(salty)
    assert all("high_sodium" not in f.tags for f in allowed)


def test_gate_removes_contraindicated_exercises():
    exercises = load_exercises()
    ex = excluded_tags(["knee_osteoarthritis"])
    allowed = filter_items(exercises, ex.exercise_tags)
    ids = {e.exercise_id for e in allowed}
    assert "EX050" not in ids  # jogging: high impact
    assert "EX062" not in ids  # lunge: deep loaded knee bend
    assert "EX049" in ids  # brisk walking survives
    assert "EX002" in ids  # a chair-supported mini-squat is "modify", not "avoid"


def test_no_conditions_excludes_nothing():
    ex = excluded_tags([])
    assert not ex.food_tags and not ex.exercise_tags
    assert is_allowed(["high_sodium"], ex.food_tags)
    assert ex.applied_populations == ()


def test_every_condition_has_rules():
    assert {"hypertension", "diabetes", "high_cholesterol", "anemia", "pregnancy",
            "knee_osteoarthritis"} <= set(known_conditions())


def test_high_cholesterol_excludes_the_solid_cooking_fats_and_what_is_cooked_in_them():
    ex = excluded_tags(["high_cholesterol"])
    assert ex.food_tags == {"solid_fat"} and not ex.exercise_tags
    foods = load_foods()
    removed = {f.name_en for f in foods} - {f.name_en for f in filter_items(foods, ex.food_tags)}
    # animal fats, tropical oils and hydrogenated fats: nothing else
    assert removed == {"Butter, salted", "Ghee, cow", "Ghee, vegetable", "Vanaspati",
                       "Margarine", "Coconut oil", "Palm oil"}
    # the liquid oils households cook in stay, and so do the foods that are
    # high in fat of the kind the guidance asks for: nuts, oilseeds, oily fish
    kept = {f.name_en for f in filter_items(foods, ex.food_tags)}
    assert {"Mustard oil", "Soybean oil", "Almond", "Walnut", "Hilsa",
            "Sesame seeds, whole, dried"} <= kept

    dishes = _recipes()
    cooked_in_one = [r for r in dishes if "solid_fat" in r.tags]
    # a spoon of ghee is enough: the tag does not wait for a quarter of the weight
    assert {"Ghee Rice", "Chicken Korma", "Dry Spiced Khichuri"} <= {r.name_en for r in cooked_in_one}
    assert all(any(line["name_en"] == "Ghee, cow" for line in r.ingredient_lines)
               for r in cooked_in_one)
    assert not filter_items(cooked_in_one, ex.food_tags)
    allowed = filter_items(dishes, ex.food_tags)
    assert len(allowed) == len(dishes) - len(cooked_in_one)
    assert {"Plain Boiled Rice", "Thin Red Lentil Soup"} <= {r.name_en for r in allowed}


def _recipes():
    from src.diet.food_db import food_index
    from src.diet.recipe import load_recipes
    return load_recipes(food_index(load_foods()))


def test_pregnancy_excludes_liver_high_mercury_fish_and_alcohol():
    excluded = excluded_tags(["pregnancy"]).food_tags
    assert {"liver", "high_mercury", "alcohol"} <= excluded
    foods = load_foods()
    removed = {f.name_en for f in foods} - {f.name_en for f in filter_items(foods, excluded)}
    assert {"Beef liver, raw", "Chicken liver, raw", "Fish oil, cod liver", "Shark",
            "Indo-pacific king mackerel, without bones, raw", "Toddy"} <= removed
    # ordinary fish and meat stay
    assert "Rohu, without bones, raw" not in removed
    assert "Beef, meat, lean, boneless, raw" not in removed
    # a dish with any liver in it goes too
    liver_dishes = [r for r in _recipes() if "liver" in r.tags]
    assert liver_dishes and not filter_items(liver_dishes, excluded)


def test_dietary_restrictions_go_through_the_same_gate():
    assert {"vegetarian", "vegan", "no_beef", "no_pork"} <= set(known_restrictions())
    vegetarian = excluded_tags([], ["vegetarian"])
    assert vegetarian.applied_restrictions == ("vegetarian",)
    foods = filter_items(load_foods(), vegetarian.food_tags)
    assert foods and not {f.food_group for f in foods} & {"meat", "fish"}
    assert {"egg", "dairy"} <= {f.food_group for f in foods}
    dishes = filter_items(_recipes(), vegetarian.food_tags)
    assert dishes and not {r.category for r in dishes} & {"Fish", "Meat"}

    vegan = excluded_tags([], ["vegan"]).food_tags
    assert not {f.food_group for f in filter_items(load_foods(), vegan)} & {
        "meat", "fish", "egg", "dairy"}
    # ghee is dairy in any amount: a khichuri finished with a spoon of it is not vegan
    assert all("Ghee, cow" not in {line["name_en"] for line in r.ingredient_lines}
               for r in filter_items(_recipes(), vegan))

    # conditions and restrictions add up; an unknown restriction excludes nothing
    both = excluded_tags(["hypertension"], ["no_beef", "not_a_restriction"])
    assert both.food_tags == {"high_sodium", "contains_beef"}
    assert both.applied_restrictions == ("no_beef",)


def test_restriction_tags_agree_with_the_recipe_datasets_own():
    # the recipe dataset tags some of the same things by hand; the tags read
    # off the ingredients must not disagree with it
    pairs = {"contains_beef": "contains_beef", "contains_fish": "contains_fish",
             "contains_shellfish": "contains_shellfish", "contains_egg": "contains_egg",
             "contains_dairy": "contains_dairy", "contains_gluten": "contains_gluten_wheat"}
    foods = {f.food_id: f for f in load_foods()}
    for recipe in _recipes():
        derived = set().union(*(foods[food_id].tags for food_id, _ in recipe.ingredients))
        for ours, theirs in pairs.items():
            assert (ours in derived) == (theirs in recipe.tags), (recipe.recipe_id, ours)
        assert ("contains_meat" in derived) == ("non_vegetarian" in recipe.tags), recipe.recipe_id


def test_dashboard_offers_every_condition_and_restriction():
    """The patient forms list these by hand (dashboard/lib/patient-options.ts):
    a key added to the reference files must be added there too."""
    from src.core.config import PROJECT_ROOT
    options = (PROJECT_ROOT / "dashboard" / "lib" / "patient-options.ts").read_text(encoding="utf-8")
    recorded = [c for c in known_conditions() if c != "pregnancy"]  # pregnancy is its own field
    for key in recorded + known_restrictions():
        assert f'key: "{key}"' in options, key
