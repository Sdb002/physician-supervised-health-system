"""Which exercises suit a patient, and in what order: the deterministic
formula the prescription ranks with when no trained exercise model is
present (src/lifestyle/recommender.py), and the patient context both score
for.

The safety gate (src.clinical.contraindication) has already removed what the
patient's conditions, age and sex rule out. What is left is ranked inside
each group of the prescription (aerobic, strength, flexibility, balance), so
the formula only has to order exercises of one kind against each other:

    1.0
    - MODIFY_PENALTY  for each of the patient's conditions the dataset rates
                      "modify" (allowed with care; the plan shows its note)
    - MODIFY_PENALTY  for an exercise suitable at 65 and over only in its
                      easier version, for a patient that age
    - LEVEL_STEP      for each fitness level the exercise is below the
                      patient's (a beginner's exercise for an advanced patient
                      still counts, but less)
    - EQUIPMENT_COST  when it needs equipment that has to be bought (a band,
                      dumbbells); household items (a chair, a towel, a water
                      bottle) cost nothing
    + DOSE_BONUS      when its source gives a dose, not only instructions
                      (not for aerobic activities: their minutes come from
                      the prescription, whatever the source says)
    + VIDEO_BONUS     for a demonstration video (half for a close variant)
"""

from dataclasses import dataclass

from src.clinical.contraindication import patient_populations
from src.lifestyle.exercise_db import FITNESS_LEVELS, PLAN_GROUPS, RATED_CONDITIONS, Exercise
from src.lifestyle.intensity import starting_level

MODIFY_PENALTY = 0.5
LEVEL_STEP = 0.25
EQUIPMENT_COST = 0.3
DOSE_BONUS = 0.2
VIDEO_BONUS = {"exact": 0.1, "close variant": 0.05}

# aerobic intensity the plan may prescribe at each starting level
# (intensity.starting_level): vigorous work is never prescribed automatically
AEROBIC_LEVELS = {"light": ("light", "moderate"), "moderate": ("moderate",)}


@dataclass(frozen=True)
class ExerciseContext:
    """What the ranking knows about a patient."""
    age: int
    sex: str
    conditions: frozenset      # the RATED_CONDITIONS the patient has
    fitness_level: str         # beginner | intermediate | advanced
    start_level: str           # light | moderate
    obese: bool
    older: bool                # under the older_adult population rule (65+)

    @property
    def level_cap(self) -> int:
        """The hardest fitness level the plan picks from: the patient's own,
        or beginner when the plan starts light (a beginner, or any high or
        critical biomarker risk)."""
        if self.start_level == "light":
            return 0
        return FITNESS_LEVELS.index(self.fitness_level)


def context_for(age: int, sex: str, conditions, fitness_level: str, overall_risk: str,
                bmi_category: str) -> ExerciseContext:
    fitness = fitness_level if fitness_level in FITNESS_LEVELS else "beginner"
    return ExerciseContext(
        age=age, sex=sex,
        conditions=frozenset(c for c in conditions if c in RATED_CONDITIONS),
        fitness_level=fitness,
        start_level=starting_level(fitness, overall_risk),
        obese=bmi_category == "obese",
        older="older_adult" in patient_populations(age, sex),
    )


def plannable(exercise: Exercise, ctx: ExerciseContext) -> bool:
    """Whether the prescription may pick this (gate-allowed) exercise for the
    patient: a planned kind (balance from 65), something done at home, no
    harder than the level cap, and for an aerobic exercise a Compendium MET
    (its minutes are counted) at an intensity the starting level allows."""
    if exercise.category not in PLAN_GROUPS:
        return False
    if exercise.category == "balance" and not ctx.older:
        return False
    if not exercise.home_feasible or exercise.level_rank > ctx.level_cap:
        return False
    if exercise.category == "aerobic":
        return (exercise.met_value is not None
                and exercise.intensity_level in AEROBIC_LEVELS[ctx.start_level])
    return True


def needs_modification(exercise: Exercise, ctx: ExerciseContext) -> list[str]:
    """The patient's conditions this exercise is rated "modify" for, and
    "older_adult" when it is suitable at their age only in its easier version."""
    found = [c for c in exercise.modify_for if c in ctx.conditions]
    if ctx.older and exercise.older_adult == "modify":
        found.append("older_adult")
    return found


def baseline_score(exercise: Exercise, ctx: ExerciseContext) -> float:
    score = 1.0
    score -= MODIFY_PENALTY * len(needs_modification(exercise, ctx))
    score -= LEVEL_STEP * max(0, ctx.level_cap - exercise.level_rank)
    if exercise.needs_equipment:
        score -= EQUIPMENT_COST
    if exercise.category != "aerobic" and exercise.source_detail == "instructions and dose":
        score += DOSE_BONUS
    score += VIDEO_BONUS.get(exercise.video_match, 0.0)
    return score
