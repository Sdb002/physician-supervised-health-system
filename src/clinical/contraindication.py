"""Hard safety gate: conditions and dietary restrictions → excluded tags →
filtered items.

Clinical rules live in data/reference/contraindications.yaml (cited per
condition); what a patient does not eat for faith, choice or allergy lives in
data/reference/dietary_restrictions.yaml. This gate runs before any ranking or
planning, and its exclusions can never be overridden downstream — an item
carrying an excluded tag simply does not exist for the rest of the pipeline.
"""

from dataclasses import dataclass
from functools import lru_cache

from src.core.config import REFERENCE_DIR, load_yaml


@dataclass(frozen=True)
class ExclusionSet:
    food_tags: frozenset[str]
    exercise_tags: frozenset[str]
    applied_conditions: tuple[str, ...]
    applied_restrictions: tuple[str, ...] = ()
    applied_populations: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def _rules() -> dict:
    return load_yaml(REFERENCE_DIR / "contraindications.yaml")["conditions"]


@lru_cache(maxsize=1)
def _populations() -> dict:
    return load_yaml(REFERENCE_DIR / "contraindications.yaml").get("populations") or {}


def patient_populations(age: int | None, sex: str | None) -> list[str]:
    """The population rules (contraindications.yaml `populations`) a patient
    of this age and sex falls under: older_adult from its min_age, and
    their sex."""
    applied = []
    for key, rule in _populations().items():
        if "min_age" in rule:
            if age is not None and age >= rule["min_age"]:
                applied.append(key)
        elif key == sex:
            applied.append(key)
    return applied


@lru_cache(maxsize=1)
def _restrictions() -> dict:
    return load_yaml(REFERENCE_DIR / "dietary_restrictions.yaml")["restrictions"]


def known_conditions() -> list[str]:
    return list(_rules().keys())


def condition_food_tags(condition: str) -> tuple[str, ...]:
    """The food tags one condition excludes on its own (empty for a
    condition with no food rule, or an unknown key) - what the gate leaves
    out because of that condition, for telling the patient what to avoid."""
    rule = _rules().get(condition) or {}
    return tuple(rule.get("exclude_food_tags") or ())


def known_restrictions() -> list[str]:
    return list(_restrictions().keys())


def excluded_tags(conditions: list[str],
                  restrictions: list[str] | tuple[str, ...] = (), *,
                  age: int | None = None, sex: str | None = None) -> ExclusionSet:
    """Union of exclusions for every recognized condition and dietary
    restriction, and for the patient's age and sex when given (exercises
    not for adults 65 and over, or written for the other sex). Unknown keys
    are ignored (they carry no rules, so nothing can be excluded)."""
    food: set[str] = set()
    exercise: set[str] = set()
    applied: list[str] = []
    for cond in conditions:
        rule = _rules().get(cond)
        if rule is None:
            continue
        food.update(rule.get("exclude_food_tags") or [])
        exercise.update(rule.get("exclude_exercise_tags") or [])
        applied.append(cond)
    kept: list[str] = []
    for restriction in restrictions:
        rule = _restrictions().get(restriction)
        if rule is None:
            continue
        food.update(rule.get("exclude_food_tags") or [])
        kept.append(restriction)
    populations = patient_populations(age, sex)
    for population in populations:
        exercise.update(_populations()[population].get("exclude_exercise_tags") or [])
    return ExclusionSet(frozenset(food), frozenset(exercise), tuple(applied), tuple(kept),
                        tuple(populations))


def is_allowed(item_tags: list[str] | set[str], excluded: frozenset[str]) -> bool:
    return not (set(item_tags) & excluded)


def filter_items(items: list, excluded: frozenset[str]) -> list:
    """Keep items whose .tags do not intersect the excluded set. Works for any
    object exposing a `tags` attribute (Food, Recipe, Exercise)."""
    return [item for item in items if is_allowed(item.tags, excluded)]
