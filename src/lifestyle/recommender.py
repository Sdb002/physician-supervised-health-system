"""Trained exercise scorer — the optional ML backend of the prescription's
ranking (src.lifestyle.fitt_vp), the counterpart of src.diet.recommender's
food and recipe models.

The model scores one exercise for one patient (src.lifestyle.ranking's
ExerciseContext: age, sex, the rated conditions, fitness level, starting
intensity, obesity). It only ever sees exercises the safety gate allowed and
the prescription may pick (ranking.plannable), and it only orders them: what
is excluded stays excluded whatever it would score. With no model file, or
one built for another feature version or scikit-learn build,
load_model() returns None and the prescription ranks with
ranking.baseline_score.

Does not import src.llm. The artifact is produced by
scripts/train_recommenders.py (--only exercise) and is not committed
(data/models/ is gitignored).
"""

import numpy as np

from src.core.config import DATA_DIR
from src.diet.recommender import load_artifact
from src.lifestyle.exercise_db import FITNESS_LEVELS, PLAN_GROUPS, RATED_CONDITIONS, TRAITS, Exercise
from src.lifestyle.ranking import ExerciseContext, baseline_score, needs_modification

MODEL_PATH = DATA_DIR / "models" / "exercise_recommender.joblib"

# Bump whenever featurize()'s output shape or meaning changes: an artifact
# trained under another version is rejected at load.
FEATURE_VERSION = 1

TRAIT_FEATURES = tuple(sorted(TRAITS))
VIDEO_MATCHES = ("exact", "close variant")

FEATURE_NAMES = tuple(
    # the patient
    ["age_scaled", "older_adult", "female"]
    + [f"condition_{c}" for c in RATED_CONDITIONS]
    + ["fitness_rank", "start_light", "obese"]
    # the exercise
    + [f"category_{g}" for g in PLAN_GROUPS]
    + ["exercise_level_rank", "levels_below_patient"]
    + [f"rated_modify_{c}" for c in RATED_CONDITIONS]
    + ["older_adult_modify"]
    + ["needs_equipment", "household_item", "has_dose"]
    + [f"video_{m.replace(' ', '_')}" for m in VIDEO_MATCHES]
    + [f"trait_{t}" for t in TRAIT_FEATURES]
    + ["met_scaled", "has_met"]
    # the two together
    + [f"needs_modification_{c}" for c in RATED_CONDITIONS]
    + ["needs_modification_older_adult", "baseline_score"]
)
FEATURE_DIM = len(FEATURE_NAMES)

_MODEL_CACHE = None
_MODEL_CACHE_LOADED = False


def featurize(exercise: Exercise, ctx: ExerciseContext) -> np.ndarray:
    """Fixed-width feature vector for one (patient, exercise) pair, shared
    verbatim by training and the app, so a feature means one thing."""
    flagged = set(needs_modification(exercise, ctx))
    traits = set(exercise.traits)
    values = [
        ctx.age / 100.0, float(ctx.older), float(ctx.sex == "female"),
        *(float(c in ctx.conditions) for c in RATED_CONDITIONS),
        float(FITNESS_LEVELS.index(ctx.fitness_level)),
        float(ctx.start_level == "light"), float(ctx.obese),
        *(float(exercise.category == g) for g in PLAN_GROUPS),
        float(exercise.level_rank), float(max(0, ctx.level_cap - exercise.level_rank)),
        *(float(c in exercise.modify_for) for c in RATED_CONDITIONS),
        float(exercise.older_adult == "modify"),
        float(exercise.needs_equipment), float(exercise.equipment.startswith("household item")),
        float(exercise.source_detail == "instructions and dose"),
        *(float(exercise.video_match == m) for m in VIDEO_MATCHES),
        *(float(t in traits) for t in TRAIT_FEATURES),
        (exercise.met_value or 0.0) / 10.0, float(exercise.met_value is not None),
        *(float(c in flagged) for c in RATED_CONDITIONS),
        float("older_adult" in flagged),
        baseline_score(exercise, ctx),
    ]
    return np.asarray(values, dtype=np.float64)


def load_model():
    """Cached exercise-model singleton (None when unavailable)."""
    global _MODEL_CACHE, _MODEL_CACHE_LOADED
    if _MODEL_CACHE_LOADED:
        return _MODEL_CACHE
    _MODEL_CACHE_LOADED = True
    _MODEL_CACHE = _load_model_uncached()
    return _MODEL_CACHE


def _load_model_uncached():
    return load_artifact(MODEL_PATH, "exercise", FEATURE_VERSION)


def active_backend() -> str:
    """"ml" when a trained exercise model is in effect, "linear" otherwise."""
    return "ml" if load_model() is not None else "linear"


def score(exercises: list[Exercise], ctx: ExerciseContext) -> list[float]:
    """One score per exercise, from the model in a single predict call when
    one is loaded and the prediction succeeds, else from the formula."""
    if not exercises:
        return []
    model = load_model()
    if model is not None:
        try:
            predicted = model.predict(np.vstack([featurize(e, ctx) for e in exercises]))
            return [float(p) for p in predicted]
        except Exception:
            pass
    return [baseline_score(e, ctx) for e in exercises]
