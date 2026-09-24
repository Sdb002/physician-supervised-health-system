"""Deterministic assessment engine: orchestrates clinical, diet, and lifestyle
modules into one Assessment result. Imports no LLM code — everything here is
reproducible from the inputs and the reference files.
"""

import copy

from src.clinical.bmi import age_from_birth_year, daily_energy_target
from src.clinical.contraindication import excluded_tags, filter_items
from src.clinical.deficiency import nutrient_targets
from src.clinical.risk_scoring import (
    bp_category,
    derive_conditions,
    overall_risk,
    score_biomarkers,
)
from src.db.models import Patient, Visit
from src.diet.food_db import NUTRIENT_COLUMNS, food_index, load_foods
from src.diet.matcher import active_backend, rank_foods, rank_recipes
from src.diet.meal_plan import build_meal_plan
from src.diet.recipe import load_recipes
from src.lifestyle.exercise_db import load_exercises
from src.lifestyle.fitt_vp import build_fitt_plan

ENGINE_VERSION = "0.1.0"


def build_assessment(patient: Patient, visit: Visit) -> dict:
    age = age_from_birth_year(patient.birth_year)
    energy = daily_energy_target(
        weight_kg=visit.weight_kg,
        height_cm=patient.height_cm,
        age=age,
        sex=patient.sex,
    )

    flags = score_biomarkers(visit.biomarkers or {}, patient.sex, patient.pregnant)

    conditions = list(derive_conditions(flags))
    for declared in patient.conditions or []:
        if declared not in conditions:
            conditions.append(declared)
    if patient.pregnant and "pregnancy" not in conditions:
        conditions.append("pregnancy")

    exclusions = excluded_tags(conditions)
    nutrition = nutrient_targets(patient.sex, patient.pregnant, flags)

    foods = load_foods()
    allowed_foods = filter_items(foods, exclusions.food_tags)
    recipes = load_recipes(food_index(foods))
    allowed_recipes = filter_items(recipes, exclusions.food_tags)

    targets = nutrition["targets"]
    emphasize = nutrition["emphasize"]

    exercises = load_exercises()
    allowed_exercises = filter_items(exercises, exclusions.exercise_tags)

    return {
        "engine_version": ENGINE_VERSION,
        "age": age,
        "anthropometrics": energy,
        "risk_flags": [f.as_dict() for f in flags],
        "bp_category": bp_category(flags),
        "overall_risk": overall_risk(flags),
        "conditions": conditions,
        "exclusions": {
            "food_tags": sorted(exclusions.food_tags),
            "exercise_tags": sorted(exclusions.exercise_tags),
        },
        "nutrition": {
            **nutrition,
            "scoring_backend": active_backend(),
            "top_foods": rank_foods(allowed_foods, emphasize, targets),
            "top_recipes": rank_recipes(allowed_recipes, emphasize, targets),
            "meal_plan": build_meal_plan(
                allowed_foods, energy["target_kcal"], targets, emphasize
            ),
        },
        "exercise_plan": build_fitt_plan(
            age=age,
            sex=patient.sex,
            weight_kg=visit.weight_kg,
            bmi_category=energy["bmi_category"],
            fitness_level=patient.fitness_level,
            overall_risk=overall_risk(flags),
            exercises=allowed_exercises,
        ),
    }


_VALID_MEALS = ("breakfast", "lunch", "dinner", "snack")
_EXERCISE_GROUPS = ("aerobic", "strength", "flexibility")


def allowed_foods_for(result: dict) -> list[dict]:
    """Current food DB filtered by this assessment's contraindication exclusions.

    Used by the plan editor so the physician always picks from live, allowed
    foods with real energy densities — never from the list frozen inside an
    old assessment (which can go stale when the dataset is replaced).
    """
    food_tags = set(result["exclusions"]["food_tags"])
    foods = filter_items(load_foods(), food_tags)
    return [
        {"food_id": f.food_id, "name_en": f.name_en, "name_bn": f.name_bn,
         "food_group": f.food_group, "kcal_per_100g": round(f.nutrients["kcal"])}
        for f in sorted(foods, key=lambda f: (f.food_group, f.name_en.lower()))
    ]


