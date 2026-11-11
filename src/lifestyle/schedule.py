"""Which days of the week each part of the exercise prescription falls on.

The FITT-VP prescription (src.lifestyle.fitt_vp) says how many days a week
each group is done - brisk activity 5, strength 2, stretching 3, balance 3
from 65 - not which days. A daily task list needs the days, so each group's
are spread over the week as evenly as its count allows, starting on a
different day per group so no day carries every group:

- brisk activity on 5 days leaves two rest days apart (Tuesday and Friday);
- the 2 strength days are three days apart, never consecutive: the same
  muscle groups need 48 hours or more between resistance sessions (ACSM's
  Guidelines for Exercise Testing and Prescription, 11th ed., 2021);
- stretching and balance alternate days.

The week runs Saturday to Friday, as the meal plan's does
(src.diet.meal_plan.WEEKDAYS).
"""

WEEK = ("saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday")

# the first day of each group's spread, as an index into WEEK
_START = {"aerobic": 0, "strength": 1, "flexibility": 0, "balance": 1}
_DAYS_KEY = {"aerobic": "aerobic_days", "strength": "strength_days",
             "flexibility": "flexibility_days", "balance": "balance_days"}


def spread_days(days_per_week: int, start: int = 0) -> list[str]:
    """`days_per_week` weekdays as evenly spaced as a 7-day week allows,
    from WEEK[start], in week order."""
    n = max(0, min(int(days_per_week), 7))
    indices = {(i * 7 // n + start) % 7 for i in range(n)} if n else set()
    return [WEEK[i] for i in sorted(indices)]


def weekly_schedule(frequency: dict) -> dict[str, list[str]]:
    """Exercise group -> its weekdays, for the groups the plan has."""
    return {group: spread_days(frequency[key], _START[group])
            for group, key in _DAYS_KEY.items() if frequency.get(key)}


def groups_on(frequency: dict, weekday: str) -> list[str]:
    """The plan's exercise groups that fall on `weekday`, in plan order."""
    return [group for group, days in weekly_schedule(frequency).items() if weekday in days]
