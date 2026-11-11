"""A week of meals, composed from household dishes (engine 0.4.0), each day
cooked with the salt that keeps it under the sodium limit (engine 0.6.0).

Each day is built the way Bangladeshi households eat it: rice with dal, a fish,
meat or egg dish and a vegetable at lunch; rice or ruti with a main dish and a
vegetable at dinner; ruti or another plain staple with an egg or vegetable
side at breakfast; fruit as the snack. That is the plate the national food
based dietary guidelines are written around (FPMU, Food Based Dietary
Guidelines for Bangladesh, 2020), and every course is a real dish from the
250-recipe dataset, so the plan reads "Plain Boiled Rice, Thin Red Lentil
Soup, Rohu Fish Light Curry, Red Amaranth Stir-fry" rather than a list of
raw food-table rows.

Within a course, dishes are ranked by src.diet.matcher's recipe scorer: the
patient's emphasized nutrients per serving, weighted by how commonly the dish
is cooked at home. Portions come in household steps - half servings of the
staple, quarter steps of the side dishes - sized so each meal lands near its
share of the day's energy target. Callers must pass recipes and foods that
already went through the contraindication gate.

Version 0.1/0.2 filled food-group slots straight from the food table, which
put rice bran, raw dried pulses and frog legs on the plan: anything that was
nutrient-dense per 100 g won, whether or not anyone eats it as a meal.
"""

import math

from src.diet import matcher
from src.diet.food_db import NUTRIENT_COLUMNS, Food, display_name
from src.diet.recipe import Recipe

MEAL_SPLIT = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}

# meal -> its courses in serving order: (course, dish categories it draws on).
# Category order is not a preference; the scorer decides between them.
MEAL_COURSES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "breakfast": (
        ("staple", ("Bread & Pitha", "Rice & Grain")),
        ("side", ("Egg", "Vegetable", "Bhorta", "Dal", "Leafy Green")),
    ),
    "lunch": (
        ("staple", ("Rice & Grain",)),
        ("dal", ("Dal",)),
        ("main", ("Fish", "Meat", "Egg")),
        ("vegetable", ("Leafy Green", "Vegetable", "Bhorta")),
    ),
    "dinner": (
        ("staple", ("Rice & Grain", "Bread & Pitha")),
        ("main", ("Fish", "Meat", "Egg")),
        ("vegetable", ("Vegetable", "Leafy Green", "Bhorta")),
    ),
}

# A patient who eats no fish or meat (a vegetarian, or anyone the gate leaves
# no fish or meat dish for) gets a second pulse dish in the main-dish course:
# dal is the protein of a vegetarian Bengali meal. Without this an egg dish
# would be the only main at lunch and dinner every day, and a vegan would
# have no main dish at all.
_MAIN_CATEGORIES = ("Fish", "Meat", "Egg")
_MEATLESS_MAIN_CATEGORIES = ("Egg", "Dal")

# Lunch is a rice meal, but a patient who eats no rice still eats lunch: when
# the gate leaves a meal none of its own staples, it takes any plain staple
# (ruti with the dal and the curry) rather than going without one.
_STAPLE_CATEGORIES = ("Rice & Grain", "Bread & Pitha")

# The plan covers a week, Saturday to Friday: the Bangladeshi week starts on
# Saturday, so that is the day patients count from.
WEEKDAYS = ("saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday")

# Across the week, each course (dal, main dish, vegetable, side, fruit) works
# through different dishes before repeating any; a repeat comes at least
# MIN_DAYS_BETWEEN_REPEATS days after the last time, and nothing is served
# more than MAX_WEEKLY_SERVINGS times - whenever the gate leaves a choice.
# Eating a variety of foods is the first key message of the national
# guidelines (FPMU, Food Based Dietary Guidelines for Bangladesh, 2020). The
# staple is exempt, as it is within a day: ruti every morning is normal.
MAX_WEEKLY_SERVINGS = 2
MIN_DAYS_BETWEEN_REPEATS = 3

# Courses whose dish should differ in kind across the day (fish at lunch,
# chicken or egg at dinner; shak at one meal, another vegetable at the next)
# when the gate leaves a choice. The staple is exempt: rice twice a day is
# how most of the country eats.
_VARIED_COURSES = {"main", "vegetable"}

