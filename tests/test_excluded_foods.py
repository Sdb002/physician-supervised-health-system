"""The foods and dishes one patient does not eat (engine 0.11.0).

Beyond the tick-box restrictions, a patient record lists single foods and
dishes picked from the food table and the recipe list. They go through the
gate: a food is left out in every form the table has it in, with every dish
that uses it, and neither the planner nor the plan editor can bring it back.
"""

import copy

import pytest

from src.diet import excluded_foods
from src.diet.food_db import food_index, load_foods
from src.diet.recipe import load_recipes

PATIENT = {"name": "Picky Case", "sex": "male", "birth_year": 1985, "height_cm": 170}
VISIT = {"weight_kg": 70, "biomarkers": {}}


@pytest.fixture(scope="module")
def tables():
    foods = load_foods()
    return foods, load_recipes(food_index(foods))


def _food(foods, name):
    return next(f for f in foods if f.name_en == name)


def _pending(client, **profile):
    patient = client.post("/patients", json={**PATIENT, **profile}).json()
    return patient, client.post(f"/patients/{patient['id']}/visits", json=VISIT).json()


def _dish_ids(result):
    return {item["recipe_id"] for day in result["nutrition"]["meal_plan"]["days"]
            for items in day["meals"].values() for item in items if item.get("recipe_id")}


def test_a_food_is_left_out_in_every_form_with_every_dish_that_uses_it(tables):
    foods, recipes = tables
    dried = _food(foods, "Lentil, dried, raw")
    boiled = _food(foods, "Lentil, boiled (without salt)")
    # chosen by either row, the food is the same entry...
    entries = excluded_foods.record([boiled.food_id], foods, recipes)
    assert entries == excluded_foods.record([dried.food_id, boiled.food_id], foods, recipes)
    assert [(e["kind"], e["name_en"], e["name_bn"]) for e in entries] == [("food", "Lentil", "মসুর ডাল")]

    own = excluded_foods.resolve(entries, foods, recipes)
    assert own.food_ids == {dried.food_id, boiled.food_id}
    with_lentil = {r.recipe_id for r in recipes
                   if any(food_id in own.food_ids for food_id, _ in r.ingredients)}
    assert own.recipe_ids == with_lentil and len(with_lentil) > 5
    assert not own.allows(dried) and not own.allows(boiled)
    assert own.allows(_food(foods, "Pea, dried, raw"))
    assert not own.missing


def test_a_food_takes_every_row_named_as_a_form_of_it(tables):
    foods, recipes = tables

    def excluded_by(row_name):
        entries = excluded_foods.record([_food(foods, row_name).food_id], foods, recipes)
        own = excluded_foods.resolve(entries, foods, recipes)
        return entries[0]["name_en"], {f.name_en for f in foods if not own.allows(f)}, own

    # the milled and the boiled rices have different Bangla names (চাল, ভাত)
    # and are one food, whichever row it is chosen by
    name, rice, own = excluded_by("Rice, BR-28, boiled (without salt)")
    assert name == "Rice" and len(rice) == 19
    assert {"Rice, BR-28, parboiled, milled, raw", "Rice, BR-28, boiled (without salt)",
            "Rice, puffed, salted", "Rice, popped", "Rice, bran, raw"} <= rice
    assert all(row.startswith("Rice,") for row in rice)

    # the boiled egg and the yolk go with the egg, the milk powders with the milk
    name, egg, _ = excluded_by("Egg, chicken, farmed, raw")
    assert name == "Egg, chicken"
    assert {"Egg, chicken, native, boiled (without salt)", "Egg, chicken, native, yolk, raw"} <= egg
    assert not any(row.startswith("Egg, duck") for row in egg)
    name, milk, own = excluded_by("Milk, cow, whole fat (pasteurized, UTH)")
    assert name == "Milk, cow" and "Milk, cow, powder, whole" in milk
    powdered = _food(foods, "Milk, cow, powder, whole").food_id
    assert {r.recipe_id for r in recipes
            if any(food_id == powdered for food_id, _ in r.ingredients)} <= own.recipe_ids

    # a narrower food stays one of its own: puffed rice without the rest of rice
    name, puffed, _ = excluded_by("Rice, puffed, salted")
    assert name == "Rice, puffed, salted" and puffed == {"Rice, puffed, salted"}


