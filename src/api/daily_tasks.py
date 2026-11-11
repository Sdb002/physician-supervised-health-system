"""The patient's daily task list: today's meals and exercise from the plan
their physician approved, ticked off one by one, and the streak of days they
finished.

A day's tasks are read off the approved plan (the physician's edited version
when there is one, as the report shows it):

- one task per meal of today's day in the week's meal plan (a one-day plan,
  from before engine 0.4.0, holds the same meals every day);
- one task per exercise group that falls on today in the weekly schedule
  (src.lifestyle.schedule) - none on a rest day.

"Today" is the clinic's calendar day (settings.clinic_utc_offset_hours,
Bangladesh time), not the server's. Only today can be ticked: a past day is
kept as it was left, so the streak is what the patient actually did, day by
day. A day counts toward the streak when every one of its tasks was done.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.models import Approval, Assessment, DailyTaskLog, Visit, utcnow
from src.lifestyle.schedule import WEEK, groups_on

MEALS = ("breakfast", "lunch", "dinner", "snack")
EXERCISE_GROUPS = ("aerobic", "strength", "flexibility", "balance")
# what a meal task shows of each plan line
_MEAL_FIELDS = ("food_id", "recipe_id", "name_en", "name_bn", "qty_g", "servings",
                "serving_size_g", "kcal")
# and of each exercise
_EXERCISE_FIELDS = ("exercise_id", "name_en", "name_bn", "dose", "equipment",
                    "use_easier_version", "easier_version")
RECENT_DAYS = 7


def clinic_today() -> date:
    offset = timedelta(hours=settings.clinic_utc_offset_hours)
    return (datetime.now(timezone.utc) + offset).date()


def clinic_day(moment: datetime) -> date:
    """The clinic's calendar day of a stored timestamp (stored as UTC)."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (moment + timedelta(hours=settings.clinic_utc_offset_hours)).date()


def weekday_of(day: date) -> str:
    # date.weekday(): Monday is 0; WEEK starts on Saturday
    return WEEK[(day.weekday() + 2) % 7]


@dataclass
class ApprovedPlan:
    visit_id: int
    approved_at: datetime
    approved_by: str
    result: dict


def latest_plan(db: Session, patient_id: int) -> ApprovedPlan | None:
    """The patient's most recent visit with an approved plan."""
    row = db.execute(
        select(Visit, Assessment, Approval)
        .join(Assessment, Assessment.visit_id == Visit.id)
        .join(Approval, Approval.assessment_id == Assessment.id)
        .where(Visit.patient_id == patient_id, Approval.decision == "approved")
        .order_by(Visit.id.desc())
    ).first()
    if row is None:
        return None
    visit, assessment, approval = row
    return ApprovedPlan(visit.id, approval.created_at, approval.physician_name,
                        approval.edited_result or assessment.result)


def first_plan_day(db: Session, patient_id: int) -> date | None:
    """The clinic day the patient's first plan was approved: before it a day
    without ticks had nothing to tick, after it a day without ticks was
    missed - whichever plan was current then."""
    first = db.scalar(
        select(Approval.created_at)
        .join(Assessment, Approval.assessment_id == Assessment.id)
        .join(Visit, Assessment.visit_id == Visit.id)
        .where(Visit.patient_id == patient_id, Approval.decision == "approved")
        .order_by(Approval.created_at)
    )
    return clinic_day(first) if first is not None else None


def _meals_of(meal_plan: dict, weekday: str) -> dict[str, list]:
    days = meal_plan.get("days") or []
    if days:
        day = next((d for d in days if d.get("weekday") == weekday), None)
        return (day or {}).get("meals") or {}
    return meal_plan.get("meals") or {}