# A staple course takes plain staples only - rice, ruti, paratha, panta bhat.
# Khichuri, pilaf and fried rice are whole meals in themselves (their grain
# share is well under this), and serving one beside dal and a curry would
# double the meal.
STAPLE_MIN_GRAIN_SHARE = 0.75

# Sweets and drinks are never planned automatically, and neither is any dish
# tagged high_sugar: free sugars belong under 10% of energy (WHO 2015
# guideline on sugars intake), so a day's plan should not be built on them.
# They stay available to the physician's plan editor.
_NEVER_PLANNED_CATEGORIES = {"Sweet", "Beverage"}
_NEVER_PLANNED_TAGS = {"high_sugar"}

# One serving of a liver dish supplies more preformed vitamin A than the
# tolerable upper intake level for adults, pregnancy included: 3000 ug RAE a
# day (Institute of Medicine 2001, Dietary Reference Intakes for Vitamin A,
# ch. 4; the UL is set on teratogenicity in pregnancy and liver toxicity).
# Nothing that crosses it in a single serving is planned or suggested
# automatically; the physician can still add it.
MAX_VIT_A_UG_PER_SERVING = 3000.0

# Eggs come whole: an egg dish's serving is one or two eggs, so it is never
# scaled down to a fraction the way a curry's portion can be.
_WHOLE_SERVING_CATEGORIES = {"Egg"}

STAPLE_SERVINGS = (0.5, 1.0, 1.5, 2.0, 2.5)
SIDE_SCALES = (1.0, 0.75, 0.5)
# Cost of each quarter-serving taken off the side dishes, as a share of the
# meal's energy: shrinking the curry is preferred only when it brings the
# meal clearly closer to target than changing the rice does.
_SIDE_SHRINK_COST = 0.05

# Fruit portions: about one fruit or a cupful (USDA MyPlate: ~150 g is one
# serving of fruit), never more than 200 g whatever the snack's energy share.
_FRUIT_MIN_G = 80
_FRUIT_MAX_G = 200

# Once a nutrient's running total passes this share of its daily target,
# stop treating it as a reason to pick MORE of it, so one very dense dish
# doesn't steer every remaining course toward the same nutrient.
_EMPHASIS_SATURATION = 1.5

# A day's cooking salt is stated in steps of this many grams, rounded down,
# so a rationed day lands under the sodium limit rather than on it.
_SALT_STEP_G = 0.1


def plannable(recipe: Recipe) -> bool:
    """Whether a gated dish may be planned or suggested without the
    physician choosing it: no sweets, drinks or high-sugar dishes, and
    nothing over the vitamin A upper limit in one serving."""
    return (recipe.category not in _NEVER_PLANNED_CATEGORIES
            and not _NEVER_PLANNED_TAGS & set(recipe.tags)
            and recipe.per_serving.get("vit_a_ug", 0.0) <= MAX_VIT_A_UG_PER_SERVING)


def is_plain_staple(recipe: Recipe) -> bool:
    return recipe.group_shares.get("grain", 0.0) >= STAPLE_MIN_GRAIN_SHARE


def serving_grams(recipe: Recipe) -> float:
    if recipe.serving_size_g:
        return recipe.serving_size_g
    return sum(qty for _, qty in recipe.ingredients) / (recipe.servings or 1)


# Groups that never make a dish what it is: water, seasonings, cooking fat.
_NOT_A_KEY_INGREDIENT = {"other", "spice", "oil"}
# An ingredient is one of a dish's key ingredients at this share of the
# dish's weight (water, seasonings and oil left out).
KEY_INGREDIENT_SHARE = 0.25


def key_ingredients(recipe: Recipe, foods_by_id: dict[str, Food]) -> frozenset[str]:
    """The foods a dish is built on. Used to keep a day from repeating one
    food under different names (potato bhaji, then potato-and-cauliflower
    curry, then chicken-and-potato curry)."""
    weights = {}
    for food_id, qty_g in recipe.ingredients:
        food = foods_by_id.get(food_id)
        if food is None or food.food_group in _NOT_A_KEY_INGREDIENT or qty_g <= 0:
            continue
        weights[food_id] = weights.get(food_id, 0.0) + qty_g
    total = sum(weights.values())
    if not total:
        return frozenset()
    return frozenset(f for f, w in weights.items() if w / total >= KEY_INGREDIENT_SHARE)


