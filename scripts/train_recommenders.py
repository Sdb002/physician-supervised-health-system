"""Train the two suitability models used by src.diet.recommender — one for
single foods, one for household recipes — each ranking its own section of the
diet recommendation.

Run from the project root:  .venv\\Scripts\\python.exe scripts\\train_recommenders.py
                            (add --only food or --only recipe to train one)

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
RandomForest/HistGradientBoosting are tuned via RandomizedSearchCV
(GroupKFold(3), optimizing held-out Spearman correlation) rather than
hand-picked constants — see tune() below.

The recipe label is the food label applied per serving, plus household
familiarity: the recipe dataset scores every dish 1-10 for how commonly it is
cooked at home (10 = the most common household dish), and a suitable dish's
label is scaled by src.diet.matcher.frequency_multiplier(score) — see
compute_recipe_label().

This script must be run from the project's own .venv (64-bit Python,
matching the running app) — the saved artifacts are version-pinned to the
sklearn build that trains them (see src.diet.recommender), so training under
a different interpreter/environment than the one serving requests would
immediately trip that check and fall back to the deterministic formula.

Outputs, per model (<kind> = food | recipe):
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
from scipy.stats import spearmanr
from sklearn.ensemble import (
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import make_scorer, mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, RandomizedSearchCV

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clinical.deficiency import nutrient_targets  # noqa: E402
from src.clinical.risk_scoring import RiskFlag  # noqa: E402
from src.diet import recommender  # noqa: E402
from src.diet.food_db import food_index, load_foods  # noqa: E402
from src.diet.matcher import (  # noqa: E402
    _density_score,
    _emphasis_score,
    frequency_multiplier,
    recipe_baseline_score,
)
from src.diet.recipe import load_recipes  # noqa: E402

RESULTS_DIR = PROJECT_ROOT / "thesis" / "results"

RANDOM_STATE = 42
NOISE_REPEATS = 4              # jittered-target variants per base archetype
TARGET_JITTER_PCT = 0.10
EMPHASIZE_SUBSET_VARIANTS = 1  # extra random non-empty subsets, beyond the full emphasize list
N_FOLDS = 5

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
# one — the saturation cap, heme interaction, sodium penalty and (for
# recipes) the familiarity scaling are (genuine threshold/interaction
# structure a sum-of-ratios can't represent).
LABEL_NOISE_STD = 0.05

# GradientBoostingRegressor is kept deliberately UNTUNED — a reference point
# showing that boosting without care underperforms both the tuned bagging
# model and the tuned histogram-boosting model below, not a shipping
# candidate. random_state pinned for reproducibility, nothing else touched.
GRADIENT_BOOSTING_PARAMS = dict(random_state=RANDOM_STATE)

# Search spaces for the two candidates that DO get tuned (see tune() below).
# Ranges bound tree complexity deliberately: an unconstrained RandomForest
# grows fully-depth trees that memorize individual rows, which on ~100k
# synthetic rows serializes to several hundred MB and is pointless besides
# (this app only ever ranks <=700 candidates per request; it doesn't need
# leaf-per-row resolution).
RANDOM_FOREST_SEARCH_SPACE = {
    "n_estimators": [100, 150, 200, 300],
    "max_depth": [8, 10, 12, 14, 18],
    "min_samples_leaf": [1, 2, 3, 5, 8],
}
HIST_GRADIENT_BOOSTING_SEARCH_SPACE = {
    "max_iter": [100, 150, 200, 300],
    "max_leaf_nodes": [15, 31, 63],
    "learning_rate": [0.03, 0.05, 0.1, 0.2],
    "l2_regularization": [0.0, 0.1, 1.0],
    "min_samples_leaf": [5, 10, 20, 30],
}
# Tuning search folds: intentionally coarser than the N_FOLDS=5 final
# evaluation below — full nested cross-validation (re-tuning inside every
# outer fold) would be the gold standard but multiplies runtime well beyond
# what's worth spending here. Still grouped by archetype, same as everywhere
# else, so tuning never picks hyperparameters that just memorize an
# archetype it'll then be "evaluated" on.
TUNING_CV_FOLDS = 3
TUNING_ITER = 15
# permutation importance of the shipped model, on a row sample
IMPORTANCE_SAMPLE = 5000
IMPORTANCE_REPEATS = 5

_spearman_scorer = make_scorer(lambda y_true, y_pred: spearmanr(y_true, y_pred).statistic)


def tune(estimator, search_space: dict, X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> dict:
    """RandomizedSearchCV grouped by archetype, optimizing held-out Spearman
    correlation (the metric this script reports as its primary evidence)
    rather than R^2/MAE. Returns the best_params_ found."""
    search = RandomizedSearchCV(
        estimator,
        param_distributions=search_space,
        n_iter=TUNING_ITER,
        cv=GroupKFold(n_splits=TUNING_CV_FOLDS),
        scoring=_spearman_scorer,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    search.fit(X, y, groups=groups)
    return search.best_params_


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

_FINDING_GROUP_PRIORS = {
    "hypertension": _HYPERTENSION_GROUP_PRIOR,
    "diabetes": _DIABETES_GROUP_PRIOR,
}

# finding key -> a RiskFlag label that src.clinical.deficiency.findings_from_flags
# recognizes (see its _LABEL_FINDINGS substring map).
_FINDING_LABELS = {
    "anemia": "moderate_anemia",
    "hypertension": "hypertension_stage1",
    "diabetes": "prediabetes",
}
_HEME_GROUPS = ("meat", "fish", "egg")


@dataclass(frozen=True)
class Archetype:
    archetype_id: str
    findings: tuple
    targets: dict
    limits: dict
    emphasize: tuple


def _flags_for_findings(findings: tuple) -> list[RiskFlag]:
    return [
        RiskFlag(biomarker="synthetic", value=0.0, unit="", label=_FINDING_LABELS[f], risk="moderate")
        for f in findings
    ]


def build_archetypes() -> list[Archetype]:
    """Every RDI group x every combination of the three modeled findings —
    grounded in the app's own nutrient_targets(), not invented numbers."""
    demographic_groups = [("male", False), ("female", False), ("female", True)]
    finding_pool = ("anemia", "hypertension", "diabetes")
    finding_combos = [
        combo for r in range(len(finding_pool) + 1) for combo in combinations(finding_pool, r)
    ]

    archetypes = []
    for sex, pregnant in demographic_groups:
        for combo in finding_combos:
            nutrition = nutrient_targets(sex, pregnant, _flags_for_findings(combo))
            archetype_id = f"{nutrition['group']}|{'+'.join(combo) or 'none'}"
            archetypes.append(Archetype(
                archetype_id=archetype_id, findings=combo,
                targets=nutrition["targets"], limits=nutrition["limits"],
                emphasize=tuple(nutrition["emphasize"]),
            ))
    return archetypes


