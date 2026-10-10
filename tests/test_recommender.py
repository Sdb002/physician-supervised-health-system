"""ML scoring backend: graceful fallback, feature shape, and dispatch.

The autouse fixture in conftest.py pins the rest of the suite to
recommender.load_model() -> None; tests here override that per-test via
monkeypatch (last set wins) to exercise the ML-active path in isolation.
"""

import joblib
import numpy as np
import pytest
import sklearn

from src.diet import matcher, recommender
from src.diet.food_db import Food


def _food(food_id: str, group: str, kcal: float, **nutrients) -> Food:
    base = {c: 0.0 for c in (
        "kcal", "protein_g", "carb_g", "fat_g", "fiber_g", "iron_mg",
        "calcium_mg", "zinc_mg", "folate_ug", "vit_a_ug", "vit_c_mg",
        "sodium_mg", "potassium_mg",
    )}
    base["kcal"] = kcal
    base.update(nutrients)
    return Food(food_id=food_id, name_en=food_id, name_bn="", food_group=group,
                nutrients=base, tags=())


class _StubModel:
    """Not a real sklearn estimator — just something with .predict(X) that
    scores each row via a caller-supplied function of the feature vector, so
    tests can pin exactly what "the model" prefers without depending on a
    real fit's convergence. Only usable via monkeypatching load_model
    directly (holds a closure, so it can't be joblib-pickled to disk)."""

    def __init__(self, fn):
        self._fn = fn

    def predict(self, x):
        return np.array([self._fn(row) for row in x])


def _use_real_loader(monkeypatch, path):
    """The conftest.py autouse fixture replaces load_model wholesale with a
    stub that always returns None — so a test exercising MODEL_PATH/file
    content behavior must point load_model back at the real (uncached)
    implementation, or it would trivially pass no matter what's on disk."""
    monkeypatch.setattr(recommender, "MODEL_PATH", path)
    monkeypatch.setattr(recommender, "load_model", recommender._load_model_uncached)


@pytest.fixture()
def valid_model_file(tmp_path, monkeypatch):
    """A real joblib artifact with matching feature/sklearn versions, on a
    LinearRegression fit to trivially prefer higher iron_mg ratio."""
    from sklearn.linear_model import LinearRegression

    rng = np.random.default_rng(0)
    x = rng.random((30, recommender.FEATURE_DIM))
    y = x[:, 0]  # first feature dim is kcal_mg... doesn't matter which; just needs to fit
    model = LinearRegression().fit(x, y)

    path = tmp_path / "food_recommender.joblib"
    joblib.dump(
        {"model": model, "feature_version": recommender.FEATURE_VERSION,
         "sklearn_version": sklearn.__version__},
        path,
    )
    _use_real_loader(monkeypatch, path)
    yield path


def test_featurize_shape_dtype_and_determinism():
    nutrients = {"kcal": 300, "protein_g": 10, "iron_mg": 5, "sodium_mg": 50}
    targets = {"kcal": 2000, "protein_g": 50, "iron_mg": 8}
    v1 = recommender.featurize(nutrients, "grain", ("high_fiber",), ["iron_mg"], targets, 0.5, 1.2)
    v2 = recommender.featurize(nutrients, "grain", ("high_fiber",), ["iron_mg"], targets, 0.5, 1.2)
    assert v1.shape == (recommender.FEATURE_DIM,)
    assert v1.dtype == np.float64
    assert np.array_equal(v1, v2)


def test_featurize_distinguishes_food_group():
    nutrients = {"kcal": 300, "iron_mg": 5}
    targets = {"iron_mg": 8}
    grain = recommender.featurize(nutrients, "grain", (), [], targets, 0.0, 0.0)
    vegetable = recommender.featurize(nutrients, "vegetable", (), [], targets, 0.0, 0.0)
    none_group = recommender.featurize(nutrients, None, (), [], targets, 0.0, 0.0)
    assert not np.array_equal(grain, vegetable)
    assert not np.array_equal(grain, none_group)
    assert not np.array_equal(vegetable, none_group)