def _course_categories(course: str, categories: tuple[str, ...],
                       recipes: list[Recipe]) -> tuple[str, ...]:
    """The dish categories a course draws on for this patient's gated dishes."""
    if course == "staple":
        has_its_staple = any(r.category in categories and plannable(r) and is_plain_staple(r)
                             for r in recipes)
        return categories if has_its_staple else _STAPLE_CATEGORIES
    if course != "main":
        return categories
    has_fish_or_meat = any(r.category in ("Fish", "Meat") and plannable(r) for r in recipes)
    return _MAIN_CATEGORIES if has_fish_or_meat else _MEATLESS_MAIN_CATEGORIES


def _active_emphasis(emphasize: list[str], totals: dict, targets: dict) -> list[str]:
    return [n for n in emphasize
            if totals.get(n, 0.0) < targets.get(n, 0.0) * _EMPHASIS_SATURATION]


def _scorer(score, items: list, key):
    """emphasize -> {item id: score} for every item, worked out once per
    emphasis. A week picks some sixty courses, but the emphasis only changes
    when a nutrient reaches its fill, so the same few score tables serve
    them all; with a trained model that is a handful of predict calls a plan
    instead of one for every dish considered."""
    tables: dict[tuple, dict[str, float]] = {}

    def scores(emphasize: list[str]) -> dict[str, float]:
        table = tables.get(tuple(emphasize))
        if table is None:
            table = dict(zip(map(key, items), score(items, emphasize)))
            tables[tuple(emphasize)] = table
        return table

    return scores


def _pick_dish(recipes: list[Recipe], meal: str, course: str, categories: tuple[str, ...],
               scores: dict[str, float], used_ids: set[str],
               used_kinds: set[str], used_keys: set[str],
               foods_by_id: dict[str, Food], week: "_Week") -> Recipe | None:
    pool = [r for r in recipes if r.category in categories and plannable(r)]
    if course == "staple":
        pool = [r for r in pool if is_plain_staple(r)]
    else:
        pool = [r for r in pool if r.recipe_id not in used_ids]
    # a dish tagged for this meal first; any dish of the right kind otherwise
    pool = [r for r in pool if meal in r.meal_type] or pool
    if course != "staple":
        pool = week.varied(pool, lambda r: r.recipe_id)
    if course in _VARIED_COURSES:
        pool = [r for r in pool if r.category not in used_kinds] or pool
    if course != "staple":
        pool = [r for r in pool
                if not key_ingredients(r, foods_by_id) & used_keys] or pool
    if not pool:
        return None
    return min(pool, key=lambda r: (-scores[r.recipe_id], r.recipe_id))


def _scalable(recipe: Recipe) -> bool:
    return recipe.category not in _WHOLE_SERVING_CATEGORIES


def _portion(meal_kcal: float, staple: Recipe | None, sides: list[Recipe]) -> tuple[float, float]:
    """(staple servings, side-dish scale) bringing the meal closest to its
    energy share, in household steps. Whole-serving dishes (eggs) keep one
    serving whatever the scale."""
    staple_kcal = staple.per_serving["kcal"] if staple else 0.0
    scalable_kcal = sum(r.per_serving["kcal"] for r in sides if _scalable(r))
    fixed_kcal = sum(r.per_serving["kcal"] for r in sides if not _scalable(r))
    staple_steps = STAPLE_SERVINGS if staple else (0.0,)
    best = None
    for side_scale in SIDE_SCALES if scalable_kcal else (1.0,):
        shrink = (1.0 - side_scale) / 0.25 * _SIDE_SHRINK_COST * meal_kcal
        for servings in staple_steps:
            total = servings * staple_kcal + side_scale * scalable_kcal + fixed_kcal
            cost = abs(total - meal_kcal) + shrink
            if best is None or cost < best[0]:
                best = (cost, servings, side_scale)
    return best[1], best[2]


def line_figures(nutrients: dict, recipe: Recipe | None = None, servings: float = 0.0) -> dict:
    """What a plan line reports about its portion: energy, the carbohydrate a
    patient with diabetes counts by the meal, and the fat and sodium a
    physician checks dish by dish. A dish also reports how much of its fat is
    the oil, ghee or butter it is cooked in, and the salt it is cooked with:
    the recipe's own here, until ration_salt sets the day's."""
    figures = {
        "kcal": round(nutrients["kcal"]),
        "carb_g": round(nutrients["carb_g"], 1),
        "fat_g": round(nutrients["fat_g"], 1),
        "sodium_mg": round(nutrients["sodium_mg"]),
    }
    if recipe is not None:
        figures["cooking_fat_g"] = round(recipe.cooking_fat_g * servings, 1)
        figures["salt_g"] = round(recipe.salt_g * servings, 2)
    return figures


