"""Hard safety gate: conditions → excluded tags → filtered items.

Rules live in data/reference/contraindications.yaml (cited per condition).
This gate runs before any ranking or planning, and its exclusions can never be
overridden downstream — an item carrying an excluded tag simply does not exist
for the rest of the pipeline.
"""

from dataclasses import dataclass
from functools import lru_cache

from src.core.config import REFERENCE_DIR, load_yaml


@dataclass(frozen=True)
class ExclusionSet:
    food_tags: frozenset[str]
    exercise_tags: frozenset[str]
    applied_conditions: tuple[str, ...]


@lru_cache(maxsize=1)
def _rules() -> dict:
    return load_yaml(REFERENCE_DIR / "contraindications.yaml")["conditions"]


def known_conditions() -> list[str]:
    return list(_rules().keys())


def excluded_tags(conditions: list[str]) -> ExclusionSet:
    """Union of exclusions for every recognized condition. Unknown condition
    keys are ignored (they carry no rules, so nothing can be excluded)."""
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
    return ExclusionSet(frozenset(food), frozenset(exercise), tuple(applied))


def is_allowed(item_tags: list[str] | set[str], excluded: frozenset[str]) -> bool:
    return not (set(item_tags) & excluded)


def filter_items(items: list, excluded: frozenset[str]) -> list:
    """Keep items whose .tags do not intersect the excluded set. Works for any
    object exposing a `tags` attribute (Food, Recipe, Exercise)."""
    return [item for item in items if is_allowed(item.tags, excluded)]
