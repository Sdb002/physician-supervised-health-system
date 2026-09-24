"""Lab deficiency → nutrient targets → food/recipe matching."""

from src.clinical.contraindication import excluded_tags, filter_items
from src.clinical.deficiency import findings_from_flags, nutrient_targets, rdi_group
from src.clinical.risk_scoring import score_biomarkers
from src.diet.food_db import load_foods
from src.diet.matcher import rank_foods


def test_rdi_group_selection():
    assert rdi_group("male", False) == "male_adult"
    assert rdi_group("female", False) == "female_adult"
    assert rdi_group("female", True) == "pregnant"


def test_anemia_triggers_iron_emphasis():
    flags = score_biomarkers({"hemoglobin": 9.0}, "female")
    assert findings_from_flags(flags) == ["anemia"]
    nutrition = nutrient_targets("female", False, flags)
    assert {"iron_mg", "folate_ug", "vit_c_mg"} <= set(nutrition["emphasize"])
    assert nutrition["targets"]["iron_mg"] == 18  # RDA, adult female
    assert "anemia" in nutrition["rationales"]


def test_pregnancy_raises_targets():
    flags = score_biomarkers({"hemoglobin": 9.0}, "female", pregnant=True)
    nutrition = nutrient_targets("female", True, flags)
    assert nutrition["group"] == "pregnant"
    assert nutrition["targets"]["iron_mg"] == 27
    assert nutrition["targets"]["folate_ug"] == 600


def test_hypertension_emphasizes_potassium_and_limits_sodium():
    flags = score_biomarkers({"systolic_bp": 150, "diastolic_bp": 95}, "male")
    nutrition = nutrient_targets("male", False, flags)
    assert "potassium_mg" in nutrition["emphasize"]
    assert nutrition["limits"]["sodium_mg"] == 2000


def test_no_findings_no_emphasis():
    flags = score_biomarkers(
        {"fasting_glucose": 90, "systolic_bp": 110, "diastolic_bp": 70, "hemoglobin": 14},
        "male",
    )
    nutrition = nutrient_targets("male", False, flags)
    assert nutrition["emphasize"] == []


def test_matcher_ranks_iron_dense_foods_for_anemia():
    flags = score_biomarkers({"hemoglobin": 9.0}, "female")
    nutrition = nutrient_targets("female", False, flags)
    foods = load_foods()
    ranked = rank_foods(foods, nutrition["emphasize"], nutrition["targets"], top_n=5)
    assert len(ranked) == 5
    by_id = {f.food_id: f for f in foods}
    # anemia emphasizes iron + folate + vit C: every top food must be dense in
    # iron or in vitamin C (absorption enhancer) — not just any food
    for r in ranked[:3]:
        n = by_id[r["food_id"]].nutrients
        assert n["iron_mg"] >= 3 or n["vit_c_mg"] >= 50
    # and each must outscore a low-iron staple (parboiled milled rice)
    rice = next(f for f in foods if f.name_en == "Rice, milled, parboiled")
    rice_ranked = rank_foods([rice], nutrition["emphasize"], nutrition["targets"])
    rice_score = rice_ranked[0]["score"] if rice_ranked else 0.0
    assert all(r["score"] > rice_score for r in ranked[:3])


def test_gate_runs_before_matching():
    """Anemic AND hypertensive: high-sodium foods (e.g. dried/salted items) may
    be iron-rich, but the contraindication gate must remove them before
    ranking ever sees them."""
    flags = score_biomarkers({"hemoglobin": 9.0, "systolic_bp": 150}, "female")
    nutrition = nutrient_targets("female", False, flags)
    ex = excluded_tags(["anemia", "hypertension"])
    allowed = filter_items(load_foods(), ex.food_tags)
    ranked = rank_foods(allowed, nutrition["emphasize"], nutrition["targets"])
    assert ranked
    assert all("high_sodium" not in r["tags"] for r in ranked)
