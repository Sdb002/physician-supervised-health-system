"""Loader for data/food/bd_food.csv.

Tolerant of an empty or missing file (returns []) so the app runs before the
real dataset is added.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.core.config import DATA_DIR
from src.diet.restriction_tags import food_restriction_tags

FOOD_CSV = DATA_DIR / "food" / "bd_food.csv"

NUTRIENT_COLUMNS = [
    "kcal", "protein_g", "carb_g", "fat_g", "fiber_g",
    "iron_mg", "calcium_mg", "zinc_mg", "folate_ug",
    "vit_a_ug", "vit_c_mg", "sodium_mg", "potassium_mg",
]

# Canonical food_group vocabulary — single source of truth, used by
# scripts/validate_datasets.py and src/diet/recommender.py.
FOOD_GROUPS = (
    "grain", "legume", "vegetable", "fruit", "fish", "meat", "egg",
    "dairy", "oil", "sweet", "spice", "other",
)


@dataclass(frozen=True)
class Food:
    food_id: str
    name_en: str
    name_bn: str
    food_group: str
    nutrients: dict  # per 100 g edible portion
    # the table's tags, then the restriction tags read off group and name
    tags: tuple = field(default_factory=tuple)
    source: str = ""


def _split_tags(raw: str) -> tuple:
    return tuple(t.strip() for t in (raw or "").split("|") if t.strip())


def load_foods(path: Path | None = None) -> list[Food]:
    path = path or FOOD_CSV
    if not path.exists():
        return []
    foods: list[Food] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not (row.get("food_id") or "").strip():
                continue
            nutrients = {col: float(row[col] or 0) for col in NUTRIENT_COLUMNS}
            name_en = row["name_en"].strip()
            food_group = (row.get("food_group") or "other").strip()
            foods.append(Food(
                food_id=row["food_id"].strip(),
                name_en=name_en,
                name_bn=(row.get("name_bn") or "").strip(),
                food_group=food_group,
                nutrients=nutrients,
                tags=(_split_tags(row.get("tags") or "")
                      + food_restriction_tags(name_en, food_group)),
                source=(row.get("source") or "").strip(),
            ))
    return foods


_PARENTHETICAL = re.compile(r"\s*\([^)]*\)")


def display_name(name_en: str) -> str:
    """A food-table name as a person would say it. Table rows read like
    "Guava, green, raw" or "Milk, cow, whole fat (pasteurized, UTH)"; in a
    plan, "raw" and bracketed source notes are noise, so they go."""
    parts = [p.strip() for p in _PARENTHETICAL.sub("", name_en).split(",")]
    kept = [p for p in parts if p and p.lower() != "raw"]
    return ", ".join(kept) or name_en


def food_index(foods: list[Food]) -> dict[str, Food]:
    return {f.food_id: f for f in foods}


def recommendable_foods(foods: list[Food]) -> list[Food]:
    """The foods the engine may recommend on its own (top foods, meal plan):
    those tagged `bangladeshi` — listed in the Food Composition Table for
    Bangladesh 2013 or used in a household recipe. The table's IFCT/USDA rows
    were compiled to fill nutrient gaps and include foods rarely eaten in
    Bangladesh (Indian millets, marine fish, offal); they still supply recipe
    nutrients and stay selectable in the physician's plan editor."""
    return [f for f in foods if "bangladeshi" in f.tags]


def untracked_nutrients(foods: list[Food]) -> frozenset[str]:
    """Nutrient columns no food in the table has a value for. The current
    dataset's source records no folate at all, so a plan can't be scored or
    reported on it - better said plainly than shown as 0% coverage."""
    return frozenset(c for c in NUTRIENT_COLUMNS if foods and all(f.nutrients[c] <= 0 for f in foods))


def eaten_in_portions(foods: list[Food]) -> list[Food]:
    """Drops seasonings (the spice group) and brewed concentrates (tea and
    coffee powder): they are used by the gram, so a "foods that suit your
    plan" list is the wrong place for them, however dense they are per 100 g
    or per 100 kcal."""
    return [f for f in foods if f.food_group != "spice" and "brewed_beverage" not in f.tags]