def tasks_for(result: dict, weekday: str) -> list[dict]:
    """The day's tasks from an approved result, in the order they are done."""
    tasks = []
    meal_plan = (result.get("nutrition") or {}).get("meal_plan") or {}
    if not meal_plan.get("note"):
        meals = _meals_of(meal_plan, weekday)
        for meal in MEALS:
            lines = meals.get(meal) or []
            if lines:
                tasks.append({
                    "key": f"meal:{meal}", "kind": "meal", "group": meal,
                    "items": [{k: line[k] for k in _MEAL_FIELDS if k in line} for line in lines],
                    "kcal": round(sum(line.get("kcal", 0) for line in lines)),
                })
    exercise = result.get("exercise_plan") or {}
    frequency = exercise.get("frequency")
    if frequency and not exercise.get("note"):
        for group in groups_on(frequency, weekday):
            picks = (exercise.get("type") or {}).get(group) or []
            if not picks:
                continue
            task = {
                "key": f"exercise:{group}", "kind": "exercise", "group": group,
                "items": [{k: e[k] for k in _EXERCISE_FIELDS if k in e} for e in picks],
            }
            if group == "aerobic":
                task["minutes"] = (exercise.get("time") or {}).get("aerobic_min_per_session")
            tasks.append(task)
    return tasks


def streaks(complete_days: set[date], today: date) -> tuple[int, int]:
    """(current, best). The current streak runs back from today when today
    is complete, else from yesterday: an unfinished today does not break it
    until the day is over."""
    day = today if today in complete_days else today - timedelta(days=1)
    current = 0
    while day in complete_days:
        current += 1
        day -= timedelta(days=1)
    best = run = 0
    previous = None
    for day in sorted(complete_days):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    return current, max(best, current)


def _log(db: Session, patient_id: int, day: date) -> DailyTaskLog | None:
    return db.scalar(select(DailyTaskLog).where(DailyTaskLog.patient_id == patient_id,
                                                DailyTaskLog.day == day))


def today_view(db: Session, patient_id: int) -> dict:
    """Everything the task page shows: today's tasks with their ticks, the
    count done, the streak and the last week at a glance."""
    today = clinic_today()
    plan = latest_plan(db, patient_id)
    tasks = tasks_for(plan.result, weekday_of(today)) if plan else []
    log = _log(db, patient_id, today)
    done = set(log.done) if log else set()
    for task in tasks:
        task["done"] = task["key"] in done

    logs = db.scalars(select(DailyTaskLog).where(DailyTaskLog.patient_id == patient_id)).all()
    complete = {entry.day for entry in logs if entry.complete}
    by_day = {entry.day: entry for entry in logs}
    current, best = streaks(complete, today)
    first_day = first_plan_day(db, patient_id)
    recent = []
    for back in range(RECENT_DAYS - 1, -1, -1):
        day = today - timedelta(days=back)
        entry = by_day.get(day)
        if entry is not None and entry.complete:
            status = "complete"
        elif day == today:
            status = "today"
        elif entry is not None and entry.done:
            status = "partial"
        elif first_day is not None and day >= first_day:
            status = "missed"
        else:
            status = "none"  # before the patient had a plan
        recent.append({"date": day.isoformat(), "weekday": weekday_of(day), "status": status})

    return {
        "date": today.isoformat(),
        "weekday": weekday_of(today),
        "plan": None if plan is None else {
            "visit_id": plan.visit_id, "approved_at": plan.approved_at,
            "approved_by": plan.approved_by,
        },
        "tasks": tasks,
        "done": sum(task["done"] for task in tasks),
        "total": len(tasks),
        "streak": {"current": current, "best": best},
        "recent": recent,
    }


class UnknownTaskError(LookupError):
    """The key is not one of today's tasks."""


def set_done(db: Session, patient_id: int, key: str, done: bool) -> dict:
    """Tick (or untick) one of today's tasks; the day's row keeps the ticks
    that are still today's tasks, its task count and whether it is complete."""
    today = clinic_today()
    plan = latest_plan(db, patient_id)
    tasks = tasks_for(plan.result, weekday_of(today)) if plan else []
    keys = [task["key"] for task in tasks]
    if key not in keys:
        raise UnknownTaskError(key)
    log = _log(db, patient_id, today)
    if log is None:
        log = DailyTaskLog(patient_id=patient_id, day=today, visit_id=plan.visit_id, done=[])
        db.add(log)
    ticked = set(log.done) & set(keys)
    if done:
        ticked.add(key)
    else:
        ticked.discard(key)
    # a new list, not an in-place change: the JSON column sees a new value
    log.done = [k for k in keys if k in ticked]
    log.visit_id = plan.visit_id
    log.total = len(keys)
    log.complete = bool(keys) and len(ticked) == len(keys)
    log.updated_at = utcnow()
    db.commit()
    return today_view(db, patient_id)