def test_featurize_exposes_brewed_beverage_tag():
    nutrients = {"kcal": 296, "potassium_mg": 6040}
    targets = {"potassium_mg": 3400}
    tea_powder = recommender.featurize(nutrients, "other", ("brewed_beverage",), [], targets, 0.0, 0.0)
    nuts = recommender.featurize(nutrients, "other", (), [], targets, 0.0, 0.0)
    index = recommender.FEATURE_NAMES.index("tag_brewed_beverage")
    assert tea_powder[index] == 1.0 and nuts[index] == 0.0


def test_featurize_recipe_shape_and_frequency():
    nutrients = {"kcal": 250, "iron_mg": 3}
    shares = {"vegetable": 0.8, "oil": 0.05, "spice": 0.15}
    common = recommender.featurize_recipe(nutrients, shares, (), 9, ["iron_mg"], {"iron_mg": 18}, 0.2, 1.0)
    rare = recommender.featurize_recipe(nutrients, shares, (), 2, ["iron_mg"], {"iron_mg": 18}, 0.2, 1.0)
    assert common.shape == (recommender.RECIPE_FEATURE_DIM,)
    index = recommender.RECIPE_FEATURE_NAMES.index("household_frequency")
    assert common[index] == pytest.approx(0.9) and rare[index] == pytest.approx(0.2)
    share_index = recommender.RECIPE_FEATURE_NAMES.index("share_vegetable")
    assert common[share_index] == pytest.approx(0.8)


def test_food_and_recipe_artifacts_are_not_interchangeable(tmp_path, monkeypatch):
    from sklearn.dummy import DummyRegressor

    food_path, recipe_path = tmp_path / "food.joblib", tmp_path / "recipe.joblib"
    joblib.dump({"model": DummyRegressor().fit([[0.0]], [0.0]), "kind": "food",
                 "feature_version": recommender.FEATURE_VERSION,
                 "sklearn_version": sklearn.__version__}, food_path)
    joblib.dump({"model": DummyRegressor().fit([[0.0]], [0.0]), "kind": "recipe",
                 "feature_version": recommender.RECIPE_FEATURE_VERSION,
                 "sklearn_version": sklearn.__version__}, recipe_path)
    # each file loads only as its own kind
    monkeypatch.setattr(recommender, "MODEL_PATH", recipe_path)
    monkeypatch.setattr(recommender, "RECIPE_MODEL_PATH", food_path)
    assert recommender._load_model_uncached() is None
    assert recommender._load_recipe_model_uncached() is None
    monkeypatch.setattr(recommender, "MODEL_PATH", food_path)
    monkeypatch.setattr(recommender, "RECIPE_MODEL_PATH", recipe_path)
    assert recommender._load_model_uncached() is not None
    assert recommender._load_recipe_model_uncached() is not None


def test_load_model_missing_file_returns_none(tmp_path, monkeypatch):
    _use_real_loader(monkeypatch, tmp_path / "does_not_exist.joblib")
    assert recommender.load_model() is None


def test_load_model_corrupt_file_returns_none(tmp_path, monkeypatch):
    path = tmp_path / "corrupt.joblib"
    path.write_bytes(b"not a joblib file")
    _use_real_loader(monkeypatch, path)
    assert recommender.load_model() is None


def test_load_model_rejects_feature_version_mismatch(tmp_path, monkeypatch):
    from sklearn.dummy import DummyRegressor

    path = tmp_path / "stale.joblib"
    joblib.dump(
        {"model": DummyRegressor().fit([[0.0]], [0.0]),
         "feature_version": recommender.FEATURE_VERSION + 1,
         "sklearn_version": sklearn.__version__},
        path,
    )
    _use_real_loader(monkeypatch, path)
    assert recommender.load_model() is None


