"""FITT-VP exercise prescription (Frequency, Intensity, Time, Type, Volume,
Progression) per ACSM's Guidelines for Exercise Testing and Prescription,
11th ed.: >=150 min/week moderate aerobic activity, resistance training on
>=2 days/week, flexibility work >=2-3 days/week, and for adults 65 and over
balance (neuromotor) training on 3 days a week (WHO guidelines on physical
activity and sedentary behaviour, 2020: varied multicomponent activity
emphasising functional balance and strength on 3 or more days a week).

Callers must pass exercises that already went through the contraindication
gate (src.clinical.contraindication.filter_items). Within each group the
plannable ones (src.lifestyle.ranking.plannable) are ranked by the trained
exercise model when one is present, otherwise by the deterministic formula
(src.lifestyle.recommender.score), and picked for variety: no two from the
same body region, and the strength exercises spread over the lower body,
the upper body and the trunk before a second one comes from any of them.
"""

import re

from src.lifestyle import recommender
from src.lifestyle.exercise_db import PLAN_GROUPS, Exercise
from src.lifestyle.intensity import target_hr_range, volume_factor
from src.lifestyle.ranking import ExerciseContext, context_for, needs_modification, plannable

_BASE_WEEKLY_AEROBIC_MIN = 150
_AEROBIC_DAYS = 5
_STRENGTH_DAYS = 2
_FLEX_DAYS = 3
_BALANCE_DAYS = 3  # 65 and over (WHO 2020); not planned below that age

# how many exercises each group of the plan lists
PICKS = {"aerobic": 2, "strength": 4, "flexibility": 3, "balance": 3}

# strength picks cover each of these before repeating one
_BODY_AREAS = {
    "thigh": "lower", "hip/glutes": "lower", "calf": "lower", "ankle/foot": "lower",
    "chest": "upper", "shoulder": "upper", "arm (biceps/triceps)": "upper",
    "upper back": "upper", "forearm/wrist/hand": "upper", "neck": "upper",
    "core/abdomen/waist": "trunk", "lower back": "trunk", "full body": "whole",
}


_CITATION = re.compile(r"\s*\[[^\]]*\]")
_LEFT_BLANK = re.compile(r"\s*\((?:(?:the )?(?:source|leaflet) leaves (?:them|it) blank|"
                         r"left blank in the leaflet)\)")
# a clause about the source rather than the exercise
_ABOUT_THE_SOURCE = re.compile(r"\bsource\b|page gives|Compendium|\bleaflet\b")


def patient_dose(exercise: Exercise) -> str:
    """The dataset's dose as a patient reads it. The source text is written
    for whoever curates the dataset: it cites ("10-15 reps [CCG]"), says what
    the source left out ("reps set by the clinician (source leaves them
    blank)", "ACE page gives no dose; general guideline: ...") and, for an
    aerobic activity, quotes the Compendium. An aerobic activity has no dose
    line: its minutes are the prescription's. The source's text stays on the
    plan as dose_source."""
    if exercise.category == "aerobic":
        return ""
    text = _LEFT_BLANK.sub("", _CITATION.sub("", exercise.dose))
    clauses = []
    for clause in (c.strip() for c in text.split(";")):
        clause = re.sub(r"^general guideline:\s*", "", clause)
        if clause and not _ABOUT_THE_SOURCE.search(clause):
            clauses.append(re.sub(r">=\s*", "at least ", clause))
    return "; ".join(clauses)


def exercise_entry(exercise: Exercise, ctx: ExerciseContext | None = None) -> dict:
    """One exercise as the plan lists it. With the patient's context, the
    notes for their conditions and whether they should start with the easier
    version (shared with the physician's plan editor, so an edited plan reads
    the same)."""
    flagged = needs_modification(exercise, ctx) if ctx else []
    conditions = ctx.conditions if ctx else frozenset()
    return {
        "exercise_id": exercise.exercise_id,
        "name_en": exercise.name_en,
        "name_bn": exercise.name_bn,
        "category": exercise.category,
        "met_value": exercise.met_value,
        "intensity_level": exercise.intensity_level,
        "fitness_level": exercise.fitness_level,
        "equipment": exercise.equipment,
        "dose": patient_dose(exercise),
        "dose_source": exercise.dose,
        "how_to": exercise.how_to,
        "easier_version": exercise.easier_version,
        "safety_notes": exercise.safety_notes,
        # the dataset's note for each of the patient's conditions it has one
        # for: the "modify" ones say what to change, the others how it helps
        "condition_notes": [
            {"condition": c, "note": exercise.notes[c], "modify": c in exercise.modify_for}
            for c in sorted(conditions) if exercise.notes.get(c)
        ],
        "use_easier_version": "older_adult" in flagged,
        "video": ({"url": exercise.video_url, "title": exercise.video_title,
                   "channel": exercise.video_channel, "match": exercise.video_match}
                  if exercise.video_url else None),
        "source": {"name": exercise.source, "url": exercise.source_url},
    }


