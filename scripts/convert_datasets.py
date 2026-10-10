"""Convert the raw food and recipe datasets into the app's canonical CSVs.

Inputs (raw exports — never hand-edited; every change to a source value is a
documented, logged correction below):
  data/food/raw/Bangladeshi_Indian_Foods_Nutrition_700_antioxidants.csv
      700 foods, per 100 g edible portion, compiled from FCTB 2013 (381 rows),
      IFCT 2017 (294), USDA SR Legacy (23) and literature (2).
  data/recipe/raw/bd_recipes_250.csv, bd_recipe_ingredients_250.csv,
  bd_recipe_steps_250.csv
      Verbatim CSV exports of the Recipes / Ingredients / Steps sheets of
      data/recipe/raw/Bangladeshi_Recipe_Dataset_250.xlsx (the master workbook,
      which also holds the method, Sources, retention/yield factor tables and
      the FCTB cooked-dish benchmark). Each ingredient's food_no is the No. of
      a row in the food file above.

Outputs:
  data/food/bd_food.csv                schema: data/food/schema.md
  data/food/corrections_log.csv        every source cell this script changed
  data/recipe/recipes.csv              schema: data/recipe/schema.md
  data/recipe/recipe_ingredients.csv
  data/recipe/recipe_steps.csv

Run from the project root:  .venv\\Scripts\\python.exe scripts\\convert_datasets.py
then validate:              .venv\\Scripts\\python.exe scripts\\validate_datasets.py

Conversion decisions (documented so they can be audited/revised):
- IDs: food_id = "F" + the source No. zero-padded (F001-F700), so every food
  traces back to its source row and to the recipe workbook's food_no.
  recipe_id keeps the source id (BDR-001..BDR-250).
- Blank (not reported) and "Tr" (trace) become 0.0 — conservative for
  ranking: a food earns no credit for an unmeasured nutrient. The source has
  no folate column, so folate_ug is 0 for every row (as before).
- The 28 IFCT 2017 cultivar rows (Brinjal-1..21, Chillies, green-1..7) are
  left out: they are one food each for a recommender, already covered by
  FCTB rows (F089 brinjal, F124 green chilli) and IFCT's own all-varieties
  mean (F288), and no recipe uses them.
- Names: FCTB's "*" cooked-dish marker is dropped ("Lentil, boiled* (without
  salt)" -> "Lentil, boiled (without salt)"). name_bn is the Bangla-script name
  where the source has one, otherwise the Roman transliteration.
- food_group comes from the source Category (Leafy Vegetables and Roots &
  Tubers -> vegetable; Nuts & Seeds and Beverages -> other). In Sugars &
  Miscellaneous only sugar, honey, jaggery and sugarcane juice are "sweet";
  salt, baking powder, betel leaves and toddy are "other".
- Tags are derived, not hand-curated. Thresholds per 100 g:
    iron_rich       iron_mg      >= 3
    calcium_rich    calcium_mg   >= 120     (15% of 800 mg NRV)
    potassium_rich  potassium_mg >= 300     (15% of 2000 mg NRV)
    high_sodium     sodium_mg    >= 400     (~FDA "high": 20% of 2300 mg DV)
    high_fat        fat_g        >= 17.5    (UK FSA traffic-light "high")
    high_fiber      fiber_g      >= 6       (EU "high fibre" claim)
    high_protein    protein_g    >= 10
    lean            fish/meat with protein_g >= 15 and fat_g <= 5
  Group/category tags: leafy_green, fruit, dairy, oil, probiotic (yogurt/doi
  by name), high_sugar (sweet group, sugary beverages, sweetened condensed
  milk). Two tags are new with this dataset:
    added_sugar      the foods the recipe workbook classes as added sugar
                     (sugar, honey, jaggery x3, sweetened condensed milk);
                     src/diet/recipe.py uses it for the WHO 10%-of-energy
                     free-sugars rule on recipes
    brewed_beverage  tea and coffee *powder*: dry concentrates brewed from a
                     few grams, so their per-100 g values (6040 mg potassium
                     for tea powder) say nothing about a cup. The recommender
                     label penalizes them like spices.
    bangladeshi      listed in the Food Composition Table for Bangladesh 2013
                     or used in a household recipe of the recipe dataset. Only
                     these are recommended on their own (top foods, meal
                     plan): the IFCT/USDA rows were compiled to fill nutrient
                     gaps and include foods rarely eaten in Bangladesh (Indian
                     millets, marine fish, offal). Every row still supplies
                     recipe nutrients and stays in the physician's plan editor.

Corrections — each one fixes a source value that is demonstrably wrong; all
are written cell by cell to data/food/corrections_log.csv:
 1. Wrong-food gap fills reverted to "not reported". The source filled some
    FCTB gaps from IFCT 2017 rows of a *different food*: amaranth stem from
    amaranth seed (iron 9.33 mg in a 92%-water stem), amaranth leaves from
    amaranth seed, drumstick pods from drumstick leaves (vitamin A 17,542 ug),
    boiled cowpea pods from dried cowpea seed, dried lotus seeds from lotus
    root. Every field those fills supplied is blanked.
 2. IFCT vitamin A stored as beta-carotene. For every IFCT plant row the
    source's "Vit A (ug RAE)" equals its beta-carotene-equivalent column
    (120/120 rows), i.e. the /12 retinol-activity conversion was never applied
    — for 73 of those rows the stored "RAE" would need more beta-carotene than
    the food's total carotenoids, which is impossible. FCTB rows are correct
    (RAE = beta-carotene eq / 12). Fixed by RAE = beta-carotene eq / 12. Dairy
    rows (khoa, paneer) are left alone: their retinol cannot be reconstructed.
 3. The same unconverted IFCT value reached FCTB rows through gap fills that
    list "Vit A" (e.g. boiled orange sweet potato: 5,376 vs 719 raw). Fixed
    from the row's own beta-carotene eq / 12 when it has one, else the filled
    value / 12.
 4. Rows whose source values are blank or garbled are replaced with cited
    values (see VALUE_CORRECTIONS): spinach and chicken breast minerals
    (blank here; garbled in the previous FCT-BD export — spinach phosphorus
    471 mg, chicken magnesium 173 mg), bay leaf (every mineral = 1, a
    placeholder), dried lotus seed sodium (13,705 mg/100 g), amaranth leaf
    vitamin A (0 after correction 1).
 5. Missing energy computed with FCTB's own Atwater formula
    (4 x protein + 9 x fat + 4 x carbohydrate + 2 x fibre) where the macros
    exist: 8 IFCT oils ("energy not reported by IFCT for pure oils") and
    nigella seed. Five USDA dried herbs have no macros and stay at 0 kcal.
"""

