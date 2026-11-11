"""Train the three suitability models: the two of src.diet.recommender — one
for single foods, one for household recipes — each ranking its own section of
the diet recommendation, and the exercise model of src.lifestyle.recommender,
which ranks each group of the exercise prescription (see "the exercise
model" below; everything above it is about the two diet models).

Run from the project root:  .venv\\Scripts\\python.exe scripts\\train_recommenders.py
                            (add --only food, recipe or exercise to train one)

There is no real preference/interaction data anywhere in this repo, so
labels are constructed
from a synthetic grid of patient archetypes, built entirely from the app's
own real reference data (data/reference/*.yaml via
src.clinical.deficiency.nutrient_targets), scored by a richer suitability
function than src.diet.matcher's deterministic formula: the same formula plus
a per-nutrient saturation cap, a citation-grounded food-group prior, a
heme-iron bioavailability interaction, and a continuous sodium-excess penalty
(see compute_food_label()/compute_recipe_label() below for the citations). A
tree ensemble can represent that added structure; a linear model structurally
cannot — that distinction is the actual evidence this script produces, via a
five-way comparison per model (hand-tuned formula vs. a fitted
LinearRegression vs. an untuned GradientBoostingRegressor vs. a
hyperparameter-tuned RandomForest vs. a tuned HistGradientBoostingRegressor)
evaluated on patient archetypes the model never trained on.
RandomForest/HistGradientBoosting are tuned by a randomized search
(GroupKFold(3), optimizing the held-out ranking metric below) rather than
hand-picked constants — see tune() below.

The archetypes cover every patient the engine can describe: each reference
intake group (sex, age band, pregnancy) x each combination of findings x each
recorded condition that rules a nutrient out of the emphasis (potassium in
chronic kidney disease). Every archetype is scored under its full emphasis,
which the suggestion lists are ranked on, and under the shorter lists the
meal planner moves through as the day's nutrients fill up, down to none —
see _emphasis_variants().

The models are judged the way they are used: one patient, one list to rank.
Every (archetype, emphasis) is a query; within it a model's scores are
compared with the label over the items the app actually ranks (the foods it
suggests on their own, the dishes it plans from), each weighted as the app
weights it before sorting (for a dish its household familiarity, for a food
the meals a week it is eaten at and its usual portion), by Spearman correlation and by how much of the model's top ten the
label also ranks in its top ten. Training labels carry noise
(LABEL_NOISE_STD); evaluation is against the noise-free label, so the
numbers say how well a model recovered the suitability function, not how
well it fits the noise.

The two tuned models are fitted under monotonic constraints (see
monotonic_constraints()): whatever else they learn, more of a nutrient never
lowers a score and more sodium never raises one.

The recipe label is the food label applied per serving. Both are a
nutritional fit and nothing else: how commonly a dish is cooked at home (the
recipe dataset's 1-10 score) is not learned but applied afterwards, by
src.diet.matcher.familiar_score, to a model's fit exactly as to the
formula's — so the evaluation applies it to label and prediction alike.

This script must be run from the project's own .venv (64-bit Python,
matching the running app) — the saved artifacts are version-pinned to the
sklearn build that trains them (see src.diet.recommender), so training under
a different interpreter/environment than the one serving requests would
immediately trip that check and fall back to the deterministic formula.

The exercise model follows the same method on its own patient grid (sex and
age, pregnancy, every combination of four conditions, fitness level and
starting intensity, obesity: 1,120 patient types), each put through the
app's own safety gate and plannable rules; a query is one group of one
patient's prescription, judged by Spearman correlation and top-3 agreement.

Outputs, per model (<kind> = food | recipe | exercise):
  data/models/<kind>_recommender.joblib          the trained model (gitignored)
  data/models/<kind>_recommender_metrics.json    five-way comparison, tuned
                                                 params, permutation importance
  thesis/results/<kind>_recommender_comparison.csv
"""

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import joblib
import numpy as np
import sklearn
from joblib import Parallel, delayed
from scipy.stats import spearmanr
from sklearn.ensemble import (
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import make_scorer, mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, ParameterSampler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clinical import deficiency  # noqa: E402
from src.clinical.contraindication import excluded_tags, filter_items  # noqa: E402
from src.diet import recommender  # noqa: E402
from src.diet.food_db import (  # noqa: E402
    eaten_in_portions,
    food_index,
    load_foods,
    recommendable_foods,
    untracked_nutrients,
)
from src.diet.habits import (  # noqa: E402
    food_habits,
    habitual_foods,
    meals_per_week_map,
    median_meals_per_week,
    portion_map,
)
from src.diet.matcher import (  # noqa: E402
    _density_score,
    _emphasis_score,
    food_baseline_score,
    frequency_multiplier,
    meal_frequency_weight,
)
from src.diet.meal_plan import plannable  # noqa: E402
from src.diet.recipe import load_recipes  # noqa: E402
from src.lifestyle import ranking as exercise_ranking  # noqa: E402
from src.lifestyle import recommender as exercise_recommender  # noqa: E402
from src.lifestyle.exercise_db import PLAN_GROUPS, load_exercises  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "thesis" / "results"

RANDOM_STATE = 42
# Target variants per archetype: the reference intakes as they are, then any
# further ones jittered by TARGET_JITTER_PCT. One is enough: with a second,
# jittered variant the frame is twice the size and ranks held-out patients no
# better, the jittered ones included (0.9970 against 0.9972 for foods).
NOISE_REPEATS = 1
TARGET_JITTER_PCT = 0.10
EMPHASIS_SUBSETS = 3           # random shorter emphasis lists per target variant
N_FOLDS = 5
TOP_K = 10                     # the app lists ten foods and ten dishes

# Mirrors src.diet.meal_plan._EMPHASIS_SATURATION: once a nutrient's ratio
# passes this, more of it stops adding to the label — the same
# diminishing-returns idea meal_plan already applies across a whole day,
# applied here to a single item's label so the model learns it too.
SATURATION_CAP = 1.5
# Heme iron (meat/fish/egg) is absorbed at meaningfully higher bioavailability
# than non-heme (plant) iron — same physiology already cited in
# src/clinical/rules/deficiency_map.yaml's anemia rationale re: vitamin C
# enhancing non-heme absorption (Hallberg et al. 1989).
HEME_BONUS = 0.5
# An item is only penalized once it alone supplies more than this share of
# the day's sodium ceiling (WHO 2012, <2000 mg/day) — below that a
# high-sodium tag alone (already a hard exclusion for hypertension patients
# via the gate) is doing the real work; this is a *softer*, continuous
# signal for everyone else.
SODIUM_SOFT_THRESHOLD = 0.15
SODIUM_PENALTY = 1.0
# Prevents trivial R^2=1.0 memorization of a deterministic function of the
# input features. This is NOT what justifies a nonlinear model over a linear
# one — the saturation cap, heme interaction, sodium penalty and the
# finding-by-food-group priors are (genuine threshold/interaction
# structure a sum-of-ratios can't represent). Added to the training labels
# only: models are evaluated against the label without it.
LABEL_NOISE_STD = 0.05

# GradientBoostingRegressor is kept deliberately UNTUNED — a reference point
# showing that boosting without care underperforms both the tuned bagging
# model and the tuned histogram-boosting model below, not a shipping
# candidate. random_state pinned for reproducibility, nothing else touched.
GRADIENT_BOOSTING_PARAMS = dict(random_state=RANDOM_STATE)

# Search spaces for the two candidates that DO get tuned (see tune() below).
# Ranges bound tree complexity deliberately: an unconstrained RandomForest
# grows fully-depth trees that memorize individual rows, which on a few
# hundred thousand synthetic rows serializes to several hundred MB and is
# pointless besides (this app only ever ranks <=700 candidates per request;
# it doesn't need leaf-per-row resolution).
RANDOM_FOREST_SEARCH_SPACE = {
    "n_estimators": [100, 150],
    "max_depth": [10, 12, 14, 18],
    "min_samples_leaf": [1, 2, 3, 5, 8],
}
# Each tree is grown on a bootstrap sample of this share of the rows: the
# frame repeats every item across several hundred patient contexts, so a
# tenth of it still shows a tree every item dozens of times, at a tenth of
# the cost (and a quarter of the rows ranked held-out patients no better).
RANDOM_FOREST_MAX_SAMPLES = 0.1
HIST_GRADIENT_BOOSTING_SEARCH_SPACE = {
    "max_iter": [300, 500],
    "max_leaf_nodes": [31, 63, 127],
    "learning_rate": [0.05, 0.1, 0.2],
    "l2_regularization": [0.0, 0.1, 1.0],
    "min_samples_leaf": [5, 10, 20],
}
# Tuning search folds: intentionally coarser than the N_FOLDS=5 final
# evaluation below — full nested cross-validation (re-tuning inside every
# outer fold) would be the gold standard but multiplies runtime well beyond
# what's worth spending here. Still grouped by archetype, same as everywhere
# else, so tuning never picks hyperparameters that just memorize an
# archetype it'll then be "evaluated" on.
TUNING_CV_FOLDS = 3
TUNING_ITER = 8
# permutation importance of the shipped model, on a row sample
IMPORTANCE_SAMPLE = 5000
IMPORTANCE_REPEATS = 5

_spearman_scorer = make_scorer(lambda y_true, y_pred: spearmanr(y_true, y_pred).statistic)

MODEL_NAMES = ("hand_tuned_baseline", "linear_regression", "gradient_boosting",
               "random_forest", "hist_gradient_boosting")


def metric_names(top_k: int) -> tuple:
    return ("spearman", f"top{top_k}", f"ndcg{top_k}", "r2", "mae")


# --- food-group appropriateness priors, each traceable to a citation already
# in this repo (see data/reference/contraindications.yaml,
# src/clinical/rules/deficiency_map.yaml) rather than invented coefficients ---

# Always-on baseline: a mild whole-food/processed-food split, independent of
# any specific finding (applies even to the "no findings" archetypes).
# spice/oil get a much larger penalty than the others: bd_food.csv's
# nutrient columns are per-100g, and value/target ratios are computed
# against that same 100g basis everywhere — realistic for a grain/vegetable/
# meat serving, but spices are consumed in single-digit gram quantities, so
# their per-100g ratios are wildly inflated relative to how they're actually
# eaten (dried turmeric's iron content per 100g overstates a real pinch by
# roughly two orders of magnitude). Without this correction spices dominate
# "top foods" for any anemia-adjacent emphasis, which is exactly the
# recommendation-quality complaint this model exists to fix.
_BASELINE_GROUP_PRIOR = {
    "vegetable": 0.15, "fruit": 0.10, "legume": 0.10, "fish": 0.10,
    "grain": 0.05, "egg": 0.05, "dairy": 0.05,
    "oil": -0.50, "sweet": -0.20, "spice": -2.00,
}
# Tea and coffee *powder* have the same per-100 g problem as spices (brewed
# from a few grams — tea powder lists 6040 mg potassium/100 g), but sit in the
# "other" group beside genuinely good picks (nuts, seeds), so they carry a
# brewed_beverage tag in bd_food.csv and get the spice correction by tag.
CONCENTRATE_PENALTY = _BASELINE_GROUP_PRIOR["spice"]
# DASH pattern (Appel et al. 1997, N Engl J Med — same citation as the
# hypertension finding's potassium/fiber emphasis in deficiency_map.yaml):
# more fruit/vegetable/low-fat dairy, less red meat and sweets.
_HYPERTENSION_GROUP_PRIOR = {
    "fruit": 0.20, "vegetable": 0.20, "dairy": 0.15,
    "meat": -0.15, "sweet": -0.15, "oil": -0.10,
}
# ADA Standards of Care 2024 (same citation as the diabetes finding's fiber
# emphasis): fiber-rich legumes/vegetables/fish, minimize added sugar.
_DIABETES_GROUP_PRIOR = {
    "legume": 0.20, "vegetable": 0.15, "fish": 0.10, "sweet": -0.30,
}

# 2018 AHA/ACC cholesterol guideline (Grundy et al., Circulation 2019 — same
# citation as the high-cholesterol finding's fiber emphasis): a diet that
# emphasizes vegetables, fruits, legumes and fish among its protein sources,
# and limits sweets and red meats. (Its whole grains and nuts have no group
# of their own in the food table: "grain" is mostly milled rice, and nuts
# share "other" with seeds and drinks.)
# Egg is the one food group that stands for dietary cholesterol: a yolk
# carries about 185 mg, nearly the whole day's allowance in the therapeutic
# diet (NCEP ATP III 2002: under 200 mg/day; 2019 ACC/AHA primary prevention
# guideline: a diet with reduced cholesterol can be beneficial). Its term is
# larger than the others because a dish is mostly not egg by weight (an egg
# curry is about a third egg, the rest onion and potato, which the vegetable
# term rewards): with no egg term, discouraging meat moved a week's dinners
# to egg dishes and took the week from 5 egg dishes to 7; at -0.15 nothing
# changed; at -0.50 the week keeps the 5 it has without the finding.
_CHOLESTEROL_GROUP_PRIOR = {
    "vegetable": 0.15, "fruit": 0.15, "legume": 0.15, "fish": 0.10,
    "meat": -0.15, "sweet": -0.15, "egg": -0.50,
}

_FINDING_GROUP_PRIORS = {
    "hypertension": _HYPERTENSION_GROUP_PRIOR,
    "diabetes": _DIABETES_GROUP_PRIOR,
    "high_cholesterol": _CHOLESTEROL_GROUP_PRIOR,
}
_HEME_GROUPS = ("meat", "fish", "egg")

# (sex, pregnant, an age inside the band): one per reference intake group of
# data/reference/rdi_values.yaml. build_archetypes() refuses to run if a
# group there has no entry here.
_DEMOGRAPHICS = (
    ("male", False, 30), ("female", False, 30),
    ("male", False, 60), ("female", False, 60),
    ("male", False, 75), ("female", False, 75),
    ("female", True, 28),
)


@dataclass(frozen=True)
class Archetype:
    archetype_id: str
    findings: tuple
    targets: dict
    limits: dict
    emphasize: tuple


def build_archetypes() -> list[Archetype]:
    """Every RDI group x every combination of the modeled findings x every
    recorded condition that takes a nutrient out of the emphasis — grounded
    in the app's own nutrient_targets(), not invented numbers. A finding is
    given as a condition recorded on the patient, which nutrient_targets
    treats as a finding whatever the day's lab values say, so one that no
    lab band derives (high cholesterol) is covered like the rest."""
    finding_pool = recommender.FINDING_FEATURES
    finding_combos = [
        combo for r in range(len(finding_pool) + 1) for combo in combinations(finding_pool, r)
    ]
    suppressing = list(deficiency._rules().get("suppress") or {})

    archetypes = []
    for sex, pregnant, age in _DEMOGRAPHICS:
        for combo in finding_combos:
            usual = deficiency.nutrient_targets(sex, pregnant, [], conditions=combo, age=age)
            variants = [("", usual)]
            for condition in suppressing:
                ruled_out = deficiency.nutrient_targets(sex, pregnant, [],
                                                        conditions=[*combo, condition], age=age)
                # the condition only makes a different patient where it
                # changes what is emphasized
                if ruled_out["emphasize"] != usual["emphasize"]:
                    variants.append((f"|{condition}", ruled_out))
            for suffix, nutrition in variants:
                archetypes.append(Archetype(
                    archetype_id=f"{nutrition['group']}|{'+'.join(combo) or 'none'}{suffix}",
                    findings=combo,
                    targets=nutrition["targets"], limits=nutrition["limits"],
                    emphasize=tuple(nutrition["emphasize"]),
                ))

    untrained = set(deficiency._rdi()["groups"]) - {a.archetype_id.split("|")[0] for a in archetypes}
    if untrained:
        raise SystemExit(f"no archetype for reference intake group(s) {sorted(untrained)} — "
                         "add them to _DEMOGRAPHICS")
    return archetypes


def _jitter_targets(targets: dict, rng: np.random.Generator) -> dict:
    return {k: v * (1.0 + rng.uniform(-TARGET_JITTER_PCT, TARGET_JITTER_PCT))
            for k, v in targets.items()}


def _emphasis_variants(emphasize: tuple, untracked: frozenset,
                       rng: np.random.Generator) -> list[list[str]]:
    """The emphasis lists one patient is scored under. The suggestion lists
    are ranked on the full emphasis. The meal planner starts from the
    nutrients the food table has values for (meal_plan.build_meal_plan
    leaves the `untracked` ones out) and scores every course against those
    the day is still short of, so its list shrinks as the plan fills up and
    can end empty: training only on the full list would leave every planned
    course an unseen input. Returns the full list, the planner's, the empty
    one, and a few random lists between the last two."""
    variants = [list(emphasize)]
    planned = [n for n in emphasize if n not in untracked]
    if planned != variants[0]:
        variants.append(planned)
    if planned:
        variants.append([])
        shorter = [list(s) for k in range(1, len(planned)) for s in combinations(planned, k)]
        picked = rng.choice(len(shorter), size=min(EMPHASIS_SUBSETS, len(shorter)), replace=False)
        variants.extend(shorter[i] for i in sorted(picked))
    return variants


def _group_prior(food_group: str | None, findings: tuple) -> float:
    score = _BASELINE_GROUP_PRIOR.get(food_group, 0.0)
    for finding in findings:
        score += _FINDING_GROUP_PRIORS.get(finding, {}).get(food_group, 0.0)
    return score


def _capped_emphasis(nutrients: dict, emphasize: list[str], targets: dict) -> float:
    total = 0.0
    for nutrient in emphasize:
        target = targets.get(nutrient)
        if target:
            total += min(nutrients.get(nutrient, 0.0) / target, SATURATION_CAP)
    return total


def _sodium_penalty(nutrients: dict, limits: dict) -> float:
    sodium_limit = limits.get("sodium_mg")
    if not sodium_limit:
        return 0.0
    sodium_ratio = nutrients.get("sodium_mg", 0.0) / sodium_limit
    return SODIUM_PENALTY * max(0.0, sodium_ratio - SODIUM_SOFT_THRESHOLD)


def _heme_bonus(nutrients: dict, targets: dict) -> float:
    iron_target = targets.get("iron_mg")
    if not iron_target:
        return 0.0
    return HEME_BONUS * min(nutrients.get("iron_mg", 0.0) / iron_target, SATURATION_CAP)


def compute_food_label(nutrients: dict, food_group: str | None, tags, findings: tuple,
                       emphasize: list[str], targets: dict, limits: dict) -> float:
    label = _capped_emphasis(nutrients, emphasize, targets) if emphasize else _density_score(nutrients)
    label += _group_prior(food_group, findings)
    if "brewed_beverage" in tags:
        label += CONCENTRATE_PENALTY
    if "anemia" in findings and food_group in _HEME_GROUPS:
        label += _heme_bonus(nutrients, targets)
    label -= _sodium_penalty(nutrients, limits)
    return label


def compute_recipe_label(nutrients: dict, group_shares: dict, findings: tuple,
                         emphasize: list[str], targets: dict, limits: dict) -> float:
    """The food label, per serving, for a mixed dish — no new coefficients:
    - the food-group prior is the weight-weighted mean of the ingredients'
      priors (a leafy-green stir-fry inherits the vegetable prior, a payesh
      the dairy/grain/sweet mix);
    - the heme bonus is scaled by the dish's meat/fish/egg share.
    Like the food label it says how well a serving suits the patient, not
    how often anyone cooks it: src.diet.matcher.familiar_score weights the
    fit by household familiarity afterwards, the model's and the formula's
    alike.
    """
    fit = _capped_emphasis(nutrients, emphasize, targets) if emphasize else _density_score(nutrients)
    fit += sum(share * _group_prior(group, findings) for group, share in group_shares.items())
    if "anemia" in findings:
        heme_share = sum(group_shares.get(g, 0.0) for g in _HEME_GROUPS)
        fit += heme_share * _heme_bonus(nutrients, targets)
    fit -= _sodium_penalty(nutrients, limits)
    return fit


def _food_example(food, archetype: Archetype, emphasize: list[str],
                  targets: dict) -> tuple[np.ndarray, float, float]:
    nutrients = food.nutrients
    label = compute_food_label(nutrients, food.food_group, food.tags, archetype.findings,
                               emphasize, targets, archetype.limits)
    vector = recommender.featurize(
        nutrients, food.food_group, food.tags, emphasize, targets,
        _emphasis_score(nutrients, emphasize, targets) if emphasize else 0.0,
        _density_score(nutrients), findings=archetype.findings, limits=archetype.limits,
    )
    return vector, label, food_baseline_score(nutrients, emphasize, targets)


def _recipe_example(recipe, archetype: Archetype, emphasize: list[str],
                    targets: dict) -> tuple[np.ndarray, float, float]:
    nutrients = recipe.per_serving
    label = compute_recipe_label(nutrients, recipe.group_shares, archetype.findings,
                                 emphasize, targets, archetype.limits)
    vector = recommender.featurize_recipe(
        nutrients, recipe.group_shares, recipe.tags, emphasize, targets,
        _emphasis_score(nutrients, emphasize, targets) if emphasize else 0.0,
        _density_score(nutrients), findings=archetype.findings, limits=archetype.limits,
    )
    return vector, label, food_baseline_score(nutrients, emphasize, targets)


def _foods_and_pool() -> tuple[list, list[bool], list[float]]:
    """Every food; whether the app suggests it on its own (a Bangladeshi
    food households cook in portions, or whole fresh fruit — see
    src.api.services.build_assessment), before any patient's own exclusions;
    and what src.diet.matcher.rank_foods multiplies a suggested food's
    positive score by: the share of a week's main meals households eat it
    at x its usual portion / 100 g."""
    foods = load_foods()
    recipes = load_recipes(food_index(foods))
    habits = food_habits(recipes)
    suggested = habitual_foods(eaten_in_portions(recommendable_foods(foods)), habits)
    meals = meals_per_week_map(suggested, habits, unknown=median_meals_per_week(habits))
    portion_g = portion_map(suggested, habits)
    weight = {f.food_id: meal_frequency_weight(meals[f.food_id]) * portion_g[f.food_id] / 100.0
              for f in suggested}
    return foods, [f.food_id in weight for f in foods], [weight.get(f.food_id, 1.0) for f in foods]


def _recipes_and_pool() -> tuple[list, list[bool], list[float]]:
    """Every recipe; whether the app plans and suggests it by itself; and
    the household familiarity its positive score is multiplied by."""
    recipes = load_recipes(food_index(load_foods()))
    return (recipes, [plannable(r) for r in recipes],
            [frequency_multiplier(r.weekly_frequency_score) for r in recipes])


# --- the exercise model -------------------------------------------------
#
# The exercise label is the prescription's formula
# (src.lifestyle.ranking.baseline_score) plus what a guideline says suits a
# patient with a particular condition, read off the traits the converter
# derived from the exercise dataset's own notes. Each term is an interaction
# between something about the patient and something about the exercise, the
# structure a tree ensemble can represent and a sum of separate weights
# cannot.

# Pregnancy: pelvic floor muscle training is recommended throughout
# pregnancy (Mottola MF et al. 2019 Canadian guideline for physical activity
# throughout pregnancy, Br J Sports Med 2018;52:1339-46), and walking and
# stationary cycling are the activities ACOG Committee Opinion 804 (2020)
# names; the dataset marks those and the ones from NHS and charity pregnancy
# workouts pregnancy_recommended.
PREGNANCY_PELVIC_FLOOR = 0.6
PREGNANCY_RECOMMENDED = 0.4
# Outside pregnancy the dataset's pelvic floor rows are treatment for bladder
# leaks (NHS, POGP), which the patient record does not hold: a general plan's
# trunk exercise should be a core exercise.
PELVIC_FLOOR_ELSEWHERE = -0.3
# Knee osteoarthritis: muscle strengthening (quadriceps, hip abductors) and
# low-impact aerobic exercise are core treatment (Bannuru RR et al. OARSI
# guidelines for the non-surgical management of knee, hip, and polyarticular
# osteoarthritis, Osteoarthritis Cartilage 2019;27:1578-89). The dataset rates
# most quadriceps work "modify" for knee osteoarthritis (keep to a pain-free
# range), so the term outweighs that penalty: at 0.5 the two cancelled and an
# advanced patient's plan had no quadriceps exercise at all.
KNEE_OA_STRENGTHENING = 0.8
KNEE_OA_LOW_IMPACT = 0.3
# Diabetes: the dataset's diabetes notes single out activity after meals.
DIABETES_POST_MEAL = 0.3
# Hypertension: sustained isometric holds and breath-holding raise blood
# pressure (ACSM GETP 11th ed.; the dataset's hypertension notes), on top of
# the "modify" penalty most such rows already carry.
HYPERTENSION_ISOMETRIC = -0.3
# Anaemia: of the aerobic activities the plan allows, the gentler first
# (ACSM GETP 11th ed., clinical populations), per MET above 3.
ANEMIA_PER_MET = -0.1
# 65 and over: balance and functional exercise from falls-prevention
# programmes (Sherrington C et al. Exercise for preventing falls in older
# people living in the community, Cochrane Database Syst Rev 2019;CD012424;
# WHO 2020), and supported, seated work.
OLDER_FALLS_PREVENTION = 0.4
OLDER_SEATED = 0.2
# Obesity: low-impact activity spares the joints (ACSM GETP 11th ed.,
# overweight and obesity).
OBESE_LOW_IMPACT = 0.3
# A plan that starts light (a beginner, or a high or critical biomarker
# risk) favours supported, seated work.
LIGHT_START_SEATED = 0.15

# (sex, age, pregnant): adults under 65 at two ages, adults 65 and over
# (the older_adult population rule), and pregnancy
_EXERCISE_DEMOGRAPHICS = (
    ("male", 35, False), ("female", 35, False),
    ("male", 55, False), ("female", 55, False),
    ("male", 72, False), ("female", 72, False),
    ("female", 28, True),
)
_EXERCISE_CONDITIONS = ("hypertension", "diabetes", "anemia", "knee_osteoarthritis")
# (fitness level, overall biomarker risk): every fitness level, and for the
# two above beginner both starting intensities (high risk starts light)
_EXERCISE_FITNESS = (("beginner", "low"), ("intermediate", "high"), ("intermediate", "low"),
                     ("advanced", "high"), ("advanced", "low"))
_EXERCISE_BMI = ("normal", "obese")
EXERCISE_TOP_K = 3  # the prescription lists 2-4 exercises per group


def compute_exercise_label(exercise, ctx) -> float:
    label = exercise_ranking.baseline_score(exercise, ctx)
    traits = set(exercise.traits)
    if "pregnancy" in ctx.conditions:
        label += PREGNANCY_PELVIC_FLOOR * ("pelvic_floor" in traits)
        label += PREGNANCY_RECOMMENDED * ("pregnancy_recommended" in traits)
    elif "pelvic_floor" in traits:
        label += PELVIC_FLOOR_ELSEWHERE
    if "knee_osteoarthritis" in ctx.conditions:
        label += KNEE_OA_STRENGTHENING * ("knee_oa_strengthening" in traits)
        label += KNEE_OA_LOW_IMPACT * ("low_impact" in traits)
    if "diabetes" in ctx.conditions:
        label += DIABETES_POST_MEAL * ("post_meal" in traits)
    if "hypertension" in ctx.conditions:
        label += HYPERTENSION_ISOMETRIC * ("isometric_hold" in traits)
    if "anemia" in ctx.conditions and exercise.met_value:
        label += ANEMIA_PER_MET * max(0.0, exercise.met_value - 3.0)
    if ctx.older:
        label += OLDER_FALLS_PREVENTION * ("falls_prevention" in traits)
        label += OLDER_SEATED * ("seated" in traits)
    if ctx.obese:
        label += OBESE_LOW_IMPACT * ("low_impact" in traits)
    if ctx.start_level == "light":
        label += LIGHT_START_SEATED * ("seated" in traits)
    return label


def build_exercise_frame(section, rng: np.random.Generator) -> "Frame":
    """Every patient type of the grid above, through the same gate and the
    same plannable rules as the app (src.clinical.contraindication,
    src.lifestyle.ranking.plannable), so a model trains on exactly the
    exercises the prescription would rank for that patient. A query is one
    group of one patient's prescription (aerobic, strength, flexibility,
    balance): the app ranks within a group, never across."""
    exercises = load_exercises()
    if not exercises:
        raise SystemExit("no exercises to train on — run scripts/convert_datasets.py first")
    features, labels, groups, queries, baselines = [], [], [], [], []
    query = 0
    combos = [c for r in range(len(_EXERCISE_CONDITIONS) + 1)
              for c in combinations(_EXERCISE_CONDITIONS, r)]
    for sex, age, pregnant in _EXERCISE_DEMOGRAPHICS:
        for combo in combos:
            conditions = [*combo, "pregnancy"] if pregnant else list(combo)
            allowed = filter_items(exercises,
                                   excluded_tags(conditions, age=age, sex=sex).exercise_tags)
            for fitness, risk in _EXERCISE_FITNESS:
                for bmi in _EXERCISE_BMI:
                    ctx = exercise_ranking.context_for(age, sex, conditions, fitness, risk, bmi)
                    archetype_id = (f"{sex}-{age}{'-pregnant' if pregnant else ''}|"
                                    f"{'+'.join(combo) or 'none'}|{fitness}-{ctx.start_level}|{bmi}")
                    for group in PLAN_GROUPS:
                        items = [e for e in allowed
                                 if e.category == group and exercise_ranking.plannable(e, ctx)]
                        if len(items) < 2:  # nothing to order
                            continue
                        for exercise in items:
                            features.append(exercise_recommender.featurize(exercise, ctx))
                            labels.append(compute_exercise_label(exercise, ctx))
                            baselines.append(exercise_ranking.baseline_score(exercise, ctx))
                            groups.append(archetype_id)
                            queries.append(query)
                        query += 1
    label = np.asarray(labels, dtype=np.float64)
    return Frame(
        X=np.vstack(features),
        y=label + rng.normal(0.0, LABEL_NOISE_STD, size=len(label)),
        label=label,
        groups=np.asarray(groups),
        queries=np.asarray(queries),
        served=np.ones(len(label), dtype=bool),
        weight=np.ones(len(label), dtype=np.float64),
        baseline=np.asarray(baselines, dtype=np.float64),
        n_items=len(exercises),
        top_k=EXERCISE_TOP_K,
    )


@dataclass(frozen=True)
class Section:
    kind: str
    model_path: Path
    feature_version: int
    feature_names: tuple
    load_items: object = None  # () -> (items, whether the app ranks each, each one's ranking weight)
    example: object = None     # (item, archetype, emphasize, targets) -> (x, label, the formula's fit)
    # (section, rng) -> Frame, for a section not built from the nutrition
    # archetypes (the exercises); build_training_frame otherwise
    build_frame: object = None


SECTIONS = {
    "food": Section(
        kind="food", model_path=recommender.MODEL_PATH,
        feature_version=recommender.FEATURE_VERSION,
        feature_names=recommender.FEATURE_NAMES,
        load_items=_foods_and_pool, example=_food_example,
    ),
    "recipe": Section(
        kind="recipe", model_path=recommender.RECIPE_MODEL_PATH,
        feature_version=recommender.RECIPE_FEATURE_VERSION,
        feature_names=recommender.RECIPE_FEATURE_NAMES,
        load_items=_recipes_and_pool, example=_recipe_example,
    ),
    "exercise": Section(
        kind="exercise", model_path=exercise_recommender.MODEL_PATH,
        feature_version=exercise_recommender.FEATURE_VERSION,
        feature_names=exercise_recommender.FEATURE_NAMES,
        build_frame=build_exercise_frame,
    ),
}


@dataclass(frozen=True)
class Frame:
    """One row per (patient context, item)."""
    X: np.ndarray
    y: np.ndarray         # the label with noise: what a model is fitted to
    label: np.ndarray     # the label without it: what a model is judged against
    groups: np.ndarray    # archetype id, the unit held out in cross-validation
    queries: np.ndarray   # one id per (archetype, targets, emphasis): one list to rank
    served: np.ndarray    # whether the app ranks this row's item
    weight: np.ndarray    # what the app multiplies the item's positive score by before sorting
    baseline: np.ndarray  # the deterministic formula's score
    n_items: int
    top_k: int = TOP_K    # how many items of a list the app shows


def build_training_frame(section: Section, rng: np.random.Generator) -> Frame:
    """`baseline` is the deterministic formula's own fit per row (what
    src.diet.matcher scores with when no model is present), kept as an
    explicit parallel array rather than decoded back out of the feature
    matrix at eval time."""
    items, in_pool, weights = section.load_items()
    if not items:
        raise SystemExit(f"no {section.kind} items to train on — run scripts/convert_datasets.py first")

    untracked = untracked_nutrients(load_foods())

    features, labels, groups, queries, baselines = [], [], [], [], []
    query = 0
    for archetype in build_archetypes():
        for repeat in range(NOISE_REPEATS):
            targets = dict(archetype.targets) if repeat == 0 else _jitter_targets(archetype.targets, rng)
            for emphasize in _emphasis_variants(archetype.emphasize, untracked, rng):
                for item in items:
                    vector, label, baseline = section.example(item, archetype, emphasize, targets)
                    features.append(vector)
                    labels.append(label)
                    groups.append(archetype.archetype_id)
                    queries.append(query)
                    baselines.append(baseline)
                query += 1

    label = np.asarray(labels, dtype=np.float64)
    return Frame(
        X=np.vstack(features),
        y=label + rng.normal(0.0, LABEL_NOISE_STD, size=len(label)),
        label=label,
        groups=np.asarray(groups),
        queries=np.asarray(queries),
        served=np.tile(np.asarray(in_pool, dtype=bool), query),
        weight=np.tile(np.asarray(weights, dtype=np.float64), query),
        baseline=np.asarray(baselines, dtype=np.float64),
        n_items=len(items),
    )


def monotonic_constraints(feature_names: tuple) -> list[int]:
    """Per feature: +1 the score never falls as it rises, -1 never rises,
    0 free. Each is a property the label has by construction, so none costs
    accuracy; what they buy is that a fitted model cannot contradict them
    anywhere, including on a dish or a patient unlike any it trained on.
    - A nutrient's share of its daily target, and the two formula scores
      built from those shares: +1. Emphasized, more of it is the point (up
      to the cap, where the label goes flat, never down); otherwise it only
      ever enters through protein + fiber density or the heme-iron bonus.
    - Sodium's share of its limit: -1.
    Energy is left free: it is the denominator of the density score.
    For an exercise:
    - the formula's score, a dose from the source, a demonstration video: +1;
    - needing modification for one of the patient's conditions or their age,
      needing bought equipment, each level below the patient's: -1;
    - being rated "modify" for a condition, or suitable at 65 and over only
      in its easier version, whether or not the patient is concerned: -1 (no
      effect when they are not, a penalty when they are)."""
    constraints = []
    for name in feature_names:
        if name.endswith("_ratio"):
            constraints.append(0 if name.startswith("kcal_")
                               else -1 if name.startswith("sodium_mg_") else 1)
        elif name in ("baseline_emphasis_score", "baseline_density_score"):
            constraints.append(1)
        elif name in _EXERCISE_MONOTONIC:
            constraints.append(_EXERCISE_MONOTONIC[name])
        elif name.startswith(("needs_modification_", "rated_modify_")):
            constraints.append(-1)
        else:
            constraints.append(0)
    return constraints


_EXERCISE_MONOTONIC = {
    "baseline_score": 1, "has_dose": 1, "video_exact": 1, "video_close_variant": 1,
    "needs_equipment": -1, "levels_below_patient": -1, "older_adult_modify": -1,
}


def _random_forest(params: dict, feature_names: tuple) -> RandomForestRegressor:
    return RandomForestRegressor(
        **params, max_samples=RANDOM_FOREST_MAX_SAMPLES,
        monotonic_cst=monotonic_constraints(feature_names),
        random_state=RANDOM_STATE, n_jobs=-1,
    )


def _hist_gradient_boosting(params: dict, feature_names: tuple) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        **params, monotonic_cst=monotonic_constraints(feature_names), random_state=RANDOM_STATE,
    )


