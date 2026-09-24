"""One-day meal plan builder (deterministic heuristic, v0.1).

Approach: split the daily energy target across meals (25/35/30/10), fill each
meal from food-group slots (staple / protein / vegetable-fruit / dairy), sizing
portions so slot energy shares are met. Within a slot, foods are chosen by the
matcher's ranking so emphasized nutrients (e.g. iron in anemia) rise to the top.
Callers must pass foods that already went through the contraindication gate.

This is a starting heuristic intended to be replaced/extended in the thesis
(e.g. linear programming for exact target satisfaction).
"""

from src.diet import matcher
from src.diet.food_db import Food, NUTRIENT_COLUMNS

MEAL_SPLIT = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}

# slot → (candidate food groups, share of the meal's kcal)
MEAL_SLOTS: dict[str, list[tuple[list[str], float]]] = {
    "breakfast": [(["grain"], 0.5), (["egg", "dairy", "legume"], 0.3), (["fruit"], 0.2)],
    "lunch": [(["grain"], 0.5), (["fish", "meat", "legume", "egg"], 0.3), (["vegetable"], 0.2)],
    "dinner": [(["grain"], 0.5), (["fish", "meat", "legume", "egg"], 0.3), (["vegetable"], 0.2)],
    "snack": [(["fruit", "dairy"], 1.0)],
}

# once a nutrient's running total already exceeds this share of its daily
# target, stop treating it as a reason to pick MORE of it — otherwise a single
# very nutrient-dense food (e.g. guava's ~228 mg vitamin C/100 g) gets re-picked
# in every remaining slot that allows its food group, and coverage compounds
# past 1000% instead of the day's foods varying once that nutrient is covered.
_EMPHASIS_SATURATION = 1.5

_MIN_QTY_G = 30
# per-group ceiling: without this, calorie-share sizing inflates low-density
# foods (raw leafy greens, watery fruit) into unrealistic "portions" (e.g.
# 350 g of raw spinach) chasing a kcal target they can't reach at a normal
# serving size — and their vitamin/mineral coverage balloons along with it.
# USDA MyPlate treats ~1 cup (~150 g) of veg/fruit as one serving; 200 g
# allows a generously-sized single portion without multiplying that further.
_MAX_QTY_G_BY_GROUP = {"vegetable": 200, "fruit": 200}
_MAX_QTY_G_DEFAULT = 350


def _pick(foods: list[Food], groups: list[str], emphasize: list[str], targets: dict,
          used: set[str]) -> Food | None:
    candidates = [f for f in foods if f.food_group in groups and f.nutrients["kcal"] > 0]
    fresh = [f for f in candidates if f.food_id not in used]
    pool = fresh or candidates
    if not pool:
        return None
    def score(f: Food) -> tuple:
        s = matcher._score_one(f.nutrients, f.food_group, f.tags, emphasize, targets,
                               empty_emphasize_fallback=0.0)
        return (-s, -matcher._density_score(f.nutrients), f.food_id)
    return sorted(pool, key=score)[0]


def build_meal_plan(foods: list[Food], target_kcal: float, targets: dict,
                    emphasize: list[str]) -> dict:
    if not foods:
        return {"meals": {}, "totals": {}, "target_kcal": target_kcal,
                "coverage": {}, "note": "food database is empty — add data/food/bd_food.csv"}

    meals: dict[str, list[dict]] = {}
    totals = {col: 0.0 for col in NUTRIENT_COLUMNS}
    used: set[str] = set()

    for meal, meal_share in MEAL_SPLIT.items():
        meal_kcal = target_kcal * meal_share
        items: list[dict] = []
        for groups, slot_share in MEAL_SLOTS[meal]:
            active_emphasize = [
                n for n in emphasize
                if totals.get(n, 0.0) < targets.get(n, 0.0) * _EMPHASIS_SATURATION
            ]
            food = _pick(foods, groups, active_emphasize, targets, used)
            if food is None:
                continue
            used.add(food.food_id)
            qty_g = meal_kcal * slot_share / food.nutrients["kcal"] * 100.0
            max_qty = _MAX_QTY_G_BY_GROUP.get(food.food_group, _MAX_QTY_G_DEFAULT)
            qty_g = round(min(max(qty_g, _MIN_QTY_G), max_qty) / 5) * 5
            item_nutrients = {c: food.nutrients[c] * qty_g / 100.0 for c in NUTRIENT_COLUMNS}
            for c in NUTRIENT_COLUMNS:
                totals[c] += item_nutrients[c]
            items.append({
                "food_id": food.food_id, "name_en": food.name_en,
                "name_bn": food.name_bn, "qty_g": qty_g,
                "kcal": round(item_nutrients["kcal"]),
            })
        meals[meal] = items

    coverage = {}
    for nutrient, target in targets.items():
        if nutrient == "kcal" or not target:
            continue
        coverage[nutrient] = round(totals.get(nutrient, 0.0) / target * 100)

    return {
        "meals": meals,
        "totals": {c: round(v, 1) for c, v in totals.items()},
        "target_kcal": round(target_kcal),
        "coverage": coverage,
    }
