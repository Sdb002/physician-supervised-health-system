"""Trained suitability scorers — optional ML backends for src.diet.matcher.

Two independent models, one per section of the diet recommendation:
- the FOOD model ranks single foods (per 100 g; food group known);
- the RECIPE model ranks household recipes (per serving; described by the
  food-group make-up of their ingredients).

Both score nutritional fit only. How habitually a food or dish is eaten is
not something to learn: src.diet.matcher weights either model's fit by
household familiarity exactly as it weights the deterministic formula's
(matcher.familiar_score), so the two backends cannot disagree about it.

Each sees the item and the patient it is being scored for: the nutrient
targets, which nutrients are emphasized, which findings the patient has
(FINDING_FEATURES) and the sodium limit. The findings are features in their
own right, not something to be guessed from the emphasis: the meal planner
drops a nutrient from the emphasis once the day has enough of it, and a
recorded condition can rule one out (potassium in kidney disease), so the
same patient is scored under many emphasis lists.

Does not import src.llm (keeps tests/test_llm_isolation.py passing) and does
not touch the contraindication gate: this module only ever scores items the
caller already filtered through src.clinical.contraindication.filter_items,
same as the deterministic formula it augments. Degrades gracefully, same
philosophy as the LLM features elsewhere in this app: with no trained model
file present, load_model()/load_recipe_model() return None and every caller
falls back to the deterministic formula. Never raises out of the load/score
functions — featurize()/featurize_recipe() are the ones that will (they're a
programming-error surface, not a runtime-degradation one).

The trained artifacts are produced by scripts/train_recommenders.py and are
NOT committed (data/models/ is gitignored) — same treatment as .venv or
node_modules: regenerable build artifacts, not reference files.
"""

import numpy as np
import sklearn

from src.core.config import DATA_DIR
from src.diet.food_db import FOOD_GROUPS, NUTRIENT_COLUMNS

MODEL_PATH = DATA_DIR / "models" / "food_recommender.joblib"
RECIPE_MODEL_PATH = DATA_DIR / "models" / "recipe_recommender.joblib"

# Bump whenever a featurize function's output shape or meaning changes.
# Loading rejects any artifact trained under a different version rather than
# letting a stale model unpickle fine and then crash model.predict() at
# request time. v2: brewed_beverage tag feature (new food dataset).
# v3 (recipes v2): the patient's findings; sodium as a share of its limit;
# each nutrient's share again where it is emphasized; the recipe model no
# longer takes the household frequency score (see the module docstring).
# v4 (recipes v3): the high_cholesterol finding.
FEATURE_VERSION = 4
RECIPE_FEATURE_VERSION = 3

# Tags that affect scoring even when they don't trigger a hard exclusion for
# this particular patient (e.g. a high_sodium food is fine for someone
# without hypertension, but still worth a mild penalty). Kept local rather
# than imported from src.diet.recipe.EXCLUSION_TAGS to avoid coupling this
# module's feature schema to that module's internal set.
EXCLUSION_TAG_FEATURES = ("high_sodium", "high_sugar", "high_fat")
FOOD_TAG_FEATURES = EXCLUSION_TAG_FEATURES + ("brewed_beverage",)
RECIPE_TAG_FEATURES = EXCLUSION_TAG_FEATURES

# The findings a model is told about: the finding keys of
# src/clinical/rules/deficiency_map.yaml (tests/test_recommender.py checks the
# two stay in step, so a finding added there cannot go unseen here).
FINDING_FEATURES = ("anemia", "hypertension", "diabetes", "high_cholesterol")

_FOOD_GROUP_INDEX = {group: i for i, group in enumerate(FOOD_GROUPS)}
_NONE_GROUP_INDEX = len(FOOD_GROUPS)  # unknown / missing food_group
FOOD_GROUP_DIM = len(FOOD_GROUPS) + 1

