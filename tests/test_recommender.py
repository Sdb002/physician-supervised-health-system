"""ML scoring backend: graceful fallback, feature shape, and dispatch.

The autouse fixture in conftest.py pins the rest of the suite to
recommender.load_model() -> None; tests here override that per-test via
monkeypatch (last set wins) to exercise the ML-active path in isolation.
"""

import joblib
import numpy as np
import pytest
import sklearn

from src.clinical import deficiency
from src.diet import matcher, recommender
from src.diet.food_db import Food
from src.diet.meal_plan import build_meal_plan
from src.diet.recipe import Recipe


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


def _recipe(recipe_id: str, category: str, kcal: float, *, frequency: int = 5,
            meals=("breakfast", "lunch", "dinner"), grain: float = 0.0, **nutrients) -> Recipe:
    per_serving = _food(recipe_id, "other", kcal, **nutrients).nutrients
    return Recipe(recipe_id=recipe_id, name_en=recipe_id, name_bn="", servings=1,
                  meal_type=tuple(meals), tags=(), source="test", ingredients=(),
                  per_serving=per_serving, category=category, weekly_frequency_score=frequency,
                  serving_size_g=150.0, group_shares={"grain": grain} if grain else {})


class _StubModel:
    """Not a real sklearn estimator — just something with .predict(X) that
    scores each row via a caller-supplied function of the feature vector, so
    tests can pin exactly what "the model" prefers without depending on a
    real fit's convergence. Only usable via monkeypatching load_model
    directly (holds a closure, so it can't be joblib-pickled to disk).
    Keeps every matrix it was asked to score."""

    def __init__(self, fn):
        self._fn = fn
        self.calls: list[np.ndarray] = []

    def predict(self, x):
        self.calls.append(np.array(x))
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


def test_featurize_recipe_shape_and_group_shares():
    nutrients = {"kcal": 250, "iron_mg": 3}
    shares = {"vegetable": 0.8, "oil": 0.05, "spice": 0.15}
    vector = recommender.featurize_recipe(nutrients, shares, (), ["iron_mg"], {"iron_mg": 18}, 0.2, 1.0)
    assert vector.shape == (recommender.RECIPE_FEATURE_DIM,)
    share_index = recommender.RECIPE_FEATURE_NAMES.index("share_vegetable")
    assert vector[share_index] == pytest.approx(0.8)
    # how often a dish is cooked is weighted in by the matcher, never learned
    assert not any("frequency" in name for name in recommender.RECIPE_FEATURE_NAMES)


def test_featurize_gives_an_emphasized_nutrient_its_share_twice():
    nutrients = {"kcal": 100, "iron_mg": 9, "vit_c_mg": 30}
    targets = {"iron_mg": 18, "vit_c_mg": 75}
    vector = recommender.featurize(nutrients, "vegetable", (), ["iron_mg"], targets, 0.5, 0.0)
    value = dict(zip(recommender.FEATURE_NAMES, vector))
    assert value["iron_mg_ratio"] == value["iron_mg_emphasized_ratio"] == pytest.approx(0.5)
    assert value["vit_c_mg_ratio"] == pytest.approx(0.4)
    assert value["vit_c_mg_emphasized_ratio"] == 0.0  # in the food, not asked for
    assert value["nothing_emphasized"] == 0.0
    unemphasized = recommender.featurize(nutrients, "vegetable", (), [], targets, 0.0, 0.0)
    assert dict(zip(recommender.FEATURE_NAMES, unemphasized))["nothing_emphasized"] == 1.0


def test_featurize_tells_the_model_the_findings():
    args = ({"kcal": 100}, "vegetable", (), ["fiber_g"], {"fiber_g": 25}, 0.0, 0.0)
    # fibre alone is emphasized for diabetes, and for hypertension with kidney
    # disease: the same emphasis, two different patients
    diabetes = dict(zip(recommender.FEATURE_NAMES,
                        recommender.featurize(*args, findings=["diabetes"])))
    hypertension = dict(zip(recommender.FEATURE_NAMES,
                            recommender.featurize(*args, findings=["hypertension"])))
    assert diabetes["finding_diabetes"] == 1.0 and diabetes["finding_hypertension"] == 0.0
    assert hypertension["finding_hypertension"] == 1.0 and hypertension["finding_diabetes"] == 0.0
    recipe = dict(zip(recommender.RECIPE_FEATURE_NAMES, recommender.featurize_recipe(
        {"kcal": 100}, {}, (), [], {}, 0.0, 0.0, findings=["anemia"])))
    assert recipe["finding_anemia"] == 1.0


