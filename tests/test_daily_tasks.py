"""The patient's daily task list: today's meals and exercise from the
approved plan, ticks, and the streak of complete days."""

from datetime import date, timedelta

import pytest

from src.api import daily_tasks
from src.api.daily_tasks import streaks, tasks_for, weekday_of
from src.lifestyle.schedule import WEEK, groups_on, spread_days, weekly_schedule

NO_AUTH = {"Authorization": ""}
PATIENT = {
    "name": "Rahim Uddin", "email": "rahim@example.com", "password": "secret-pass-2",
    "role": "patient", "profile": {"sex": "male", "birth_year": 1980, "height_cm": 168},
}
# a Saturday, the first day of the plan's week
SATURDAY = date(2026, 11, 7)


# --- the weekly exercise schedule -------------------------------------------

def test_days_are_spread_over_the_week():
    assert spread_days(5) == ["saturday", "sunday", "monday", "wednesday", "thursday"]
    assert spread_days(3) == ["saturday", "monday", "wednesday"]
    assert spread_days(7) == list(WEEK)
    assert spread_days(0) == []


def test_strength_days_are_never_consecutive():
    # ACSM: 48 h or more between resistance sessions for the same muscles
    for days in (1, 2, 3):
        indices = [WEEK.index(d) for d in weekly_schedule({"strength_days": days})["strength"]]
        gaps = [(b - a) % 7 for a, b in zip(indices, indices[1:] + indices[:1])] if days > 1 else [7]
        assert min(gaps) >= 2, (days, indices)


def test_each_group_gets_its_days_a_week():
    frequency = {"aerobic_days": 5, "strength_days": 2, "flexibility_days": 3, "balance_days": 3}
    schedule = weekly_schedule(frequency)
    assert {g: len(d) for g, d in schedule.items()} == {
        "aerobic": 5, "strength": 2, "flexibility": 3, "balance": 3}
    assert sum(len(groups_on(frequency, day)) for day in WEEK) == 13
    # no balance training below 65: the plan has no balance days
    assert "balance" not in weekly_schedule({"aerobic_days": 5})


def test_weekdays_follow_the_plans_week():
    assert weekday_of(SATURDAY) == "saturday"
    assert weekday_of(SATURDAY + timedelta(days=6)) == "friday"


# --- tasks and streaks ---------------------------------------------------------

_RESULT = {
    "nutrition": {"meal_plan": {"days": [
        {"weekday": "saturday", "meals": {
            "breakfast": [{"recipe_id": "BDR-010", "name_en": "Ruti", "name_bn": "রুটি",
                           "qty_g": 108, "servings": 1, "kcal": 290}],
            "lunch": [{"recipe_id": "BDR-001", "name_en": "Rice", "name_bn": "ভাত",
                       "qty_g": 122, "servings": 0.5, "kcal": 160},
                      {"food_id": "F233", "name_en": "Potato", "name_bn": "আলু", "qty_g": 80,
                       "kcal": 54}],
            "snack": [{"food_id": "F500", "name_en": "Guava", "name_bn": "পেয়ারা",
                       "qty_g": 100, "kcal": 51}]}},
        {"weekday": "tuesday", "meals": {"dinner": [{"name_en": "Dal", "name_bn": "ডাল",
                                                     "qty_g": 200, "kcal": 120}]}},
    ]}},
    "exercise_plan": {
        "frequency": {"aerobic_days": 5, "strength_days": 2, "flexibility_days": 3},
        "time": {"aerobic_min_per_session": 30},
        "type": {"aerobic": [{"exercise_id": "E1", "name_en": "Brisk walking", "name_bn": "দ্রুত হাঁটা",
                              "met_value": 3.5, "equipment": "none"}],
                 "strength": [{"exercise_id": "E2", "name_en": "Chair squat", "name_bn": "চেয়ার স্কোয়াট",
                               "dose": "2 sets of 10", "equipment": "household item"}],
                 "flexibility": [{"exercise_id": "E3", "name_en": "Calf stretch", "name_bn": "পায়ের স্ট্রেচ",
                                  "dose": "hold 30 s", "equipment": "none"}]},
    },
}


def test_a_days_tasks_are_its_meals_then_its_exercise():
    tasks = tasks_for(_RESULT, "saturday")
    assert [t["key"] for t in tasks] == ["meal:breakfast", "meal:lunch", "meal:snack",
                                        "exercise:aerobic", "exercise:flexibility"]
    lunch = tasks[1]
    assert [i["name_en"] for i in lunch["items"]] == ["Rice", "Potato"] and lunch["kcal"] == 214
    assert tasks[3]["minutes"] == 30
    # Tuesday is a rest day from brisk activity: its only task is the meal
    assert [t["key"] for t in tasks_for(_RESULT, "tuesday")] == ["meal:dinner"]
    # Sunday: strength and brisk activity, and no meals in this plan
    assert [t["key"] for t in tasks_for(_RESULT, "sunday")] == ["exercise:aerobic",
                                                               "exercise:strength"]


