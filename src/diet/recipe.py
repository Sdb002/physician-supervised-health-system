"""Recipes: metadata + ingredient join → computed per-serving nutrition.

recipes.csv carries no nutrient columns by design; nutrition is always derived
here from bd_food.csv so there is a single source of truth — a corrected food
row flows into every recipe that uses it.

Per-serving nutrition follows the FAO/INFOODS mixed-recipe method the recipe
dataset was built with: each ingredient's raw edible grams x the food table's
per-100 g values, with vitamin A and C multiplied by that ingredient's USDA
Release 6 retention factor (rf_vit_a / rf_vit_c in recipe_ingredients.csv) for
cooking losses; the sum is divided by servings. Yield (cooked weight) changes
only serving_size_g, never per-serving nutrients.

Exclusion-tag inheritance (documented heuristic):
- an ingredient's exclusion tag (high_sodium / high_sugar / high_fat) is
  inherited when that ingredient makes up >= 25% of the recipe's weight;
- a recipe is tagged high_sodium when one serving exceeds 600 mg sodium
  (30% of the WHO 2000 mg/day ceiling in a single dish; also the US FDA
  "healthy" ceiling for a main dish, 21 CFR 101.65);
- a recipe is tagged high_sugar when ingredients tagged added_sugar supply
  more than 10% of its energy (WHO 2015 free-sugars guideline) — this is what
  catches milk sweets like payesh, where sugar is a small share of the weight.

Restriction tags (contains_beef, contains_egg, liver, ... - see
src/diet/restriction_tags.py) are inherited from every ingredient whatever its
share: a spoon of ghee makes a dish dairy, and a little liver makes it liver.
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path

from src.core.config import DATA_DIR
from src.diet.food_db import NUTRIENT_COLUMNS, Food
from src.diet.restriction_tags import RESTRICTION_TAGS

RECIPES_CSV = DATA_DIR / "recipe" / "recipes.csv"
INGREDIENTS_CSV = DATA_DIR / "recipe" / "recipe_ingredients.csv"
STEPS_CSV = DATA_DIR / "recipe" / "recipe_steps.csv"

EXCLUSION_TAGS = {"high_sodium", "high_sugar", "high_fat"}
_INHERIT_WEIGHT_SHARE = 0.25
_SODIUM_MG_PER_SERVING_CAP = 600.0
_ADDED_SUGAR_ENERGY_SHARE = 0.10

# Table salt is 39 g of sodium in 100 g. Nothing else a kitchen cooks with
# comes near it (baking powder, the next saltiest row of the food table, is
# under 12 g), so an ingredient at or above this is the salt the cook adds.
_SALT_MIN_SODIUM_MG_PER_100G = 30000.0

# nutrient column -> its retention-factor column in recipe_ingredients.csv
RETENTION_COLUMNS = {"vit_a_ug": "rf_vit_a", "vit_c_mg": "rf_vit_c"}


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
    category: str = ""
    diet_type: str = ""
    # 1-10 from the recipe dataset: 10 = the most commonly cooked household
    # dish, 1 = rare/special. None when the source gives no score.
    weekly_frequency_score: int | None = None
    frequency_tier: str = ""
    serving_size_g: float | None = None
    cooking_method: str = ""
    total_time_min: int | None = None
    notes: str = ""
    group_shares: dict = field(default_factory=dict)  # food_group -> share of raw weight
    # grams of oil, ghee or butter the recipe cooks one serving in
    cooking_fat_g: float = 0.0
    # grams of salt the recipe adds to one serving, and the sodium in it
    salt_g: float = 0.0
    salt_sodium_mg: float = 0.0
    ingredient_lines: tuple = ()  # display rows, in recipe order
    steps: tuple = ()


def _split(raw: str) -> tuple:
    return tuple(t.strip() for t in (raw or "").split("|") if t.strip())


def _optional_int(raw: str | None) -> int | None:
    raw = (raw or "").strip()
    return int(float(raw)) if raw else None


def _optional_float(raw: str | None) -> float | None:
    raw = (raw or "").strip()
    return float(raw) if raw else None


def per_serving_nutrients(ingredients: list[tuple[str, float]], servings: int,
                          foods: dict[str, Food],
                          retention: list[dict] | None = None) -> dict:
    """`retention`, when given, is aligned with `ingredients`: one
    {nutrient column: factor} dict per ingredient (missing = no loss)."""
    total = {col: 0.0 for col in NUTRIENT_COLUMNS}
    for index, (food_id, qty_g) in enumerate(ingredients):
        food = foods[food_id]
        factors = retention[index] if retention else {}
        for col in NUTRIENT_COLUMNS:
            total[col] += food.nutrients[col] * qty_g / 100.0 * factors.get(col, 1.0)
    return {col: round(total[col] / servings, 2) for col in NUTRIENT_COLUMNS}


def _inherited_tags(ingredients: list[tuple[str, float]], per_serving: dict,
                    foods: dict[str, Food]) -> set[str]:
    total_weight = sum(q for _, q in ingredients)
    inherited: set[str] = set()
    for food_id, _ in ingredients:
        inherited |= set(foods[food_id].tags) & RESTRICTION_TAGS
    if total_weight > 0:
        for food_id, qty_g in ingredients:
            if qty_g / total_weight >= _INHERIT_WEIGHT_SHARE:
                inherited |= set(foods[food_id].tags) & EXCLUSION_TAGS
    if per_serving.get("sodium_mg", 0) > _SODIUM_MG_PER_SERVING_CAP:
        inherited.add("high_sodium")
    total_kcal = sum(foods[f].nutrients["kcal"] * q / 100.0 for f, q in ingredients)
    sugar_kcal = sum(foods[f].nutrients["kcal"] * q / 100.0
                     for f, q in ingredients if "added_sugar" in foods[f].tags)
    if total_kcal > 0 and sugar_kcal / total_kcal > _ADDED_SUGAR_ENERGY_SHARE:
        inherited.add("high_sugar")
    return inherited


def group_shares(ingredients: list[tuple[str, float]], foods: dict[str, Food]) -> dict:
    """Share of the recipe's raw ingredient weight per food group."""
    total = sum(q for _, q in ingredients)
    shares: dict[str, float] = {}
    if total <= 0:
        return shares
    for food_id, qty_g in ingredients:
        group = foods[food_id].food_group
        shares[group] = shares.get(group, 0.0) + qty_g / total
    return {g: round(s, 4) for g, s in sorted(shares.items())}