def test_a_dish_is_left_out_by_itself(tables):
    foods, recipes = tables
    entries = excluded_foods.record(["BDR-152"], foods, recipes)
    assert entries[0]["kind"] == "recipe" and entries[0]["name_en"] == "Ghee Rice"
    own = excluded_foods.resolve(entries, foods, recipes)
    # the dish goes; the rice and ghee it is made of stay
    assert own.recipe_ids == {"BDR-152"} and not own.food_ids


def test_an_unknown_id_is_refused_and_a_repeat_is_kept_once(tables):
    foods, recipes = tables
    with pytest.raises(ValueError, match="not a food or dish"):
        excluded_foods.record(["F999999"], foods, recipes)
    with pytest.raises(ValueError, match="at most"):
        excluded_foods.record([f.food_id for f in foods][:excluded_foods.MAX_EXCLUDED + 1],
                              foods, recipes)
    assert len(excluded_foods.record(["BDR-152", "BDR-152"], foods, recipes)) == 1
    assert excluded_foods.resolve([], foods, recipes) is excluded_foods.NO_EXCLUSIONS
    assert excluded_foods.resolve(None, foods, recipes).allows(foods[0])


def test_an_entry_never_moves_to_another_food_when_the_table_is_replaced(tables):
    foods, recipes = tables
    lentil, rohu = _food(foods, "Lentil, dried, raw"), _food(foods, "Rohu, without bones, raw")
    entry = excluded_foods.record([lentil.food_id], foods, recipes)[0]

    # a new table has put lentil's id on another row: the entry follows the
    # name it was chosen under, not the id
    renumbered = {**entry, "id": rohu.food_id}
    own = excluded_foods.resolve([renumbered], foods, recipes)
    assert lentil.food_id in own.food_ids and rohu.food_id not in own.food_ids

    # ...and when the name is gone too, it is reported, not guessed
    gone = {**entry, "id": "F999999", "source_name": "Lentil, heirloom, raw"}
    own = excluded_foods.resolve([gone], foods, recipes)
    assert not own.food_ids and not own.recipe_ids and not own.items
    assert own.missing == ("Lentil",)

    # a form that sends an id back keeps the entry it stood for, stale or not
    assert excluded_foods.record(["F999999"], foods, recipes, kept=[gone]) == [gone]


def test_a_fresh_pick_is_told_from_an_old_entry_on_the_same_id(tables):
    foods, recipes = tables
    lentil, rohu = _food(foods, "Lentil, dried, raw"), _food(foods, "Rohu, without bones, raw")
    # a new table has put rohu on the id an old "Lentil" entry was recorded under
    old = {**excluded_foods.record([lentil.food_id], foods, recipes)[0], "id": rohu.food_id}
    rohu_entry = excluded_foods.record([rohu.food_id], foods, recipes)

    # the form sends the old entry back under its own name: it stays as it is
    assert excluded_foods.record([(rohu.food_id, "Lentil")], foods, recipes, kept=[old]) == [old]
    # the doctor took it off and picked the food that has the id now
    assert excluded_foods.record([(rohu.food_id, "Rohu")], foods, recipes, kept=[old]) == rohu_entry
    # both in one list are two entries, each leaving out its own food
    both = excluded_foods.record([(rohu.food_id, "Lentil"), (rohu.food_id, "Rohu")],
                                 foods, recipes, kept=[old])
    assert both == [old] + rohu_entry
    assert {lentil.food_id, rohu.food_id} <= excluded_foods.resolve(both, foods, recipes).food_ids

    # a name the id does not carry and no kept entry has: the list is out of date
    with pytest.raises(ValueError, match="no longer what"):
        excluded_foods.record([(rohu.food_id, "Hilsa")], foods, recipes)


