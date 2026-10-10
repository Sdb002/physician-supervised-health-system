"""Daily energy target (Mifflin-St Jeor x activity factor, adjusted by BMI
category) and the record of how it was worked out.

A reviewer of the printed plan could not validate the calorie target: the
report showed resting, maintenance and target energy but none of the inputs.
The result now carries them.
"""

from src.clinical.bmi import ACTIVITY_FACTORS, daily_energy_target, mifflin_st_jeor


def test_target_is_reproducible_from_its_recorded_basis():
    energy = daily_energy_target(weight_kg=78, height_cm=158, age=36, sex="female")
    basis = energy["basis"]
    assert (basis["weight_kg"], basis["height_cm"], basis["age"], basis["sex"]) == (78, 158, 36, "female")
    assert basis["equation"] == "mifflin_st_jeor"

    resting = mifflin_st_jeor(basis["weight_kg"], basis["height_cm"], basis["age"], basis["sex"])
    assert energy["ree_kcal"] == round(resting)
    assert energy["tdee_kcal"] == round(resting * basis["activity_factor"])
    assert energy["target_kcal"] == round(resting * basis["activity_factor"] + basis["adjustment_kcal"])
    assert basis["floor_applied"] is False


def test_an_unstated_activity_level_is_recorded_as_assumed():
    assumed = daily_energy_target(78, 158, 36, "female")["basis"]
    assert assumed["activity"] == "light"
    assert assumed["activity_factor"] == ACTIVITY_FACTORS["light"]
    assert assumed["activity_assumed"] is True

    stated = daily_energy_target(78, 158, 36, "female", activity="moderate")["basis"]
    assert stated["activity"] == "moderate"
    assert stated["activity_factor"] == ACTIVITY_FACTORS["moderate"]
    assert stated["activity_assumed"] is False


def test_the_floor_is_recorded_when_it_sets_the_target():
    # a small, older, obese woman: maintenance minus the deficit falls under 1200
    energy = daily_energy_target(weight_kg=55, height_cm=140, age=70, sex="female")
    assert energy["bmi_category"] == "obese"
    assert energy["target_kcal"] == energy["basis"]["floor_kcal"] == 1200
    assert energy["basis"]["floor_applied"] is True
