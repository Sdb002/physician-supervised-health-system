"""Validate all three datasets against their schemas, plus referential
cross-checks, and write a validation_report.md next to each dataset.

Run from the project root:  .venv\\Scripts\\python.exe scripts\\validate_datasets.py
Exit code 1 if any dataset has errors (warnings don't fail the run).
"""

import csv
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import DATA_DIR, REFERENCE_DIR, load_yaml  # noqa: E402
from src.diet.food_db import FOOD_GROUPS  # noqa: E402

FOOD_TAGS = {"staple", "high_protein", "lean", "high_fiber", "iron_rich",
             "calcium_rich", "potassium_rich", "leafy_green", "fruit", "dairy",
             "probiotic", "omega3", "oil", "high_fat", "high_sugar",
             "high_sodium", "dessert", "added_sugar", "brewed_beverage",
             "bangladeshi"}
NUTRIENT_COLUMNS = ["kcal", "protein_g", "carb_g", "fat_g", "fiber_g", "iron_mg",
                    "calcium_mg", "zinc_mg", "folate_ug", "vit_a_ug", "vit_c_mg",
                    "sodium_mg", "potassium_mg"]
MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack"}
# weekly_frequency_score -> frequency_tier, as defined by the recipe
# dataset's Frequency_Scale sheet (10 = the most commonly cooked dish)
FREQUENCY_TIERS = {
    10: "Daily staple", 9: "Near-daily", 8: "Very frequent", 7: "Very frequent",
    6: "Frequent", 5: "Weekly", 4: "Regular", 3: "Occasional",
    2: "Festive/seasonal", 1: "Rare/special",
}
EXERCISE_CATEGORIES = {"aerobic", "strength", "flexibility"}
CONTRA_TAGS = {"high_impact", "high_exertion", "knee_stress", "wrist_stress",
               "abdominal_pressure", "supine_position", "balance_required"}


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate_food() -> tuple[list[str], list[str], int]:
    errors, warnings = [], []
    rows = read_csv(DATA_DIR / "food" / "bd_food.csv")
    seen_ids = set()
    for i, row in enumerate(rows, start=2):
        rid = row.get("food_id", "")
        if not re.fullmatch(r"F\d+", rid):
            errors.append(f"row {i}: bad food_id {rid!r}")
        if rid in seen_ids:
            errors.append(f"row {i}: duplicate food_id {rid}")
        seen_ids.add(rid)
        for col in NUTRIENT_COLUMNS:
            try:
                value = float(row[col])
                if value < 0:
                    errors.append(f"row {i} ({rid}): {col} negative")
                if col == "kcal" and value > 900:
                    errors.append(f"row {i} ({rid}): kcal {value} > 900/100g")
            except (ValueError, KeyError):
                errors.append(f"row {i} ({rid}): {col} not numeric")
        if row.get("food_group") not in FOOD_GROUPS:
            errors.append(f"row {i} ({rid}): unknown food_group {row.get('food_group')!r}")
        for tag in filter(None, (row.get("tags") or "").split("|")):
            if tag not in FOOD_TAGS:
                warnings.append(f"row {i} ({rid}): unregistered tag {tag!r}")
        if not (row.get("source") or "").strip():
            errors.append(f"row {i} ({rid}): missing source citation")
        if (row.get("source") or "").strip() == "DEMO":
            pass  # counted below
    demo = sum(1 for r in rows if (r.get("source") or "").strip() == "DEMO")
    if demo:
        warnings.append(f"{demo}/{len(rows)} rows are DEMO placeholders — replace with real data")
    return errors, warnings, len(rows)