FEATURE_DIM = (
    len(NUTRIENT_COLUMNS) * 3  # ratio, is_emphasized, ratio if emphasized, per nutrient
    + 3  # baseline _emphasis_score, _density_score (model sees the baseline it's refining), and which applies
    + FOOD_GROUP_DIM  # one-hot, plus "none"
    + len(FOOD_TAG_FEATURES)
    + 1  # raw kcal, scaled
    + len(FINDING_FEATURES)
)
RECIPE_FEATURE_DIM = (
    len(NUTRIENT_COLUMNS) * 3
    + 3
    + len(FOOD_GROUPS)  # share of the recipe's ingredient weight per food group
    + len(RECIPE_TAG_FEATURES)
    + 1  # kcal per serving, scaled
    + len(FINDING_FEATURES)
)


def _nutrient_feature_names() -> list[str]:
    names = []
    for col in NUTRIENT_COLUMNS:
        names.append(f"{col}_ratio")
        names.append(f"{col}_emphasized")
        names.append(f"{col}_emphasized_ratio")
    return names + ["baseline_emphasis_score", "baseline_density_score", "nothing_emphasized"]


# Human-readable label per featurize() output column, in the same order —
# used for feature-importance reporting (notebooks/04_recommender_training.ipynb),
# not consumed by the models themselves.
FEATURE_NAMES = tuple(
    _nutrient_feature_names()
    + [f"group_{g}" for g in FOOD_GROUPS] + ["group_none"]
    + [f"tag_{t}" for t in FOOD_TAG_FEATURES]
    + ["kcal_scaled"]
    + [f"finding_{f}" for f in FINDING_FEATURES]
)
RECIPE_FEATURE_NAMES = tuple(
    _nutrient_feature_names()
    + [f"share_{g}" for g in FOOD_GROUPS]
    + [f"tag_{t}" for t in RECIPE_TAG_FEATURES]
    + ["kcal_per_serving_scaled"]
    + [f"finding_{f}" for f in FINDING_FEATURES]
)
assert len(FEATURE_NAMES) == FEATURE_DIM
assert len(RECIPE_FEATURE_NAMES) == RECIPE_FEATURE_DIM

_MODEL_CACHE = None
_MODEL_CACHE_LOADED = False
_RECIPE_MODEL_CACHE = None
_RECIPE_MODEL_CACHE_LOADED = False


def _nutrient_features(nutrients: dict, emphasize: list[str], targets: dict, limits: dict,
                       emphasis_score: float, density_score: float) -> list[float]:
    """Each nutrient as a share of the day's reference amount: its target,
    or for a nutrient with a ceiling instead of a target (sodium) its limit.
    Carbohydrate and fat have neither, so their ratios stay 0. The share is
    given a second time for the nutrients the patient needs more of, and 0
    for the others, so "more of what is emphasized" is one feature a model
    can be held to (see monotonic_constraints in the training script)."""
    emphasize_set = set(emphasize)
    values: list[float] = []
    for col in NUTRIENT_COLUMNS:
        reference = targets.get(col) or limits.get(col)
        ratio = (nutrients.get(col, 0.0) / reference) if reference else 0.0
        emphasized = col in emphasize_set
        values.extend((ratio, 1.0 if emphasized else 0.0, ratio if emphasized else 0.0))
    values.append(emphasis_score)
    values.append(density_score)
    # which of the two formula scores applies: density, when nothing is emphasized
    values.append(0.0 if emphasize_set else 1.0)
    return values


def _finding_features(findings) -> list[float]:
    found = set(findings)
    return [1.0 if finding in found else 0.0 for finding in FINDING_FEATURES]


