"""How Bangladeshi households actually use each food, read off the recipe dataset.

The food table lists 672 foods, but a table row is not a meal: it holds rice
bran, frog legs, cultivar-level sweet potato leaves and green chilli on equal
footing with rice and lentils, and a per-100 g nutrient score cannot tell them
apart. The 250-recipe dataset can. Every dish records the grams of each food it
uses per serving and how commonly households cook it (weekly_frequency_score,
10 = daily staple), so a food's place in everyday cooking falls out of the
dishes it appears in:

- familiarity: the highest frequency score among the dishes that use it, so
  rice inherits plain boiled rice's 10 and lentils the daily dal's 9;
- meals per week: how many of a week's main meals have the food on the
  plate, from every dish that uses it in a portion-sized amount (see
  meals_per_week) - what "top foods" are ranked by, so the foods households
  eat most often come first;
- typical grams per serving: the median across those dishes, which separates
  ingredients eaten in portions from seasonings used by the gram (green
  chilli, garlic, coriander leaves).

Food-based dietary guidance is built on the foods a population habitually eats
(FAO/WHO 1998, WHO Technical Report Series 880; FPMU, Food Based Dietary
Guidelines for Bangladesh, 2020) - the same rationale src.diet.matcher's
recipe frequency weighting cites.
"""

import re
import statistics
from dataclasses import dataclass

from src.diet.food_db import Food
from src.diet.recipe import Recipe

# Median grams per serving below which a food is a seasoning, not a portion:
# a dish's green chilli or garlic is a few grams, while its smallest real
# vegetable component is several times that.
CONDIMENT_G_PER_SERVING = 10.0

# How many meals a week a dish of each frequency score is eaten at: the
# "meals_per_week_midpoint" column of the recipe workbook's Frequency_Scale
# sheet (data/recipe/raw/Bangladeshi_Recipe_Dataset_250.xlsx): 14 = at most
# main meals, often twice a day; 7 = about once a day; 0.3 = about once a
# month; 0.03 = once or twice a year.
MEALS_PER_WEEK_MIDPOINT = {10: 14.0, 9: 7.0, 8: 5.0, 7: 4.0, 6: 2.5,
                           5: 1.5, 4: 0.7, 3: 0.3, 2: 0.1, 1: 0.03}
# Three main meals a day: a food cannot be eaten at more meals than that.
MAIN_MEALS_PER_WEEK = 21.0


@dataclass(frozen=True)
class FoodHabit:
    familiarity: int | None  # 1-10, from the dishes using the food
    typical_g: float  # median grams per serving across those dishes
    dish_count: int
    meals_per_week: float = 0.0  # main meals a week with the food on the plate


def meals_per_week(dish_meals: list[float]) -> float:
    """Main meals a week at which at least one of these dishes is eaten,
    given how many meals a week each one is. Adding them up would overcount:
    the workbook's HIES_Check sheet notes that its 250 dishes' midpoints sum
    to 28.8 dish-servings a day, because many dishes stand in for one another
    - so onion, in 174 dishes, would be eaten 140 times a week. Each dish is
    instead taken as an independent chance of being at a given meal, and the
    food is eaten at the meals at least one of them is: rice is on the plate
    at 15 of 21 meals, lentils 13, a fish one dish uses 1.5, and nothing
    goes past 21."""
    none_of_them = 1.0
    for meals in dish_meals:
        none_of_them *= 1.0 - min(meals, MAIN_MEALS_PER_WEEK) / MAIN_MEALS_PER_WEEK
    return MAIN_MEALS_PER_WEEK * (1.0 - none_of_them)


def food_habits(recipes: list[Recipe]) -> dict[str, FoodHabit]:
    """food_id -> how households use it. Foods that appear in no dish are
    absent from the map. Only a portion-sized use (CONDIMENT_G_PER_SERVING
    or more per serving) counts as a meal the food is eaten at: a pinch of
    lentil flour in a batter is not a plate of dal."""
    grams: dict[str, list[float]] = {}
    scores: dict[str, list[int]] = {}
    meals: dict[str, list[float]] = {}
    for recipe in recipes:
        servings = recipe.servings or 1
        for food_id, qty_g in recipe.ingredients:
            if qty_g <= 0:
                continue
            grams.setdefault(food_id, []).append(qty_g / servings)
            if recipe.weekly_frequency_score is not None:
                scores.setdefault(food_id, []).append(recipe.weekly_frequency_score)
                if qty_g / servings >= CONDIMENT_G_PER_SERVING:
                    meals.setdefault(food_id, []).append(
                        MEALS_PER_WEEK_MIDPOINT[min(max(recipe.weekly_frequency_score, 1), 10)])
    return {
        food_id: FoodHabit(
            familiarity=max(scores[food_id]) if food_id in scores else None,
            typical_g=statistics.median(per_serving),
            dish_count=len(per_serving),
            meals_per_week=meals_per_week(meals.get(food_id, [])),
        )
        for food_id, per_serving in grams.items()
    }


# Juice is not whole fruit: the WHO counts its sugars as free sugars (WHO
# 2015, Guideline: sugars intake for adults and children).
_JUICE = re.compile(r"\bjuice\b", re.IGNORECASE)

