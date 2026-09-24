"""Convert the raw FCT-BD spreadsheet export into the canonical bd_food.csv.

Input:  data/food/raw/fct_bd_250_export.csv — the "250 Common Bangladeshi
Foods" sheet exported from Excel (title rows, section header rows like
"CEREALS & GRAINS", multi-line column headers). Values per 100 g edible
portion, from the Food Composition Table for Bangladesh (INFS, University of
Dhaka & FAO, 2013).

Output: data/food/bd_food.csv in the schema defined by data/food/schema.md.

Run from the project root:  .venv\\Scripts\\python.exe scripts\\convert_fct_food.py

Conversion decisions (documented so they can be audited/revised):
- "Tr" (trace) and "–" (not reported) become 0.0 — conservative for ranking:
  a food earns no credit for an unmeasured nutrient.
- The source table has NO folate column, so folate_ug is 0 for every row.
  Folate-based ranking/coverage is inert until a folate source is merged in.
- name_bn uses the Bangla-script column when it survived the export encoding,
  otherwise the Roman transliteration column. (ANSI/cp1252 exports destroy
  Bangla script — re-export as "CSV UTF-8" from Excel and re-run to fix.)
- Sections map to food_group; NUTS & SEEDS and BEVERAGES fall to "other".
  In SUGARS & MISCELLANEOUS, only honey/jaggery/sugar are "sweet"; salt and
  betel leaves are "other".
- Tags are derived, not hand-curated. Thresholds per 100 g:
    iron_rich       iron_mg      >= 3       (project convention, see schema.md)
    calcium_rich    calcium_mg   >= 120     (15% of 800 mg NRV)
    potassium_rich  potassium_mg >= 300     (15% of 2000 mg NRV)
    high_sodium     sodium_mg    >= 400     (~FDA "high": 20% of 2300 mg DV)
    high_fat        fat_g        >= 17.5    (UK FSA traffic-light "high")
    high_fiber      fiber_g      >= 6       (EU "high fibre" claim)
    high_protein    protein_g    >= 10
    lean            fish/meat with protein_g >= 15 and fat_g <= 5
  Group/section tags: leafy_green (LEAFY VEGETABLES), fruit, dairy, oil,
  high_sugar (sweet group + beverages named with sugar / soft drink),
  probiotic (yogurt/curd/doi/dahi by name). omega3/staple/dessert are not
  derivable from the table and are left off.
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = PROJECT_ROOT / "data" / "food" / "raw" / "fct_bd_250_export.csv"
OUT_CSV = PROJECT_ROOT / "data" / "food" / "bd_food.csv"

SOURCE = "FCT-BD 2013 (INFS, Univ. of Dhaka & FAO)"

SECTION_GROUPS = {
    "CEREALS & GRAINS": "grain",
    "PULSES & LEGUMES": "legume",
    "VEGETABLES": "vegetable",
    "LEAFY VEGETABLES": "vegetable",
    "ROOTS & TUBERS": "vegetable",
    "NUTS & SEEDS": "other",
    "SPICES & HERBS": "spice",
    "FRUITS": "fruit",
    "FISH & SHELLFISH": "fish",
    "MEAT & POULTRY": "meat",
    "EGGS": "egg",
    "MILK & DAIRY": "dairy",
    "OILS & FATS": "oil",
    "BEVERAGES": "other",
    "SUGARS & MISCELLANEOUS": "sweet",
}

# raw header (normalized) → canonical nutrient column
NUTRIENT_MAP = {
    "Energy (kcal)": "kcal",
    "Protein (g)": "protein_g",
    "Carbohydrate (g)": "carb_g",
    "Fat (g)": "fat_g",
    "Dietary Fibre (g)": "fiber_g",
    "Iron": "iron_mg",
    "Calcium": "calcium_mg",
    "Zinc": "zinc_mg",
    "Vit A (µg RAE)": "vit_a_ug",
    "Vit C (mg)": "vit_c_mg",
    "Sodium": "sodium_mg",
    "Potassium": "potassium_mg",
}

OUT_COLUMNS = [
    "food_id", "name_en", "name_bn", "food_group",
    "kcal", "protein_g", "carb_g", "fat_g", "fiber_g",
    "iron_mg", "calcium_mg", "zinc_mg", "folate_ug",
    "vit_a_ug", "vit_c_mg", "sodium_mg", "potassium_mg",
    "tags", "source",
]

_MISSING = {"", "-", "–", "—"}


def _norm_header(cell: str) -> str:
    """Collapse the multi-line headers: 'Carbo-\\nhydrate (g)' → 'Carbohydrate (g)'."""
    return " ".join(cell.split()).replace("- ", "")


def _read_raw(path: Path) -> list[list[str]]:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=encoding, newline="") as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"cannot decode {path} as UTF-8 or cp1252")


def _parse_value(cell: str) -> tuple[float, bool]:
    """Returns (value, was_imputed). Trace and not-reported become 0."""
    cell = cell.strip()
    if cell in _MISSING or cell.lower() == "tr":
        return 0.0, True
    return float(cell), False


def _derive_tags(name_en: str, section: str, group: str, n: dict) -> list[str]:
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
    if section == "LEAFY VEGETABLES":
        tags.append("leafy_green")
    if group == "fruit":
        tags.append("fruit")
    if group == "dairy":
        tags.append("dairy")
    if group == "oil":
        tags.append("oil")
    lower = name_en.lower()
    if group == "sweet" or (
        section == "BEVERAGES" and ("sugar" in lower or "soft drink" in lower)
    ):
        tags.append("high_sugar")
    if any(word in lower for word in ("yogurt", "yoghurt", "curd", "doi", "dahi")):
        tags.append("probiotic")
    return tags


def convert() -> int:
    rows = _read_raw(RAW_CSV)

    header_i = next(i for i, r in enumerate(rows) if r and r[0].strip() == "No.")
    header = [_norm_header(c) for c in rows[header_i]]
    col = {name: header.index(name) for name in NUTRIENT_MAP}
    en_i = header.index("English Name")
    roman_i = header.index("Bangla Name (Roman)")
    script_i = roman_i + 1  # header text itself is mangled in ANSI exports

    out, imputed, script_ok = [], 0, 0
    section = None
    for row in rows[header_i + 1:]:
        first = row[0].strip()
        if first in SECTION_GROUPS:
            section = first
            continue
        if not first.isdigit():
            continue  # notes / footer rows

        name_en = row[en_i].strip()
        group = SECTION_GROUPS[section]
        if section == "SUGARS & MISCELLANEOUS" and not any(
            w in name_en.lower() for w in ("honey", "jaggery", "sugar")
        ):
            group = "other"  # salt, betel leaves

        nutrients = {}
        for raw_name, canonical in NUTRIENT_MAP.items():
            value, was_imputed = _parse_value(row[col[raw_name]])
            nutrients[canonical] = value
            imputed += was_imputed
        nutrients["folate_ug"] = 0.0  # absent from the source table

        script = row[script_i].strip()
        has_script = any(ord(ch) > 127 for ch in script)
        script_ok += has_script
        name_bn = script if has_script else row[roman_i].strip()

        out.append({
            "food_id": f"F{int(first):03d}",
            "name_en": name_en,
            "name_bn": " ".join(name_bn.split()),
            "food_group": group,
            **{k: f"{v:g}" for k, v in nutrients.items()},
            "tags": "|".join(_derive_tags(name_en, section, group, nutrients)),
            "source": SOURCE,
        })

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        writer.writerows(out)

    groups: dict[str, int] = {}
    for r in out:
        groups[r["food_group"]] = groups.get(r["food_group"], 0) + 1
    print(f"wrote {len(out)} foods to {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"groups: {dict(sorted(groups.items()))}")
    print(f"{imputed} trace/not-reported values set to 0")
    if script_ok:
        print(f"Bangla script names kept for {script_ok}/{len(out)} rows")
    else:
        print("Bangla script column was destroyed by the export encoding — "
              "name_bn falls back to Roman transliteration. Re-export the "
              "sheet as 'CSV UTF-8' and re-run to restore it.")
    return 0


if __name__ == "__main__":
    sys.exit(convert())
