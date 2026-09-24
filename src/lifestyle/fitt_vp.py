"""FITT-VP exercise prescription (Frequency, Intensity, Time, Type, Volume,
Progression) per ACSM's Guidelines for Exercise Testing and Prescription,
11th ed.: >=150 min/week moderate aerobic activity, resistance training on
>=2 days/week, flexibility work >=2-3 days/week.

Callers must pass exercises that already went through the contraindication
gate (src.clinical.contraindication.filter_items).
"""

from src.lifestyle.exercise_db import Exercise
from src.lifestyle.intensity import starting_level, target_hr_range, volume_factor

_BASE_WEEKLY_AEROBIC_MIN = 150
_AEROBIC_DAYS = 5
_STRENGTH_DAYS = 2
_FLEX_DAYS = 3


def _by_category(exercises: list[Exercise], category: str) -> list[Exercise]:
    return sorted(
        [e for e in exercises if e.category == category],
        key=lambda e: (e.met_value, e.exercise_id),
    )


def _pick_aerobic(exercises: list[Exercise], level: str, n: int = 2) -> list[Exercise]:
    aerobic = _by_category(exercises, "aerobic")
    allowed_levels = {"light": ("light", "moderate"), "moderate": ("moderate",),
                      "vigorous": ("moderate", "vigorous")}[level]
    matching = [e for e in aerobic if e.intensity_level in allowed_levels]
    return (matching or aerobic)[:n]


def _fmt(exercises: list[Exercise]) -> list[dict]:
    return [
        {"exercise_id": e.exercise_id, "name_en": e.name_en, "name_bn": e.name_bn,
         "met_value": e.met_value, "equipment": e.equipment,
         "intensity_level": e.intensity_level}
        for e in exercises
    ]


def build_fitt_plan(age: int, sex: str, weight_kg: float, bmi_category: str,
                    fitness_level: str, overall_risk: str,
                    exercises: list[Exercise]) -> dict:
    if not exercises:
        return {"note": "exercise database is empty — add data/lifestyle/exercises.csv"}

    level = starting_level(fitness_level, overall_risk)
    factor = volume_factor(age, bmi_category, fitness_level, sex)
    weekly_min = round(_BASE_WEEKLY_AEROBIC_MIN * factor / 10) * 10
    session_min = max(round(weekly_min / _AEROBIC_DAYS / 5) * 5, 10)
    hr_lo, hr_hi = target_hr_range(age, level)

    aerobic = _pick_aerobic(exercises, level)
    strength = _by_category(exercises, "strength")[:2]
    flexibility = _by_category(exercises, "flexibility")[:2]

    met_min = sum(e.met_value for e in aerobic) / max(len(aerobic), 1) * weekly_min
    # kcal = MET × weight(kg) × hours
    est_kcal = (met_min / 60.0) * weight_kg

    return {
        "frequency": {"aerobic_days": _AEROBIC_DAYS, "strength_days": _STRENGTH_DAYS,
                      "flexibility_days": _FLEX_DAYS},
        "intensity": {"level": level, "target_hr_bpm": [hr_lo, hr_hi]},
        "time": {"aerobic_min_per_session": session_min,
                 "aerobic_min_per_week": weekly_min},
        "type": {"aerobic": _fmt(aerobic), "strength": _fmt(strength),
                 "flexibility": _fmt(flexibility)},
        "volume": {"met_min_per_week": round(met_min),
                   "est_kcal_per_week": round(est_kcal),
                   "volume_factor": factor},
        "progression": (
            "Increase weekly aerobic time by ~10% every 1-2 weeks as tolerated, "
            "toward 150-300 min/week moderate activity (ACSM GETP 11th ed.)."
        ),
    }