def _jitter_targets(targets: dict, rng: np.random.Generator) -> dict:
    return {k: v * (1.0 + rng.uniform(-TARGET_JITTER_PCT, TARGET_JITTER_PCT))
            for k, v in targets.items()}


def _emphasize_variants(emphasize: tuple, rng: np.random.Generator) -> list[list[str]]:
    """The full emphasize list, plus a few random non-empty subsets — meal_plan
    ._pick calls the scorer with a shrinking emphasize list as nutrients
    saturate mid-plan, so training only on the full list would leave that a
    genuinely unseen input pattern at inference."""
    variants = [list(emphasize)]
    if len(emphasize) > 1:
        for _ in range(EMPHASIZE_SUBSET_VARIANTS):
            k = int(rng.integers(1, len(emphasize)))
            variants.append(list(rng.choice(emphasize, size=k, replace=False)))
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
                       emphasize: list[str], targets: dict, limits: dict,
                       rng: np.random.Generator) -> float:
    label = _capped_emphasis(nutrients, emphasize, targets) if emphasize else _density_score(nutrients)
    label += _group_prior(food_group, findings)
    if "brewed_beverage" in tags:
        label += CONCENTRATE_PENALTY
    if "anemia" in findings and food_group in _HEME_GROUPS:
        label += _heme_bonus(nutrients, targets)
    label -= _sodium_penalty(nutrients, limits)
    label += rng.normal(0.0, LABEL_NOISE_STD)
    return label