def test_the_catalogue_lists_every_dish_and_each_everyday_food_once(tables):
    foods, recipes = tables
    listed = excluded_foods.catalogue(foods, recipes)
    assert sum(entry["kind"] == "recipe" for entry in listed) == len(recipes)
    ids = [entry["id"] for entry in listed]
    assert len(ids) == len(set(ids))

    # no two foods are listed under one name: the milled rices (চাল) and the
    # boiled rices (ভাত) are both "Rice", and are one entry
    names = [entry["name_en"] for entry in listed if entry["kind"] == "food"]
    assert len(names) == len(set(names))

    # rice is named by what its rows' names share, and says what goes with
    # it: its sixteen rows, and the bran, popped and puffed rice
    rice = next(e for e in listed if e["kind"] == "food" and e["name_bn"] == "চাল")
    assert rice["name_en"] == "Rice" and rice["forms"] == 19 and rice["dishes"] > 20
    assert "BR-28" in rice["keywords"] and "ভাত" in rice["keywords"]
    # a search for "puffed" still finds puffed rice alone, not all of rice
    assert "puffed" not in rice["keywords"].lower()
    # a search for "prawn" finds the prawns listed under their one shrimp
    assert any("Prawn" in e["keywords"] and e["forms"] == 7 for e in listed)
    # every entry can be recorded as it is listed
    assert len(excluded_foods.record(ids[:excluded_foods.MAX_EXCLUDED], foods, recipes)) \
        == excluded_foods.MAX_EXCLUDED
    assert "source_name" not in rice


def test_the_catalogue_needs_no_sign_in(client):
    signed_out = {"Authorization": "Bearer not-a-token"}
    assert client.get("/patients", headers=signed_out).status_code == 401
    response = client.get("/foods/catalogue", headers=signed_out)
    assert response.status_code == 200
    assert {"id", "kind", "name_en", "name_bn", "food_group", "forms", "dishes"} <= set(response.json()[0])


def test_a_plan_leaves_out_what_the_patient_does_not_eat(client, tables):
    foods, recipes = tables
    usual = _pending(client)[1]["result"]
    # the usual plan is full of both
    rohu = _food(foods, "Rohu, without bones, raw")
    lentil = _food(foods, "Lentil, dried, raw")
    uses = lambda food: {r.recipe_id for r in recipes  # noqa: E731
                         if any(food_id == food.food_id for food_id, _ in r.ingredients)}
    assert _dish_ids(usual) & uses(rohu) and _dish_ids(usual) & uses(lentil)
    assert usual["excluded_foods"] == [] and usual["exclusions"]["recipe_ids"] == []

    patient, assessment = _pending(client, excluded_foods=[rohu.food_id, lentil.food_id, "BDR-112"])
    assert [f["name_en"] for f in patient["excluded_foods"]] == ["Rohu", "Lentil", "Dry Spiced Chicken"]
    result = assessment["result"]
    assert [f["name_en"] for f in result["excluded_foods"]] == ["Rohu", "Lentil", "Dry Spiced Chicken"]
    left_out = set(result["exclusions"]["recipe_ids"])
    assert uses(rohu) | uses(lentil) | {"BDR-112"} == left_out

    # nothing planned or suggested uses them, and the week is still whole
    assert not _dish_ids(result) & left_out
    assert not {r["recipe_id"] for r in result["nutrition"]["top_recipes"]} & left_out
    suggested = {f["food_id"] for f in result["nutrition"]["top_foods"]}
    assert not suggested & set(result["exclusions"]["food_ids"])
    for day in result["nutrition"]["meal_plan"]["days"]:
        assert {item["course"] for item in day["meals"]["lunch"]} == {"staple", "dal", "main", "vegetable"}

    # the plan editor neither offers nor accepts them
    offered = client.get(f"/review/{assessment['id']}/foods").json()
    offered_ids = {f.get("recipe_id") or f["food_id"] for f in offered}
    assert not offered_ids & (left_out | set(result["exclusions"]["food_ids"]))
    assert "BDR-021" in offered_ids or len(offered_ids) > 300  # the rest is still there
    for refused in ({"recipe_id": "BDR-112", "qty_g": 150}, {"recipe_id": "BDR-079", "qty_g": 200},
                    {"food_id": lentil.food_id, "qty_g": 50}):
        response = client.post(f"/review/{assessment['id']}/recompute",
                               json={"days": [{"lunch": [refused]}]})
        assert response.status_code == 422, refused
        assert "the patient does not eat it" in response.json()["detail"]