def validate_recipes(food_ids: set[str]) -> tuple[list[str], list[str], int]:
    errors, warnings = [], []
    recipes = read_csv(DATA_DIR / "recipe" / "recipes.csv")
    ingredients = read_csv(DATA_DIR / "recipe" / "recipe_ingredients.csv")
    steps_path = DATA_DIR / "recipe" / "recipe_steps.csv"
    steps = read_csv(steps_path) if steps_path.exists() else []
    recipe_ids = set()
    for i, row in enumerate(recipes, start=2):
        rid = row.get("recipe_id", "")
        if not re.fullmatch(r"BDR-\d{3}", rid):
            errors.append(f"recipes row {i}: bad recipe_id {rid!r}")
        if rid in recipe_ids:
            errors.append(f"recipes row {i}: duplicate recipe_id {rid}")
        recipe_ids.add(rid)
        try:
            if int(row["servings"]) <= 0:
                errors.append(f"recipes row {i} ({rid}): servings must be > 0")
        except (ValueError, KeyError):
            errors.append(f"recipes row {i} ({rid}): servings not an integer")
        try:
            if float(row["serving_size_g"]) <= 0:
                errors.append(f"recipes row {i} ({rid}): serving_size_g must be > 0")
        except (ValueError, KeyError):
            errors.append(f"recipes row {i} ({rid}): serving_size_g not numeric")
        try:
            score = int(row["weekly_frequency_score"])
            if not 1 <= score <= 10:
                errors.append(f"recipes row {i} ({rid}): weekly_frequency_score {score} outside 1-10")
            elif row.get("frequency_tier") != FREQUENCY_TIERS[score]:
                warnings.append(
                    f"recipes row {i} ({rid}): frequency_tier {row.get('frequency_tier')!r} "
                    f"does not match score {score} ({FREQUENCY_TIERS[score]!r})"
                )
        except (ValueError, KeyError):
            errors.append(f"recipes row {i} ({rid}): weekly_frequency_score not an integer")
        meal_types = list(filter(None, (row.get("meal_type") or "").split("|")))
        if not meal_types:
            errors.append(f"recipes row {i} ({rid}): no meal_type")
        for mt in meal_types:
            if mt not in MEAL_TYPES:
                errors.append(f"recipes row {i} ({rid}): unknown meal_type {mt!r}")
        if not (row.get("source") or "").strip():
            errors.append(f"recipes row {i} ({rid}): missing source citation")

    with_ingredients = set()
    for i, row in enumerate(ingredients, start=2):
        rid, fid = row.get("recipe_id", ""), row.get("food_id", "")
        if rid not in recipe_ids:
            errors.append(f"ingredients row {i}: unknown recipe_id {rid!r}")
        if fid not in food_ids:
            errors.append(f"ingredients row {i}: food_id {fid!r} not in bd_food.csv")
        try:
            if float(row["qty_g"]) <= 0:
                errors.append(f"ingredients row {i}: qty_g must be > 0")
        except (ValueError, KeyError):
            errors.append(f"ingredients row {i}: qty_g not numeric")
        for rf in ("rf_vit_a", "rf_vit_c"):
            try:
                if not 0 < float(row[rf]) <= 1:
                    errors.append(f"ingredients row {i}: {rf} must be in (0, 1]")
            except (ValueError, KeyError):
                errors.append(f"ingredients row {i}: {rf} not numeric")
        with_ingredients.add(rid)
    for rid in recipe_ids - with_ingredients:
        errors.append(f"recipe {rid} has no ingredients")

    step_numbers: dict[str, list[int]] = {}
    for i, row in enumerate(steps, start=2):
        rid = row.get("recipe_id", "")
        if rid not in recipe_ids:
            errors.append(f"steps row {i}: unknown recipe_id {rid!r}")
        if not (row.get("instruction") or "").strip():
            errors.append(f"steps row {i}: empty instruction")
        try:
            step_numbers.setdefault(rid, []).append(int(row["step_no"]))
        except (ValueError, KeyError):
            errors.append(f"steps row {i}: step_no not an integer")
    for rid, numbers in step_numbers.items():
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            errors.append(f"recipe {rid}: step numbers are not 1..{len(numbers)}")
    for rid in sorted(recipe_ids - set(step_numbers)):
        warnings.append(f"recipe {rid} has no cooking steps")
    return errors, warnings, len(recipes)


