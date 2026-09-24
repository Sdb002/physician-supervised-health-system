"""Physician plan editing: numbers recomputed server-side, gate re-enforced."""

PATIENT = {"name": "Edit Case", "sex": "female", "birth_year": 1985, "height_cm": 158}
VISIT = {"weight_kg": 62, "biomarkers": {"hemoglobin": 10.5}}  # anemia → iron emphasized


def _pending(client):
    patient_id = client.post("/patients", json=PATIENT).json()["id"]
    return client.post(f"/patients/{patient_id}/visits", json=VISIT).json()


def test_recompute_rebuilds_numbers_deterministically(client):
    assessment = _pending(client)
    result = assessment["result"]
    meals = result["nutrition"]["meal_plan"]["meals"]
    plan = result["exercise_plan"]

    # keep only the first breakfast item at a new quantity; keep other meals as-is
    first = meals["breakfast"][0]
    edit = {
        "meals": {
            meal: [{"food_id": i["food_id"], "qty_g": i["qty_g"]} for i in items]
            for meal, items in meals.items()
        },
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
    edit["meals"]["breakfast"] = [{"food_id": first["food_id"], "qty_g": 200}]

    response = client.post(f"/review/{assessment['id']}/recompute", json=edit)
    assert response.status_code == 200
    edited = response.json()

    new_first = edited["nutrition"]["meal_plan"]["meals"]["breakfast"][0]
    assert new_first["qty_g"] == 200
    # kcal was recomputed from the food DB, proportional to quantity
    expected_kcal = round(first["kcal"] / first["qty_g"] * 200)
    assert abs(new_first["kcal"] - expected_kcal) <= 2
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
        json={"meals": {"breakfast": [{"food_id": "NOT_A_FOOD", "qty_g": 100}]}},
    )
    assert response.status_code == 422
    assert "no longer in the food database" in response.json()["detail"]


def test_recompute_detects_stale_id_name_collision(client):
    """If the dataset was replaced and an id now denotes a different food, the
    error must use the name the physician SAW, not the colliding food's name."""
    assessment = _pending(client)
    real_item = assessment["result"]["nutrition"]["meal_plan"]["meals"]["breakfast"][0]
    response = client.post(
        f"/review/{assessment['id']}/recompute",
        json={"meals": {"breakfast": [
            {"food_id": real_item["food_id"], "qty_g": 100,
             "name_en": "Food From Old Dataset"},
        ]}},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Food From Old Dataset" in detail
    assert "older version of the food database" in detail


def test_allowed_foods_endpoint_serves_live_food_db(client):
    assessment = _pending(client)
    response = client.get(f"/review/{assessment['id']}/foods")
    assert response.status_code == 200
    foods = response.json()
    assert len(foods) > 0
    assert {"food_id", "name_en", "name_bn", "food_group", "kcal_per_100g"} <= set(foods[0])
    # every entry carries a usable energy density for the live editor
    assert all(f["kcal_per_100g"] >= 0 for f in foods)


def test_recompute_only_while_pending(client):
    assessment = _pending(client)
    client.post(f"/review/{assessment['id']}/decision",
                json={"decision": "rejected", "physician_name": "Dr Edit"})
    response = client.post(f"/review/{assessment['id']}/recompute",
                           json={"meals": {}})
    assert response.status_code == 409