def ration_salt(dishes: list[tuple[dict, Recipe, float]], totals: dict,
                sodium_limit_mg: float | None) -> dict:
    """Set a day's cooking salt so the day stays under the sodium limit.

    Most of the sodium in a home-cooked dish is the salt the cook adds (a
    median 88% across the recipe dataset), and every dal, curry and bhaji
    takes about a gram a serving, so no choice of dishes brings a day under
    the limit: cooked as written, a planned day carries about 5 to 8 g of salt,
    where the limit allows under 5 g from all sources (WHO 2012, Guideline:
    Sodium intake for adults and children). What a household can change is
    the salt in the pot. A day at or over the limit therefore keeps its
    dishes and is cooked with less salt: whatever fits once the sodium
    already in the fish, meat, eggs, vegetables and fruit is counted, every
    dish taking the same share of its recipe's salt.

    `dishes` are the day's dish lines as (plan line, recipe, servings);
    `totals` are the day's nutrients with every dish salted as its recipe
    says. Lines and totals are updated in place. Returns the day's cooking
    salt, `salt_g`, beside `recipe_salt_g`, what the recipes as written
    would use. A day whose other sodium alone reaches the limit is given no
    salt and stays over it, for the reviewing physician to see.
    """
    recipe_g = sum(recipe.salt_g * servings for _, recipe, servings in dishes)
    recipe_mg = sum(recipe.salt_sodium_mg * servings for _, recipe, servings in dishes)
    salt_g = recipe_g
    if sodium_limit_mg is not None and recipe_g > 0 and totals["sodium_mg"] >= sodium_limit_mg:
        other_mg = totals["sodium_mg"] - recipe_mg
        fits_g = max(sodium_limit_mg - other_mg, 0.0) / (recipe_mg / recipe_g)
        steps = math.floor(round(fits_g / _SALT_STEP_G, 6))
        salt_g = min(steps * _SALT_STEP_G, recipe_g)
    if salt_g < recipe_g:
        share = salt_g / recipe_g
        for item, recipe, servings in dishes:
            left_out_mg = recipe.salt_sodium_mg * (1.0 - share)
            item["salt_g"] = round(recipe.salt_g * servings * share, 2)
            item["sodium_mg"] = round(
                (recipe.per_serving.get("sodium_mg", 0.0) - left_out_mg) * servings)
        totals["sodium_mg"] -= recipe_mg * (1.0 - share)
    return {"salt_g": round(salt_g, 1), "recipe_salt_g": round(recipe_g, 1)}


def _dish_item(recipe: Recipe, course: str, servings: float) -> tuple[dict, dict]:
    nutrients = {c: recipe.per_serving.get(c, 0.0) * servings for c in NUTRIENT_COLUMNS}
    grams = serving_grams(recipe)
    item = {
        "recipe_id": recipe.recipe_id, "name_en": recipe.name_en, "name_bn": recipe.name_bn,
        "course": course, "category": recipe.category,
        "servings": servings, "serving_size_g": round(grams),
        "qty_g": round(grams * servings),
        **line_figures(nutrients, recipe, servings),
    }
    return item, nutrients


def _pick_fruit(fruits: list[Food], scores: dict[str, float],
                familiarity: dict[str, int | None], week: "_Week") -> Food | None:
    pool = week.varied([f for f in fruits if f.nutrients["kcal"] > 0], lambda f: f.food_id)
    if not pool:
        return None
    return min(pool, key=lambda f: (
        -matcher.familiar_score(scores[f.food_id], familiarity.get(f.food_id)), f.food_id))