def validate_exercises() -> tuple[list[str], list[str], int]:
    errors, warnings = [], []
    rows = read_csv(DATA_DIR / "lifestyle" / "exercises.csv")
    seen_ids = set()
    for i, row in enumerate(rows, start=2):
        eid = row.get("exercise_id", "")
        if not re.fullmatch(r"E\d+", eid):
            errors.append(f"row {i}: bad exercise_id {eid!r}")
        if eid in seen_ids:
            errors.append(f"row {i}: duplicate exercise_id {eid}")
        seen_ids.add(eid)
        if row.get("category") not in EXERCISE_CATEGORIES:
            errors.append(f"row {i} ({eid}): unknown category {row.get('category')!r}")
        try:
            met = float(row["met_value"])
            if not 0 < met <= 20:
                errors.append(f"row {i} ({eid}): met_value {met} outside (0, 20]")
            level = row.get("intensity_level")
            expected = "light" if met < 3 else "moderate" if met < 6 else "vigorous"
            if level != expected:
                errors.append(
                    f"row {i} ({eid}): intensity_level {level!r} inconsistent with "
                    f"MET {met} (expected {expected!r})"
                )
        except (ValueError, KeyError):
            errors.append(f"row {i} ({eid}): met_value not numeric")
        for tag in filter(None, (row.get("contra_tags") or "").split("|")):
            if tag not in CONTRA_TAGS:
                warnings.append(f"row {i} ({eid}): unregistered contra_tag {tag!r}")
    return errors, warnings, len(rows)


def cross_check_contraindications() -> list[str]:
    """Every exclusion tag referenced by a condition rule should exist in the
    corresponding vocabulary, or the rule can never fire."""
    warnings = []
    rules = load_yaml(REFERENCE_DIR / "contraindications.yaml")["conditions"]
    for condition, rule in rules.items():
        for tag in rule.get("exclude_food_tags") or []:
            if tag not in FOOD_TAGS:
                warnings.append(f"{condition}: food tag {tag!r} not in food vocabulary")
        for tag in rule.get("exclude_exercise_tags") or []:
            if tag not in CONTRA_TAGS:
                warnings.append(f"{condition}: exercise tag {tag!r} not in contra vocabulary")
    return warnings


def write_report(dataset_dir: Path, name: str, errors: list[str],
                 warnings: list[str], count: int) -> None:
    status = "FAIL" if errors else "PASS"
    lines = [
        f"# Validation report — {name}",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- Rows: {count}",
        f"- Status: **{status}** ({len(errors)} errors, {len(warnings)} warnings)",
        "",
    ]
    if errors:
        lines += ["## Errors", ""] + [f"- {e}" for e in errors] + [""]
    if warnings:
        lines += ["## Warnings", ""] + [f"- {w}" for w in warnings] + [""]
    if not errors and not warnings:
        lines += ["No issues found.", ""]
    lines += ["_Generated by `scripts/validate_datasets.py`._"]
    (dataset_dir / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    food_rows = read_csv(DATA_DIR / "food" / "bd_food.csv")
    food_ids = {r["food_id"] for r in food_rows if r.get("food_id")}

    food_errors, food_warnings, n_food = validate_food()
    recipe_errors, recipe_warnings, n_recipes = validate_recipes(food_ids)
    ex_errors, ex_warnings, n_ex = validate_exercises()
    ex_warnings += cross_check_contraindications()

    write_report(DATA_DIR / "food", "bd_food.csv", food_errors, food_warnings, n_food)
    write_report(DATA_DIR / "recipe", "recipes", recipe_errors, recipe_warnings, n_recipes)
    write_report(DATA_DIR / "lifestyle", "exercises.csv", ex_errors, ex_warnings, n_ex)

    total_errors = len(food_errors) + len(recipe_errors) + len(ex_errors)
    total_warnings = len(food_warnings) + len(recipe_warnings) + len(ex_warnings)
    print(f"food: {n_food} rows | recipes: {n_recipes} | exercises: {n_ex}")
    print(f"{total_errors} errors, {total_warnings} warnings — reports written to data/*/validation_report.md")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
