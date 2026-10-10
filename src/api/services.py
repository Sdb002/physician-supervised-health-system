"""Deterministic assessment engine: orchestrates clinical, diet, and lifestyle
modules into one Assessment result. Imports no LLM code — everything here is
reproducible from the inputs and the reference files.
"""

import copy

from src.clinical.bmi import PREGNANCY_KCAL, age_from_birth_year, daily_energy_target
from src.clinical.contraindication import excluded_tags, filter_items
from src.clinical.deficiency import ADULT_AGE, nutrient_targets
from src.clinical.risk_scoring import (
    bp_category,
    derive_conditions,
    overall_risk,
    score_biomarkers,
)
from src.db.models import Patient, Visit
from src.diet.food_db import (
    NUTRIENT_COLUMNS,
    display_name,
    eaten_in_portions,
    food_index,
    load_foods,
    recommendable_foods,
    untracked_nutrients,
)
from src.diet.habits import (
    familiarity_map,
    food_habits,
    habitual_foods,
    median_familiarity,
    portion_map,
    typical_portion_g,
)
from src.diet.matcher import active_backend, active_recipe_backend, rank_foods, rank_recipes
from src.diet.meal_plan import (
    MAX_VIT_A_UG_PER_SERVING,
    WEEKDAYS,
    build_meal_plan,
    coverage,
    line_figures,
    plannable,
    ration_salt,
    serving_grams,
    summarize_week,
)
from src.diet.recipe import Recipe, load_recipes
from src.lifestyle.exercise_db import load_exercises
from src.lifestyle.fitt_vp import build_fitt_plan

# 0.2.0: 672-food / 250-recipe datasets; recipes ranked as their own section
# 0.3.0: meal plan composed from household dishes; foods ranked by habit too
# 0.4.0: a week of meals (Saturday to Friday) instead of one day
# 0.5.0: plan lines report carbohydrate, fat and sodium; the energy target
#        records the inputs and steps it was worked out from
# 0.6.0: each day's cooking salt is set so the day stays under the sodium
#        limit; days and dish lines report that salt
# 0.7.0: no weight-loss deficit in pregnancy, trimester energy and pregnancy
#        food exclusions; reference intakes by age band; recorded conditions
#        drive the nutrient emphasis; dietary restrictions; the recorded
#        activity level; cautions for the reviewing physician
ENGINE_VERSION = "0.7.0"

# "Foods that suit your plan" spans the food groups rather than listing ten
# leafy greens: at most this many from any one group.
TOP_FOODS_PER_GROUP = 3
# ...and suggested dishes span dal, fish, greens and the rest the same way.
TOP_RECIPES_PER_CATEGORY = 3


def _cautions(patient: Patient, age: int, nutrition_cautions: list[str]) -> list[str]:
    """What the reviewing physician should check before approving: where the
    engine worked from an assumption, or emphasized something that is not
    safe for every patient. Shown on the review screen, never to the patient."""
    cautions = []
    if age < ADULT_AGE:
        cautions.append(
            f"This patient is {age}. The energy equation, the body mass index "
            "categories (and any weight adjustment made from them) and the nutrient "
            f"reference values are for adults aged {ADULT_AGE} and over; there are none "
            "here for children or adolescents, so check every target before approving."
        )
    if patient.pregnant and patient.pregnancy_trimester is None:
        cautions.append(
            "No trimester is recorded, so no pregnancy energy was added (the second "
            f"trimester adds {PREGNANCY_KCAL[2]} kcal a day, the third {PREGNANCY_KCAL[3]}). "
            "Record the trimester on the patient to add it."
        )
    return cautions + nutrition_cautions