def compute_recipe_label(nutrients: dict, group_shares: dict, frequency_score: int | None,
                         findings: tuple, emphasize: list[str], targets: dict, limits: dict,
                         rng: np.random.Generator) -> float:
    """The food label, per serving, for a mixed dish — no new coefficients:
    - the food-group prior is the weight-weighted mean of the ingredients'
      priors (a leafy-green stir-fry inherits the vegetable prior, a payesh
      the dairy/grain/sweet mix);
    - the heme bonus is scaled by the dish's meat/fish/egg share;
    - household familiarity scales a positive fit by
      frequency_multiplier(score) (1.0 for a daily staple down to 0.25 for a
      once-a-year dish), exactly as the deterministic recipe score does. A
      negative fit (an unsuitable dish) is left as is: being common does not
      make an unsuitable dish better, nor being rare make it less bad.
    """
    fit = _capped_emphasis(nutrients, emphasize, targets) if emphasize else _density_score(nutrients)
    fit += sum(share * _group_prior(group, findings) for group, share in group_shares.items())
    if "anemia" in findings:
        heme_share = sum(group_shares.get(g, 0.0) for g in _HEME_GROUPS)
        fit += heme_share * _heme_bonus(nutrients, targets)
    fit -= _sodium_penalty(nutrients, limits)
    label = fit * frequency_multiplier(frequency_score) if fit > 0 else fit
    label += rng.normal(0.0, LABEL_NOISE_STD)
    return label


def _food_example(food, archetype: Archetype, emphasize: list[str], targets: dict,
                  rng: np.random.Generator) -> tuple[np.ndarray, float, float]:
    nutrients = food.nutrients
    emphasis = _emphasis_score(nutrients, emphasize, targets) if emphasize else 0.0
    density = _density_score(nutrients)
    baseline = emphasis if emphasize else density
    label = compute_food_label(nutrients, food.food_group, food.tags, archetype.findings,
                               emphasize, targets, archetype.limits, rng)
    vector = recommender.featurize(nutrients, food.food_group, food.tags, emphasize,
                                   targets, emphasis, density)
    return vector, label, baseline


def _recipe_example(recipe, archetype: Archetype, emphasize: list[str], targets: dict,
                    rng: np.random.Generator) -> tuple[np.ndarray, float, float]:
    nutrients = recipe.per_serving
    emphasis = _emphasis_score(nutrients, emphasize, targets) if emphasize else 0.0
    density = _density_score(nutrients)
    baseline = recipe_baseline_score(nutrients, recipe.weekly_frequency_score, emphasize, targets)
    label = compute_recipe_label(nutrients, recipe.group_shares, recipe.weekly_frequency_score,
                                 archetype.findings, emphasize, targets, archetype.limits, rng)
    vector = recommender.featurize_recipe(
        nutrients, recipe.group_shares, recipe.tags, recipe.weekly_frequency_score,
        emphasize, targets, emphasis, density,
    )
    return vector, label, baseline


@dataclass(frozen=True)
class Section:
    kind: str
    model_path: Path
    feature_version: int
    feature_names: tuple
    load_items: object  # () -> list of Food / Recipe
    example: object     # (item, archetype, emphasize, targets, rng) -> (x, y, baseline)


SECTIONS = {
    "food": Section(
        kind="food", model_path=recommender.MODEL_PATH,
        feature_version=recommender.FEATURE_VERSION,
        feature_names=recommender.FEATURE_NAMES,
        load_items=load_foods, example=_food_example,
    ),
    "recipe": Section(
        kind="recipe", model_path=recommender.RECIPE_MODEL_PATH,
        feature_version=recommender.RECIPE_FEATURE_VERSION,
        feature_names=recommender.RECIPE_FEATURE_NAMES,
        load_items=lambda: load_recipes(food_index(load_foods())),
        example=_recipe_example,
    ),
}


