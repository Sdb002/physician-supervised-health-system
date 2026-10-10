"""Trained suitability scorers — optional ML backends for src.diet.matcher.

Two independent models, one per section of the diet recommendation:
- the FOOD model ranks single foods (per 100 g; food group known);
- the RECIPE model ranks household recipes (per serving; described by the
  food-group make-up of their ingredients and the recipe dataset's 1-10
  household frequency score, 10 = the most commonly cooked dish).

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
FEATURE_VERSION = 2
RECIPE_FEATURE_VERSION = 1

# Tags that affect scoring even when they don't trigger a hard exclusion for
# this particular patient (e.g. a high_sodium food is fine for someone
# without hypertension, but still worth a mild penalty). Kept local rather
# than imported from src.diet.recipe.EXCLUSION_TAGS to avoid coupling this
# module's feature schema to that module's internal set.
EXCLUSION_TAG_FEATURES = ("high_sodium", "high_sugar", "high_fat")
FOOD_TAG_FEATURES = EXCLUSION_TAG_FEATURES + ("brewed_beverage",)
RECIPE_TAG_FEATURES = EXCLUSION_TAG_FEATURES

_FOOD_GROUP_INDEX = {group: i for i, group in enumerate(FOOD_GROUPS)}
_NONE_GROUP_INDEX = len(FOOD_GROUPS)  # unknown / missing food_group
FOOD_GROUP_DIM = len(FOOD_GROUPS) + 1

FEATURE_DIM = (
    len(NUTRIENT_COLUMNS) * 2  # value/target ratio + is_emphasized, per nutrient
    + 2  # baseline _emphasis_score, _density_score (model sees the baseline it's refining)
    + FOOD_GROUP_DIM  # one-hot, plus "none"
    + len(FOOD_TAG_FEATURES)
    + 1  # raw kcal, scaled
)
RECIPE_FEATURE_DIM = (
    len(NUTRIENT_COLUMNS) * 2
    + 2
    + len(FOOD_GROUPS)  # share of the recipe's ingredient weight per food group
    + len(RECIPE_TAG_FEATURES)
    + 1  # kcal per serving, scaled
    + 1  # household frequency score / 10
)


def _nutrient_feature_names() -> list[str]:
    names = []
    for col in NUTRIENT_COLUMNS:
        names.append(f"{col}_ratio")
        names.append(f"{col}_emphasized")
    return names + ["baseline_emphasis_score", "baseline_density_score"]


# Human-readable label per featurize() output column, in the same order —
# used for feature-importance reporting (notebooks/04_recommender_training.ipynb),
# not consumed by the models themselves.
FEATURE_NAMES = tuple(
    _nutrient_feature_names()
    + [f"group_{g}" for g in FOOD_GROUPS] + ["group_none"]
    + [f"tag_{t}" for t in FOOD_TAG_FEATURES]
    + ["kcal_scaled"]
)
RECIPE_FEATURE_NAMES = tuple(
    _nutrient_feature_names()
    + [f"share_{g}" for g in FOOD_GROUPS]
    + [f"tag_{t}" for t in RECIPE_TAG_FEATURES]
    + ["kcal_per_serving_scaled", "household_frequency"]
)
assert len(FEATURE_NAMES) == FEATURE_DIM
assert len(RECIPE_FEATURE_NAMES) == RECIPE_FEATURE_DIM

_MODEL_CACHE = None
_MODEL_CACHE_LOADED = False
_RECIPE_MODEL_CACHE = None
_RECIPE_MODEL_CACHE_LOADED = False


def _nutrient_features(nutrients: dict, emphasize: list[str], targets: dict,
                       emphasis_score: float, density_score: float) -> list[float]:
    emphasize_set = set(emphasize)
    values: list[float] = []
    for col in NUTRIENT_COLUMNS:
        target = targets.get(col)
        values.append((nutrients.get(col, 0.0) / target) if target else 0.0)
        values.append(1.0 if col in emphasize_set else 0.0)
    values.append(emphasis_score)
    values.append(density_score)
    return values


def featurize(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
              targets: dict, emphasis_score: float, density_score: float) -> np.ndarray:
    """Fixed-width feature vector for one (patient-context, food) pair.

    Shared verbatim between training (scripts/train_recommenders.py) and
    inference (ml_score/ml_score_batch below) so there is exactly one
    definition of what a feature means — no train/serve skew.
    """
    tag_set = set(tags)
    values = _nutrient_features(nutrients, emphasize, targets, emphasis_score, density_score)

    group_onehot = [0.0] * FOOD_GROUP_DIM
    group_onehot[_FOOD_GROUP_INDEX.get(food_group, _NONE_GROUP_INDEX)] = 1.0
    values.extend(group_onehot)

    values.extend(1.0 if tag in tag_set else 0.0 for tag in FOOD_TAG_FEATURES)
    values.append(nutrients.get("kcal", 0.0) / 100.0)
    return np.asarray(values, dtype=np.float64)


def featurize_recipe(nutrients: dict, group_shares: dict, tags, frequency_score: int | None,
                     emphasize: list[str], targets: dict, emphasis_score: float,
                     density_score: float) -> np.ndarray:
    """Fixed-width feature vector for one (patient-context, recipe) pair.

    A recipe with no frequency score is encoded as 10/10 — the same "no
    familiarity adjustment" that src.diet.matcher.frequency_multiplier
    applies to it in the deterministic fallback.
    """
    tag_set = set(tags)
    values = _nutrient_features(nutrients, emphasize, targets, emphasis_score, density_score)
    values.extend(float(group_shares.get(g, 0.0)) for g in FOOD_GROUPS)
    values.extend(1.0 if tag in tag_set else 0.0 for tag in RECIPE_TAG_FEATURES)
    values.append(nutrients.get("kcal", 0.0) / 100.0)
    values.append((frequency_score if frequency_score is not None else 10) / 10.0)
    return np.asarray(values, dtype=np.float64)


def _load_artifact(path, kind: str, feature_version: int):
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
    return _load_artifact(MODEL_PATH, "food", FEATURE_VERSION)


def load_recipe_model():
    """Cached recipe-model singleton (None when unavailable)."""
    global _RECIPE_MODEL_CACHE, _RECIPE_MODEL_CACHE_LOADED
    if _RECIPE_MODEL_CACHE_LOADED:
        return _RECIPE_MODEL_CACHE
    _RECIPE_MODEL_CACHE_LOADED = True
    _RECIPE_MODEL_CACHE = _load_recipe_model_uncached()
    return _RECIPE_MODEL_CACHE


def _load_recipe_model_uncached():
    return _load_artifact(RECIPE_MODEL_PATH, "recipe", RECIPE_FEATURE_VERSION)


def ml_score(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
            targets: dict, emphasis_score: float, density_score: float) -> float | None:
    """Food score, or None if no model is loaded or prediction fails for
    any reason — callers treat None as "fall back to the deterministic
    formula", never as an error."""
    model = load_model()
    if model is None:
        return None
    try:
        features = featurize(
            nutrients, food_group, tags, emphasize, targets, emphasis_score, density_score
        )
        return float(model.predict(features.reshape(1, -1))[0])
    except Exception:
        return None


