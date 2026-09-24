"""Trained food/recipe suitability scorer — optional ML backend for
src.diet.matcher's ranking.

Does not import src.llm (keeps tests/test_llm_isolation.py passing) and does
not touch the contraindication gate: this module only ever scores items the
caller already filtered through src.clinical.contraindication.filter_items,
same as the deterministic formula it augments. Degrades gracefully, same
philosophy as the LLM features elsewhere in this app: with no trained model
file present, load_model() returns None and every caller falls back to the
deterministic formula. Never raises out of load_model()/ml_score() —
featurize() is the one function that will (it's a programming-error
surface, not a runtime-degradation one).

The trained artifact is produced by scripts/train_food_recommender.py and is
NOT committed (data/models/ is gitignored) — same treatment as .venv or
node_modules: a regenerable build artifact, not a reference file.
"""

import numpy as np
import sklearn

from src.core.config import DATA_DIR
from src.diet.food_db import NUTRIENT_COLUMNS, FOOD_GROUPS

MODEL_PATH = DATA_DIR / "models" / "food_recommender.joblib"

# Bump whenever featurize()'s output shape or meaning changes. load_model()
# rejects any artifact trained under a different version rather than letting
# a stale model unpickle fine and then crash model.predict() at request time.
FEATURE_VERSION = 1

# Tags that affect scoring even when they don't trigger a hard exclusion for
# this particular patient (e.g. a high_sodium food is fine for someone
# without hypertension, but still worth a mild penalty). Kept local rather
# than imported from src.diet.recipe.EXCLUSION_TAGS to avoid coupling this
# module's feature schema to that module's internal set.
EXCLUSION_TAG_FEATURES = ("high_sodium", "high_sugar", "high_fat")

_FOOD_GROUP_INDEX = {group: i for i, group in enumerate(FOOD_GROUPS)}
_NONE_GROUP_INDEX = len(FOOD_GROUPS)  # recipes have no food_group
FOOD_GROUP_DIM = len(FOOD_GROUPS) + 1

FEATURE_DIM = (
    len(NUTRIENT_COLUMNS) * 2  # value/target ratio + is_emphasized, per nutrient
    + 2  # baseline _emphasis_score, _density_score (model sees the baseline it's refining)
    + FOOD_GROUP_DIM  # one-hot, plus "none" for recipes
    + len(EXCLUSION_TAG_FEATURES)
    + 1  # raw kcal, scaled
)

# Human-readable label per featurize() output column, in the same order —
# used for feature-importance reporting (notebooks/04_recommender_training.ipynb),
# not consumed by the model itself.
FEATURE_NAMES = []
for _col in NUTRIENT_COLUMNS:
    FEATURE_NAMES.append(f"{_col}_ratio")
    FEATURE_NAMES.append(f"{_col}_emphasized")
FEATURE_NAMES.append("baseline_emphasis_score")
FEATURE_NAMES.append("baseline_density_score")
FEATURE_NAMES.extend(f"group_{g}" for g in FOOD_GROUPS)
FEATURE_NAMES.append("group_none")
FEATURE_NAMES.extend(f"tag_{t}" for t in EXCLUSION_TAG_FEATURES)
FEATURE_NAMES.append("kcal_scaled")
FEATURE_NAMES = tuple(FEATURE_NAMES)
assert len(FEATURE_NAMES) == FEATURE_DIM

_MODEL_CACHE = None
_MODEL_CACHE_LOADED = False


def featurize(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
              targets: dict, emphasis_score: float, density_score: float) -> np.ndarray:
    """Fixed-width feature vector for one (patient-context, item) pair.

    Shared verbatim between training (scripts/train_food_recommender.py) and
    inference (ml_score/ml_score_batch below) so there is exactly one
    definition of what a feature means — no train/serve skew.
    """
    emphasize_set = set(emphasize)
    tag_set = set(tags)

    values: list[float] = []
    for col in NUTRIENT_COLUMNS:
        target = targets.get(col)
        values.append((nutrients.get(col, 0.0) / target) if target else 0.0)
        values.append(1.0 if col in emphasize_set else 0.0)

    values.append(emphasis_score)
    values.append(density_score)

    group_onehot = [0.0] * FOOD_GROUP_DIM
    group_onehot[_FOOD_GROUP_INDEX.get(food_group, _NONE_GROUP_INDEX)] = 1.0
    values.extend(group_onehot)

    values.extend(1.0 if tag in tag_set else 0.0 for tag in EXCLUSION_TAG_FEATURES)

    values.append(nutrients.get("kcal", 0.0) / 100.0)

    return np.asarray(values, dtype=np.float64)


def load_model():
    """Cached singleton. Returns None (never raises) if there is no model
    file, it fails to unpickle, or it was trained under a different feature
    schema / sklearn version than the one currently running."""
    global _MODEL_CACHE, _MODEL_CACHE_LOADED
    if _MODEL_CACHE_LOADED:
        return _MODEL_CACHE
    _MODEL_CACHE_LOADED = True
    _MODEL_CACHE = _load_model_uncached()
    return _MODEL_CACHE


def _load_model_uncached():
    if not MODEL_PATH.exists():
        return None
    try:
        import joblib
        payload = joblib.load(MODEL_PATH)
    except Exception:
        return None
    if not isinstance(payload, dict) or "model" not in payload:
        return None
    if payload.get("feature_version") != FEATURE_VERSION:
        return None
    if payload.get("sklearn_version") != sklearn.__version__:
        return None
    return payload["model"]


def _reset_cache_for_tests():
    """Test-only hook: forces the next load_model() call to re-read the
    file instead of returning the cached singleton."""
    global _MODEL_CACHE, _MODEL_CACHE_LOADED
    _MODEL_CACHE = None
    _MODEL_CACHE_LOADED = False


def ml_score(nutrients: dict, food_group: str | None, tags, emphasize: list[str],
            targets: dict, emphasis_score: float, density_score: float) -> float | None:
    """None if no model is loaded or prediction fails for any reason —
    callers treat None as "fall back to the deterministic formula", never
    as an error."""
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


def ml_score_batch(feature_matrix: np.ndarray) -> np.ndarray | None:
    """Vectorized scoring for many rows at once — used by the training
    script's evaluation code, where N is large enough for batching to
    matter. matcher.py's ranking functions use ml_score() per item instead:
    at this app's scale (<=250 foods) batching saves negligible time and a
    per-item call keeps the same code path for rank_foods/rank_recipes and
    meal_plan's greedy slot-by-slot picker, with no risk of a batch/list
    ordering bug silently mis-ranking items."""
    model = load_model()
    if model is None or feature_matrix.size == 0:
        return None
    try:
        return model.predict(feature_matrix)
    except Exception:
        return None