def build_training_frame(section: Section, rng: np.random.Generator):
    """Returns (X, y, groups, baseline, n_items) — baseline is the
    deterministic formula's own score per row (what src.diet.matcher ranks
    with when no model is present), kept as an explicit parallel array
    rather than decoded back out of the feature matrix at eval time."""
    items = section.load_items()
    if not items:
        raise SystemExit(f"no {section.kind} items to train on — run scripts/convert_datasets.py first")

    features, labels, groups, baselines = [], [], [], []
    for archetype in build_archetypes():
        for noise_i in range(NOISE_REPEATS):
            targets = dict(archetype.targets) if noise_i == 0 else _jitter_targets(archetype.targets, rng)
            for emphasize in _emphasize_variants(archetype.emphasize, rng):
                for item in items:
                    vector, label, baseline = section.example(item, archetype, emphasize, targets, rng)
                    features.append(vector)
                    labels.append(label)
                    groups.append(archetype.archetype_id)
                    baselines.append(baseline)

    return (
        np.vstack(features),
        np.asarray(labels, dtype=np.float64),
        np.asarray(groups),
        np.asarray(baselines, dtype=np.float64),
        len(items),
    )


def _fold_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "spearman": float(spearmanr(y_true, y_pred).statistic),
    }


def evaluate(X: np.ndarray, y: np.ndarray, groups: np.ndarray, baseline: np.ndarray,
             rf_params: dict, histgb_params: dict) -> dict:
    """GroupKFold split BY ARCHETYPE, not by item: real deployment always
    scores against the same fixed catalog but always sees novel patient
    target/emphasize combinations, so generalization must be measured across
    unseen archetypes, not unseen items."""
    n_splits = min(N_FOLDS, len(np.unique(groups)))
    gkf = GroupKFold(n_splits=n_splits)
    per_fold = {"hand_tuned_baseline": [], "linear_regression": [],
                "gradient_boosting": [], "random_forest": [], "hist_gradient_boosting": []}

    for train_idx, test_idx in gkf.split(X, y, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        per_fold["hand_tuned_baseline"].append(_fold_metrics(y_test, baseline[test_idx]))

        linear = LinearRegression().fit(X_train, y_train)
        per_fold["linear_regression"].append(_fold_metrics(y_test, linear.predict(X_test)))

        boosted = GradientBoostingRegressor(**GRADIENT_BOOSTING_PARAMS).fit(X_train, y_train)
        per_fold["gradient_boosting"].append(_fold_metrics(y_test, boosted.predict(X_test)))

        forest = RandomForestRegressor(**rf_params).fit(X_train, y_train)
        per_fold["random_forest"].append(_fold_metrics(y_test, forest.predict(X_test)))

        histgb = HistGradientBoostingRegressor(**histgb_params).fit(X_train, y_train)
        per_fold["hist_gradient_boosting"].append(_fold_metrics(y_test, histgb.predict(X_test)))

    summary = {}
    for name, folds in per_fold.items():
        summary[name] = {
            metric: {
                "mean": float(np.mean([f[metric] for f in folds])),
                "std": float(np.std([f[metric] for f in folds])),
            }
            for metric in ("r2", "mae", "spearman")
        }
    return summary


def _feature_importance(model, X: np.ndarray, y: np.ndarray, names: tuple) -> list[dict]:
    """Permutation importance (drop in Spearman correlation when a feature is
    shuffled) — model-agnostic, so it works for whichever estimator wins
    (HistGradientBoosting has no feature_importances_)."""
    rng = np.random.default_rng(RANDOM_STATE)
    idx = rng.choice(len(X), size=min(IMPORTANCE_SAMPLE, len(X)), replace=False)
    result = permutation_importance(
        model, X[idx], y[idx], scoring=_spearman_scorer,
        n_repeats=IMPORTANCE_REPEATS, random_state=RANDOM_STATE, n_jobs=-1,
    )
    ranked = sorted(
        zip(names, result.importances_mean, result.importances_std),
        key=lambda t: -t[1],
    )
    return [{"feature": n, "mean": float(m), "std": float(s)} for n, m, s in ranked]


def _write_comparison_csv(path: Path, summary: dict) -> None:
    rows = sorted(
        ({"model": name,
          "spearman_mean": m["spearman"]["mean"], "spearman_std": m["spearman"]["std"],
          "r2_mean": m["r2"]["mean"], "mae_mean": m["mae"]["mean"]}
         for name, m in summary.items()),
        key=lambda r: -r["spearman_mean"],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def train(section: Section, rng: np.random.Generator) -> dict:
    print(f"\n=== {section.kind} model ===")
    print("building synthetic training frame from the dataset + cited reference targets...")
    X, y, groups, baseline, n_items = build_training_frame(section, rng)
    print(f"{n_items} {section.kind}s -> {X.shape[0]} rows, {X.shape[1]} features, "
          f"{len(np.unique(groups))} archetypes")

    print(f"tuning RandomForest ({TUNING_ITER} candidates x {TUNING_CV_FOLDS}-fold GroupKFold)...")
    rf_params = tune(
        RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1),
        RANDOM_FOREST_SEARCH_SPACE, X, y, groups,
    )
    rf_params = {**rf_params, "random_state": RANDOM_STATE, "n_jobs": -1}
    print(f"  best params: {rf_params}")

    print(f"tuning HistGradientBoosting ({TUNING_ITER} candidates x {TUNING_CV_FOLDS}-fold GroupKFold)...")
    histgb_params = tune(
        HistGradientBoostingRegressor(random_state=RANDOM_STATE),
        HIST_GRADIENT_BOOSTING_SEARCH_SPACE, X, y, groups,
    )
    histgb_params = {**histgb_params, "random_state": RANDOM_STATE}
    print(f"  best params: {histgb_params}")

    print(f"evaluating via {N_FOLDS}-fold GroupKFold (held out by archetype)...")
    summary = evaluate(X, y, groups, baseline, rf_params, histgb_params)

    print("\nmodel                     spearman(mean)  r2(mean)   mae(mean)")
    for name, metrics in summary.items():
        print(f"{name:24s}  {metrics['spearman']['mean']:+.3f}         "
              f"{metrics['r2']['mean']:+.3f}     {metrics['mae']['mean']:.3f}")

    # GradientBoostingRegressor is untuned on purpose (a reference point, not
    # a shipping candidate) — only the two tuned models compete to be shipped.
    tuned_names = ("random_forest", "hist_gradient_boosting")
    winner_name = max(tuned_names, key=lambda n: summary[n]["spearman"]["mean"])
    print(f"\nwinner: {winner_name} (higher held-out Spearman correlation)")

    if winner_name == "random_forest":
        winner = RandomForestRegressor(**rf_params)
    else:
        winner = HistGradientBoostingRegressor(**histgb_params)
    winner.fit(X, y)  # refit on everything for the shipped artifact

    print("permutation feature importance of the shipped model...")
    importance = _feature_importance(winner, X, y, section.feature_names)

    # n_jobs=-1 speeds up training/CV, but src.diet.matcher calls
    # model.predict() one row at a time (see recommender.ml_score) — parallel
    # dispatch on a single-row predict is pure thread-pool overhead with no
    # benefit, and floods the log with joblib/sklearn warnings on every item
    # scored. Serve serially; train in parallel.
    if hasattr(winner, "n_jobs"):
        winner.n_jobs = None

    section.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": winner, "kind": section.kind, "feature_version": section.feature_version,
         "sklearn_version": sklearn.__version__},
        section.model_path,
    )
    print(f"saved model -> {section.model_path.relative_to(PROJECT_ROOT)}")

    metrics_path = section.model_path.with_name(f"{section.kind}_recommender_metrics.json")
    metrics = {
        "kind": section.kind, "winner": winner_name, "n_items": n_items,
        "n_rows": int(X.shape[0]), "n_features": int(X.shape[1]),
        "n_archetypes": int(len(np.unique(groups))),
        "n_folds": min(N_FOLDS, len(np.unique(groups))),
        "tuned_params": {"random_forest": rf_params, "hist_gradient_boosting": histgb_params},
        "metrics": summary,
        "feature_importance": importance,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"saved metrics -> {metrics_path.relative_to(PROJECT_ROOT)}")

    csv_path = RESULTS_DIR / f"{section.kind}_recommender_comparison.csv"
    _write_comparison_csv(csv_path, summary)
    print(f"saved comparison table -> {csv_path.relative_to(PROJECT_ROOT)}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=sorted(SECTIONS), help="train just one model")
    args = parser.parse_args()
    kinds = [args.only] if args.only else ["food", "recipe"]
    for kind in kinds:
        # a fresh generator per model, so training one never shifts the other's data
        train(SECTIONS[kind], np.random.default_rng(RANDOM_STATE))


if __name__ == "__main__":
    main()