def recipe_ml_score(nutrients: dict, group_shares: dict, tags, frequency_score: int | None,
                    emphasize: list[str], targets: dict, emphasis_score: float,
                    density_score: float) -> float | None:
    """Recipe score, or None (fall back) — same contract as ml_score()."""
    model = load_recipe_model()
    if model is None:
        return None
    try:
        features = featurize_recipe(
            nutrients, group_shares, tags, frequency_score, emphasize, targets,
            emphasis_score, density_score,
        )
        return float(model.predict(features.reshape(1, -1))[0])
    except Exception:
        return None


def ml_score_batch(feature_matrix: np.ndarray, kind: str = "food") -> np.ndarray | None:
    """Vectorized scoring for many rows at once — used by the training
    script's evaluation code, where N is large enough for batching to
    matter. matcher.py's ranking functions score per item instead: at this
    app's scale (<=700 foods, 250 recipes) batching saves negligible time
    and a per-item call keeps the same code path for rank_foods/rank_recipes
    and meal_plan's greedy slot-by-slot picker, with no risk of a batch/list
    ordering bug silently mis-ranking items."""
    model = load_recipe_model() if kind == "recipe" else load_model()
    if model is None or feature_matrix.size == 0:
        return None
    try:
        return model.predict(feature_matrix)
    except Exception:
        return None
