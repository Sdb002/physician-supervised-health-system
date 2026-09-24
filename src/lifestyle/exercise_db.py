"""Loader for data/lifestyle/exercises.csv. Tolerant of empty/missing file."""

import csv
from dataclasses import dataclass, field
from pathlib import Path

from src.core.config import DATA_DIR

EXERCISES_CSV = DATA_DIR / "lifestyle" / "exercises.csv"


@dataclass(frozen=True)
class Exercise:
    exercise_id: str
    name_en: str
    name_bn: str
    category: str  # aerobic | strength | flexibility
    met_value: float
    equipment: str
    intensity_level: str  # light | moderate | vigorous
    tags: tuple = field(default_factory=tuple)  # contra_tags — checked by the gate
    source: str = ""


def load_exercises(path: Path | None = None) -> list[Exercise]:
    path = path or EXERCISES_CSV
    if not path.exists():
        return []
    exercises: list[Exercise] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not (row.get("exercise_id") or "").strip():
                continue
            exercises.append(Exercise(
                exercise_id=row["exercise_id"].strip(),
                name_en=row["name_en"].strip(),
                name_bn=(row.get("name_bn") or "").strip(),
                category=(row.get("category") or "aerobic").strip(),
                met_value=float(row["met_value"]),
                equipment=(row.get("equipment") or "none").strip(),
                intensity_level=(row.get("intensity_level") or "moderate").strip(),
                tags=tuple(t.strip() for t in (row.get("contra_tags") or "").split("|") if t.strip()),
                source=(row.get("source") or "").strip(),
            ))
    return exercises
