"""Deterministic patient-report text (English/Bangla) — the no-LLM fallback.

Renders the approved assessment into readable text with fixed templates, so
the report endpoint works even without an API key. The LLM path in
src/llm/report_writer.py produces friendlier prose from the same data.
"""

_LABELS = {
    "en": {
        "greeting": "Dear {name},",
        "intro": "Your physician has reviewed and approved this health plan for you.",
        "findings": "What your check-up found",
        "bmi": "Body mass index (BMI): {bmi} ({category})",
        "conditions": "Conditions considered in this plan: {items}",
        "why": "Why this plan",
        "diet": "Your daily food plan (target: {kcal} kcal)",
        "diet_week": "Your food plan for the week (target: {kcal} kcal a day)",
        "diet_total": "Planned total: about {kcal} kcal/day",
        "diet_week_total": "Planned: about {kcal} kcal a day on average",
        "salt": "Cooking salt for the day: {g} g in your portions",
        "salt_less": "Cooking salt for the day: {g} g in your portions, less than the {recipe} g the recipes list",
        "salt_note": "Cook each day's dishes with no more salt than the amount shown for that day, and add no salt at the table.",
        "foods": "Foods that suit your plan",
        "recipes": "Recommended home recipes",
        "recipe_line": "{name} ({category}) — 1 serving ≈ {grams} g, {kcal} kcal; {tier}",
        "exercise": "Your exercise plan",
        "aerobic": "Aerobic activity: {min} minutes per session, {days} days a week (target heart rate {lo}-{hi} beats/min)",
        "strength": "Strength training: {days} days a week",
        "flexibility": "Flexibility / stretching: {days} days a week",
        "progression": "How to progress: {text}",
        "safety": "For your safety, foods and exercises that are not suitable for your condition were removed before this plan was made.",
        "comment": "A note from your physician: {comment}",
        "closing": "This plan was approved by your physician. If anything is unclear or you feel unwell, please contact them.",
        "no_flags": "All measured values were in the normal range.",
    },
    "bn": {
        "greeting": "প্রিয় {name},",
        "intro": "আপনার চিকিৎসক এই স্বাস্থ্য পরিকল্পনাটি পর্যালোচনা করে অনুমোদন করেছেন।",
        "findings": "আপনার পরীক্ষায় যা পাওয়া গেছে",
        "bmi": "বডি মাস ইনডেক্স (BMI): {bmi} ({category})",
        "conditions": "এই পরিকল্পনায় বিবেচিত অবস্থা: {items}",
        "why": "কেন এই পরিকল্পনা",
        "diet": "আপনার দৈনিক খাবারের পরিকল্পনা (লক্ষ্য: {kcal} কিলোক্যালরি)",
        "diet_week": "আপনার সপ্তাহের খাবারের পরিকল্পনা (লক্ষ্য: দিনে {kcal} কিলোক্যালরি)",
        "diet_total": "পরিকল্পিত মোট: প্রায় {kcal} কিলোক্যালরি/দিন",
        "diet_week_total": "পরিকল্পিত: গড়ে দিনে প্রায় {kcal} কিলোক্যালরি",
        "salt": "সারা দিনের রান্নার লবণ: আপনার অংশে {g} গ্রাম",
        "salt_less": "সারা দিনের রান্নার লবণ: আপনার অংশে {g} গ্রাম, রেসিপিতে লেখা {recipe} গ্রামের চেয়ে কম",
        "salt_note": "প্রতিদিনের রান্নায় ওই দিনের জন্য দেখানো পরিমাণের বেশি লবণ দেবেন না, আর পাতে আলাদা লবণ নেবেন না।",
        "foods": "আপনার পরিকল্পনার উপযোগী খাবার",
        "recipes": "সুপারিশকৃত ঘরোয়া রান্না",
        "recipe_line": "{name} ({category}) — ১ পরিবেশন ≈ {grams} গ্রাম, {kcal} কিলোক্যালরি; {tier}",
        "exercise": "আপনার ব্যায়ামের পরিকল্পনা",
        "aerobic": "অ্যারোবিক ব্যায়াম: প্রতিবার {min} মিনিট, সপ্তাহে {days} দিন (লক্ষ্য হৃদস্পন্দন {lo}-{hi} বার/মিনিট)",
        "strength": "শক্তি ব্যায়াম: সপ্তাহে {days} দিন",
        "flexibility": "নমনীয়তা / স্ট্রেচিং: সপ্তাহে {days} দিন",
        "progression": "কীভাবে এগোবেন: {text}",
        "safety": "আপনার নিরাপত্তার জন্য, আপনার অবস্থার সাথে মানানসই নয় এমন খাবার ও ব্যায়াম এই পরিকল্পনা তৈরির আগেই বাদ দেওয়া হয়েছে।",
        "comment": "আপনার চিকিৎসকের মন্তব্য: {comment}",
        "closing": "এই পরিকল্পনাটি আপনার চিকিৎসক অনুমোদন করেছেন। কিছু অস্পষ্ট হলে বা অসুস্থ বোধ করলে চিকিৎসকের সাথে যোগাযোগ করুন।",
        "no_flags": "পরিমাপ করা সব মান স্বাভাবিক সীমার মধ্যে ছিল।",
    },
}

