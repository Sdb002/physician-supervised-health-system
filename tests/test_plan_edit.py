"""Physician plan editing: numbers recomputed server-side, gate re-enforced."""

PATIENT = {"name": "Edit Case", "sex": "female", "birth_year": 1985, "height_cm": 158}
VISIT = {"weight_kg": 62, "biomarkers": {"hemoglobin": 10.5}}  # anemia → iron emphasized


def _pending(client, patient=PATIENT, visit=VISIT):
    patient_id = client.post("/patients", json=patient).json()["id"]
    return client.post(f"/patients/{patient_id}/visits", json=visit).json()


def _ref(item: dict) -> dict:
    """A plan item as the editor sends it back: a dish or a food."""
    if item.get("recipe_id"):
        return {"recipe_id": item["recipe_id"], "qty_g": item["qty_g"]}
    return {"food_id": item["food_id"], "qty_g": item["qty_g"]}


def test_recompute_rebuilds_numbers_deterministically(client):
    assessment = _pending(client)
    result = assessment["result"]
    days = result["nutrition"]["meal_plan"]["days"]
    plan = result["exercise_plan"]

    # keep only Saturday's first breakfast item at a new quantity; keep the rest as-is
    first = days[0]["meals"]["breakfast"][0]
    edit = {
        "days": [
            {meal: [_ref(i) for i in items] for meal, items in day["meals"].items()}
            for day in days
        ],
        "exercise": {
            "aerobic_days": 3,
            "strength_days": plan["frequency"]["strength_days"],
            "flexibility_days": plan["frequency"]["flexibility_days"],
            "aerobic_min_per_session": 20,
            "type": {
                group: [e["exercise_id"] for e in plan["type"][group]]
                for group in ("aerobic", "strength", "flexibility")
            },
        },
    }
    edit["days"][0]["breakfast"] = [{**_ref(first), "qty_g": 200}]

    response = client.post(f"/review/{assessment['id']}/recompute", json=edit)
    assert response.status_code == 200
    edited = response.json()

    edited_days = edited["nutrition"]["meal_plan"]["days"]
    assert [d["weekday"] for d in edited_days] == [d["weekday"] for d in days]
    new_first = edited_days[0]["meals"]["breakfast"][0]
    assert new_first["qty_g"] == 200
    # kcal was recomputed from the recipe/food data, proportional to quantity
    expected_kcal = round(first["kcal"] / first["qty_g"] * 200)
    assert abs(new_first["kcal"] - expected_kcal) <= 2
    # ...and so were the carbohydrate, fat and sodium the line reports
    for nutrient in ("carb_g", "fat_g", "sodium_mg"):
        expected = first[nutrient] / first["qty_g"] * 200
        assert abs(new_first[nutrient] - expected) <= max(1.0, expected * 0.02)
    assert edited["nutrition"]["meal_plan"]["edited_by_physician"] is True
    assert edited["nutrition"]["meal_plan"]["coverage"]  # coverage recomputed

    ex = edited["exercise_plan"]
    assert ex["time"]["aerobic_min_per_week"] == 60  # 20 min × 3 days
    assert ex["frequency"]["aerobic_days"] == 3
    assert ex["edited_by_physician"] is True

    # approving with the edited result is what the patient's report shows
    decision = client.post(
        f"/review/{assessment['id']}/decision",
        json={"decision": "approved", "physician_name": "Dr Edit",
              "edited_result": edited},
    )
    assert decision.status_code == 201
    report = client.get(f"/report/{assessment['visit_id']}?use_llm=false")
    assert report.status_code == 200
    assert f"({200} g)" in report.json()["text"]


def test_recompute_rejects_unknown_or_excluded_food(client):
    assessment = _pending(client)
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"days": [{"breakfast": [{"food_id": "NOT_A_FOOD", "qty_g": 100}]}]},
    )
    assert response.status_code == 422
    assert "no longer in the food database" in response.json()["detail"]


def test_recompute_detects_stale_id_name_collision(client):
    """If the dataset was replaced and an id now denotes a different food, the
    error must use the name the physician SAW, not the colliding food's name."""
    assessment = _pending(client)
    real_item = assessment["result"]["nutrition"]["meal_plan"]["days"][0]["meals"]["breakfast"][0]
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"days": [{"breakfast": [
            {**_ref(real_item), "qty_g": 100, "name_en": "Food From Old Dataset"},
        ]}]},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Food From Old Dataset" in detail
    assert "comes from an older version of the" in detail


