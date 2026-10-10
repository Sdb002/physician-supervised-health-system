"""Lab deficiency → nutrient targets → food/recipe matching."""

from src.clinical.contraindication import excluded_tags, filter_items
from src.clinical.deficiency import findings_from_flags, nutrient_targets, rdi_group
from src.clinical.risk_scoring import score_biomarkers
from src.diet.food_db import eaten_in_portions, load_foods, recommendable_foods
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
    rice = next(f for f in foods if f.name_en == "Rice, BR-28, parboiled, milled, raw")
    rice_ranked = rank_foods([rice], nutrition["emphasize"], nutrition["targets"])
    rice_score = rice_ranked[0]["score"] if rice_ranked else 0.0
    assert all(r["score"] > rice_score for r in ranked[:3])


def test_recommendation_pool_is_bangladeshi_foods_eaten_in_portions():
    foods = load_foods()
    pool = recommendable_foods(foods)
    assert 300 < len(pool) < len(foods)  # IFCT/USDA gap-fill rows are left out
    by_name = {f.name_en: f for f in foods}
    assert by_name["Goat, spleen"] not in pool  # IFCT offal, rarely eaten in Bangladesh
    assert by_name["Spinach, raw"] in pool  # FCTB
    assert by_name["Mint leaves"] in pool  # IFCT, but used in household recipes
    portions = eaten_in_portions(pool)
    assert all(f.food_group != "spice" for f in portions)
    assert by_name["Tea, powder"] not in portions  # brewed concentrate


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


def test_reference_intakes_follow_the_age_band():
    assert rdi_group("female", False, 30) == "female_adult"
    assert rdi_group("female", False, 51) == "female_51_70"
    assert rdi_group("male", False, 70) == "male_51_70"
    assert rdi_group("male", False, 71) == "male_over_70"
    assert rdi_group("female", True, 44) == "pregnant"
    # reported: a 60-year-old woman kept the 18 mg iron target of a
    # menstruating adult
    older = nutrient_targets("female", False, [], age=60)["targets"]
    assert older["iron_mg"] == 8 and older["calcium_mg"] == 1200
    assert nutrient_targets("female", False, [], age=30)["targets"]["iron_mg"] == 18
    assert nutrient_targets("male", False, [], age=75)["targets"]["calcium_mg"] == 1200


def test_a_recorded_condition_drives_the_emphasis_without_a_lab_flag():
    # known hypertension, normal pressure on the day of the visit
    flags = score_biomarkers({"systolic_bp": 118, "diastolic_bp": 76}, "male")
    assert nutrient_targets("male", False, flags)["emphasize"] == []
    nutrition = nutrient_targets("male", False, flags, conditions=["hypertension"])
    assert nutrition["emphasize"] == ["potassium_mg", "fiber_g"]
    assert "hypertension" in nutrition["rationales"]
    # a condition with no emphasis rule adds nothing
    assert nutrient_targets("male", False, [], conditions=["knee_osteoarthritis"])["emphasize"] == []


def test_kidney_disease_stops_the_potassium_emphasis():
    emphasized = nutrient_targets("male", False, [], conditions=["hypertension"])
    assert "potassium_mg" in emphasized["emphasize"]
    # the physician is told to check before approving
    assert any("kidney function" in caution for caution in emphasized["cautions"])

    kidney = nutrient_targets("male", False, [],
                              conditions=["hypertension", "chronic_kidney_disease"])
    assert kidney["emphasize"] == ["fiber_g"]
    assert kidney["cautions"] == []
    assert "chronic_kidney_disease" in kidney["rationales"]
    # with nothing to suppress, the condition has nothing to explain
    alone = nutrient_targets("male", False, [], conditions=["chronic_kidney_disease"])
    assert alone["emphasize"] == [] and alone["rationales"] == {}


def test_every_finding_explains_itself_to_the_patient_in_both_languages():
    nutrition = nutrient_targets("female", False, [],
                                 conditions=["anemia", "hypertension", "diabetes"])
    assert set(nutrition["patient_rationales"]) == {"anemia", "hypertension", "diabetes"}
    for text in nutrition["patient_rationales"].values():
        assert text["en"] and text["bn"] and text["en"] != text["bn"]
        # the physician's wording stays out of the patient's
        assert "contraindication gate" not in text["en"]