# Human-readable clinical vocabulary. Without this the patient report printed
# raw engine keys - "fasting_glucose: 132.0 mg/dL - hypertension stage2" - in
# both languages, so the Bangla report was half English.
_BIOMARKERS = {
    "en": {
        "fasting_glucose": "Fasting blood glucose",
        "systolic_bp": "Blood pressure (upper / systolic)",
        "diastolic_bp": "Blood pressure (lower / diastolic)",
        "hemoglobin": "Haemoglobin",
    },
    "bn": {
        "fasting_glucose": "খালি পেটে রক্তে গ্লুকোজ",
        "systolic_bp": "রক্তচাপ (উপরের / সিস্টোলিক)",
        "diastolic_bp": "রক্তচাপ (নিচের / ডায়াস্টোলিক)",
        "hemoglobin": "হিমোগ্লোবিন",
    },
}

_RISK_LABELS = {
    "en": {
        "normal": "within the normal range",
        "elevated": "slightly raised",
        "prediabetes": "pre-diabetes range",
        "diabetes_range": "diabetes range",
        "hypoglycemia": "low blood sugar",
        "hypertension_stage1": "high blood pressure, stage 1",
        "hypertension_stage2": "high blood pressure, stage 2",
        "hypertensive_crisis": "dangerously high blood pressure",
        "mild_anemia": "mild anaemia",
        "moderate_anemia": "moderate anaemia",
        "severe_anemia": "severe anaemia",
    },
    "bn": {
        "normal": "স্বাভাবিক সীমার মধ্যে",
        "elevated": "কিছুটা বেশি",
        "prediabetes": "প্রি-ডায়াবেটিসের মাত্রা",
        "diabetes_range": "ডায়াবেটিসের মাত্রা",
        "hypoglycemia": "রক্তে শর্করা কম",
        "hypertension_stage1": "উচ্চ রক্তচাপ, ধাপ ১",
        "hypertension_stage2": "উচ্চ রক্তচাপ, ধাপ ২",
        "hypertensive_crisis": "বিপজ্জনকভাবে উচ্চ রক্তচাপ",
        "mild_anemia": "মৃদু রক্তস্বল্পতা",
        "moderate_anemia": "মাঝারি রক্তস্বল্পতা",
        "severe_anemia": "তীব্র রক্তস্বল্পতা",
    },
}

_CONDITIONS = {
    "en": {"diabetes": "diabetes", "hypertension": "high blood pressure", "anemia": "anaemia",
           "pregnancy": "pregnancy", "chronic_kidney_disease": "kidney disease",
           "knee_osteoarthritis": "knee osteoarthritis"},
    "bn": {"diabetes": "ডায়াবেটিস", "hypertension": "উচ্চ রক্তচাপ", "anemia": "রক্তস্বল্পতা",
           "pregnancy": "গর্ভাবস্থা", "chronic_kidney_disease": "কিডনি রোগ",
           "knee_osteoarthritis": "হাঁটুর অস্টিওআর্থ্রাইটিস"},
}

_BMI_CATEGORIES = {
    "bn": {"underweight": "কম ওজন", "normal": "স্বাভাবিক ওজন", "overweight": "অতিরিক্ত ওজন",
           "obese": "স্থূলতা"},
}


def _term(table: dict, lang: str, key: str) -> str:
    """Look a key up in a bilingual table, falling back to English and then to
    a de-underscored version of the key itself, so an engine value we have not
    translated yet still reads as words rather than a raw identifier."""
    for candidate in (lang, "en"):
        text = table.get(candidate, {}).get(key)
        if text:
            return text
    return key.replace("_", " ")