import csv
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FOOD_RAW = PROJECT_ROOT / "data" / "food" / "raw" / "Bangladeshi_Indian_Foods_Nutrition_700_antioxidants.csv"
RECIPE_RAW = PROJECT_ROOT / "data" / "recipe" / "raw"
FOOD_OUT = PROJECT_ROOT / "data" / "food" / "bd_food.csv"
CORRECTIONS_OUT = PROJECT_ROOT / "data" / "food" / "corrections_log.csv"
RECIPES_OUT = PROJECT_ROOT / "data" / "recipe" / "recipes.csv"
INGREDIENTS_OUT = PROJECT_ROOT / "data" / "recipe" / "recipe_ingredients.csv"
STEPS_OUT = PROJECT_ROOT / "data" / "recipe" / "recipe_steps.csv"

RECIPE_SOURCE = "Bangladeshi Recipe Dataset 250, v2 (2026-09-27)"

# raw header -> canonical nutrient column (per 100 g edible portion)
NUTRIENT_MAP = {
    "Energy (kcal)": "kcal",
    "Protein (g)": "protein_g",
    "Carbohydrate (g)": "carb_g",
    "Fat (g)": "fat_g",
    "Dietary Fibre (g)": "fiber_g",
    "Iron (mg)": "iron_mg",
    "Calcium (mg)": "calcium_mg",
    "Zinc (mg)": "zinc_mg",
    "Vit A (ug RAE)": "vit_a_ug",
    "Vit C (mg)": "vit_c_mg",
    "Sodium (mg)": "sodium_mg",
    "Potassium (mg)": "potassium_mg",
}
BETA_CAROTENE = "Beta-Carotene Eq (ug)"
VIT_A = "Vit A (ug RAE)"