def cooking_fat_per_serving(ingredients: list[tuple[str, float]], servings: int,
                            foods: dict[str, Food]) -> float:
    """Grams of added fat (the food table's oil group: oils, ghee, butter)
    per serving. The food table has no saturated-fat column, so this and the
    serving's total fat are what a recipe can report about its fat."""
    added = sum(qty_g for food_id, qty_g in ingredients if foods[food_id].food_group == "oil")
    return round(added / servings, 1)


def added_salt_per_serving(ingredients: list[tuple[str, float]], servings: int,
                           foods: dict[str, Food]) -> tuple[float, float]:
    """(grams of salt, mg of sodium in it) the recipe adds to one serving.
    This is the part of a dish's sodium the cook decides; the rest comes
    with the fish, meat, eggs and vegetables themselves."""
    grams = sodium_mg = 0.0
    for food_id, qty_g in ingredients:
        per_100g = foods[food_id].nutrients["sodium_mg"]
        if per_100g >= _SALT_MIN_SODIUM_MG_PER_100G:
            grams += qty_g
            sodium_mg += per_100g * qty_g / 100.0
    return round(grams / servings, 3), round(sodium_mg / servings, 2)


def _load_steps(path: Path | None) -> dict[str, list[tuple[int, str]]]:
    steps: dict[str, list[tuple[int, str]]] = {}
    if path is None or not path.exists():
        return steps
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rid = (row.get("recipe_id") or "").strip()
            if rid:
                steps.setdefault(rid, []).append(
                    (int(row["step_no"]), row["instruction"].strip())
                )
    return {rid: sorted(items) for rid, items in steps.items()}


def load_recipes(foods: dict[str, Food],
                 recipes_path: Path | None = None,
                 ingredients_path: Path | None = None,
                 steps_path: Path | None = None) -> list[Recipe]:
    # steps default to the real file only alongside the real recipe files
    if steps_path is None and recipes_path is None:
        steps_path = STEPS_CSV
    recipes_path = recipes_path or RECIPES_CSV
    ingredients_path = ingredients_path or INGREDIENTS_CSV
    if not recipes_path.exists() or not ingredients_path.exists():
        return []

    rows_by_recipe: dict[str, list[dict]] = {}
    with open(ingredients_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rid = (row.get("recipe_id") or "").strip()
            if rid:
                rows_by_recipe.setdefault(rid, []).append(row)
    steps_by_recipe = _load_steps(steps_path)

    recipes: list[Recipe] = []
    with open(recipes_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rid = (row.get("recipe_id") or "").strip()
            if not rid:
                continue
            rows = sorted(rows_by_recipe.get(rid, []),
                          key=lambda r: _optional_int(r.get("seq")) or 0)
            ingredients = [(r["food_id"].strip(), float(r["qty_g"])) for r in rows]
            # skip recipes whose ingredients reference foods not (yet) in the DB
            if not ingredients or any(fid not in foods for fid, _ in ingredients):
                continue
            retention = [
                {col: float(r[rf_col]) for col, rf_col in RETENTION_COLUMNS.items()
                 if (r.get(rf_col) or "").strip()}
                for r in rows
            ]
            servings = int(row["servings"])
            per_serving = per_serving_nutrients(ingredients, servings, foods, retention)
            tags = set(_split(row.get("tags") or ""))
            tags |= _inherited_tags(ingredients, per_serving, foods)
            salt_g, salt_sodium_mg = added_salt_per_serving(ingredients, servings, foods)
            lines = tuple(
                {"food_id": food_id, "name_en": foods[food_id].name_en,
                 "name_bn": foods[food_id].name_bn,
                 "household_measure": (r.get("household_measure") or "").strip(),
                 "qty_g": qty_g, "optional": (r.get("is_optional") or "0").strip() == "1"}
                for (food_id, qty_g), r in zip(ingredients, rows)
            )
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
                category=(row.get("category") or "").strip(),
                diet_type=(row.get("diet_type") or "").strip(),
                weekly_frequency_score=_optional_int(row.get("weekly_frequency_score")),
                frequency_tier=(row.get("frequency_tier") or "").strip(),
                serving_size_g=_optional_float(row.get("serving_size_g")),
                cooking_method=(row.get("cooking_method") or "").strip(),
                total_time_min=_optional_int(row.get("total_time_min")),
                notes=(row.get("notes") or "").strip(),
                group_shares=group_shares(ingredients, foods),
                cooking_fat_g=cooking_fat_per_serving(ingredients, servings, foods),
                salt_g=salt_g,
                salt_sodium_mg=salt_sodium_mg,
                ingredient_lines=lines,
                steps=tuple(text for _, text in steps_by_recipe.get(rid, [])),
            ))
    return recipes