_MEAL_NAMES = {
    "en": {"breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner", "snack": "Snack"},
    "bn": {"breakfast": "সকালের নাস্তা", "lunch": "দুপুরের খাবার", "dinner": "রাতের খাবার", "snack": "হালকা নাস্তা"},
}

_WEEKDAY_NAMES = {
    "en": {"saturday": "Saturday", "sunday": "Sunday", "monday": "Monday", "tuesday": "Tuesday",
           "wednesday": "Wednesday", "thursday": "Thursday", "friday": "Friday"},
    "bn": {"saturday": "শনিবার", "sunday": "রবিবার", "monday": "সোমবার", "tuesday": "মঙ্গলবার",
           "wednesday": "বুধবার", "thursday": "বৃহস্পতিবার", "friday": "শুক্রবার"},
}

# recipe dataset vocabularies (data/recipe/schema.md); English is the source
_RECIPE_CATEGORIES = {
    "bn": {
        "Vegetable": "সবজি", "Fish": "মাছ", "Meat": "মাংস", "Bhorta": "ভর্তা",
        "Rice & Grain": "ভাত ও শস্য", "Bread & Pitha": "রুটি ও পিঠা",
        "Leafy Green": "শাক", "Sweet": "মিষ্টি", "Dal": "ডাল", "Snack": "নাস্তা",
        "Egg": "ডিম", "Beverage": "পানীয়", "Salad & Chutney": "সালাদ ও চাটনি",
    },
}
_FREQUENCY_TIERS = {
    "en": {
        "Daily staple": "an everyday staple", "Near-daily": "cooked almost daily",
        "Very frequent": "cooked most days", "Frequent": "cooked a few times a week",
        "Weekly": "cooked about weekly", "Regular": "cooked a few times a month",
        "Occasional": "cooked occasionally", "Festive/seasonal": "a festive or seasonal dish",
        "Rare/special": "a special-occasion dish",
    },
    "bn": {
        "Daily staple": "প্রতিদিনের প্রধান খাবার", "Near-daily": "প্রায় প্রতিদিন রান্না হয়",
        "Very frequent": "সপ্তাহের বেশিরভাগ দিন রান্না হয়",
        "Frequent": "সপ্তাহে কয়েকবার রান্না হয়", "Weekly": "সপ্তাহে প্রায় একবার রান্না হয়",
        "Regular": "মাসে কয়েকবার রান্না হয়", "Occasional": "মাঝে মাঝে রান্না হয়",
        "Festive/seasonal": "উৎসব বা মৌসুমি রান্না", "Rare/special": "বিশেষ উপলক্ষের রান্না",
    },
}
_TOP_FOODS_IN_REPORT = 8
_TOP_RECIPES_IN_REPORT = 6


