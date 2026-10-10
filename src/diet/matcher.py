"""Rank foods and recipes against a patient's nutrient targets.

Foods and recipes are ranked separately, each by its own scorer. When a
trained model is available (see src.diet.recommender — one model per
section), its prediction is used as the primary score. Otherwise each falls
back to the deterministic v0.1 heuristic: for each emphasized nutrient, an
item earns value / daily_target — i.e. the fraction of the day's target one
unit (100 g of food, or one recipe serving) supplies. With no emphasized
nutrients, items are ranked by protein + fiber density per 100 kcal as a
neutral "nutrient-dense" default. Recipes are additionally weighted by how
commonly the dish is cooked at home (see frequency_multiplier). The
contraindication gate must be applied by the caller BEFORE ranking (see
src.clinical.contraindication.filter_items) — the models only ever score
items already filtered by that gate, never re-admit an excluded item.
"""

from src.diet import recommender
from src.diet.food_db import Food, display_name
from src.diet.habits import variant_key
from src.diet.recipe import Recipe

# Familiarity weighting for recipes. weekly_frequency_score is the recipe
# dataset's 1-10 household-frequency score (10 = the most commonly cooked
# dish, 1 = a once-a-year festive dish). Food-based dietary guidance is built
# on the foods a population habitually eats, because familiar dishes are the
# ones people actually cook and keep eating (FAO/WHO 1998, WHO Technical
# Report Series 880; FPMU, Food Based Dietary Guidelines for Bangladesh,
# 2020). A score-10 staple keeps its full nutritional score; a score-1 dish
# keeps FREQUENCY_FLOOR of it, so a festive dish (score 2, a few times a
# year) needs about three times the nutritional fit of a daily staple to
# outrank it. Scaling rather than adding means familiarity reorders dishes
# that already suit the patient but can never lift a dish that does nothing
# for their targets.
FREQUENCY_FLOOR = 0.25


def frequency_multiplier(score: int | None) -> float:
    """1.0 for score 10 down to FREQUENCY_FLOOR for score 1; 1.0 (no
    adjustment) when the recipe has no score."""
    if score is None:
        return 1.0
    clamped = min(max(score, 1), 10)
    return FREQUENCY_FLOOR + (1.0 - FREQUENCY_FLOOR) * (clamped - 1) / 9.0


def _emphasis_score(nutrients: dict, emphasize: list[str], targets: dict) -> float:
    score = 0.0
    for nutrient in emphasize:
        target = targets.get(nutrient)
        if target:
            score += nutrients.get(nutrient, 0.0) / target
    return score


def _density_score(nutrients: dict) -> float:
    kcal = nutrients.get("kcal", 0.0)
    if kcal <= 0:
        # no recorded energy (water, salt, or a source gap — five USDA dried
        # herbs list fibre but no energy): "per 100 kcal" is undefined, and
        # dividing by ~0 would rank dried oregano first for everyone
        return 0.0
    return (nutrients.get("protein_g", 0.0) + nutrients.get("fiber_g", 0.0)) * 100.0 / kcal


def _score_one(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
              targets: dict, *, empty_emphasize_fallback: float) -> float:
    """ML-or-fallback primary score for one food.

    `empty_emphasize_fallback` is what the caller used as the score before
    an ML backend existed, for the case where there's nothing to emphasize:
    rank_foods falls back to density, meal_plan._pick falls back to a flat
    0.0. Kept explicit per call site rather than hardcoded here so each one's
    pre-ML behavior is unchanged whenever no trained model file is present
    (the default on a fresh checkout).
    """
    model = recommender.load_model()
    if model is not None:
        emphasis = _emphasis_score(nutrients, emphasize, targets) if emphasize else 0.0
        density = _density_score(nutrients)
        ml = recommender.ml_score(
            nutrients, food_group, tags, emphasize, targets, emphasis, density
        )
        if ml is not None:
            return ml
    if emphasize:
        return _emphasis_score(nutrients, emphasize, targets)
    return empty_emphasize_fallback


def recipe_baseline_score(nutrients: dict, frequency_score: int | None,
                          emphasize: list[str], targets: dict) -> float:
    """The deterministic recipe score: nutritional fit (emphasis, or density
    when nothing is emphasized) x household familiarity."""
    fit = _emphasis_score(nutrients, emphasize, targets) if emphasize else _density_score(nutrients)
    return fit * frequency_multiplier(frequency_score)


def _score_recipe(recipe: Recipe, emphasize: list[str], targets: dict) -> float:
    if recommender.load_recipe_model() is not None:
        emphasis = _emphasis_score(recipe.per_serving, emphasize, targets) if emphasize else 0.0
        density = _density_score(recipe.per_serving)
        ml = recommender.recipe_ml_score(
            recipe.per_serving, recipe.group_shares, recipe.tags,
            recipe.weekly_frequency_score, emphasize, targets, emphasis, density,
        )
        if ml is not None:
            return ml
    return recipe_baseline_score(
        recipe.per_serving, recipe.weekly_frequency_score, emphasize, targets
    )