# Fresh fruit only: at most 1.5 kcal/g, the upper bound of "low energy
# density" (CDC 2005, Low-Energy-Dense Foods and Weight Management, after
# Rolls). Every fresh fruit in the table falls under it, banana and mango
# included; tamarind pulp and dried dates (2.4-2.8 kcal/g) do not, and they
# are neither a snack portion nor a fruit serving.
FRESH_FRUIT_MAX_KCAL_PER_100G = 150.0


def _whole_fresh_fruit(food: Food) -> bool:
    return (not _JUICE.search(food.name_en)
            and food.nutrients["kcal"] <= FRESH_FRUIT_MAX_KCAL_PER_100G)


# Aromatics that go into nearly every curry by the spoonful-to-handful: the
# recipe workbook's HIES_Check sheet counts "onion, garlic, ginger and
# chillies" as spices/condiments, not vegetables. Onion passes the gram test
# (a curry's sliced onion is 15-20 g a serving) and is in 174 dishes, so
# without this it would head "top foods" for nearly every patient.
_AROMATIC = re.compile(r"^(onion|garlic|ginger|chilli)\b", re.IGNORECASE)


def habitual_foods(foods: list[Food], habits: dict[str, FoodHabit]) -> list[Food]:
    """The foods worth recommending on their own: whole fruit, which rarely
    shows up as a recipe ingredient, plus every food that households cook
    with in portion-sized amounts. Foods no dish uses (rice bran, frog legs),
    seasonings, cooking aromatics and juices stay in the food table - recipe
    nutrition and the physician's plan editor still use them - but are never
    suggested by themselves."""
    kept = []
    for food in foods:
        if _AROMATIC.match(food.name_en):
            continue
        habit = habits.get(food.food_id)
        if food.food_group == "fruit":
            # fruit no dish uses is eaten as is; fruit dishes use by the
            # spoonful (lemon, tamarind) is a sour seasoning
            eaten_as_fruit = habit is None or habit.typical_g >= CONDIMENT_G_PER_SERVING
            if eaten_as_fruit and _whole_fresh_fruit(food):
                kept.append(food)
        elif habit is not None and habit.typical_g >= CONDIMENT_G_PER_SERVING:
            kept.append(food)
    return kept


# A piece of whole fruit (USDA MyPlate counts ~150 g as a serving; 100 g is a
# small guava or a slice of papaya), for fruit no dish uses.
DEFAULT_PORTION_G = 100.0


def typical_portion_g(food: Food, habits: dict[str, FoodHabit],
                      default_g: float = DEFAULT_PORTION_G) -> float:
    habit = habits.get(food.food_id)
    return habit.typical_g if habit is not None else default_g


def portion_map(foods: list[Food], habits: dict[str, FoodHabit]) -> dict[str, float]:
    """food_id -> grams in a usual portion, for ranking foods by what a
    serving supplies rather than what 100 g does: per 100 g, sesame seeds
    and dried lentils out-score every vegetable, but nobody eats 100 g of
    sesame, and a serving of dal uses about 30 g of dry lentils."""
    return {f.food_id: typical_portion_g(f, habits) for f in foods}


def median_familiarity(recipes: list[Recipe]) -> int | None:
    scores = [r.weekly_frequency_score for r in recipes if r.weekly_frequency_score is not None]
    return round(statistics.median(scores)) if scores else None


def familiarity_map(foods: list[Food], habits: dict[str, FoodHabit],
                    unknown: int | None = None) -> dict[str, int | None]:
    """food_id -> familiarity for ranking. A food no dish uses (in practice
    only whole fruit gets this far) takes `unknown` - the dataset's median
    household frequency - so a fruit nobody cooks with ranks as an ordinary
    food, neither ahead of the rice and lentils households eat daily nor
    behind a once-a-year festive ingredient."""
    return {f.food_id: (habits[f.food_id].familiarity if f.food_id in habits else unknown)
            for f in foods}


def median_meals_per_week(habits: dict[str, FoodHabit]) -> float:
    """The median meals a week across every food some dish uses in a
    portion - the same for every patient, whatever their exclusions."""
    known = [h.meals_per_week for h in habits.values() if h.meals_per_week > 0]
    return statistics.median(known) if known else 0.0


def meals_per_week_map(foods: list[Food], habits: dict[str, FoodHabit],
                       unknown: float = 0.0) -> dict[str, float]:
    """food_id -> main meals a week the food is eaten at, for ranking "top
    foods". A food no dish uses in a portion (in practice whole fruit, which
    the recipe dataset does not cover) takes `unknown` - the median from
    median_meals_per_week - so it ranks as an ordinary food, neither ahead
    of the rice and lentils eaten at most meals nor behind a once-a-year
    festive ingredient, the same rule familiarity_map applies."""
    def meals(food: Food) -> float:
        habit = habits.get(food.food_id)
        return habit.meals_per_week if habit is not None and habit.meals_per_week > 0 else unknown
    return {f.food_id: meals(f) for f in foods}


_PARENTHETICAL = re.compile(r"\s*\([^)]*\)")


def variant_key(food: Food) -> str:
    """One key per everyday food, so the table's preparation and cultivar
    variants collapse: নটে শাক and নটে শাক (সিদ্ধ), or মিষ্টি আলু শাক and its
    (এসপি-৪/৭/৮) cultivars. The Bangla name carries the variant in brackets;
    the English name is the fallback when a row has no Bangla name."""
    if food.name_bn:
        return _PARENTHETICAL.sub("", food.name_bn).strip()
    return food.name_en.split(",")[0].strip().lower()
