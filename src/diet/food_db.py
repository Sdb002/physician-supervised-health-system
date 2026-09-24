"""Loader for data/food/bd_food.csv.

Tolerant of an empty or missing file (returns []) so the app runs before the
real dataset is added.
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path

from src.core.config import DATA_DIR

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
            foods.append(Food(
                food_id=row["food_id"].strip(),
                name_en=row["name_en"].strip(),
                name_bn=(row.get("name_bn") or "").strip(),
                food_group=(row.get("food_group") or "other").strip(),
                nutrients=nutrients,
                tags=_split_tags(row.get("tags") or ""),
                source=(row.get("source") or "").strip(),
            ))
    return foods


def food_index(foods: list[Food]) -> dict[str, Food]:
    return {f.food_id: f for f in foods}