def active_backend() -> str:
    """Which food scorer is in effect: "ml" if a trained food model is
    present and loads cleanly, "linear" otherwise."""
    return "ml" if recommender.load_model() is not None else "linear"


def active_recipe_backend() -> str:
    """Same as active_backend(), for the recipe scorer."""
    return "ml" if recommender.load_recipe_model() is not None else "linear"


def familiar_score(score: float, familiarity: int | None) -> float:
    """A nutritional score weighted by how habitually the item is eaten. Only
    a positive score is scaled: familiarity reorders items that already suit
    the patient and must never make an unsuitable one look less bad."""
    return score * frequency_multiplier(familiarity) if score > 0 else score


def rank_foods(foods: list[Food], emphasize: list[str], targets: dict,
               top_n: int = 10, familiarity: dict[str, int | None] | None = None,
               per_group: int | None = None,
               portion_g: dict[str, float] | None = None) -> list[dict]:
    """Best foods for the patient, one per everyday food: the table's raw,
    boiled and cultivar rows of the same food (habits.variant_key) yield a
    single entry, the best-scoring one. With `familiarity` (food_id -> 1-10,
    see src.diet.habits), scores are weighted the same way recipes are.
    With `portion_g` (food_id -> grams in a usual portion), a positive score
    is weighted by portion / 100 g, so foods compete on what a serving
    supplies. `per_group` caps entries per food group, so a list meant to
    widen what a patient eats spans vegetables, fruit, pulses and fish
    instead of ten leafy greens."""
    familiarity = familiarity or {}
    portion_g = portion_g or {}
    scored = []
    for food in foods:
        score = _score_one(
            food.nutrients, food.food_group, food.tags, emphasize, targets,
            empty_emphasize_fallback=_density_score(food.nutrients),
        )
        if food.food_id in familiarity:
            score = familiar_score(score, familiarity[food.food_id])
        if food.food_id in portion_g and score > 0:
            score *= portion_g[food.food_id] / 100.0
        scored.append((score, food))
    scored.sort(key=lambda pair: (-pair[0], pair[1].food_id))
    seen: set[str] = set()
    group_counts: dict[str, int] = {}
    ranked = []
    for s, f in scored:
        if s <= 0 or len(ranked) >= top_n:
            break
        key = variant_key(f)
        if key in seen:
            continue
        if per_group is not None and group_counts.get(f.food_group, 0) >= per_group:
            continue
        seen.add(key)
        group_counts[f.food_group] = group_counts.get(f.food_group, 0) + 1
        ranked.append(
            {"food_id": f.food_id, "name_en": display_name(f.name_en), "name_bn": f.name_bn,
             "score": round(s, 3), "tags": list(f.tags),
             "food_group": f.food_group, "kcal_per_100g": round(f.nutrients["kcal"])}
        )
    return ranked


def _recipe_entry(recipe: Recipe, score: float) -> dict:
    return {
        "recipe_id": recipe.recipe_id, "name_en": recipe.name_en, "name_bn": recipe.name_bn,
        "score": round(score, 3), "tags": list(recipe.tags),
        "category": recipe.category, "diet_type": recipe.diet_type,
        "meal_type": list(recipe.meal_type),
        "weekly_frequency_score": recipe.weekly_frequency_score,
        "frequency_tier": recipe.frequency_tier,
        "servings": recipe.servings,
        "serving_size_g": recipe.serving_size_g,
        "cooking_method": recipe.cooking_method,
        "total_time_min": recipe.total_time_min,
        "per_serving_kcal": recipe.per_serving["kcal"],
        "per_serving": dict(recipe.per_serving),
        "ingredients": [
            {"name_en": line["name_en"], "name_bn": line["name_bn"],
             "household_measure": line["household_measure"],
             "qty_g": line["qty_g"], "optional": line["optional"]}
            for line in recipe.ingredient_lines
        ],
        "steps": list(recipe.steps),
        "notes": recipe.notes,
    }


def rank_recipes(recipes: list[Recipe], emphasize: list[str], targets: dict,
                 top_n: int = 10, per_category: int | None = None) -> list[dict]:
    """`per_category` caps dishes per recipe category (dal, fish, leafy
    greens...), so suggestions cover a meal's parts instead of ten stir-fries."""
    scored = [(_score_recipe(recipe, emphasize, targets), recipe) for recipe in recipes]
    scored.sort(key=lambda pair: (-pair[0], pair[1].recipe_id))
    counts: dict[str, int] = {}
    ranked = []
    for s, r in scored:
        if s <= 0 or len(ranked) >= top_n:
            break
        if per_category is not None and counts.get(r.category, 0) >= per_category:
            continue
        counts[r.category] = counts.get(r.category, 0) + 1
        ranked.append(_recipe_entry(r, s))
    return ranked