def featurize(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
              targets: dict, emphasis_score: float, density_score: float, *,
              findings=(), limits: dict | None = None) -> np.ndarray:
    """Fixed-width feature vector for one (patient-context, food) pair.

    Shared verbatim between training (scripts/train_recommenders.py) and
    inference (src.diet.matcher) so there is exactly one definition of what
    a feature means — no train/serve skew. `findings` are the patient's
    finding keys and `limits` the nutrient ceilings ({"sodium_mg": 2000}).
    """
    tag_set = set(tags)
    values = _nutrient_features(nutrients, emphasize, targets, limits or {},
                                emphasis_score, density_score)

    group_onehot = [0.0] * FOOD_GROUP_DIM
    group_onehot[_FOOD_GROUP_INDEX.get(food_group, _NONE_GROUP_INDEX)] = 1.0
    values.extend(group_onehot)

    values.extend(1.0 if tag in tag_set else 0.0 for tag in FOOD_TAG_FEATURES)
    values.append(nutrients.get("kcal", 0.0) / 100.0)
    values.extend(_finding_features(findings))
    return np.asarray(values, dtype=np.float64)


def featurize_recipe(nutrients: dict, group_shares: dict, tags, emphasize: list[str],
                     targets: dict, emphasis_score: float, density_score: float, *,
                     findings=(), limits: dict | None = None) -> np.ndarray:
    """Fixed-width feature vector for one (patient-context, recipe) pair:
    featurize() for a dish, with its nutrients per serving and the share of
    its weight each food group makes up in place of a single food group."""
    tag_set = set(tags)
    values = _nutrient_features(nutrients, emphasize, targets, limits or {},
                                emphasis_score, density_score)
    values.extend(float(group_shares.get(g, 0.0)) for g in FOOD_GROUPS)
    values.extend(1.0 if tag in tag_set else 0.0 for tag in RECIPE_TAG_FEATURES)
    values.append(nutrients.get("kcal", 0.0) / 100.0)
    values.extend(_finding_features(findings))
    return np.asarray(values, dtype=np.float64)


def load_artifact(path, kind: str, feature_version: int):
    """None (never raises) if there is no file, it fails to unpickle, or it
    was trained for another kind of item / feature schema / sklearn build."""
    if not path.exists():
        return None
    try:
        import joblib
        payload = joblib.load(path)
    except Exception:
        return None
    if not isinstance(payload, dict) or "model" not in payload:
        return None
    if payload.get("kind", "food") != kind:
        return None
    if payload.get("feature_version") != feature_version:
        return None
    if payload.get("sklearn_version") != sklearn.__version__:
        return None
    return payload["model"]


def load_model():
    """Cached food-model singleton (None when unavailable)."""
    global _MODEL_CACHE, _MODEL_CACHE_LOADED
    if _MODEL_CACHE_LOADED:
        return _MODEL_CACHE
    _MODEL_CACHE_LOADED = True
    _MODEL_CACHE = _load_model_uncached()
    return _MODEL_CACHE


def _load_model_uncached():
    return load_artifact(MODEL_PATH, "food", FEATURE_VERSION)


def load_recipe_model():
    """Cached recipe-model singleton (None when unavailable)."""
    global _RECIPE_MODEL_CACHE, _RECIPE_MODEL_CACHE_LOADED
    if _RECIPE_MODEL_CACHE_LOADED:
        return _RECIPE_MODEL_CACHE
    _RECIPE_MODEL_CACHE_LOADED = True
    _RECIPE_MODEL_CACHE = _load_recipe_model_uncached()
    return _RECIPE_MODEL_CACHE


def _load_recipe_model_uncached():
    return load_artifact(RECIPE_MODEL_PATH, "recipe", RECIPE_FEATURE_VERSION)


def ml_score_batch(feature_rows, kind: str = "food") -> np.ndarray | None:
    """One score per feature row, in the order given, from a single predict
    call — or None if no model is loaded, there is nothing to score, or
    prediction fails for any reason. Callers treat None as "fall back to the
    deterministic formula", never as an error.

    Everything is scored in batches: a predict call costs about a
    millisecond before it looks at a single row, and a week's plan scores
    several thousand (patient, dish) pairs, so one call per pair made a plan
    take seconds instead of a fraction of one."""
    model = load_recipe_model() if kind == "recipe" else load_model()
    if model is None or len(feature_rows) == 0:
        return None
    try:
        return np.asarray(model.predict(np.vstack(feature_rows)), dtype=np.float64)
    except Exception:
        return None