FOOD_COLUMNS = [
    "food_id", "name_en", "name_bn", "food_group",
    "kcal", "protein_g", "carb_g", "fat_g", "fiber_g",
    "iron_mg", "calcium_mg", "zinc_mg", "folate_ug",
    "vit_a_ug", "vit_c_mg", "sodium_mg", "potassium_mg",
    "tags", "source",
]

CATEGORY_GROUPS = {
    "Cereals & Grains": "grain",
    "Pulses & Legumes": "legume",
    "Vegetables": "vegetable",
    "Leafy Vegetables": "vegetable",
    "Roots & Tubers": "vegetable",
    "Nuts & Seeds": "other",
    "Spices & Herbs": "spice",
    "Fruits": "fruit",
    "Fish & Shellfish": "fish",
    "Meat & Poultry": "meat",
    "Eggs": "egg",
    "Milk & Dairy": "dairy",
    "Oils & Fats": "oil",
    "Beverages": "other",
    "Sugars & Miscellaneous": "other",  # sweet only for SWEET_FOODS below
}
PLANT_CATEGORIES = {
    "Cereals & Grains", "Pulses & Legumes", "Vegetables", "Leafy Vegetables",
    "Roots & Tubers", "Nuts & Seeds", "Spices & Herbs", "Fruits",
}
# Sugars & Miscellaneous rows that are sugars (the rest is salt, baking
# powder, betel leaves, toddy). By source No.
SWEET_FOODS = {693, 694, 695, 696, 698, 699}
# the recipe workbook's is_added_sugar classification (Foods_Source sheet)
ADDED_SUGAR_FOODS = {655, 693, 694, 695, 696, 698}
BREWED_BEVERAGE_FOODS = {683, 689}  # coffee powder, tea powder
NAME_FIXES = {696: "Jaggery liquid, date palm"}  # source typo "Jagggery"

# correction 1: gap fills that came from a different food (source No. -> donor)
WRONG_FOOD_GAP_FILLS = {
    76: "amaranth seed (IFCT 2017 A001)",
    128: "dried cowpea seed (IFCT 2017 B005)",
    131: "drumstick leaves (IFCT 2017 C019)",
    178: "amaranth seed (IFCT 2017 A002)",
    266: "lotus root (IFCT 2017 F005)",
}
# "Gap Filled" field names -> raw headers
GAP_FIELDS = {
    "Calcium": "Calcium (mg)", "Iron": "Iron (mg)", "Magnesium": "Magnesium (mg)",
    "Phosphorus": "Phosphorus (mg)", "Potassium": "Potassium (mg)",
    "Sodium": "Sodium (mg)", "Zinc": "Zinc (mg)", "Vit A": VIT_A,
    "Thiamin B1": "Thiamin B1 (mg)", "Riboflavin B2": "Riboflavin B2 (mg)",
    "Niacin": "Niacin (mg)", "Vit C": "Vit C (mg)",
}
IFCT_PLANT_DONORS = set("ABCDEFGHIJ")  # IFCT 2017 food-group letters for plant foods

