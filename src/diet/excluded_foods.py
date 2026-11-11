"""The foods and dishes one patient does not eat.

The dietary restrictions (data/reference/dietary_restrictions.yaml) cover what
whole groups of people leave out: beef, eggs, nuts. This is the rest - the one
fish a patient is allergic to, the gourd they will not touch, a dish they
cannot stand. They are picked from the food table and the recipe list, kept
on the patient, and applied with the hard gate (src/clinical/contraindication.py):
what is excluded here is never ranked, planned or offered to the plan editor.

A food is left out in every form the table lists it in - raw and boiled, each
cultivar and species, and every row named as a form of it (see
_everyday_foods: the milled and the boiled rices are one food, and "Egg,
chicken" takes the boiled egg and the yolk with it) - together with every
dish that uses any of them in any amount. As with an allergy, presence is
what counts.

An entry keeps the name of the table row it was chosen as (`source_name`)
beside its id. Ids are row numbers of the food table and the recipe list:
when a dataset is replaced, an id can come to mean a different food. An
exclusion that silently moved to another food is worse than one reported as
lost, so an entry whose id no longer carries its name is looked up by name,
and failing that is reported as missing.
"""

from dataclasses import dataclass

from src.diet.food_db import Food, display_name
from src.diet.habits import variant_key
from src.diet.recipe import Recipe

MAX_EXCLUDED = 200


@dataclass(frozen=True)
class OwnExclusions:
    """What one patient's entries exclude from the tables as they are now."""
    items: tuple[dict, ...]         # the entries still found, as recorded
    food_ids: frozenset[str]        # every form of every excluded food
    recipe_ids: frozenset[str]      # the excluded dishes, and every dish using an excluded food
    missing: tuple[str, ...]        # names of entries the tables no longer have

    def allows(self, item) -> bool:
        return (getattr(item, "food_id", None) not in self.food_ids
                and getattr(item, "recipe_id", None) not in self.recipe_ids)


NO_EXCLUSIONS = OwnExclusions((), frozenset(), frozenset(), ())


@dataclass(frozen=True, eq=False)
class _EverydayFood:
    """One food as a patient would name it, and the table rows it stands for."""
    name: str                   # "Rice", "Egg, chicken"
    shown: Food                 # the row it is identified by: the one most dishes use
    rows: tuple[Food, ...]      # its preparations and cultivars, in table order
    covered: tuple[Food, ...]   # those, and every other row named as a form of it


def _name_parts(food: Food) -> list[str]:
    """A row's name in its comma-separated parts, as a person would say it:
    "Rice, BR-28, boiled (without salt)" is Rice / BR-28 / boiled."""
    return [part.strip() for part in display_name(food.name_en).split(",")]


def _shared_parts(rows: list[Food]) -> list[str]:
    """The leading name parts every row has: Rice for the milled rices, Egg /
    chicken for farmed and native. None when the names start differently
    (the prawns and the one shrimp)."""
    shared = []
    for parts in zip(*map(_name_parts, rows)):
        if len(set(parts)) > 1:
            break
        shared.append(parts[0])
    return shared


def _dishes_by_food(recipes: list[Recipe]) -> dict[str, set[str]]:
    """food_id -> the dishes that use that row, in any amount."""
    dishes: dict[str, set[str]] = {}
    for recipe in recipes:
        for food_id, _ in recipe.ingredients:
            dishes.setdefault(food_id, set()).add(recipe.recipe_id)
    return dishes


def _everyday_foods(foods: list[Food], dishes: dict[str, set[str]]) -> list[_EverydayFood]:
    """The food table as the foods a patient would name, in table order.

    Rows are one food when habits.variant_key says so (one Bangla name, its
    bracketed variety taken off: the eleven milled rices, the seven prawns),
    and so are two such groups that come out under the same name - the milled
    rices (চাল) and the boiled rices (ভাত) are both "Rice". A food is
    identified by the row most dishes use (the rice households cook, not the
    first cultivar in the table) and named by what its rows' names share;
    rows with nothing in common keep the identifying row's name.

    A food also covers every other row named as a form of it: "Egg, chicken"
    takes "Egg, chicken, native, boiled" and the yolk, "Milk, cow" the milk
    powders, "Rice" the puffed rice. Those rows stay foods of their own as
    well, for the patient who eats rice but not puffed rice."""
    groups: dict[str, list[Food]] = {}
    for food in foods:
        groups.setdefault(variant_key(food), []).append(food)
    named: dict[str, list[Food]] = {}
    for key, rows in groups.items():
        shared = ", ".join(_shared_parts(rows)).casefold()
        # rows with no name in common are merged with nothing
        named.setdefault(shared or f"\0{key}", []).extend(rows)

    by_first_part: dict[str, list[tuple[list[str], Food]]] = {}
    for food in foods:
        parts = [part.casefold() for part in _name_parts(food)]
        by_first_part.setdefault(parts[0], []).append((parts, food))

    everyday = []
    for rows in named.values():
        shown = max(rows, key=lambda f: len(dishes.get(f.food_id, ())))  # the first row wins a tie
        name_parts = _shared_parts(rows) or _name_parts(shown)
        prefix = [part.casefold() for part in name_parts]
        own = {f.food_id for f in rows}
        forms_of_it = [f for parts, f in by_first_part.get(prefix[0], [])
                       if parts[:len(prefix)] == prefix and f.food_id not in own]
        everyday.append(_EverydayFood(", ".join(name_parts), shown, tuple(rows),
                                      tuple(rows + forms_of_it)))
    return everyday