def build_assessment(patient: Patient, visit: Visit) -> dict:
    age = age_from_birth_year(patient.birth_year)
    energy = daily_energy_target(
        weight_kg=visit.weight_kg,
        height_cm=patient.height_cm,
        age=age,
        sex=patient.sex,
        activity=patient.activity_level,
        pregnant=patient.pregnant,
        trimester=patient.pregnancy_trimester,
    )

    flags = score_biomarkers(visit.biomarkers or {}, patient.sex, patient.pregnant)

    conditions = list(derive_conditions(flags))
    for declared in patient.conditions or []:
        if declared not in conditions:
            conditions.append(declared)
    if patient.pregnant and "pregnancy" not in conditions:
        conditions.append("pregnancy")

    exclusions = excluded_tags(conditions, patient.dietary_restrictions or [])
    nutrition = nutrient_targets(patient.sex, patient.pregnant, flags,
                                 conditions=conditions, age=age)
    cautions = _cautions(patient, age, nutrition.pop("cautions"))

    foods = load_foods()
    allowed_foods = filter_items(foods, exclusions.food_tags)
    recipes = load_recipes(food_index(foods))
    allowed_recipes = filter_items(recipes, exclusions.food_tags)
    # habits come from every dish, gated or not: whether households eat a
    # food doesn't depend on this patient's exclusions
    habits = food_habits(recipes)
    candidate_foods = [
        f for f in habitual_foods(eaten_in_portions(recommendable_foods(allowed_foods)), habits)
        # liver: a usual portion is over the vitamin A upper limit (see meal_plan)
        if f.nutrients["vit_a_ug"] * typical_portion_g(f, habits) / 100.0
        <= MAX_VIT_A_UG_PER_SERVING
    ]
    familiarity = familiarity_map(candidate_foods, habits, unknown=median_familiarity(recipes))
    suggested_recipes = [r for r in allowed_recipes if plannable(r)]

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
        "dietary_restrictions": list(exclusions.applied_restrictions),
        "cautions": cautions,
        "exclusions": {
            "food_tags": sorted(exclusions.food_tags),
            "exercise_tags": sorted(exclusions.exercise_tags),
        },
        "nutrition": {
            **nutrition,
            "scoring_backend": active_backend(),
            "recipe_scoring_backend": active_recipe_backend(),
            "top_foods": rank_foods(candidate_foods, emphasize, targets,
                                    familiarity=familiarity, per_group=TOP_FOODS_PER_GROUP,
                                    portion_g=portion_map(candidate_foods, habits)),
            "top_recipes": rank_recipes(suggested_recipes, emphasize, targets,
                                        per_category=TOP_RECIPES_PER_CATEGORY),
            "meal_plan": build_meal_plan(
                suggested_recipes,
                [f for f in candidate_foods if f.food_group == "fruit"],
                energy["target_kcal"], targets, emphasize,
                familiarity=familiarity, untracked=untracked_nutrients(foods),
                foods_by_id=food_index(foods),
                sodium_limit_mg=nutrition["limits"].get("sodium_mg"),
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
    """Current dishes and foods filtered by this assessment's contraindication
    exclusions: what the plan editor may add.

    Used by the plan editor so the physician always picks from live, allowed
    items with real energy densities — never from the list frozen inside an
    old assessment (which can go stale when the dataset is replaced). Dishes
    come first: plans are built from them. Every gated-in dish is offered,
    sweets included; only the automatic planner holds those back.
    """
    food_tags = set(result["exclusions"]["food_tags"])
    all_foods = load_foods()
    foods = filter_items(all_foods, food_tags)
    recipes = filter_items(load_recipes(food_index(all_foods)), food_tags)
    dishes = [
        {"kind": "recipe", "recipe_id": r.recipe_id, "name_en": r.name_en, "name_bn": r.name_bn,
         "food_group": r.category or "Dish",
         "serving_size_g": round(serving_grams(r)),
         "kcal_per_100g": round(r.per_serving["kcal"] / serving_grams(r) * 100)}
        for r in sorted(recipes, key=lambda r: (r.category, r.name_en.lower()))
        if serving_grams(r) > 0
    ]
    return dishes + [
        {"kind": "food", "food_id": f.food_id, "name_en": f.name_en, "name_bn": f.name_bn,
         "food_group": f.food_group, "kcal_per_100g": round(f.nutrients["kcal"])}
        for f in sorted(foods, key=lambda f: (f.food_group, f.name_en.lower()))
    ]


def _edited_dish(item, meal: str, all_recipes: dict, allowed_recipes: dict,
                 food_tags: set) -> tuple[dict, dict, Recipe, float]:
    """A physician's dish line, re-validated and recomputed from the recipe
    data: grams -> servings -> per-serving nutrients. Also returns the recipe
    and the servings, which the day's salt is worked out from."""
    claimed = item.name_en.strip()
    recipe = allowed_recipes.get(item.recipe_id)
    if recipe is None:
        stale = all_recipes.get(item.recipe_id)
        if stale is None or (claimed and stale.name_en != claimed):
            label = claimed or item.recipe_id
            raise ValueError(
                f"'{label}' ({meal}) is no longer in the recipe database — "
                "remove it and choose a replacement from the list"
            )
        blocked = ", ".join(sorted(set(stale.tags) & food_tags)) or "contraindicated"
        raise ValueError(f"'{stale.name_en}' ({meal}) is excluded for this patient — {blocked}")
    if claimed and recipe.name_en != claimed:
        raise ValueError(
            f"'{claimed}' ({meal}) comes from an older version of the recipe "
            "database — remove it and add its replacement from the list"
        )
    grams = serving_grams(recipe)
    qty_g = round(item.qty_g)
    servings = qty_g / grams
    nutrients = {c: recipe.per_serving.get(c, 0.0) * servings for c in NUTRIENT_COLUMNS}
    row = {
        "recipe_id": recipe.recipe_id, "name_en": recipe.name_en, "name_bn": recipe.name_bn,
        "category": recipe.category, "servings": round(servings, 2),
        "serving_size_g": round(grams), "qty_g": qty_g,
        **line_figures(nutrients, recipe, servings),
    }
    return row, nutrients, recipe, servings


def _edited_food(item, meal: str, all_foods: dict, allowed_foods: dict,
                 food_tags: set) -> tuple[dict, dict]:
    """A physician's single-food line, re-validated and recomputed from the
    food table."""
    claimed = item.name_en.strip()
    food = allowed_foods.get(item.food_id)
    # the engine shows foods by their display name, the editor's list by the
    # table name; either is the same food
    if (food is not None and claimed
            and claimed not in (food.name_en, display_name(food.name_en))):
        # the dataset was replaced: this id now denotes a different food
        raise ValueError(
            f"'{claimed}' ({meal}) comes from an older version of the food "
            "database — remove it and add its replacement from the list"
        )
    if food is None:
        stale = all_foods.get(item.food_id)
        if stale is None or (claimed and claimed not in (
                stale.name_en, display_name(stale.name_en))):
            label = claimed or item.food_id
            raise ValueError(
                f"'{label}' ({meal}) is no longer in the food database — "
                "remove it and choose a replacement from the list"
            )
        blocked = ", ".join(sorted(set(stale.tags) & food_tags)) or "contraindicated"
        raise ValueError(f"'{stale.name_en}' ({meal}) is excluded for this patient — {blocked}")
    qty_g = round(item.qty_g)
    nutrients = {c: food.nutrients[c] * qty_g / 100.0 for c in NUTRIENT_COLUMNS}
    row = {
        "food_id": food.food_id, "name_en": display_name(food.name_en),
        "name_bn": food.name_bn, "qty_g": qty_g, **line_figures(nutrients),
    }
    return row, nutrients


def recompute_edited_result(result: dict, weight_kg: float, edit) -> dict:
    """Rebuild the diet/exercise plan from physician edits, deterministically.

    Every edited food/exercise is re-validated against this assessment's
    contraindication exclusions, and all derived numbers (item kcal, totals,
    coverage, weekly volume) are recomputed from the reference datasets —
    nothing numeric is trusted from the client. Each edited day's cooking
    salt is fitted to the sodium limit again, as the planner does. Raises
    ValueError on any item the gate does not allow.
    """
    edited = copy.deepcopy(result)
    food_tags = set(result["exclusions"]["food_tags"])
    exercise_tags = set(result["exclusions"]["exercise_tags"])
    targets = result["nutrition"]["targets"]
    sodium_limit_mg = (result["nutrition"].get("limits") or {}).get("sodium_mg")
    target_kcal = (
        result["nutrition"]["meal_plan"].get("target_kcal")
        or result["anthropometrics"]["target_kcal"]
    )

    food_list = load_foods()
    all_foods = food_index(food_list)
    allowed_foods = {
        f.food_id: f for f in filter_items(list(all_foods.values()), food_tags)
    }
    recipe_list = load_recipes(all_foods)
    all_recipes = {r.recipe_id: r for r in recipe_list}
    allowed_recipes = {r.recipe_id: r for r in filter_items(recipe_list, food_tags)}
    untracked = untracked_nutrients(food_list)

    def edited_day(day_meals: dict) -> tuple[dict, dict, dict]:
        meals: dict[str, list[dict]] = {}
        totals = {c: 0.0 for c in NUTRIENT_COLUMNS}
        dishes = []
        for meal, items in day_meals.items():
            if meal not in _VALID_MEALS:
                raise ValueError(f"unknown meal: {meal}")
            rows = []
            for item in items:
                if item.recipe_id is not None:
                    row, nutrients, recipe, servings = _edited_dish(
                        item, meal, all_recipes, allowed_recipes, food_tags)
                    dishes.append((row, recipe, servings))
                else:
                    row, nutrients = _edited_food(item, meal, all_foods, allowed_foods, food_tags)
                for c in NUTRIENT_COLUMNS:
                    totals[c] += nutrients[c]
                rows.append(row)
            meals[meal] = rows
        return meals, totals, ration_salt(dishes, totals, sodium_limit_mg)

    original_days = result["nutrition"]["meal_plan"].get("days") or []
    if original_days and edit.days is None:
        raise ValueError("this plan covers a week — send the edited plan as days")
    if edit.days is not None:
        # a week plan: keep each day's weekday from the plan being edited
        week = []
        for index, day_meals in enumerate(edit.days):
            weekday = (original_days[index]["weekday"] if index < len(original_days)
                       else WEEKDAYS[index % len(WEEKDAYS)])
            meals, totals, salt = edited_day(day_meals)
            week.append((weekday, meals, totals, salt))
        plan = summarize_week(week, target_kcal, targets, untracked)
    else:
        # a one-day plan from an assessment made before weekly plans (engine < 0.4.0)
        meals, totals, salt = edited_day(edit.meals or {})
        plan = {
            "meals": meals,
            "totals": {c: round(v, 1) for c, v in totals.items()},
            **salt,
            "target_kcal": round(target_kcal),
            "coverage": coverage(totals, targets, untracked),
        }
        tracked_out = sorted(n for n in untracked if n in targets and n != "kcal")
        if tracked_out:
            plan["untracked"] = tracked_out
    plan["edited_by_physician"] = True
    edited["nutrition"]["meal_plan"] = plan

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