# correction 4: (source No., raw header) -> (value, citation)
VALUE_CORRECTIONS = {
    (216, "Calcium (mg)"): (99, "USDA FDC 168462 Spinach, raw"),
    (216, "Iron (mg)"): (2.71, "USDA FDC 168462 Spinach, raw"),
    (216, "Zinc (mg)"): (0.53, "USDA FDC 168462 Spinach, raw"),
    (216, "Sodium (mg)"): (79, "USDA FDC 168462 Spinach, raw"),
    (216, "Potassium (mg)"): (558, "USDA FDC 168462 Spinach, raw"),
    (595, "Calcium (mg)"): (5, "USDA FDC 171077 Chicken breast, skinless, raw"),
    (595, "Iron (mg)"): (0.37, "USDA FDC 171077 Chicken breast, skinless, raw"),
    (595, "Zinc (mg)"): (0.68, "USDA FDC 171077 Chicken breast, skinless, raw"),
    (595, "Sodium (mg)"): (45, "USDA FDC 171077 Chicken breast, skinless, raw"),
    (595, "Potassium (mg)"): (334, "USDA FDC 171077 Chicken breast, skinless, raw"),
    (283, "Calcium (mg)"): (834, "previous FCT-BD export, FCTB 07_0001 (= USDA SR 02004)"),
    (283, "Iron (mg)"): (43, "previous FCT-BD export, FCTB 07_0001 (= USDA SR 02004)"),
    (283, "Zinc (mg)"): (3.7, "previous FCT-BD export, FCTB 07_0001 (= USDA SR 02004)"),
    (283, "Sodium (mg)"): (23, "previous FCT-BD export, FCTB 07_0001 (= USDA SR 02004)"),
    (283, "Potassium (mg)"): (529, "previous FCT-BD export, FCTB 07_0001 (= USDA SR 02004)"),
    (266, "Sodium (mg)"): (5, "USDA FDC 170149 Lotus seeds, dried"),
    (178, VIT_A): (146, "USDA FDC 168385 Amaranth leaves, raw"),
}

# recipe meal_slot tokens -> app meal types; the rest become descriptive tags
MEAL_SLOT_MAP = {
    "breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner", "snack": "snack",
    "iftar": "snack", "dessert": "snack", "beverage": "snack",
}
OCCASION_TAGS = {"festival", "iftar", "dessert", "beverage"}
ALLERGEN_COLUMNS = [
    "contains_dairy", "contains_egg", "contains_fish", "contains_shellfish",
    "contains_nuts_seeds_coconut", "contains_mustard_seed",
    "contains_gluten_wheat", "contains_beef",
]


def _read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _parse(cell: str) -> float | None:
    """None = not reported. Trace becomes 0.0."""
    cell = cell.strip()
    if not cell:
        return None
    if cell.lower() == "tr":
        return 0.0
    return float(cell)


def _fmt(value: float | None) -> str:
    return f"{round(value or 0.0, 3):g}"


class FoodRow:
    def __init__(self, raw: dict):
        self.raw = raw
        self.no = int(raw["No."])
        self.values = {col: _parse(raw[col]) for col in [*NUTRIENT_MAP, BETA_CAROTENE]}
        self.citations: list[str] = []

    @property
    def food_id(self) -> str:
        return f"F{self.no:03d}"


class CorrectionLog:
    def __init__(self):
        self.rows: list[dict] = []

    def set(self, food: FoodRow, column: str, value: float | None, rule: str, evidence: str):
        old = food.values.get(column)
        if old == value:
            return
        self.rows.append({
            "food_id": food.food_id, "name_en": food.raw["English Name"],
            "column": column, "source_value": "" if old is None else _fmt(old),
            "new_value": "" if value is None else _fmt(value),
            "rule": rule, "evidence": evidence,
        })
        food.values[column] = value


def _gap_fill(raw: dict) -> tuple[str | None, list[str]]:
    """'IFCT 2017 [C019]: Vit A, Thiamin B1' -> ('C019', [raw headers])."""
    match = re.match(r"IFCT 2017 \[([A-Z]\d+)\]:\s*(.+)", raw["Gap Filled"].strip())
    if not match:
        return None, []
    fields = [GAP_FIELDS[name.strip()] for name in match.group(2).split(",")]
    return match.group(1), fields