def test_finding_features_are_the_findings_of_the_rules_file():
    assert set(recommender.FINDING_FEATURES) == set(deficiency._rules()["findings"])


def test_featurize_measures_sodium_against_its_limit():
    # sodium has a ceiling, not a target: without the limit the model was
    # blind to it, whatever the dish
    nutrients, targets = {"kcal": 100, "sodium_mg": 500}, {"iron_mg": 18}
    index = recommender.FEATURE_NAMES.index("sodium_mg_ratio")
    blind = recommender.featurize(nutrients, "fish", (), [], targets, 0.0, 0.0)
    told = recommender.featurize(nutrients, "fish", (), [], targets, 0.0, 0.0,
                                 limits={"sodium_mg": 2000})
    assert blind[index] == 0.0 and told[index] == pytest.approx(0.25)


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


def _rows(count: int = 5) -> list[np.ndarray]:
    return [
        recommender.featurize({"kcal": 100 * i, "iron_mg": i}, "grain", (), ["iron_mg"],
                              {"iron_mg": 8}, float(i), float(i) / 2)
        for i in range(1, count + 1)
    ]


def test_ml_score_batch_none_without_model():
    assert recommender.load_model() is None  # default fixture state
    assert recommender.ml_score_batch(_rows()) is None


def test_ml_score_batch_none_with_nothing_to_score(monkeypatch):
    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(lambda row: 1.0))
    assert recommender.ml_score_batch([]) is None


def test_ml_score_batch_returns_none_when_predict_raises(monkeypatch):
    def _boom(row):
        raise RuntimeError("predict blew up")

    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(_boom))
    assert recommender.ml_score_batch(_rows()) is None


def test_ml_score_batch_scores_every_row_in_order_in_one_call(monkeypatch):
    model = _StubModel(lambda row: float(row.sum()))
    monkeypatch.setattr(recommender, "load_model", lambda: model)
    rows = _rows()
    scores = recommender.ml_score_batch(rows)
    assert np.allclose(scores, [row.sum() for row in rows])
    assert np.allclose(recommender.ml_score_batch(np.vstack(rows)), scores)  # a matrix works too
    assert len(model.calls) == 2 and model.calls[0].shape == (5, recommender.FEATURE_DIM)


def test_a_failing_model_falls_back_to_the_formula(monkeypatch):
    def _boom(row):
        raise RuntimeError("predict blew up")

    monkeypatch.setattr(recommender, "load_model", lambda: _StubModel(_boom))
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: _StubModel(_boom))
    foods = [_food("iron_rich", "meat", kcal=200, iron_mg=6)]
    assert matcher.score_foods(foods, ["iron_mg"], {"iron_mg": 8}) == [pytest.approx(0.75)]
    dishes = [_recipe("curry", "Meat", 200, frequency=10, iron_mg=6)]
    assert matcher.score_recipes(dishes, ["iron_mg"], {"iron_mg": 8}) == [pytest.approx(0.75)]


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
    vegetable_index = recommender.FEATURE_NAMES.index("group_vegetable")
    model = _StubModel(lambda row: float(row[vegetable_index]) * 10.0)
    monkeypatch.setattr(recommender, "load_model", lambda: model)
    ranked = matcher.rank_foods(foods, emphasize=["iron_mg"], targets={"iron_mg": 8})
    assert ranked[0]["food_id"] == "iron_poor"  # the vegetable, despite less iron
    assert len(model.calls) == 1  # the whole list in one predict call


