"""BMI, BMI category, and energy requirement.

Citations:
- WHO Expert Consultation. Appropriate body-mass index for Asian populations.
  Lancet 2004;363(9403):157-63 — Asian-Pacific cutoffs (23.0 overweight,
  27.5 obese), used by default for the Bangladeshi population.
- Mifflin MD et al. A new predictive equation for resting energy expenditure.
  Am J Clin Nutr 1990;51(2):241-7.
"""

from datetime import date


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("weight and height must be positive")
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m * h_m), 1)


def bmi_category(bmi: float, asian_cutoffs: bool = True) -> str:
    if bmi < 18.5:
        return "underweight"
    if asian_cutoffs:
        if bmi < 23.0:
            return "normal"
        if bmi < 27.5:
            return "overweight"
        return "obese"
    if bmi < 25.0:
        return "normal"
    if bmi < 30.0:
        return "overweight"
    return "obese"


def age_from_birth_year(birth_year: int, today: date | None = None) -> int:
    today = today or date.today()
    return max(0, today.year - birth_year)


def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Resting energy expenditure, kcal/day."""
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age
    return base + (5.0 if sex == "male" else -161.0)


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}

# Energy adjustment by BMI category: modest deficit for weight loss, surplus for
# underweight. Floors per conventional dietetic practice minimums.
_ADJUST = {"underweight": +400, "normal": 0, "overweight": -400, "obese": -500}
_FLOOR = {"male": 1500, "female": 1200}


def daily_energy_target(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity: str = "light",
    asian_cutoffs: bool = True,
) -> dict:
    bmi = compute_bmi(weight_kg, height_cm)
    category = bmi_category(bmi, asian_cutoffs)
    ree = mifflin_st_jeor(weight_kg, height_cm, age, sex)
    tdee = ree * ACTIVITY_FACTORS.get(activity, 1.375)
    target = max(tdee + _ADJUST[category], _FLOOR.get(sex, 1200))
    return {
        "bmi": bmi,
        "bmi_category": category,
        "ree_kcal": round(ree),
        "tdee_kcal": round(tdee),
        "target_kcal": round(target),
    }