class _Week:
    """What the week has served so far, for the variety rules."""

    def __init__(self) -> None:
        self.day = 0
        self.uses: dict[str, int] = {}
        self.last_day: dict[str, int] = {}

    def _gap(self, item_id: str) -> int:
        last = self.last_day.get(item_id)
        return self.day - last if last is not None else self.day + 1

    def varied(self, pool: list, key) -> list:
        """The most varied choices the pool allows, in order of preference:
        not yet served this week; else a spaced repeat under the weekly cap;
        else anything not served yesterday; else the whole pool."""
        tiers = (
            lambda x: key(x) not in self.uses,
            lambda x: (self.uses[key(x)] < MAX_WEEKLY_SERVINGS
                       and self._gap(key(x)) >= MIN_DAYS_BETWEEN_REPEATS),
            lambda x: self._gap(key(x)) > 1,
        )
        for preferred in tiers:
            narrowed = [x for x in pool if preferred(x)]
            if narrowed:
                return narrowed
        return pool

    def serve(self, item_id: str) -> None:
        self.uses[item_id] = self.uses.get(item_id, 0) + 1
        self.last_day[item_id] = self.day

    def next_day(self) -> None:
        self.day += 1


def _build_day(recipes: list[Recipe], fruits: list[Food], target_kcal: float, targets: dict,
               emphasize: list[str], familiarity: dict[str, int | None],
               foods_by_id: dict[str, Food], week: _Week, dish_scores, fruit_scores,
               sodium_limit_mg: float | None = None) -> tuple[dict, dict, dict]:
    """One day's meals, nutrient totals and cooking salt. `dish_scores` and
    `fruit_scores` give every dish's and fruit's score under an emphasis
    (see _scorer)."""
    meals: dict[str, list[dict]] = {}
    totals = {col: 0.0 for col in NUTRIENT_COLUMNS}
    dishes: list[tuple[dict, Recipe, float]] = []
    used_ids: set[str] = set()
    used_kinds: set[str] = set()
    used_keys: set[str] = set()

    def add(items: list[dict], item: dict, nutrients: dict) -> None:
        items.append(item)
        for c in NUTRIENT_COLUMNS:
            totals[c] += nutrients[c]

    for meal, share in MEAL_SPLIT.items():
        meal_kcal = target_kcal * share
        items: list[dict] = []

        if meal == "snack":
            fruit = _pick_fruit(fruits, fruit_scores(_active_emphasis(emphasize, totals, targets)),
                                familiarity, week)
            if fruit is not None:
                week.serve(fruit.food_id)
                qty_g = meal_kcal / fruit.nutrients["kcal"] * 100.0
                qty_g = round(min(max(qty_g, _FRUIT_MIN_G), _FRUIT_MAX_G) / 10) * 10
                nutrients = {c: fruit.nutrients[c] * qty_g / 100.0 for c in NUTRIENT_COLUMNS}
                add(items, {"food_id": fruit.food_id, "name_en": display_name(fruit.name_en),
                            "name_bn": fruit.name_bn, "course": "fruit", "qty_g": qty_g,
                            **line_figures(nutrients)}, nutrients)
            meals[meal] = items
            continue

        chosen: list[tuple[str, Recipe]] = []
        for course, categories in MEAL_COURSES[meal]:
            categories = _course_categories(course, categories, recipes)
            dish = _pick_dish(recipes, meal, course, categories,
                              dish_scores(_active_emphasis(emphasize, totals, targets)),
                              used_ids, used_kinds, used_keys, foods_by_id, week)
            if dish is None:
                continue
            chosen.append((course, dish))
            used_ids.add(dish.recipe_id)
            if course in _VARIED_COURSES:
                used_kinds.add(dish.category)
            if course != "staple":
                used_keys.update(key_ingredients(dish, foods_by_id))
                week.serve(dish.recipe_id)

        staple = next((r for c, r in chosen if c == "staple"), None)
        sides = [r for c, r in chosen if c != "staple"]
        staple_servings, side_scale = _portion(meal_kcal, staple, sides)
        for course, dish in chosen:
            if course == "staple":
                servings = staple_servings
            else:
                servings = side_scale if _scalable(dish) else 1.0
            item, nutrients = _dish_item(dish, course, servings)
            add(items, item, nutrients)
            dishes.append((item, dish, servings))
        meals[meal] = items
    return meals, totals, ration_salt(dishes, totals, sodium_limit_mg)