def _close(a: float, b: float) -> bool:
    # absolute slack: the source rounds beta-carotene to 1 decimal (1.05 vs 1.0)
    return abs(a - b) <= max(0.05 * b, 0.051)


def apply_corrections(foods: list[FoodRow], log: CorrectionLog) -> None:
    by_no = {f.no: f for f in foods}

    # 1. wrong-food gap fills -> not reported
    for no, donor in WRONG_FOOD_GAP_FILLS.items():
        food = by_no[no]
        _, fields = _gap_fill(food.raw)
        for column in fields:
            if column in food.values:
                log.set(food, column, None, "wrong-food gap fill reverted",
                        f"value was filled from {donor}, a different food")
        food.citations.append(f"gap fill from {donor} reverted")

    # 2. IFCT rows whose vitamin A is beta-carotene, not RAE
    for food in foods:
        if food.raw["Source"] != "IFCT 2017" or food.raw["Category"] == "Milk & Dairy":
            continue
        vit_a, beta = food.values[VIT_A], food.values[BETA_CAROTENE]
        if vit_a and beta and _close(vit_a, beta):
            log.set(food, VIT_A, beta / 12, "IFCT vitamin A: beta-carotene eq / 12",
                    "stored 'RAE' equals beta-carotene eq (no /12 applied)")

    # 3. IFCT-sourced vitamin A gap fills on FCTB rows
    for food in foods:
        donor, fields = _gap_fill(food.raw)
        if (donor is None or donor[0] not in IFCT_PLANT_DONORS
                or VIT_A not in fields or food.no in WRONG_FOOD_GAP_FILLS):
            continue
        vit_a, beta = food.values[VIT_A], food.values[BETA_CAROTENE]
        if not vit_a:
            continue
        if beta:
            log.set(food, VIT_A, beta / 12, "gap-filled vitamin A: own beta-carotene eq / 12",
                    f"vitamin A was filled from IFCT {donor} beta-carotene")
        else:
            log.set(food, VIT_A, vit_a / 12, "gap-filled vitamin A: filled value / 12",
                    f"vitamin A was filled from IFCT {donor} beta-carotene")

    # 4. cited replacements
    for (no, column), (value, citation) in VALUE_CORRECTIONS.items():
        food = by_no[no]
        log.set(food, column, float(value), "cited replacement", citation)
        if citation not in food.citations:
            food.citations.append(citation)

    # 5. missing energy from macros (FCTB Atwater formula)
    for food in foods:
        v = food.values
        if v["Energy (kcal)"] is not None:
            continue
        protein, fat, carb = v["Protein (g)"], v["Fat (g)"], v["Carbohydrate (g)"]
        if None in (protein, fat, carb):
            continue
        kcal = 4 * protein + 9 * fat + 4 * carb + 2 * (v["Dietary Fibre (g)"] or 0.0)
        log.set(food, "Energy (kcal)", min(kcal, 900.0), "energy from macros",
                "4P + 9F + 4C + 2 fibre (FCTB 2013 formula)")


def _food_group(food: FoodRow) -> str:
    if food.no in SWEET_FOODS:
        return "sweet"
    return CATEGORY_GROUPS[food.raw["Category"]]


def _derive_tags(food: FoodRow, group: str, n: dict, recipe_foods: set[int]) -> list[str]:
    tags = []
    if n["iron_mg"] >= 3:
        tags.append("iron_rich")
    if n["calcium_mg"] >= 120:
        tags.append("calcium_rich")
    if n["potassium_mg"] >= 300:
        tags.append("potassium_rich")
    if n["sodium_mg"] >= 400:
        tags.append("high_sodium")
    if n["fat_g"] >= 17.5:
        tags.append("high_fat")
    if n["fiber_g"] >= 6:
        tags.append("high_fiber")
    if n["protein_g"] >= 10:
        tags.append("high_protein")
    if group in ("fish", "meat") and n["protein_g"] >= 15 and n["fat_g"] <= 5:
        tags.append("lean")
    category = food.raw["Category"]
    if category == "Leafy Vegetables":
        tags.append("leafy_green")
    if group in ("fruit", "dairy", "oil"):
        tags.append(group)
    lower = food.raw["English Name"].lower()
    if (group == "sweet" or food.no in ADDED_SUGAR_FOODS or (
            category == "Beverages" and ("sugar" in lower or "soft drink" in lower))):
        tags.append("high_sugar")
    if food.no in ADDED_SUGAR_FOODS:
        tags.append("added_sugar")
    if food.no in BREWED_BEVERAGE_FOODS:
        tags.append("brewed_beverage")
    if any(word in lower for word in ("yogurt", "yoghurt", "curd", "doi", "dahi")):
        tags.append("probiotic")
    if food.raw["Source"] == "FCTB 2013" or food.no in recipe_foods:
        tags.append("bangladeshi")
    return tags


