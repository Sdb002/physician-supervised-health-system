"""Rank foods and recipes against a patient's nutrient targets.

Scoring: when a trained model is available (see src.diet.recommender), its
prediction is used as the primary score. Otherwise falls back to the
deterministic v0.1 heuristic: for each emphasized nutrient, an item earns
value / daily_target — i.e. the fraction of the day's target one unit (100 g of
food, or one recipe serving) supplies. With no emphasized nutrients, items are
ranked by protein + fiber density per 100 kcal as a neutral "nutrient-dense"
default. The contraindication gate must be applied by the caller BEFORE ranking
(see src.clinical.contraindication.filter_items) — the model only ever scores
items already filtered by that gate, never re-admits an excluded item.
"""

from src.diet import recommender
from src.diet.food_db import Food
from src.diet.recipe import Recipe


def _emphasis_score(nutrients: dict, emphasize: list[str], targets: dict) -> float:
    score = 0.0
    for nutrient in emphasize:
        target = targets.get(nutrient)
        if target:
            score += nutrients.get(nutrient, 0.0) / target
    return score


def _density_score(nutrients: dict) -> float:
    kcal = max(nutrients.get("kcal", 0.0), 1.0)
    return (nutrients.get("protein_g", 0.0) + nutrients.get("fiber_g", 0.0)) * 100.0 / kcal


def _score_one(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
              targets: dict, *, empty_emphasize_fallback: float) -> float:
    """ML-or-fallback primary score for one item.

    `empty_emphasize_fallback` is what the caller used as the score before
    an ML backend existed, for the case where there's nothing to emphasize:
    rank_foods/rank_recipes fall back to density, meal_plan._pick falls back
    to a flat 0.0. Kept explicit per call site rather than hardcoded here so
    each one's pre-ML behavior is unchanged whenever no trained model file
    is present (the default on a fresh checkout).
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


def active_backend() -> str:
    """Which scorer is actually in effect right now: "ml" if a trained model
    file is present and loads cleanly, "linear" otherwise."""
    return "ml" if recommender.load_model() is not None else "linear"


def rank_foods(foods: list[Food], emphasize: list[str], targets: dict,
               top_n: int = 10) -> list[dict]:
    scored = []
    for food in foods:
        score = _score_one(
            food.nutrients, food.food_group, food.tags, emphasize, targets,
            empty_emphasize_fallback=_density_score(food.nutrients),
        )
        scored.append((score, food))
    scored.sort(key=lambda pair: (-pair[0], pair[1].food_id))
    return [
        {"food_id": f.food_id, "name_en": f.name_en, "name_bn": f.name_bn,
         "score": round(s, 3), "tags": list(f.tags),
         "food_group": f.food_group, "kcal_per_100g": round(f.nutrients["kcal"])}
        for s, f in scored[:top_n] if s > 0
    ]


def rank_recipes(recipes: list[Recipe], emphasize: list[str], targets: dict,
                 top_n: int = 10) -> list[dict]:
    scored = []
    for recipe in recipes:
        score = _score_one(
            recipe.per_serving, None, recipe.tags, emphasize, targets,
            empty_emphasize_fallback=_density_score(recipe.per_serving),
        )
        scored.append((score, recipe))
    scored.sort(key=lambda pair: (-pair[0], pair[1].recipe_id))
    return [
        {"recipe_id": r.recipe_id, "name_en": r.name_en, "name_bn": r.name_bn,
         "score": round(s, 3), "tags": list(r.tags),
         "per_serving_kcal": r.per_serving["kcal"]}
        for s, r in scored[:top_n] if s > 0
    ]
