"""Recipe ranking: nutritional fit x household familiarity, gate first.

The recipe dataset scores every dish 1-10 for how commonly it is cooked at
home (10 = the most common household dish). Ranking must prefer common
dishes among those that suit the patient — without ever letting
familiarity lift a dish that does nothing for the patient's targets.
"""

import numpy as np
import pytest

from src.clinical.contraindication import excluded_tags, filter_items
from src.clinical.deficiency import nutrient_targets
from src.clinical.risk_scoring import score_biomarkers
from src.diet import matcher, recommender
from src.diet.food_db import food_index, load_foods
from src.diet.matcher import FREQUENCY_FLOOR, frequency_multiplier, rank_recipes
from src.diet.recipe import Recipe, load_recipes

_NUTRIENTS = ("kcal", "protein_g", "carb_g", "fat_g", "fiber_g", "iron_mg",
              "calcium_mg", "zinc_mg", "folate_ug", "vit_a_ug", "vit_c_mg",
              "sodium_mg", "potassium_mg")


def _recipe(recipe_id: str, frequency: int | None, tags: tuple = (), **nutrients) -> Recipe:
    per_serving = {c: 0.0 for c in _NUTRIENTS}
    per_serving.update(nutrients)
    return Recipe(recipe_id=recipe_id, name_en=recipe_id, name_bn="", servings=4,
                  meal_type=("lunch",), tags=tags, source="TEST", ingredients=(),
                  per_serving=per_serving, weekly_frequency_score=frequency,
                  group_shares={"vegetable": 1.0})


@pytest.fixture(scope="module")
def recipes():
    return load_recipes(food_index(load_foods()))


def test_frequency_multiplier_scale():
    assert frequency_multiplier(10) == pytest.approx(1.0)
    assert frequency_multiplier(1) == pytest.approx(FREQUENCY_FLOOR)
    assert frequency_multiplier(None) == pytest.approx(1.0)  # no score -> no adjustment
    values = [frequency_multiplier(s) for s in range(1, 11)]
    assert values == sorted(values)  # more common never ranks lower


def test_familiarity_reorders_equally_suitable_recipes():
    common = _recipe("common", 9, kcal=200, iron_mg=4)
    festive = _recipe("festive", 2, kcal=200, iron_mg=4)
    ranked = rank_recipes([festive, common], ["iron_mg"], {"iron_mg": 18})
    assert [r["recipe_id"] for r in ranked] == ["common", "festive"]
    assert ranked[0]["score"] > ranked[1]["score"]


def test_familiarity_never_lifts_an_unsuitable_recipe():
    staple_without_iron = _recipe("staple", 10, kcal=300, iron_mg=0)
    ranked = rank_recipes([staple_without_iron], ["iron_mg"], {"iron_mg": 18})
    assert ranked == []  # score 0 for an iron-emphasized patient, however common


def test_a_much_better_rare_dish_still_beats_a_weak_common_one():
    weak_common = _recipe("weak_common", 10, kcal=200, iron_mg=1)
    strong_rare = _recipe("strong_rare", 1, kcal=200, iron_mg=6)
    ranked = rank_recipes([weak_common, strong_rare], ["iron_mg"], {"iron_mg": 18})
    assert ranked[0]["recipe_id"] == "strong_rare"  # 6 x 0.25 > 1 x 1.0


def test_real_recipes_rank_with_full_details_for_anemia(recipes):
    flags = score_biomarkers({"hemoglobin": 9.0}, "female")
    nutrition = nutrient_targets("female", False, flags)
    ranked = rank_recipes(recipes, nutrition["emphasize"], nutrition["targets"])
    assert len(ranked) == 10
    for entry in ranked:
        assert 1 <= entry["weekly_frequency_score"] <= 10
        assert entry["frequency_tier"]
        assert entry["ingredients"] and entry["steps"]
        assert entry["per_serving"]["iron_mg"] >= 0
    scores = [entry["score"] for entry in ranked]
    assert scores == sorted(scores, reverse=True)


def test_gate_removes_sugary_and_salty_recipes_before_ranking(recipes):
    flags = score_biomarkers({"fasting_glucose": 130, "systolic_bp": 150}, "male")
    nutrition = nutrient_targets("male", False, flags)
    ex = excluded_tags(["diabetes", "hypertension"])
    allowed = filter_items(recipes, ex.food_tags)
    assert len(allowed) < len(recipes)
    ranked = rank_recipes(allowed, nutrition["emphasize"], nutrition["targets"], top_n=50)
    assert ranked
    assert all(not ({"high_sugar", "high_sodium"} & set(r["tags"])) for r in ranked)


class _StubModel:
    def __init__(self, fn):
        self._fn = fn

    def predict(self, x):
        return np.array([self._fn(row) for row in x])


def test_ranking_uses_trained_recipe_model_when_present(monkeypatch):
    common = _recipe("common", 9, kcal=200, iron_mg=4)
    festive = _recipe("festive", 2, kcal=200, iron_mg=4)
    # a stub that prefers the LESS common dish — the opposite of the
    # deterministic formula — proves the model path is really used
    freq_index = recommender.RECIPE_FEATURE_NAMES.index("household_frequency")
    monkeypatch.setattr(recommender, "load_recipe_model",
                        lambda: _StubModel(lambda row: 2.0 - row[freq_index]))
    ranked = rank_recipes([common, festive], ["iron_mg"], {"iron_mg": 18})
    assert ranked[0]["recipe_id"] == "festive"
    assert matcher.active_recipe_backend() == "ml"