def _spearman(label: np.ndarray, predicted: np.ndarray) -> float:
    # a scorer that gives every item the same score has ranked nothing
    if np.ptp(predicted) == 0 or np.ptp(label) == 0:
        return 0.0
    return float(spearmanr(label, predicted).statistic)


def _top_k_agreement(label: np.ndarray, predicted: np.ndarray, top_k: int = TOP_K) -> float:
    """Share of a scorer's top TOP_K that the label also ranks in its top
    TOP_K, counting every item tied with the label's last place as in it.
    The ties are real: no food in the table has a folate value, so with
    folate the only nutrient still emphasized every vegetable has the same
    label, and which ten of them come first means nothing."""
    k = min(top_k, len(label))
    cutoff = np.sort(label)[-k]
    chosen = np.argsort(-predicted, kind="stable")[:k]
    return float(np.mean(label[chosen] >= cutoff))


def _ndcg(label: np.ndarray, predicted: np.ndarray, top_k: int = TOP_K) -> float:
    """NDCG@TOP_K with the label as the gain; an item the label scores at or
    below zero (one the app would never list) is worth nothing."""
    gain = np.clip(label, 0.0, None)
    k = min(top_k, len(label))
    discount = 1.0 / np.log2(np.arange(2, k + 2))
    ideal = float((np.sort(gain)[::-1][:k] * discount).sum())
    if ideal <= 0:
        return float("nan")
    return float((gain[np.argsort(-predicted, kind="stable")[:k]] * discount).sum()) / ideal


