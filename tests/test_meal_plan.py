"""Meal-plan portion sizing and emphasis saturation.

Regression coverage for a reported bug: an anemia patient's plan repeatedly
picked whichever food was most vitamin-C-dense (vit_c_mg is "emphasized" for
anemia since it aids iron absorption) in every fruit/vegetable slot, because
scoring had no notion of "already covered" — vitamin C coverage reached
>1500% of the RDI in the reported plan, compounded by low-kcal-density
vegetables/fruit being scaled up to an unrealistic 350 g "portion" to hit a
kcal share they can't reach at a normal serving size. See data/food/schema.md
for the food-data half of the same incident (two rows — chicken breast and
spinach — had physiologically implausible iron/calcium values).
"""

from src.diet.food_db import Food
from src.diet.meal_plan import _MAX_QTY_G_BY_GROUP, build_meal_plan


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


def test_low_kcal_density_food_is_capped_to_a_realistic_portion():
    foods = [
        _food("watery_veg", "vegetable", kcal=10, vit_c_mg=5),
        _food("grain", "grain", kcal=350, protein_g=8),
    ]
    plan = build_meal_plan(foods, target_kcal=2000, targets={"vit_c_mg": 75}, emphasize=[])
    veg_items = [it for meal in plan["meals"].values() for it in meal
                if it["food_id"] == "watery_veg"]
    assert veg_items
    assert all(it["qty_g"] <= _MAX_QTY_G_BY_GROUP["vegetable"] for it in veg_items)


def test_emphasis_does_not_compound_past_saturation():
    # two nutrients are emphasized (as anemia emphasizes both iron and vit C,
    # the latter for iron absorption). One vitamin-C bomb (guava-like) and one
    # iron-rich food are available in BOTH the fruit and vegetable slots, plus
    # a neutral filler. Without saturation-awareness, the algorithm has no
    # reason to ever prefer the iron-rich/neutral options over re-adding more
    # vitamin C, so both vit-C-dense foods get used and coverage compounds.
    # With saturation, vit C should stop being chased after the first pick
    # covers it, so the second vitamin-C-dense candidate goes unused in favor
    # of the still-uncovered iron-rich (or neutral) option.
    foods = [
        _food("grain", "grain", kcal=350, protein_g=8),
        _food("vitc_fruit", "fruit", kcal=60, vit_c_mg=228),
        _food("iron_fruit", "fruit", kcal=60, iron_mg=10, vit_c_mg=5),
        _food("neutral_fruit", "fruit", kcal=60),
        _food("vitc_veg", "vegetable", kcal=60, vit_c_mg=140),
        _food("iron_veg", "vegetable", kcal=60, iron_mg=8, vit_c_mg=5),
        _food("neutral_veg", "vegetable", kcal=60),
    ]
    plan = build_meal_plan(foods, target_kcal=1800,
                           targets={"vit_c_mg": 75, "iron_mg": 18},
                           emphasize=["vit_c_mg", "iron_mg"])
    used_ids = {it["food_id"] for meal in plan["meals"].values() for it in meal}
    assert "vitc_fruit" in used_ids  # the single best vit-C source is still picked
    assert "vitc_veg" not in used_ids  # but a second one isn't, once vit C is covered
    assert plan["coverage"]["vit_c_mg"] < 600  # would be ~830%+ with both used