def test_changing_what_a_patient_does_not_eat_rebuilds_the_plan_awaiting_review(client, tables):
    foods, _ = tables
    patient, assessment = _pending(client)
    rice = _food(foods, "Rice, BR-28, parboiled, milled, raw")
    assert any(item["name_en"] == "Plain Boiled Rice"
               for day in assessment["result"]["nutrition"]["meal_plan"]["days"]
               for items in day["meals"].values() for item in items)

    response = client.patch(f"/patients/{patient['id']}", json={"excluded_foods": [rice.food_id]})
    assert response.status_code == 200
    # any rice row stands for rice, in every form the table has it in
    assert [f["name_en"] for f in response.json()["excluded_foods"]] == ["Rice"]

    rebuilt = client.get(f"/review/{assessment['id']}").json()["assessment"]["result"]
    names = {item["name_en"] for day in rebuilt["nutrition"]["meal_plan"]["days"]
             for items in day["meals"].values() for item in items}
    assert "Plain Boiled Rice" not in names and len(rebuilt["exclusions"]["food_ids"]) == 19
    # bread carries the meals that had rice: lunch is a rice meal, but it
    # does not go without a staple
    for day in rebuilt["nutrition"]["meal_plan"]["days"]:
        staples = [item for item in day["meals"]["lunch"] if item["course"] == "staple"]
        assert len(staples) == 1, day["weekday"]
        assert staples[0]["category"] == "Bread & Pitha"
        assert staples[0]["recipe_id"] not in rebuilt["exclusions"]["recipe_ids"]

    # sending the list back as the form does (each id with its name) changes
    # nothing, and neither does the bare id; an empty list clears it
    kept = response.json()["excluded_foods"]
    for sent in ({"id": kept[0]["id"], "name_en": "Rice"}, kept[0]["id"]):
        again = client.patch(f"/patients/{patient['id']}", json={"excluded_foods": [sent]})
        assert again.json()["excluded_foods"] == kept
    # a name the id does not carry is refused, and the record is left alone
    wrong = client.patch(f"/patients/{patient['id']}",
                         json={"excluded_foods": [{"id": kept[0]["id"], "name_en": "Lentil"}]})
    assert wrong.status_code == 422 and "no longer what" in wrong.json()["detail"]
    assert client.get(f"/patients/{patient['id']}").json()["excluded_foods"] == kept
    cleared = client.patch(f"/patients/{patient['id']}", json={"excluded_foods": []})
    assert cleared.json()["excluded_foods"] == []
    back = client.get(f"/review/{assessment['id']}").json()["assessment"]["result"]
    assert back["exclusions"]["food_ids"] == [] and back["excluded_foods"] == []


def test_an_id_that_is_no_food_is_refused_at_the_door(client):
    assert client.post("/patients", json={**PATIENT, "excluded_foods": ["nonsense"]}).status_code == 422
    patient = client.post("/patients", json=PATIENT).json()
    response = client.patch(f"/patients/{patient['id']}", json={"excluded_foods": ["BDR-999"]})
    assert response.status_code == 422 and "not a food or dish" in response.json()["detail"]
    assert client.get(f"/patients/{patient['id']}").json()["excluded_foods"] == []


def test_a_patient_can_say_what_they_do_not_eat_when_signing_up(client, tables):
    foods, _ = tables
    brinjal = _food(foods, "Brinjal, purple, long, raw")
    profile = {"sex": "female", "birth_year": 1992, "height_cm": 157,
               "excluded_foods": [brinjal.food_id]}
    account = {"name": "Self Registered", "email": "self@test.local",
               "password": "password123", "role": "patient", "profile": profile}
    assert client.post("/auth/register", json=account).status_code == 201
    token = client.post("/auth/login", json={"email": "self@test.local",
                                             "password": "password123"}).json()["token"]
    mine = client.get("/me/dashboard", headers={"Authorization": f"Bearer {token}"}).json()
    assert [f["name_en"] for f in mine["patient"]["excluded_foods"]] == ["Brinjal, purple, long"]

    bad = {**account, "email": "other@test.local", "profile": {**profile, "excluded_foods": ["F0"]}}
    assert client.post("/auth/register", json=bad).status_code == 422