def test_load_model_rejects_sklearn_version_mismatch(tmp_path, monkeypatch):
    from sklearn.dummy import DummyRegressor

    path = tmp_path / "stale.joblib"
    joblib.dump(
        {"model": DummyRegressor().fit([[0.0]], [0.0]),
         "feature_version": recommender.FEATURE_VERSION,
         "sklearn_version": "0.0.0-not-real"},
        path,
    )
    _use_real_loader(monkeypatch, path)
    assert recommender.load_model() is None


def test_load_model_accepts_matching_versions(valid_model_file):
    assert recommender.load_model() is not None


def test_ml_score_none_without_model():
    assert recommender.load_model() is None  # default fixture state
    score = recommender.ml_score({"kcal": 100}, "grain", (), [], {}, 0.0, 0.0)
    assert score is None


def test_ml_score_returns_none_when_predict_raises(monkeypatch):
    def _boom(x):
        raise RuntimeError("predict blew up")

    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(_boom))
    score = recommender.ml_score({"kcal": 100}, "grain", (), [], {}, 0.0, 0.0)
    assert score is None


def test_ml_score_batch_matches_ml_score_per_item_order(monkeypatch):
    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(lambda row: float(row.sum())))
    rows = [
        recommender.featurize({"kcal": 100 * i, "iron_mg": i}, "grain", (), ["iron_mg"],
                              {"iron_mg": 8}, float(i), float(i) / 2)
        for i in range(1, 6)
    ]
    matrix = np.vstack(rows)
    batch_scores = recommender.ml_score_batch(matrix)
    per_item_scores = [
        recommender.ml_score({"kcal": 100 * i, "iron_mg": i}, "grain", (), ["iron_mg"],
                             {"iron_mg": 8}, float(i), float(i) / 2)
        for i in range(1, 6)
    ]
    assert np.allclose(batch_scores, per_item_scores)


def test_active_backend_reflects_model_presence(monkeypatch):
    monkeypatch.setattr(recommender, "load_model", lambda: None)
    assert matcher.active_backend() == "linear"

    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(lambda row: 1.0))
    assert matcher.active_backend() == "ml"


def test_ranking_falls_back_to_linear_formula_without_model():
    # Same setup as tests/test_deficiency_match.py-style checks: no model
    # loaded (default fixture state) -> today's exact linear-formula winner.
    foods = [
        _food("iron_rich", "meat", kcal=200, iron_mg=6),
        _food("iron_poor", "vegetable", kcal=200, iron_mg=0.1),
    ]
    ranked = matcher.rank_foods(foods, emphasize=["iron_mg"], targets={"iron_mg": 8})
    assert ranked[0]["food_id"] == "iron_rich"


def test_ranking_uses_trained_model_when_present(monkeypatch):
    foods = [
        _food("iron_rich", "meat", kcal=200, iron_mg=6),
        _food("iron_poor", "vegetable", kcal=200, iron_mg=0.1),
    ]
    # A stub model that inverts the linear formula's preference: it scores
    # purely on food_group, strongly favoring "vegetable" over "meat" —
    # deliberately the opposite ranking from the deterministic fallback, so
    # a passing test proves the ML path is genuinely being used, not just
    # coincidentally agreeing with the baseline.
    def prefers_vegetable(row):
        # food_group one-hot block starts right after the 26 nutrient
        # features + 2 baseline-score features; "vegetable" is index 2 in
        # FOOD_GROUPS (grain, legume, vegetable, ...).
        from src.diet.food_db import FOOD_GROUPS
        offset = 13 * 2 + 2
        vegetable_index = offset + FOOD_GROUPS.index("vegetable")
        return float(row[vegetable_index]) * 10.0

    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(prefers_vegetable))
    ranked = matcher.rank_foods(foods, emphasize=["iron_mg"], targets={"iron_mg": 8})
    assert ranked[0]["food_id"] == "iron_poor"  # the vegetable, despite less iron