def _clean_name(food: FoodRow) -> str:
    name = NAME_FIXES.get(food.no, food.raw["English Name"])
    return " ".join(name.replace("*", "").split())


def _source(food: FoodRow) -> str:
    ref = food.raw["Source Ref"].strip()
    base = food.raw["Source"].strip() + (f" [{ref}]" if ref else "")
    return "; ".join([base, *food.citations])


def convert_foods() -> tuple[list[dict], list[dict], set[int]]:
    raw_rows = _read_csv(FOOD_RAW)
    excluded = {
        int(r["No."]) for r in raw_rows
        if r["Source"] == "IFCT 2017" and re.search(r"-\d+$", r["English Name"].strip())
    }
    foods = [FoodRow(r) for r in raw_rows if int(r["No."]) not in excluded]
    log = CorrectionLog()
    apply_corrections(foods, log)
    recipe_foods = {int(i["food_no"]) for i in _read_csv(RECIPE_RAW / "bd_recipe_ingredients_250.csv")}

    out = []
    for food in foods:
        nutrients = {canonical: food.values[raw] or 0.0 for raw, canonical in NUTRIENT_MAP.items()}
        nutrients["folate_ug"] = 0.0  # absent from the source
        group = _food_group(food)
        script = food.raw["Bangla Name (Script)"].strip()
        name_bn = script or food.raw["Bangla Name (Roman)"].strip()
        out.append({
            "food_id": food.food_id,
            "name_en": _clean_name(food),
            "name_bn": " ".join(name_bn.split()),
            "food_group": group,
            **{k: _fmt(v) for k, v in nutrients.items()},
            "tags": "|".join(_derive_tags(food, group, nutrients, recipe_foods)),
            "source": _source(food),
        })
    return out, log.rows, excluded


def _flag(row: dict, column: str) -> bool:
    return row[column].strip() == "1"