def test_allowed_foods_endpoint_serves_live_food_db(client):
    assessment = _pending(client)
    response = client.get(f"/review/{assessment['id']}/foods")
    assert response.status_code == 200
    foods = response.json()
    assert len(foods) > 0
    dishes = [f for f in foods if f["kind"] == "recipe"]
    singles = [f for f in foods if f["kind"] == "food"]
    assert dishes and singles
    assert {"recipe_id", "name_en", "food_group", "serving_size_g", "kcal_per_100g"} <= set(dishes[0])
    assert {"food_id", "name_en", "name_bn", "food_group", "kcal_per_100g"} <= set(singles[0])
    # every entry carries a usable energy density for the live editor
    assert all(f["kcal_per_100g"] >= 0 for f in foods)


def test_plan_is_a_week_built_from_dishes(client):
    days = _pending(client)["result"]["nutrition"]["meal_plan"]["days"]
    assert len(days) == 7 and days[0]["weekday"] == "saturday"
    for day in days:
        meals = day["meals"]
        for meal in ("breakfast", "lunch", "dinner"):
            assert meals[meal] and all(item.get("recipe_id") for item in meals[meal])
        assert [item["course"] for item in meals["lunch"]] == ["staple", "dal", "main", "vegetable"]


def test_every_day_of_the_plan_stays_under_the_sodium_limit(client):
    result = _pending(client)["result"]
    limit = result["nutrition"]["limits"]["sodium_mg"]
    for day in result["nutrition"]["meal_plan"]["days"]:
        assert day["totals"]["sodium_mg"] < limit
        assert 0 < day["salt_g"] <= day["recipe_salt_g"]


def test_recompute_fits_the_salt_of_an_edited_day_to_the_sodium_limit(client):
    assessment = _pending(client)
    result = assessment["result"]
    days = result["nutrition"]["meal_plan"]["days"]
    limit = result["nutrition"]["limits"]["sodium_mg"]
    edit = {"days": [
        {meal: [_ref(i) for i in items] for meal, items in day["meals"].items()}
        for day in days
    ]}
    # the physician doubles Saturday's lunch: twice those dishes' salt as written
    edit["days"][0]["lunch"] = [{**ref, "qty_g": ref["qty_g"] * 2}
                                for ref in edit["days"][0]["lunch"]]

    response = client.post(f"/review/{assessment['id']}/recompute", json=edit)
    assert response.status_code == 200
    edited_days = response.json()["nutrition"]["meal_plan"]["days"]
    saturday = edited_days[0]
    assert saturday["recipe_salt_g"] > days[0]["recipe_salt_g"]
    assert saturday["salt_g"] < saturday["recipe_salt_g"]
    assert all(day["totals"]["sodium_mg"] < limit for day in edited_days)
    dishes = [item for items in saturday["meals"].values() for item in items
              if item.get("recipe_id")]
    assert abs(sum(item["salt_g"] for item in dishes) - saturday["salt_g"]) <= 0.05


def test_a_week_plan_must_be_edited_as_a_week(client):
    assessment = _pending(client)
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"meals": {"lunch": [{"recipe_id": "BDR-001", "qty_g": 243}]}},
    )
    assert response.status_code == 422
    assert "covers a week" in response.json()["detail"]


def test_recompute_rejects_a_dish_the_gate_excludes(client):
    # diabetes (fasting glucose 160) excludes high_sugar: rice pudding is out
    diabetic = _pending(client, visit={"weight_kg": 70, "biomarkers": {"fasting_glucose": 160}})
    response = client.post(
        f"/review/{diabetic['id']}/recompute",
        json={"days": [{"snack": [{"recipe_id": "BDR-133", "qty_g": 150}]}]},
    )
    assert response.status_code == 422
    assert "excluded for this patient" in response.json()["detail"]


def test_recompute_scales_a_dish_by_weight(client):
    assessment = _pending(client)
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"days": [{"lunch": [{"recipe_id": "BDR-001", "qty_g": 486}]}]},  # 2 x 243 g
    )
    assert response.status_code == 200
    rice = response.json()["nutrition"]["meal_plan"]["days"][0]["meals"]["lunch"][0]
    assert rice["servings"] == 2.0 and rice["name_en"] == "Plain Boiled Rice"


def test_edit_item_must_name_exactly_one_kind(client):
    assessment = _pending(client)
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"days": [{"lunch": [{"food_id": "F001", "recipe_id": "BDR-001", "qty_g": 100}]}]},
    )
    assert response.status_code == 422


def test_recompute_only_while_pending(client):
    assessment = _pending(client)
    client.post(f"/review/{assessment['id']}/decision",
                json={"decision": "rejected", "physician_name": "Dr Edit"})
    response = client.post(f"/review/{assessment['id']}/recompute",
                           json={"meals": {}})
    assert response.status_code == 409


def _plan_dishes(result):
    return [item for day in result["nutrition"]["meal_plan"]["days"]
            for items in day["meals"].values() for item in items if item.get("recipe_id")]