def build_meal_plan(recipes: list[Recipe], fruits: list[Food], target_kcal: float,
                    targets: dict, emphasize: list[str],
                    familiarity: dict[str, int | None] | None = None,
                    untracked: frozenset[str] | set[str] = frozenset(),
                    foods_by_id: dict[str, Food] | None = None,
                    sodium_limit_mg: float | None = None,
                    findings=()) -> dict:
    """A week of meals, Saturday to Friday, each day sized to the daily
    energy target. `recipes` and `fruits` must already be gated.
    `sodium_limit_mg` is the daily sodium limit each day's cooking salt is
    fitted to (see ration_salt); without one, dishes keep their recipes' salt.
    It and `findings`, the patient's finding keys, also go to the scorers
    (see src.diet.matcher.score_recipes).
    `untracked` lists the nutrients the food table records for no food at
    all (folate in the current dataset): coverage cannot be computed for
    them, so they are reported as untracked instead of as a misleading 0%,
    and they are left out of the emphasis the dishes are picked on.
    `foods_by_id` (the whole food table) lets each day avoid repeating a
    dish's key ingredients."""
    if not recipes:
        return {"days": [], "totals": {}, "target_kcal": round(target_kcal),
                "coverage": {}, "note": "recipe database is empty — add data/recipe/recipes.csv"}

    familiarity = familiarity or {}
    foods_by_id = foods_by_id or {}
    # A nutrient no food has a value for tells no two dishes apart, and its
    # total never rises, so it would stay emphasized all week. Once the
    # others had their fill it was the only one left: every dish scored 0
    # and the recipe id picked the course. Without it, a day whose tracked
    # nutrients are covered falls back to the nutrient-dense default.
    emphasize = [n for n in emphasize if n not in untracked]
    limits = {"sodium_mg": sodium_limit_mg} if sodium_limit_mg is not None else None
    dish_scores = _scorer(
        lambda dishes, emphasis: matcher.score_recipes(dishes, emphasis, targets, findings, limits),
        recipes, lambda r: r.recipe_id)
    fruit_scores = _scorer(
        lambda foods, emphasis: matcher.score_foods(foods, emphasis, targets, findings, limits),
        fruits, lambda f: f.food_id)
    week = _Week()
    days = []
    for weekday in WEEKDAYS:
        meals, totals, salt = _build_day(recipes, fruits, target_kcal, targets, emphasize,
                                         familiarity, foods_by_id, week, dish_scores,
                                         fruit_scores, sodium_limit_mg)
        days.append((weekday, meals, totals, salt))
        week.next_day()
    return summarize_week(days, target_kcal, targets, untracked)


def summarize_week(days: list[tuple[str, dict, dict, dict]], target_kcal: float,
                   targets: dict, untracked=frozenset()) -> dict:
    """The plan document for (weekday, meals, totals, salt) days: each day
    with its own totals and cooking salt, plus the week's average day for
    totals, salt and coverage - the targets are daily, so a week is judged
    by its average day."""
    count = len(days) or 1
    average = {c: sum(t[c] for _, _, t, _ in days) / count for c in NUTRIENT_COLUMNS}
    plan = {
        "days": [
            {"day": index + 1, "weekday": weekday, "meals": meals,
             "totals": {c: round(v, 1) for c, v in totals.items()}, **salt}
            for index, (weekday, meals, totals, salt) in enumerate(days)
        ],
        "totals": {c: round(v, 1) for c, v in average.items()},
        **{key: round(sum(salt[key] for *_, salt in days) / count, 1)
           for key in ("salt_g", "recipe_salt_g")},
        "target_kcal": round(target_kcal),
        "coverage": coverage(average, targets, untracked),
    }
    tracked_out = sorted(n for n in untracked if n in targets and n != "kcal")
    if tracked_out:
        plan["untracked"] = tracked_out
    return plan


def unfilled_courses(plan: dict) -> list[tuple[str, str, str]]:
    """(weekday, meal, course) for every course of a week plan that has
    nothing in it. The planner fills a course whenever the gate leaves it a
    dish of the right kind, so an empty one means the patient's exclusions
    took them all: a lunch that is rice alone, a day without a staple."""
    courses = {**{meal: [course for course, _ in served] for meal, served in MEAL_COURSES.items()},
               "snack": ["fruit"]}
    unfilled = []
    for day in plan.get("days") or []:
        for meal, expected in courses.items():
            served = {item.get("course") for item in day["meals"].get(meal, [])}
            unfilled += [(day["weekday"], meal, course) for course in expected
                         if course not in served]
    return unfilled


def coverage(totals: dict, targets: dict, untracked=frozenset()) -> dict:
    return {
        nutrient: round(totals.get(nutrient, 0.0) / target * 100)
        for nutrient, target in targets.items()
        if nutrient != "kcal" and target and nutrient not in untracked
    }