def convert_recipes(food_ids: set[str]) -> tuple[list[dict], list[dict], list[dict]]:
    raw_recipes = _read_csv(RECIPE_RAW / "bd_recipes_250.csv")
    raw_ingredients = _read_csv(RECIPE_RAW / "bd_recipe_ingredients_250.csv")
    raw_steps = _read_csv(RECIPE_RAW / "bd_recipe_steps_250.csv")

    recipes = []
    for r in raw_recipes:
        slots = [t.strip() for t in r["meal_slot"].split(";") if t.strip()]
        meal_types = list(dict.fromkeys(MEAL_SLOT_MAP[s] for s in slots if s in MEAL_SLOT_MAP))
        tags = [r["diet_type"].strip().lower().replace("-", "_").replace(" ", "_")]
        tags += [s for s in slots if s in OCCASION_TAGS]
        tags += [c for c in ALLERGEN_COLUMNS if _flag(r, c)]
        if _flag(r, "flag_deep_fried"):
            tags.append("deep_fried")
        recipes.append({
            "recipe_id": r["recipe_id"].strip(),
            "name_en": r["recipe_name_en"].strip(),
            "name_bn": r["recipe_name_bn_script"].strip() or r["recipe_name_bn_roman"].strip(),
            "name_bn_roman": r["recipe_name_bn_roman"].strip(),
            "category": r["recipe_category"].strip(),
            "meal_type": "|".join(meal_types),
            "diet_type": r["diet_type"].strip(),
            "weekly_frequency_score": int(r["weekly_frequency_score"]),
            "frequency_tier": r["frequency_tier"].strip(),
            "servings": int(r["servings"]),
            "serving_size_g": round(float(r["serving_size_g"])),
            "cooking_method": r["cooking_method"].strip(),
            "total_time_min": int(float(r["total_time_min"])),
            "tags": "|".join(dict.fromkeys(tags)),
            "notes": r["notes"].strip(),
            "source": f"{RECIPE_SOURCE}; {r['provenance_type'].strip()} [{r['source_ids'].strip()}]",
        })

    ingredients = []
    for i in raw_ingredients:
        food_id = f"F{int(i['food_no']):03d}"
        if food_id not in food_ids:
            raise SystemExit(f"{i['recipe_id']}: ingredient food_no {i['food_no']} "
                             "is not in the converted food table")
        ingredients.append({
            "recipe_id": i["recipe_id"].strip(),
            "seq": int(i["ingredient_seq"]),
            "food_id": food_id,
            "qty_g": _fmt(float(i["quantity_g"])),
            "household_measure": i["household_measure"].strip(),
            "role": i["ingredient_role"].strip(),
            "is_optional": int(_flag(i, "is_optional")),
            "rf_vit_a": _fmt(float(i["rf_vit_a"])),
            "rf_vit_c": _fmt(float(i["rf_vit_c"])),
        })

    steps = [
        {"recipe_id": s["recipe_id"].strip(), "step_no": int(s["step_no"]),
         "instruction": s["instruction"].strip()}
        for s in raw_steps
    ]
    return recipes, ingredients, steps


RECIPE_COLUMNS = [
    "recipe_id", "name_en", "name_bn", "name_bn_roman", "category", "meal_type",
    "diet_type", "weekly_frequency_score", "frequency_tier", "servings",
    "serving_size_g", "cooking_method", "total_time_min", "tags", "notes", "source",
]
INGREDIENT_COLUMNS = [
    "recipe_id", "seq", "food_id", "qty_g", "household_measure", "role",
    "is_optional", "rf_vit_a", "rf_vit_c",
]
STEP_COLUMNS = ["recipe_id", "step_no", "instruction"]
CORRECTION_COLUMNS = ["food_id", "name_en", "column", "source_value", "new_value", "rule", "evidence"]


def main() -> int:
    foods, corrections, excluded = convert_foods()
    _write_csv(FOOD_OUT, FOOD_COLUMNS, foods)
    _write_csv(CORRECTIONS_OUT, CORRECTION_COLUMNS, corrections)

    recipes, ingredients, steps = convert_recipes({f["food_id"] for f in foods})
    _write_csv(RECIPES_OUT, RECIPE_COLUMNS, recipes)
    _write_csv(INGREDIENTS_OUT, INGREDIENT_COLUMNS, ingredients)
    _write_csv(STEPS_OUT, STEP_COLUMNS, steps)

    groups: dict[str, int] = {}
    for f in foods:
        groups[f["food_group"]] = groups.get(f["food_group"], 0) + 1
    rules: dict[str, int] = {}
    for c in corrections:
        rules[c["rule"]] = rules.get(c["rule"], 0) + 1
    print(f"wrote {len(foods)} foods to {FOOD_OUT.relative_to(PROJECT_ROOT)} "
          f"({len(excluded)} IFCT cultivar rows left out)")
    print(f"groups: {dict(sorted(groups.items()))}")
    print(f"{len(corrections)} corrected cells -> {CORRECTIONS_OUT.relative_to(PROJECT_ROOT)}")
    for rule, n in rules.items():
        print(f"  {n:4}  {rule}")
    print(f"wrote {len(recipes)} recipes, {len(ingredients)} ingredient rows, "
          f"{len(steps)} steps to {RECIPES_OUT.parent.relative_to(PROJECT_ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
