"""Recipes: metadata + ingredient join → computed per-serving nutrition.

recipes.csv carries no nutrient columns by design; nutrition is always derived
here from bd_food.csv so there is a single source of truth.

Exclusion-tag inheritance (documented heuristic, v0.1):
- an ingredient's exclusion tag (high_sodium / high_sugar / high_fat) is
  inherited when that ingredient makes up >= 25% of the recipe's weight;
- additionally, a recipe is tagged high_sodium when one serving exceeds
  600 mg sodium (30% of the WHO 2000 mg/day ceiling in a single dish).
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from src.core.config import DATA_DIR
from src.diet.food_db import NUTRIENT_COLUMNS, Food

RECIPES_CSV = DATA_DIR / "recipe" / "recipes.csv"
INGREDIENTS_CSV = DATA_DIR / "recipe" / "recipe_ingredients.csv"

EXCLUSION_TAGS = {"high_sodium", "high_sugar", "high_fat"}
_INHERIT_WEIGHT_SHARE = 0.25
_SODIUM_MG_PER_SERVING_CAP = 600.0


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    name_en: str
    name_bn: str
    servings: int
    meal_type: tuple
    tags: tuple  # metadata tags + inherited exclusion tags
    source: str
    ingredients: tuple  # of (food_id, qty_g)
    per_serving: dict  # computed nutrients per serving


def _split(raw: str) -> tuple:
    return tuple(t.strip() for t in (raw or "").split("|") if t.strip())


def per_serving_nutrients(ingredients: list[tuple[str, float]], servings: int,
                          foods: dict[str, Food]) -> dict:
    total = {col: 0.0 for col in NUTRIENT_COLUMNS}
    for food_id, qty_g in ingredients:
        food = foods[food_id]
        for col in NUTRIENT_COLUMNS:
            total[col] += food.nutrients[col] * qty_g / 100.0
    return {col: round(total[col] / servings, 2) for col in NUTRIENT_COLUMNS}


def _inherited_tags(ingredients: list[tuple[str, float]], per_serving: dict,
                    foods: dict[str, Food]) -> set[str]:
    total_weight = sum(q for _, q in ingredients)
    inherited: set[str] = set()
    if total_weight > 0:
        for food_id, qty_g in ingredients:
            if qty_g / total_weight >= _INHERIT_WEIGHT_SHARE:
                inherited |= set(foods[food_id].tags) & EXCLUSION_TAGS
    if per_serving.get("sodium_mg", 0) > _SODIUM_MG_PER_SERVING_CAP:
        inherited.add("high_sodium")
    return inherited


def load_recipes(foods: dict[str, Food],
                 recipes_path: Path | None = None,
                 ingredients_path: Path | None = None) -> list[Recipe]:
    recipes_path = recipes_path or RECIPES_CSV
    ingredients_path = ingredients_path or INGREDIENTS_CSV
    if not recipes_path.exists() or not ingredients_path.exists():
        return []

    by_recipe: dict[str, list[tuple[str, float]]] = {}
    with open(ingredients_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rid = (row.get("recipe_id") or "").strip()
            if rid:
                by_recipe.setdefault(rid, []).append(
                    (row["food_id"].strip(), float(row["qty_g"]))
                )

    recipes: list[Recipe] = []
    with open(recipes_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rid = (row.get("recipe_id") or "").strip()
            if not rid:
                continue
            ingredients = by_recipe.get(rid, [])
            # skip recipes whose ingredients reference foods not (yet) in the DB
            if not ingredients or any(fid not in foods for fid, _ in ingredients):
                continue
            servings = int(row["servings"])
            per_serving = per_serving_nutrients(ingredients, servings, foods)
            tags = set(_split(row.get("tags") or ""))
            tags |= _inherited_tags(ingredients, per_serving, foods)
            recipes.append(Recipe(
                recipe_id=rid,
                name_en=row["name_en"].strip(),
                name_bn=(row.get("name_bn") or "").strip(),
                servings=servings,
                meal_type=_split(row.get("meal_type") or ""),
                tags=tuple(sorted(tags)),
                source=(row.get("source") or "").strip(),
                ingredients=tuple(ingredients),
                per_serving=per_serving,
            ))
    return recipes
