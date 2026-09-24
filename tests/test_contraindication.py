"""The hard safety gate: condition → excluded tags → filtered items."""

from src.clinical.contraindication import (
    excluded_tags,
    filter_items,
    is_allowed,
    known_conditions,
)
from src.diet.food_db import load_foods
from src.lifestyle.exercise_db import load_exercises


def test_hypertension_exclusions():
    ex = excluded_tags(["hypertension"])
    assert "high_sodium" in ex.food_tags
    assert "high_exertion" in ex.exercise_tags
    assert ex.applied_conditions == ("hypertension",)


def test_unknown_condition_is_ignored():
    ex = excluded_tags(["hypertension", "no_such_condition"])
    assert ex.applied_conditions == ("hypertension",)


def test_exclusions_are_a_union():
    ex = excluded_tags(["hypertension", "diabetes", "knee_osteoarthritis"])
    assert {"high_sodium", "high_sugar"} <= set(ex.food_tags)
    assert {"high_exertion", "high_impact", "knee_stress"} <= set(ex.exercise_tags)


def test_gate_removes_high_sodium_foods():
    foods = load_foods()
    salty = [f for f in foods if "high_sodium" in f.tags]
    assert salty  # dataset must contain high-sodium foods (salted/dried items)
    ex = excluded_tags(["hypertension"])
    allowed = filter_items(foods, ex.food_tags)
    assert len(allowed) == len(foods) - len(salty)
    assert all("high_sodium" not in f.tags for f in allowed)


def test_gate_removes_contraindicated_exercises():
    exercises = load_exercises()
    ex = excluded_tags(["knee_osteoarthritis"])
    allowed = filter_items(exercises, ex.exercise_tags)
    ids = {e.exercise_id for e in allowed}
    assert "E008" not in ids  # stair climbing: high_impact + knee_stress
    assert "E005" not in ids  # squats: knee_stress
    assert "E001" in ids  # brisk walking survives


def test_no_conditions_excludes_nothing():
    ex = excluded_tags([])
    assert not ex.food_tags and not ex.exercise_tags
    assert is_allowed(["high_sodium"], ex.food_tags)


def test_every_condition_has_rules():
    assert {"hypertension", "diabetes", "anemia", "pregnancy",
            "knee_osteoarthritis"} <= set(known_conditions())
