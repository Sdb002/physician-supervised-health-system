"""Soft intensity/volume scaling by age, BMI category, and fitness level.

Citations:
- Tanaka H, Monahan KD, Seals DR. Age-predicted maximal heart rate revisited.
  J Am Coll Cardiol 2001;37(1):153-6 — HRmax = 208 − 0.7 × age.
- ACSM's Guidelines for Exercise Testing and Prescription, 11th ed. —
  %HRmax bands: light 57–63%, moderate 64–76%, vigorous 77–95%.

Sex is accepted for interface completeness but applies no scaling: ACSM
prescribes volume by the same absolute weekly targets for all adults.
"""

_HR_BANDS = {"light": (0.57, 0.63), "moderate": (0.64, 0.76), "vigorous": (0.77, 0.95)}


def hr_max(age: int) -> float:
    return 208.0 - 0.7 * age


def target_hr_range(age: int, level: str) -> tuple[int, int]:
    lo, hi = _HR_BANDS[level]
    peak = hr_max(age)
    return round(peak * lo), round(peak * hi)


def starting_level(fitness_level: str, overall_risk: str) -> str:
    """Starting aerobic intensity. Any high/critical biomarker risk, or a
    beginner fitness level, starts light; otherwise moderate. Vigorous work is
    never auto-prescribed — that is a physician's call during review."""
    if overall_risk in ("high", "critical") or fitness_level == "beginner":
        return "light"
    return "moderate"


def volume_factor(age: int, bmi_category: str, fitness_level: str, sex: str) -> float:
    """Fraction of the ACSM baseline weekly volume to start at."""
    factor = 1.0
    if fitness_level == "beginner":
        factor *= 0.6
    elif fitness_level == "intermediate":
        factor *= 0.8
    if age >= 60:
        factor *= 0.8
    if bmi_category == "obese":
        factor *= 0.85
    return max(round(factor, 2), 0.4)