def test_the_plan_editor_follows_a_food_by_name_after_the_table_is_replaced(client, tables):
    from src.api.services import allowed_foods_for

    foods, _ = tables
    lentil, rohu = _food(foods, "Lentil, dried, raw"), _food(foods, "Rohu, without bones, raw")
    result = _pending(client, excluded_foods=[lentil.food_id])[1]["result"]
    assert result["excluded_foods"][0]["source_name"] == "Lentil, dried, raw"

    def offered(assessment):
        return {f.get("recipe_id") or f["food_id"] for f in allowed_foods_for(assessment)}

    # the assessment as it reads once a new table has put rohu on lentil's
    # old id: the ids it listed are rohu's now, the row name is still lentil's
    stale = copy.deepcopy(result)
    stale["excluded_foods"][0]["id"] = rohu.food_id
    stale["exclusions"].update(food_ids=[rohu.food_id], recipe_ids=[])
    assert rohu.food_id in offered(stale) and lentil.food_id not in offered(stale)

    # an assessment that kept no row names is held to the ids it listed
    del stale["excluded_foods"][0]["source_name"]
    assert rohu.food_id not in offered(stale) and lentil.food_id in offered(stale)


def test_the_physician_is_told_when_exclusions_leave_meals_without_a_course(client, tables):
    foods, _ = tables
    short = "Too few dishes are left for this patient to fill the plan"
    assert not any(short in caution for caution in _pending(client)[1]["result"]["cautions"])

    # salt is in nine dishes out of ten: without it most meals are the staple alone
    result = _pending(client, excluded_foods=[_food(foods, "Salt").food_id])[1]["result"]
    left_out = len(result["exclusions"]["recipe_ids"])
    assert left_out > 200
    caution = next(caution for caution in result["cautions"] if short in caution)
    assert "of the week's 28 meals are missing a course" in caution
    assert "dal" in caution and "main dish" in caution and "vegetable" in caution
    assert f"{left_out} of them by the foods recorded as not eaten" in caution


def test_a_refused_dish_says_every_reason_it_is_excluded(client):
    # Ghee Rice is cooked in a solid fat, and this patient does not eat it either
    _, assessment = _pending(client, conditions=["high_cholesterol"], excluded_foods=["BDR-152"])
    response = client.post(f"/review/{assessment['id']}/recompute",
                           json={"days": [{"lunch": [{"recipe_id": "BDR-152", "qty_g": 150}]}]})
    assert response.status_code == 422
    assert "solid_fat, the patient does not eat it" in response.json()["detail"]


def test_the_catalogue_is_built_once_and_an_empty_list_reads_no_table(monkeypatch):
    from src.api import services

    listed = services.excludable_foods()
    monkeypatch.setattr(services, "load_foods", lambda: pytest.fail("the food table was read"))
    assert services.excludable_foods() is listed
    assert services.excluded_food_entries([]) == []
    assert services.excluded_food_entries([], kept=[{"id": "F001"}]) == []


def test_the_physician_is_told_when_an_excluded_food_has_left_the_table():
    from src.api.services import build_assessment
    from src.db.models import Patient, Visit

    stale = {"id": "F999999", "kind": "food", "name_en": "Lotus stem",
             "name_bn": "", "source_name": "Lotus stem, heirloom, raw"}
    patient = Patient(name="Stale", sex="male", birth_year=1980, height_cm=170, pregnant=False,
                      conditions=[], dietary_restrictions=[], excluded_foods=[stale],
                      fitness_level="beginner", notes="")
    result = build_assessment(patient, Visit(weight_kg=70, biomarkers={}))
    assert result["excluded_foods"] == [] and result["exclusions"]["food_ids"] == []
    assert any("'Lotus stem' is recorded as something this patient does not eat" in caution
               for caution in result["cautions"])