def test_a_vegetarian_patient_is_planned_and_offered_no_meat_or_fish(client):
    assessment = _pending(client, patient={**PATIENT, "dietary_restrictions": ["vegetarian"]})
    result = assessment["result"]
    assert result["dietary_restrictions"] == ["vegetarian"]
    assert {"contains_meat", "contains_fish"} <= set(result["exclusions"]["food_tags"])
    dishes = _plan_dishes(result)
    assert dishes and not {d["category"] for d in dishes} & {"Fish", "Meat"}
    # every lunch and dinner still has a main dish
    for day in result["nutrition"]["meal_plan"]["days"]:
        for meal in ("lunch", "dinner"):
            assert any(item["course"] == "main" for item in day["meals"][meal])
    assert not {f["food_group"] for f in result["nutrition"]["top_foods"]} & {"fish", "meat"}

    # the plan editor neither offers nor accepts what the patient does not eat
    offered = client.get(f"/review/{assessment['id']}/foods").json()
    assert not {f["food_group"] for f in offered} & {"Fish", "Meat", "fish", "meat"}
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"days": [{"lunch": [{"recipe_id": "BDR-079", "qty_g": 200}]}]},  # a fish curry
    )
    assert response.status_code == 422
    assert "excluded for this patient" in response.json()["detail"]


def test_changing_the_patient_rebuilds_the_plan_awaiting_review(client):
    assessment = _pending(client)
    patient_id = client.get(f"/review/{assessment['id']}").json()["patient"]["id"]
    before = {d["category"] for d in _plan_dishes(assessment["result"])}
    assert before & {"Fish", "Meat"}

    response = client.patch(f"/patients/{patient_id}",
                            json={"dietary_restrictions": ["vegetarian"],
                                  "activity_level": "moderate"})
    assert response.status_code == 200
    assert response.json()["dietary_restrictions"] == ["vegetarian"]
    assert response.json()["name"] == PATIENT["name"]  # fields not sent are kept

    rebuilt = client.get(f"/review/{assessment['id']}").json()["assessment"]["result"]
    assert not {d["category"] for d in _plan_dishes(rebuilt)} & {"Fish", "Meat"}
    basis = rebuilt["anthropometrics"]["basis"]
    assert basis["activity"] == "moderate" and basis["activity_assumed"] is False


def test_an_approved_plan_is_not_rebuilt_when_the_patient_changes(client):
    assessment = _pending(client)
    patient_id = client.get(f"/review/{assessment['id']}").json()["patient"]["id"]
    client.post(f"/review/{assessment['id']}/decision",
                json={"decision": "approved", "physician_name": "Dr Edit"})
    client.patch(f"/patients/{patient_id}", json={"dietary_restrictions": ["vegan"]})
    report = client.get(f"/report/{assessment['visit_id']}?use_llm=false").json()
    assert report["result"]["nutrition"]["meal_plan"] == assessment["result"]["nutrition"]["meal_plan"]


def test_pregnancy_is_planned_without_a_deficit_and_with_the_trimester(client):
    pregnant = {**PATIENT, "pregnant": True}
    assessment = _pending(client, patient=pregnant, visit={"weight_kg": 62, "biomarkers": {}})
    result = assessment["result"]
    anthro = result["anthropometrics"]
    assert anthro["basis"]["adjustment_kcal"] == 0 and anthro["target_kcal"] == anthro["tdee_kcal"]
    assert {"liver", "high_mercury", "alcohol"} <= set(result["exclusions"]["food_tags"])
    assert any("No trimester is recorded" in caution for caution in result["cautions"])

    patient_id = client.get(f"/review/{assessment['id']}").json()["patient"]["id"]
    client.patch(f"/patients/{patient_id}", json={"pregnancy_trimester": 3})
    rebuilt = client.get(f"/review/{assessment['id']}").json()["assessment"]["result"]
    assert rebuilt["anthropometrics"]["target_kcal"] == anthro["tdee_kcal"] + 452
    assert not any("No trimester" in caution for caution in rebuilt["cautions"])

    # no longer pregnant: the trimester goes with it
    cleared = client.patch(f"/patients/{patient_id}", json={"pregnant": False}).json()
    assert cleared["pregnancy_trimester"] is None


def test_the_physician_is_cautioned_about_a_patient_under_19(client):
    this_year = __import__("datetime").date.today().year
    teen = _pending(client, patient={**PATIENT, "birth_year": this_year - 15})
    assert any("for adults aged 19 and over" in caution for caution in teen["result"]["cautions"])
    adult = _pending(client)
    assert not any("for adults aged" in caution for caution in adult["result"]["cautions"])