def _as_ranked(score: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """The score the app sorts by — src.diet.matcher.familiar_score, and for
    foods rank_foods' portion weighting: a positive fit is multiplied, an
    unsuitable item's is left as it is."""
    return np.where(score > 0, score * weight, score)


def ranking_metrics(frame: Frame, rows: np.ndarray, predicted: np.ndarray) -> dict:
    """How well `predicted` (aligned with `rows`) orders each query's served
    items once weighted as the app weights them, averaged over the queries
    in `rows`."""
    served = frame.served[rows]
    weight, queries = frame.weight[rows][served], frame.queries[rows][served]
    label = _as_ranked(frame.label[rows][served], weight)
    predicted = _as_ranked(predicted[served], weight)
    order = np.argsort(queries, kind="stable")
    per_query = np.split(order, np.flatnonzero(np.diff(queries[order])) + 1)
    k = frame.top_k
    return {
        "spearman": float(np.mean([_spearman(label[q], predicted[q]) for q in per_query])),
        f"top{k}": float(np.mean([_top_k_agreement(label[q], predicted[q], k) for q in per_query])),
        f"ndcg{k}": float(np.nanmean([_ndcg(label[q], predicted[q], k) for q in per_query])),
    }


def tune(make_estimator, search_space: dict, frame: Frame, feature_names: tuple) -> dict:
    """Randomized search grouped by archetype, optimizing the held-out
    within-patient Spearman correlation over the items the app ranks (the
    metric this script reports as its primary evidence) rather than R^2/MAE.
    Returns the best parameters found."""
    folds = list(GroupKFold(n_splits=TUNING_CV_FOLDS).split(frame.X, groups=frame.groups))
    best_params, best_score = None, -np.inf
    for params in ParameterSampler(search_space, n_iter=TUNING_ITER, random_state=RANDOM_STATE):
        scores = []
        for train_idx, test_idx in folds:
            model = make_estimator(params, feature_names).fit(frame.X[train_idx], frame.y[train_idx])
            scores.append(ranking_metrics(frame, test_idx, model.predict(frame.X[test_idx]))["spearman"])
        if np.mean(scores) > best_score:
            best_params, best_score = params, float(np.mean(scores))
    return best_params


def evaluate(frame: Frame, feature_names: tuple, rf_params: dict, histgb_params: dict) -> dict:
    """GroupKFold split BY ARCHETYPE, not by item: real deployment always
    scores against the same fixed catalog but always sees novel patient
    target/emphasize combinations, so generalization must be measured across
    unseen archetypes, not unseen items."""
    n_splits = min(N_FOLDS, len(np.unique(frame.groups)))
    folds = list(GroupKFold(n_splits=n_splits).split(frame.X, groups=frame.groups))
    per_fold = {name: [] for name in MODEL_NAMES}

    def boosted_fold(train_idx: np.ndarray, test_idx: np.ndarray) -> np.ndarray:
        model = GradientBoostingRegressor(**GRADIENT_BOOSTING_PARAMS)
        return model.fit(frame.X[train_idx], frame.y[train_idx]).predict(frame.X[test_idx])

    # GradientBoostingRegressor fits on one core and is by far the slowest
    # model here, so its folds are fitted side by side; the others use every
    # core by themselves
    boosted = Parallel(n_jobs=n_splits, prefer="threads")(
        delayed(boosted_fold)(*fold) for fold in folds)

    for (train_idx, test_idx), boosted_prediction in zip(folds, boosted):
        X_train, y_train, X_test = frame.X[train_idx], frame.y[train_idx], frame.X[test_idx]
        predictions = {
            "hand_tuned_baseline": frame.baseline[test_idx],
            "linear_regression": LinearRegression().fit(X_train, y_train).predict(X_test),
            "gradient_boosting": boosted_prediction,
            "random_forest": _random_forest(rf_params, feature_names)
            .fit(X_train, y_train).predict(X_test),
            "hist_gradient_boosting": _hist_gradient_boosting(histgb_params, feature_names)
            .fit(X_train, y_train).predict(X_test),
        }
        label = frame.label[test_idx]
        for name, predicted in predictions.items():
            per_fold[name].append({
                **ranking_metrics(frame, test_idx, predicted),
                "r2": float(r2_score(label, predicted)),
                "mae": float(mean_absolute_error(label, predicted)),
            })

    return {
        name: {
            metric: {
                "mean": float(np.mean([f[metric] for f in folds])),
                "std": float(np.std([f[metric] for f in folds])),
            }
            for metric in metric_names(frame.top_k)
        }
        for name, folds in per_fold.items()
    }


def _feature_importance(model, frame: Frame, names: tuple) -> list[dict]:
    """Permutation importance (drop in Spearman correlation when a feature is
    shuffled) — model-agnostic, so it works for whichever estimator wins
    (HistGradientBoosting has no feature_importances_)."""
    rng = np.random.default_rng(RANDOM_STATE)
    idx = rng.choice(len(frame.X), size=min(IMPORTANCE_SAMPLE, len(frame.X)), replace=False)
    result = permutation_importance(
        model, frame.X[idx], frame.label[idx], scoring=_spearman_scorer,
        n_repeats=IMPORTANCE_REPEATS, random_state=RANDOM_STATE, n_jobs=-1,
    )
    ranked = sorted(
        zip(names, result.importances_mean, result.importances_std),
        key=lambda t: -t[1],
    )
    return [{"feature": n, "mean": float(m), "std": float(s)} for n, m, s in ranked]


def _write_comparison_csv(path: Path, summary: dict, top_k: int) -> None:
    rows = sorted(
        ({"model": name,
          "spearman_mean": m["spearman"]["mean"], "spearman_std": m["spearman"]["std"],
          f"top{top_k}_mean": m[f"top{top_k}"]["mean"],
          f"ndcg{top_k}_mean": m[f"ndcg{top_k}"]["mean"],
          "r2_mean": m["r2"]["mean"], "mae_mean": m["mae"]["mean"]}
         for name, m in summary.items()),
        key=lambda r: -r["spearman_mean"],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def train(section: Section, rng: np.random.Generator) -> dict | None:
    """Train, compare and save one model. Returns its metrics, or None when
    no model was saved because none ranked better than the formula."""
    print(f"\n=== {section.kind} model ===")
    print("building synthetic training frame from the dataset + cited reference targets...")
    frame = (section.build_frame or build_training_frame)(section, rng)
    names = section.feature_names
    n_archetypes = len(np.unique(frame.groups))
    n_queries = int(frame.queries.max()) + 1
    n_served = int(frame.served.sum()) // n_queries
    print(f"{frame.n_items} {section.kind}s ({n_served} in each list the app ranks, on average) -> "
          f"{frame.X.shape[0]} rows, {frame.X.shape[1]} features, "
          f"{n_archetypes} archetypes, {n_queries} queries")

    print(f"tuning RandomForest ({TUNING_ITER} candidates x {TUNING_CV_FOLDS}-fold GroupKFold)...")
    rf_params = tune(_random_forest, RANDOM_FOREST_SEARCH_SPACE, frame, names)
    print(f"  best params: {rf_params}")

    print(f"tuning HistGradientBoosting ({TUNING_ITER} candidates x {TUNING_CV_FOLDS}-fold GroupKFold)...")
    histgb_params = tune(_hist_gradient_boosting, HIST_GRADIENT_BOOSTING_SEARCH_SPACE, frame, names)
    print(f"  best params: {histgb_params}")

    print(f"evaluating via {N_FOLDS}-fold GroupKFold (held out by archetype)...")
    summary = evaluate(frame, names, rf_params, histgb_params)

    k = frame.top_k
    print(f"\nmodel                     spearman   top-{k:<2d}     ndcg@{k:<2d}   r2        mae")
    for name, metrics in summary.items():
        print(f"{name:24s}  {metrics['spearman']['mean']:+.3f}     {metrics[f'top{k}']['mean']:.3f}     "
              f"{metrics[f'ndcg{k}']['mean']:.3f}     {metrics['r2']['mean']:+.3f}    "
              f"{metrics['mae']['mean']:.3f}")

    # GradientBoostingRegressor is untuned on purpose (a reference point, not
    # a shipping candidate) — only the two tuned models compete to be shipped.
    tuned_names = ("random_forest", "hist_gradient_boosting")
    winner_name = max(tuned_names, key=lambda n: summary[n]["spearman"]["mean"])
    print(f"\nwinner: {winner_name} (higher held-out Spearman correlation)")

    # the comparison is the record of this run whether or not a model comes of it
    csv_path = RESULTS_DIR / f"{section.kind}_recommender_comparison.csv"
    _write_comparison_csv(csv_path, summary, frame.top_k)
    print(f"saved comparison table -> {csv_path.relative_to(PROJECT_ROOT)}")
    metrics_path = section.model_path.with_name(f"{section.kind}_recommender_metrics.json")

    # a model that ranks no better than the formula it replaces is not an
    # improvement on having no model: leave the app on the formula. A model
    # from an earlier run would still load and go on scoring, so it goes too,
    # with the metrics that describe it.
    if (summary[winner_name]["spearman"]["mean"]
            <= summary["hand_tuned_baseline"]["spearman"]["mean"]):
        for earlier in (section.model_path, metrics_path):
            if earlier.exists():
                earlier.unlink()
                print(f"removed {earlier.relative_to(PROJECT_ROOT)} (from an earlier run)")
        print(f"{winner_name} does not rank held-out patients better than the "
              f"deterministic formula — no {section.kind} model saved")
        return None

    if winner_name == "random_forest":
        winner = _random_forest(rf_params, names)
    else:
        winner = _hist_gradient_boosting(histgb_params, names)
    winner.fit(frame.X, frame.y)  # refit on everything for the shipped artifact

    print("permutation feature importance of the shipped model...")
    importance = _feature_importance(winner, frame, names)

    # n_jobs=-1 speeds up training/CV, but the app scores a few hundred rows
    # per predict call (see recommender.ml_score_batch) — too few for
    # parallel dispatch to pay for its thread pool. Serve serially; train in
    # parallel.
    if hasattr(winner, "n_jobs"):
        winner.n_jobs = None

    section.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": winner, "kind": section.kind, "feature_version": section.feature_version,
         "sklearn_version": sklearn.__version__},
        section.model_path,
    )
    print(f"saved model -> {section.model_path.relative_to(PROJECT_ROOT)}")

    metrics = {
        "kind": section.kind, "winner": winner_name, "n_items": frame.n_items,
        "n_served_items": n_served,
        "n_rows": int(frame.X.shape[0]), "n_features": int(frame.X.shape[1]),
        "n_archetypes": n_archetypes, "n_queries": n_queries,
        "n_folds": min(N_FOLDS, n_archetypes),
        "tuned_params": {"random_forest": rf_params, "hist_gradient_boosting": histgb_params},
        "monotonic_constraints": {name: sign for name, sign
                                  in zip(names, monotonic_constraints(names)) if sign},
        "metrics": summary,
        "feature_importance": importance,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"saved metrics -> {metrics_path.relative_to(PROJECT_ROOT)}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=sorted(SECTIONS), help="train just one model")
    args = parser.parse_args()
    kinds = [args.only] if args.only else ["food", "recipe", "exercise"]
    # a fresh generator per model, so training one never shifts the other's data
    unsaved = [kind for kind in kinds
               if train(SECTIONS[kind], np.random.default_rng(RANDOM_STATE)) is None]
    if unsaved:
        # one model losing to the formula does not stop the other being trained
        raise SystemExit(f"no model saved for: {', '.join(unsaved)} — "
                         "the app scores those with the deterministic formula")


if __name__ == "__main__":
    main()