def _pick(ranked: list[Exercise], group: str) -> list[Exercise]:
    """The top PICKS[group] of a ranked list, at most one per body region
    for strength and flexibility work (aerobic activities are mostly whole-
    body and balance exercises mostly ankle-and-hip work, so there only the
    exercise must differ); strength picks take the best of the lower body,
    the upper body and the trunk first."""
    n = PICKS[group]
    picked: list[Exercise] = []
    if group == "strength":
        for area in ("lower", "upper", "trunk"):
            best = next((e for e in ranked if _BODY_AREAS.get(e.body_region) == area), None)
            if best is not None:
                picked.append(best)
        picked.sort(key=ranked.index)
    regions = {e.body_region for e in picked}
    one_per_region = group in ("strength", "flexibility")
    for exercise in ranked:
        if len(picked) >= n:
            break
        if exercise in picked or (one_per_region and exercise.body_region in regions):
            continue
        picked.append(exercise)
        regions.add(exercise.body_region)
    return picked[:n]


def rank_group(exercises: list[Exercise], ctx: ExerciseContext, group: str) -> list[Exercise]:
    """The plannable exercises of one group, best first (ties by id)."""
    candidates = [e for e in exercises if e.category == group and plannable(e, ctx)]
    scores = recommender.score(candidates, ctx)
    order = sorted(zip(candidates, scores), key=lambda pair: (-pair[1], pair[0].exercise_id))
    return [e for e, _ in order]


def build_fitt_plan(age: int, sex: str, weight_kg: float, bmi_category: str,
                    fitness_level: str, overall_risk: str,
                    exercises: list[Exercise], conditions=()) -> dict:
    """`conditions` are the patient's condition keys: the ranking reads the
    ones the exercise dataset rates (pregnancy, hypertension, diabetes,
    anaemia, knee osteoarthritis) and each pick carries their notes."""
    if not exercises:
        return {"note": "exercise database is empty — add data/lifestyle/exercises.csv"}

    ctx = context_for(age, sex, conditions, fitness_level, overall_risk, bmi_category)
    level = ctx.start_level
    factor = volume_factor(age, bmi_category, ctx.fitness_level, sex)
    weekly_min = round(_BASE_WEEKLY_AEROBIC_MIN * factor / 10) * 10
    session_min = max(round(weekly_min / _AEROBIC_DAYS / 5) * 5, 10)
    hr_lo, hr_hi = target_hr_range(age, level)

    picks = {group: _pick(rank_group(exercises, ctx, group), group)
             for group in PLAN_GROUPS if group != "balance" or ctx.older}
    aerobic = picks["aerobic"]
    met_min = sum(e.met_value for e in aerobic) / max(len(aerobic), 1) * weekly_min
    # kcal = MET × weight(kg) × hours
    est_kcal = (met_min / 60.0) * weight_kg

    frequency = {"aerobic_days": _AEROBIC_DAYS, "strength_days": _STRENGTH_DAYS,
                 "flexibility_days": _FLEX_DAYS}
    if ctx.older:
        frequency["balance_days"] = _BALANCE_DAYS

    return {
        "frequency": frequency,
        "intensity": {"level": level, "target_hr_bpm": [hr_lo, hr_hi]},
        "time": {"aerobic_min_per_session": session_min,
                 "aerobic_min_per_week": weekly_min},
        "type": {group: [exercise_entry(e, ctx) for e in chosen]
                 for group, chosen in picks.items()},
        "volume": {"met_min_per_week": round(met_min),
                   "est_kcal_per_week": round(est_kcal),
                   "volume_factor": factor},
        "progression": (
            "Increase weekly aerobic time by ~10% every 1-2 weeks as tolerated, "
            "toward 150-300 min/week moderate activity (ACSM GETP 11th ed.)."
        ),
        "scoring_backend": recommender.active_backend(),
    }
