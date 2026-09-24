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
        "diet_total": "Planned total: about {kcal} kcal/day",
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
        "diet_total": "পরিকল্পিত মোট: প্রায় {kcal} কিলোক্যালরি/দিন",
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
    "en": {"diabetes": "diabetes", "hypertension": "high blood pressure", "anemia": "anaemia"},
    "bn": {"diabetes": "ডায়াবেটিস", "hypertension": "উচ্চ রক্তচাপ", "anemia": "রক্তস্বল্পতা"},
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


def template_report(patient_name: str, result: dict, lang: str = "en",
                    comment: str = "") -> str:
    t = _LABELS.get(lang, _LABELS["en"])
    meal_names = _MEAL_NAMES.get(lang, _MEAL_NAMES["en"])
    name_key = "name_bn" if lang == "bn" else "name_en"

    lines = [t["greeting"].format(name=patient_name), "", t["intro"], ""]

    lines.append(f"## {t['findings']}")
    anthro = result.get("anthropometrics", {})
    if anthro:
        lines.append("- " + t["bmi"].format(bmi=anthro.get("bmi"), category=anthro.get("bmi_category")))
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
    if rationales:
        lines.append(f"## {t['why']}")
        for finding, why in rationales.items():
            lines.append(f"- {_term(_CONDITIONS, lang, finding)}: {why}")
        lines.append("")

    meal_plan = result.get("nutrition", {}).get("meal_plan", {})
    lines.append(f"## {t['diet'].format(kcal=meal_plan.get('target_kcal', anthro.get('target_kcal', '')))}")
    for meal, items in (meal_plan.get("meals") or {}).items():
        item_text = ", ".join(
            f"{item.get(name_key) or item['name_en']} ({item['qty_g']} g)" for item in items
        )
        lines.append(f"- {meal_names.get(meal, meal)}: {item_text}")
    totals = meal_plan.get("totals") or {}
    if totals.get("kcal"):
        lines.append("- " + t["diet_total"].format(kcal=round(totals["kcal"])))
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
