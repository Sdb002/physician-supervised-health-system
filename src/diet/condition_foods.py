"""Per condition: the foods that help and the foods and dishes to avoid.

The plan already acts on every condition at once - the gate leaves out what
any of them rules out, and the suggestion list is ranked on all the
emphasized nutrients together. A patient with high blood pressure and
diabetes still asks "what should I eat for my pressure, and what should I
stay away from?", so this splits the same evidence by condition:

- eat: the foods that are a real source (EU "source of" claim thresholds,
  data/reference/nutrient_sources.yaml) of that condition's own nutrients
  (src/clinical/rules/deficiency_map.yaml, e.g. potassium and fibre for
  hypertension), ranked, like "top foods", by how many meals a week
  households eat them (src.diet.habits) and what a usual portion supplies.
  They come from the foods the patient's whole gate allowed, so a
  hypertensive diabetic's blood-pressure list never offers jaggery.
- avoid: the foods and household dishes carrying the tags that condition
  excludes (data/reference/contraindications.yaml, each rule cited there),
  the most commonly eaten first, since those are the ones worth telling a
  patient about. They are exactly what the gate removed for that
  condition; nothing here re-admits an item to the plan.

A condition with neither (knee osteoarthritis has no food rule; kidney
disease only stops potassium being emphasized) gets no entry: the
condition's own explanation is in nutrition.patient_rationales.
"""

from functools import lru_cache

from src.clinical.contraindication import condition_food_tags
from src.clinical.deficiency import finding_nutrients
from src.core.config import REFERENCE_DIR, load_yaml
from src.diet.food_db import Food, display_name, recommendable_foods
from src.diet.habits import FoodHabit, meals_per_week_map, variant_key
from src.diet.matcher import rank_foods
from src.diet.recipe import Recipe

# Short lists: a patient reads them, and a block per condition adds up.
EAT_PER_CONDITION = 8
EAT_PER_GROUP = 2
AVOID_PER_CONDITION = 8


# Foods no condition's eat list offers, though the gate allows them. The
# food table has no saturated fat, so a fibre-rich but fat-heavy food
# (coconut kernel, 33 g fat per 100 g, mostly saturated) can't be told from
# peanuts, and the guidance behind every condition with an eat list limits
# saturated fat: AHA/ACC 2018 for cholesterol (the physician's caution in
# deficiency_map.yaml already asks them to check coconut), the ADA Standards
# of Care for diabetes, the DASH pattern for blood pressure. The plan may
# still use these foods; only the "good to eat" lists leave them out.
_NOT_SUGGESTED = {"high_fat"}


@lru_cache(maxsize=1)
def _source_rules() -> dict:
    return load_yaml(REFERENCE_DIR / "nutrient_sources.yaml")


def is_source(nutrients: dict, nutrient: str) -> bool:
    """Whether 100 g of a food is a "source of" the nutrient by the EU
    nutrition-claim thresholds (data/reference/nutrient_sources.yaml): 15%
    of the reference value for a vitamin or mineral, 3 g (or 1.5 g per
    100 kcal) of fibre, 12% of energy from protein. A nutrient with no
    threshold is never sourced."""
    rules = _source_rules()
    value = nutrients.get(nutrient, 0.0)
    kcal = nutrients.get("kcal", 0.0)
    if nutrient == "fiber_g":
        fiber = rules["fiber"]
        return (value >= fiber["min_g_per_100g"]
                or (kcal > 0 and value * 100.0 / kcal >= fiber["min_g_per_100kcal"]))
    if nutrient == "protein_g":
        return kcal > 0 and value * 4.0 / kcal >= rules["protein"]["min_energy_share"]
    nrv = rules["nrv"].get(nutrient)
    return nrv is not None and value >= rules["significant_share_of_nrv"] * nrv


def _avoid_foods(foods: list[Food], tags: set[str], habits: dict[str, FoodHabit]) -> list[dict]:
    """Bangladeshi foods carrying one of `tags`, most often eaten first -
    one entry per everyday food, as in "top foods"."""
    tagged = [f for f in recommendable_foods(foods) if tags & set(f.tags)]
    meals = meals_per_week_map(tagged, habits)
    tagged.sort(key=lambda f: (-meals[f.food_id], display_name(f.name_en)))
    seen: set[str] = set()
    entries = []
    for food in tagged:
        key = variant_key(food)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"food_id": food.food_id, "name_en": display_name(food.name_en),
                        "name_bn": food.name_bn, "food_group": food.food_group,
                        "reasons": sorted(tags & set(food.tags))})
        if len(entries) >= AVOID_PER_CONDITION:
            break
    return entries


def _avoid_dishes(recipes: list[Recipe], tags: set[str]) -> list[dict]:
    """Household dishes carrying one of `tags`, the most commonly cooked
    first."""
    tagged = [r for r in recipes if tags & set(r.tags)]
    tagged.sort(key=lambda r: (-(r.weekly_frequency_score or 0), r.name_en))
    return [{"recipe_id": r.recipe_id, "name_en": r.name_en, "name_bn": r.name_bn,
             "category": r.category, "reasons": sorted(tags & set(r.tags))}
            for r in tagged[:AVOID_PER_CONDITION]]


def condition_food_guide(conditions: list[str], *, foods: list[Food], recipes: list[Recipe],
                         allowed_foods: list[Food], habits: dict[str, FoodHabit],
                         meals_per_week: dict[str, float], portion_g: dict[str, float],
                         targets: dict, untracked: frozenset[str] = frozenset(),
                         findings=(), limits: dict | None = None) -> list[dict]:
    """One entry per condition of the patient's that changes what they eat,
    in the order the conditions are listed. `allowed_foods` are the foods
    the patient's gate and own exclusions let through and "top foods" is
    ranked from; `foods` and `recipes` are the whole tables, which the
    avoid lists are read from."""
    guide = []
    for condition in conditions:
        # folate has no value in the food table (see food_db.untracked_nutrients)
        nutrients = [n for n in finding_nutrients(condition, conditions) if n not in untracked]
        # only real sources of the condition's nutrients, ranked as "top
        # foods" are; the model is told this condition alone, so another
        # finding (anaemia's liking for fish and meat) does not decide the
        # list for blood pressure
        sources = [f for f in allowed_foods
                   if any(is_source(f.nutrients, n) for n in nutrients)
                   and not _NOT_SUGGESTED & set(f.tags)]
        eat = rank_foods(sources, nutrients, targets, top_n=EAT_PER_CONDITION,
                         meals_per_week=meals_per_week, per_group=EAT_PER_GROUP,
                         portion_g=portion_g,
                         findings=[f for f in findings if f == condition],
                         limits=limits) if sources else []
        tags = set(condition_food_tags(condition))
        avoid_foods = _avoid_foods(foods, tags, habits) if tags else []
        avoid_dishes = _avoid_dishes(recipes, tags) if tags else []
        if not (eat or avoid_foods or avoid_dishes):
            continue
        guide.append({"condition": condition, "nutrients": nutrients, "eat": eat,
                      "avoid_tags": sorted(tags), "avoid_foods": avoid_foods,
                      "avoid_dishes": avoid_dishes})
    return guide