def test_familiarity_weights_the_recipe_models_fit_as_it_does_the_formulas(monkeypatch):
    dishes = [_recipe("festive", "Meat", 200, frequency=1, iron_mg=4),
              _recipe("daily", "Meat", 200, frequency=10, iron_mg=4)]
    # a model that finds the two dishes equally suitable: the common one leads,
    # by exactly the formula's margin
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: _StubModel(lambda row: 2.0))
    festive, daily = matcher.score_recipes(dishes, ["iron_mg"], {"iron_mg": 18})
    assert daily == pytest.approx(2.0) and festive == pytest.approx(2.0 * matcher.FREQUENCY_FLOOR)
    # ...and one that finds them unsuitable: being common does not soften that
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: _StubModel(lambda row: -1.0))
    assert matcher.score_recipes(dishes, ["iron_mg"], {"iron_mg": 18}) == [-1.0, -1.0]


def test_the_models_are_told_the_findings_and_the_sodium_limit(monkeypatch):
    food_model, recipe_model = _StubModel(lambda row: 1.0), _StubModel(lambda row: 1.0)
    monkeypatch.setattr(recommender, "load_model", lambda: food_model)
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: recipe_model)
    kitchen = [
        _recipe("rice", "Rice & Grain", 275, grain=1.0, sodium_mg=400),
        _recipe("dal", "Dal", 170, sodium_mg=400),
        _recipe("fish", "Fish", 270, sodium_mg=400),
        _recipe("shak", "Leafy Green", 90, sodium_mg=400),
    ]
    fruits = [_food("guava", "fruit", kcal=68, sodium_mg=400)]
    context = dict(findings=["hypertension"], limits={"sodium_mg": 2000})

    matcher.rank_foods(fruits, ["fiber_g"], {"fiber_g": 25}, **context)
    matcher.rank_recipes(kitchen, ["fiber_g"], {"fiber_g": 25}, **context)
    build_meal_plan(kitchen, fruits, 1800, targets={"fiber_g": 25}, emphasize=["fiber_g"],
                    sodium_limit_mg=2000, findings=["hypertension"])

    for model, names in ((food_model, recommender.FEATURE_NAMES),
                         (recipe_model, recommender.RECIPE_FEATURE_NAMES)):
        assert len(model.calls) >= 2  # the ranking, then the plan
        for matrix in model.calls:
            assert (matrix[:, names.index("finding_hypertension")] == 1.0).all()
            assert (matrix[:, names.index("finding_diabetes")] == 0.0).all()
            assert matrix[:, names.index("sodium_mg_ratio")] == pytest.approx(0.2)


def test_a_weeks_plan_scores_each_emphasis_once(monkeypatch):
    # sixty-odd courses and seven snacks are picked from score tables worked
    # out once per emphasis, not from a predict call per dish considered
    food_model, recipe_model = _StubModel(lambda row: 1.0), _StubModel(lambda row: 1.0)
    monkeypatch.setattr(recommender, "load_model", lambda: food_model)
    monkeypatch.setattr(recommender, "load_recipe_model", lambda: recipe_model)
    kitchen = [
        _recipe("rice", "Rice & Grain", 275, grain=1.0),
        _recipe("ruti", "Bread & Pitha", 267, grain=0.99, fiber_g=4),
        _recipe("dal", "Dal", 170, fiber_g=3), _recipe("fish", "Fish", 270),
        _recipe("chicken", "Meat", 300), _recipe("egg", "Egg", 190),
        _recipe("shak", "Leafy Green", 90, fiber_g=3, iron_mg=3),
        _recipe("bhaji", "Vegetable", 120, fiber_g=2),
    ]
    plan = build_meal_plan(kitchen, [_food("guava", "fruit", kcal=68, fiber_g=5)], 1800,
                           targets={"fiber_g": 25, "iron_mg": 18},
                           emphasize=["fiber_g", "iron_mg"])
    assert len(plan["days"]) == 7
    # two nutrients can be emphasized in four ways (both, either, neither)
    assert 1 <= len(recipe_model.calls) <= 4 and 1 <= len(food_model.calls) <= 4
    assert all(len(matrix) == len(kitchen) for matrix in recipe_model.calls)