def test_a_one_day_plan_holds_the_same_meals_every_day():
    one_day = {"nutrition": {"meal_plan": {"meals": {"lunch": [{"name_en": "Rice", "qty_g": 100}]}}}}
    for weekday in WEEK:
        assert [t["key"] for t in tasks_for(one_day, weekday)] == ["meal:lunch"]


def test_streaks_count_back_from_today_or_yesterday():
    today = SATURDAY
    days = {today - timedelta(days=n) for n in (1, 2, 3, 6, 7)}
    # today not done yet: the streak still stands on yesterday
    assert streaks(days, today) == (3, 3)
    assert streaks(days | {today}, today) == (4, 4)
    # yesterday missed: it is broken, the best is kept
    assert streaks({today - timedelta(days=n) for n in (2, 3, 4, 5)}, today) == (0, 4)
    assert streaks(set(), today) == (0, 0)


# --- through the API -----------------------------------------------------------

@pytest.fixture()
def patient(client):
    """A patient with a login and an approved plan; returns their headers."""
    reg = client.post("/auth/register", json=PATIENT, headers=NO_AUTH).json()
    token = client.post("/auth/login", json={"email": PATIENT["email"],
                                             "password": PATIENT["password"]},
                        headers=NO_AUTH).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assessment = client.post(f"/patients/{reg['patient_id']}/visits", json={
        "weight_kg": 72, "biomarkers": {"fasting_glucose": 130, "hemoglobin": 13.5}}).json()
    client.post(f"/review/{assessment['id']}/decision",
                json={"decision": "approved", "physician_name": "Dr Test"})
    return headers


def _on(monkeypatch, day: date) -> None:
    monkeypatch.setattr(daily_tasks, "clinic_today", lambda: day)


def _tick_all(client, headers) -> dict:
    view = client.get("/me/tasks", headers=headers).json()
    for task in view["tasks"]:
        view = client.put(f"/me/tasks/{task['key']}", json={"done": True}, headers=headers).json()
    return view


def test_a_patient_ticks_off_the_day_and_builds_a_streak(client, patient, monkeypatch):
    _on(monkeypatch, SATURDAY)
    view = client.get("/me/tasks", headers=patient).json()
    keys = [t["key"] for t in view["tasks"]]
    # Saturday: the week's first day of meals, brisk activity and stretching
    assert keys[:4] == ["meal:breakfast", "meal:lunch", "meal:dinner", "meal:snack"]
    assert {"exercise:aerobic", "exercise:flexibility"} <= set(keys)
    assert view["done"] == 0 and view["total"] == len(keys)
    assert view["streak"] == {"current": 0, "best": 0}
    assert view["recent"][-1] == {"date": "2026-11-07", "weekday": "saturday", "status": "today"}

    # one tick: counted, and not yet a complete day
    view = client.put("/me/tasks/meal:breakfast", json={"done": True}, headers=patient).json()
    assert view["done"] == 1 and view["tasks"][0]["done"] is True
    assert view["streak"]["current"] == 0
    # untick works too
    view = client.put("/me/tasks/meal:breakfast", json={"done": False}, headers=patient).json()
    assert view["done"] == 0

    view = _tick_all(client, patient)
    assert view["done"] == view["total"]
    assert view["streak"] == {"current": 1, "best": 1}
    assert view["recent"][-1]["status"] == "complete"

    # Sunday, nothing ticked yet: the streak stands on Saturday
    _on(monkeypatch, SATURDAY + timedelta(days=1))
    view = client.get("/me/tasks", headers=patient).json()
    assert view["weekday"] == "sunday" and view["streak"]["current"] == 1
    view = _tick_all(client, patient)
    assert view["streak"] == {"current": 2, "best": 2}

    # Monday half done, Tuesday: Monday broke the streak, the best is kept
    _on(monkeypatch, SATURDAY + timedelta(days=2))
    client.put("/me/tasks/meal:lunch", json={"done": True}, headers=patient)
    _on(monkeypatch, SATURDAY + timedelta(days=3))
    view = client.get("/me/tasks", headers=patient).json()
    assert view["streak"] == {"current": 0, "best": 2}
    assert [d["status"] for d in view["recent"][-4:]] == ["complete", "complete", "partial", "today"]


def test_only_todays_tasks_can_be_ticked(client, patient, monkeypatch):
    _on(monkeypatch, SATURDAY + timedelta(days=3))  # Tuesday: no strength
    assert client.put("/me/tasks/exercise:strength", json={"done": True},
                      headers=patient).status_code == 404
    assert client.put("/me/tasks/meal:supper", json={"done": True},
                      headers=patient).status_code == 404


def test_no_plan_no_tasks_and_staff_cannot_use_it(client):
    reg = client.post("/auth/register", json=PATIENT, headers=NO_AUTH)
    assert reg.status_code in (200, 201)
    token = client.post("/auth/login", json={"email": PATIENT["email"],
                                             "password": PATIENT["password"]},
                        headers=NO_AUTH).json()["token"]
    view = client.get("/me/tasks", headers={"Authorization": f"Bearer {token}"}).json()
    assert view["plan"] is None and view["tasks"] == [] and view["total"] == 0
    assert {d["status"] for d in view["recent"]} <= {"none", "today"}
    # the doctor's own token is not a patient's
    assert client.get("/me/tasks").status_code == 403
