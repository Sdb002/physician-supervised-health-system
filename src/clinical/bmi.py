"""BMI, BMI category, and energy requirement.

Citations:
- WHO Expert Consultation. Appropriate body-mass index for Asian populations.
  Lancet 2004;363(9403):157-63 — Asian-Pacific cutoffs (23.0 overweight,
  27.5 obese), used by default for the Bangladeshi population.
- Mifflin MD et al. A new predictive equation for resting energy expenditure.
  Am J Clin Nutr 1990;51(2):241-7.
- Institute of Medicine (2005). Dietary Reference Intakes for Energy,
  Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and Amino
  Acids, ch. 5 — extra energy in pregnancy by trimester.
- Institute of Medicine (2009). Weight Gain During Pregnancy: Reexamining the
  Guidelines — weight loss is not advised in pregnancy at any body mass index.
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
# Used when no activity level is given for the patient. The result records
# that it was assumed, so the report can say so.
DEFAULT_ACTIVITY = "light"

# Energy adjustment by BMI category: modest deficit for weight loss, surplus for
# underweight. Floors per conventional dietetic practice minimums.
_ADJUST = {"underweight": +400, "normal": 0, "overweight": -400, "obese": -500}
_FLOOR = {"male": 1500, "female": 1200}

# Extra energy a day in pregnancy, by trimester (IOM 2005). In pregnancy the
# body-mass-index adjustment above is not applied at all: weight loss is not
# advised (IOM 2009), and a body mass index worked out from the weight during
# pregnancy is not the pre-pregnancy one the categories are defined on.
PREGNANCY_KCAL = {1: 0, 2: 340, 3: 452}


def daily_energy_target(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity: str | None = None,
    asian_cutoffs: bool = True,
    pregnant: bool = False,
    trimester: int | None = None,
) -> dict:
    """The energy target, with the inputs and steps it was worked out from
    (`basis`) so a reader of the report can check the arithmetic.

    In pregnancy there is no weight-loss or weight-gain adjustment; the
    trimester's extra energy is added instead. With no trimester recorded
    nothing is added, and the basis says so."""
    bmi = compute_bmi(weight_kg, height_cm)
    category = bmi_category(bmi, asian_cutoffs)
    ree = mifflin_st_jeor(weight_kg, height_cm, age, sex)
    level = activity if activity in ACTIVITY_FACTORS else DEFAULT_ACTIVITY
    tdee = ree * ACTIVITY_FACTORS[level]
    floor = _FLOOR.get(sex, 1200)
    adjustment = 0 if pregnant else _ADJUST[category]
    pregnancy_kcal = PREGNANCY_KCAL.get(trimester, 0) if pregnant else 0
    target = max(tdee + adjustment + pregnancy_kcal, floor)
    pregnancy = {
        "pregnancy": {
            "trimester": trimester if trimester in PREGNANCY_KCAL else None,
            "extra_kcal": pregnancy_kcal,
        }
    } if pregnant else {}
    return {
        "bmi": bmi,
        "bmi_category": category,
        "ree_kcal": round(ree),
        "tdee_kcal": round(tdee),
        "target_kcal": round(target),
        "basis": {
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "age": age,
            "sex": sex,
            "equation": "mifflin_st_jeor",
            "activity": level,
            "activity_factor": ACTIVITY_FACTORS[level],
            "activity_assumed": activity not in ACTIVITY_FACTORS,
            "adjustment_kcal": adjustment,
            "floor_kcal": floor,
            "floor_applied": tdee + adjustment + pregnancy_kcal < floor,
            **pregnancy,
        },
    }