def _by_row(everyday: list[_EverydayFood]) -> dict[str, _EverydayFood]:
    """food_id -> the everyday food that row is."""
    return {f.food_id: food for food in everyday for f in food.rows}


def _food_entry(food: _EverydayFood) -> dict:
    return {
        "id": food.shown.food_id, "kind": "food", "name_en": food.name,
        # the Bangla name without its bracketed variety, when the row has one
        "name_bn": variant_key(food.shown) if food.shown.name_bn else "",
        "source_name": food.shown.name_en,
    }


def _dish_entry(recipe: Recipe) -> dict:
    return {"id": recipe.recipe_id, "kind": "recipe", "name_en": recipe.name_en,
            "name_bn": recipe.name_bn, "source_name": recipe.name_en}


def catalogue(foods: list[Food], recipes: list[Recipe]) -> list[dict]:
    """Everything that can be excluded, for a picker: every dish, then every
    everyday food once. A food says how many table rows go with it (`forms`)
    and how many dishes, and carries its own rows' names as `keywords`, so
    "prawn" finds the food listed under its one shrimp."""
    dishes_of = _dishes_by_food(recipes)

    def listed(entry: dict, **shown) -> dict:
        return {**{key: value for key, value in entry.items() if key != "source_name"}, **shown}

    dishes = [
        listed(_dish_entry(r), food_group=r.category or "Dish", forms=1, dishes=1, keywords="")
        for r in sorted(recipes, key=lambda r: (r.category, r.name_en.lower()))
    ]
    everyday = [
        listed(
            _food_entry(food), food_group=food.rows[0].food_group, forms=len(food.covered),
            dishes=len(set().union(*(dishes_of.get(f.food_id, ()) for f in food.covered))),
            keywords=" | ".join(f"{display_name(f.name_en)} {f.name_bn}".strip() for f in food.rows),
        )
        for food in _everyday_foods(foods, dishes_of)
    ]
    everyday.sort(key=lambda entry: (entry["food_group"], entry["name_en"].lower()))
    return dishes + everyday


def record(chosen: list, foods: list[Food], recipes: list[Recipe],
           kept: list[dict] | None = None) -> list[dict]:
    """The entries to store on a patient for what a form sent, in the order
    chosen and without repeats. Each item is an id, or an (id, name) pair:
    the id with the name the form showed it under.

    An item that is one of the patient's `kept` entries keeps that entry
    untouched: a form that sends back what it was given must not re-point an
    old entry at whatever the id means today. The name is what tells the two
    apart once a dataset replacement has put another food on a kept entry's
    id: the old entry comes back under its own name, a fresh pick of the new
    food under that food's. A bare id is taken for the kept entry.

    Raises ValueError for an id that is neither a food nor a dish, and for a
    name the id does not carry: the list it was chosen from is out of date."""
    if len(chosen) > MAX_EXCLUDED:
        raise ValueError(f"at most {MAX_EXCLUDED} foods and dishes can be excluded")
    food_of = _by_row(_everyday_foods(foods, _dishes_by_food(recipes)))
    recipe_by_id = {r.recipe_id: r for r in recipes}
    entries: dict[tuple, dict] = {}
    for item in chosen:
        item_id, name = (item, None) if isinstance(item, str) else item
        entry = next((kept_entry for kept_entry in kept or []
                      if kept_entry["id"] == item_id and name in (None, kept_entry.get("name_en"))),
                     None)
        if entry is None:
            if item_id in food_of:
                entry = _food_entry(food_of[item_id])
            elif item_id in recipe_by_id:
                entry = _dish_entry(recipe_by_id[item_id])
            else:
                raise ValueError(f"'{item_id}' is not a food or dish in the database")
            if name is not None and name != entry["name_en"]:
                raise ValueError(
                    f"'{name}' is no longer what '{item_id}' is in the food database — "
                    "reload the list and choose it again"
                )
        # two rows of one food are the same entry; an old entry and the food
        # that now has its id are not
        entries.setdefault((entry["id"], entry.get("source_name")), entry)
    return list(entries.values())


def resolve(entries: list[dict] | None, foods: list[Food],
            recipes: list[Recipe]) -> OwnExclusions:
    """What a patient's stored entries exclude today."""
    if not entries:
        return NO_EXCLUSIONS
    dishes_of = _dishes_by_food(recipes)
    food_of = _by_row(_everyday_foods(foods, dishes_of))
    food_by_id = {f.food_id: f for f in foods}
    food_by_name = {f.name_en: f for f in foods}
    recipe_by_id = {r.recipe_id: r for r in recipes}
    recipe_by_name = {r.name_en: r for r in recipes}

    items, missing = [], []
    food_ids: set[str] = set()
    recipe_ids: set[str] = set()
    for entry in entries:
        source = entry.get("source_name") or entry.get("name_en", "")
        if entry.get("kind") == "recipe":
            recipe = recipe_by_id.get(entry.get("id"))
            if recipe is None or recipe.name_en != source:
                recipe = recipe_by_name.get(source)
            if recipe is None:
                missing.append(entry.get("name_en") or source)
                continue
            recipe_ids.add(recipe.recipe_id)
        else:
            food = food_by_id.get(entry.get("id"))
            if food is None or food.name_en != source:
                food = food_by_name.get(source)
            if food is None:
                missing.append(entry.get("name_en") or source)
                continue
            food_ids.update(f.food_id for f in food_of[food.food_id].covered)
        items.append(entry)

    for food_id in food_ids:
        recipe_ids.update(dishes_of.get(food_id, ()))
    return OwnExclusions(tuple(items), frozenset(food_ids), frozenset(recipe_ids), tuple(missing))