def template_report(patient_name: str, result: dict, lang: str = "en",
                    comment: str = "") -> str:
    t = _LABELS.get(lang, _LABELS["en"])
    meal_names = _MEAL_NAMES.get(lang, _MEAL_NAMES["en"])
    name_key = "name_bn" if lang == "bn" else "name_en"

    lines = [t["greeting"].format(name=patient_name), "", t["intro"], ""]

    lines.append(f"## {t['findings']}")
    anthro = result.get("anthropometrics", {})
    if anthro:
        lines.append("- " + t["bmi"].format(
            bmi=anthro.get("bmi"),
            category=_term(_BMI_CATEGORIES, lang, anthro.get("bmi_category") or "")))
    flags = result.get("risk_flags", [])
    abnormal = [f for f in flags if f.get("risk") != "none"]
    if abnormal:
        for f in abnormal:
            name = _term(_BIOMARKERS, lang, f["biomarker"])
            status = _term(_RISK_LABELS, lang, f["label"])
            lines.append(f"- {name}: {f['value']} {f['unit']} — {status}")
    else:
        lines.append("- " + t["no_flags"])
    conditions = result.get("conditions") or []
    if conditions:
        lines.append("- " + t["conditions"].format(
            items=", ".join(_term(_CONDITIONS, lang, c) for c in conditions)))
    lines.append("")

    rationales = result.get("nutrition", {}).get("rationales") or {}
    # engine 0.7.0 onwards: each finding in the patient's words and language;
    # older assessments carry only the rules file's wording for the physician
    in_patient_words = result.get("nutrition", {}).get("patient_rationales") or {}
    if rationales:
        lines.append(f"## {t['why']}")
        for finding, why in rationales.items():
            said = (in_patient_words.get(finding) or {}).get(lang)
            lines.append(f"- {said}" if said else f"- {_term(_CONDITIONS, lang, finding)}: {why}")
        lines.append("")

    meal_plan = result.get("nutrition", {}).get("meal_plan", {})
    target = meal_plan.get("target_kcal", anthro.get("target_kcal", ""))

    def meal_lines(meals: dict, indent: str) -> None:
        for meal, items in meals.items():
            item_text = ", ".join(
                f"{item.get(name_key) or item['name_en']} ({item['qty_g']} g)" for item in items
            )
            lines.append(f"{indent}- {meal_names.get(meal, meal)}: {item_text}")

    def salt_line(day: dict, indent: str) -> None:
        # engine 0.6.0 onwards: the cooking salt that keeps the day under the
        # sodium limit, which can be less than the recipes as written use
        if day.get("salt_g") is None:
            return
        key = "salt_less" if day["salt_g"] < day.get("recipe_salt_g", 0) else "salt"
        lines.append(f"{indent}- " + t[key].format(g=day["salt_g"], recipe=day.get("recipe_salt_g")))

    totals = meal_plan.get("totals") or {}
    if meal_plan.get("days"):
        # engine 0.4.0 onwards: a week, Saturday to Friday
        weekdays = _WEEKDAY_NAMES.get(lang, _WEEKDAY_NAMES["en"])
        lines.append(f"## {t['diet_week'].format(kcal=target)}")
        for day in meal_plan["days"]:
            lines.append(f"- {weekdays.get(day.get('weekday'), day.get('day'))}")
            meal_lines(day.get("meals") or {}, "  ")
            salt_line(day, "  ")
        if totals.get("kcal"):
            lines.append("- " + t["diet_week_total"].format(kcal=round(totals["kcal"])))
    else:
        lines.append(f"## {t['diet'].format(kcal=target)}")
        meal_lines(meal_plan.get("meals") or {}, "")
        salt_line(meal_plan, "")
        if totals.get("kcal"):
            lines.append("- " + t["diet_total"].format(kcal=round(totals["kcal"])))
    if meal_plan.get("salt_g") is not None:
        lines.append("- " + t["salt_note"])
    lines.append("")

    nutrition = result.get("nutrition", {})
    top_foods = (nutrition.get("top_foods") or [])[:_TOP_FOODS_IN_REPORT]
    if top_foods:
        lines.append(f"## {t['foods']}")
        lines.append("- " + ", ".join(f.get(name_key) or f["name_en"] for f in top_foods))
        lines.append("")

    top_recipes = (nutrition.get("top_recipes") or [])[:_TOP_RECIPES_IN_REPORT]
    if top_recipes:
        lines.append(f"## {t['recipes']}")
        for recipe in top_recipes:
            category = recipe.get("category") or ""
            tier = recipe.get("frequency_tier") or ""
            lines.append("- " + t["recipe_line"].format(
                name=recipe.get(name_key) or recipe["name_en"],
                category=_term(_RECIPE_CATEGORIES, lang, category) if category else "",
                grams=round(recipe.get("serving_size_g") or 0),
                kcal=round(recipe.get("per_serving_kcal") or 0),
                tier=_term(_FREQUENCY_TIERS, lang, tier) if tier else "",
            ))
        lines.append("")

    plan = result.get("exercise_plan", {})
    lines.append(f"## {t['exercise']}")
    if plan.get("time"):
        hr_lo, hr_hi = plan["intensity"]["target_hr_bpm"]
        lines.append("- " + t["aerobic"].format(
            min=plan["time"]["aerobic_min_per_session"],
            days=plan["frequency"]["aerobic_days"],
            lo=hr_lo, hi=hr_hi,
        ))
        lines.append("- " + t["strength"].format(days=plan["frequency"]["strength_days"]))
        lines.append("- " + t["flexibility"].format(days=plan["frequency"]["flexibility_days"]))
        for group in ("aerobic", "strength", "flexibility"):
            for ex in plan.get("type", {}).get(group, []):
                label = ex.get(name_key) or ex["name_en"]
                lines.append(f"  - {label}")
        if plan.get("progression"):
            lines.append("- " + t["progression"].format(text=plan["progression"]))
    lines.append("")

    exclusions = result.get("exclusions") or {}
    if exclusions.get("food_tags") or exclusions.get("exercise_tags"):
        lines.append(t["safety"])
        lines.append("")
    if comment.strip():
        lines.append(t["comment"].format(comment=comment.strip()))
        lines.append("")
    lines.append(t["closing"])
    return "\n".join(lines)