def recompute_edited_result(result: dict, weight_kg: float, edit) -> dict:
    """Rebuild the diet/exercise plan from physician edits, deterministically.

    Every edited food/exercise is re-validated against this assessment's
    contraindication exclusions, and all derived numbers (item kcal, totals,
    coverage, weekly volume) are recomputed from the reference datasets —
    nothing numeric is trusted from the client. Raises ValueError on any item
    the gate does not allow.
    """
    edited = copy.deepcopy(result)
    food_tags = set(result["exclusions"]["food_tags"])
    exercise_tags = set(result["exclusions"]["exercise_tags"])
    targets = result["nutrition"]["targets"]
    target_kcal = (
        result["nutrition"]["meal_plan"].get("target_kcal")
        or result["anthropometrics"]["target_kcal"]
    )

    all_foods = food_index(load_foods())
    allowed_foods = {
        f.food_id: f for f in filter_items(list(all_foods.values()), food_tags)
    }
    meals: dict[str, list[dict]] = {}
    totals = {c: 0.0 for c in NUTRIENT_COLUMNS}
    for meal, items in edit.meals.items():
        if meal not in _VALID_MEALS:
            raise ValueError(f"unknown meal: {meal}")
        rows = []
        for item in items:
            claimed = item.name_en.strip()
            food = allowed_foods.get(item.food_id)
            if food is not None and claimed and food.name_en != claimed:
                # the dataset was replaced: this id now denotes a different food
                raise ValueError(
                    f"'{claimed}' ({meal}) comes from an older version of the food "
                    "database — remove it and add its replacement from the list"
                )
            if food is None:
                stale = all_foods.get(item.food_id)
                if stale is None or (claimed and stale.name_en != claimed):
                    label = claimed or item.food_id
                    raise ValueError(
                        f"'{label}' ({meal}) is no longer in the food database — "
                        "remove it and choose a replacement from the list"
                    )
                blocked = ", ".join(sorted(set(stale.tags) & food_tags)) or "contraindicated"
                raise ValueError(
                    f"'{stale.name_en}' ({meal}) is excluded for this patient — {blocked}"
                )
            qty_g = round(item.qty_g)
            nutrients = {c: food.nutrients[c] * qty_g / 100.0 for c in NUTRIENT_COLUMNS}
            for c in NUTRIENT_COLUMNS:
                totals[c] += nutrients[c]
            rows.append({
                "food_id": food.food_id, "name_en": food.name_en,
                "name_bn": food.name_bn, "qty_g": qty_g,
                "kcal": round(nutrients["kcal"]),
            })
        meals[meal] = rows

    coverage = {
        nutrient: round(totals.get(nutrient, 0.0) / target * 100)
        for nutrient, target in targets.items()
        if nutrient != "kcal" and target
    }
    edited["nutrition"]["meal_plan"] = {
        "meals": meals,
        "totals": {c: round(v, 1) for c, v in totals.items()},
        "target_kcal": round(target_kcal),
        "coverage": coverage,
        "edited_by_physician": True,
    }

    if edit.exercise is not None and result.get("exercise_plan", {}).get("time"):
        plan = copy.deepcopy(result["exercise_plan"])
        ex = edit.exercise
        all_exercises = {e.exercise_id: e for e in load_exercises()}
        allowed_exercises = {
            e.exercise_id: e
            for e in filter_items(list(all_exercises.values()), exercise_tags)
        }
        new_type: dict[str, list[dict]] = {}
        for group in _EXERCISE_GROUPS:
            ids = ex.type.get(group)
            if ids is None:
                new_type[group] = plan["type"].get(group, [])
                continue
            rows = []
            for exercise_id in ids:
                exercise = allowed_exercises.get(exercise_id)
                if exercise is None:
                    stale = all_exercises.get(exercise_id)
                    name = stale.name_en if stale else f"one {group} exercise"
                    raise ValueError(
                        f"'{name}' is not allowed for this patient — remove it"
                    )
                if exercise.category != group:
                    raise ValueError(
                        f"exercise '{exercise_id}' is {exercise.category}, not {group}"
                    )
                rows.append({
                    "exercise_id": exercise.exercise_id,
                    "name_en": exercise.name_en, "name_bn": exercise.name_bn,
                    "met_value": exercise.met_value, "equipment": exercise.equipment,
                    "intensity_level": exercise.intensity_level,
                })
            new_type[group] = rows

        weekly_min = ex.aerobic_min_per_session * ex.aerobic_days
        aerobic_rows = new_type.get("aerobic") or []
        met_avg = (
            sum(r["met_value"] for r in aerobic_rows) / len(aerobic_rows)
            if aerobic_rows else 0.0
        )
        met_min = met_avg * weekly_min
        plan["frequency"] = {
            "aerobic_days": ex.aerobic_days,
            "strength_days": ex.strength_days,
            "flexibility_days": ex.flexibility_days,
        }
        plan["time"] = {
            "aerobic_min_per_session": ex.aerobic_min_per_session,
            "aerobic_min_per_week": weekly_min,
        }
        plan["type"] = new_type
        plan["volume"] = {
            "met_min_per_week": round(met_min),
            "est_kcal_per_week": round(met_min / 60.0 * weight_kg),
            "volume_factor": plan["volume"]["volume_factor"],
        }
        plan["edited_by_physician"] = True
        edited["exercise_plan"] = plan

    return edited
