import type { MealItem, PlanSalt } from "@/lib/api";
import type { Lang } from "@/lib/use-lang";

/* Patient-facing wording for engine identifiers. Display vocabulary only -
 * it mirrors the tables in src/api/report_template.py so the screens and the
 * written report use the same words. No thresholds or clinical logic belong
 * here; the engine decides every level and label. */

const BIOMARKERS: Record<Lang, Record<string, string>> = {
  en: {
    fasting_glucose: "Fasting blood glucose",
    systolic_bp: "Blood pressure, upper",
    diastolic_bp: "Blood pressure, lower",
    hemoglobin: "Haemoglobin",
  },
  bn: {
    fasting_glucose: "খালি পেটে রক্তে গ্লুকোজ",
    systolic_bp: "রক্তচাপ (উপরের)",
    diastolic_bp: "রক্তচাপ (নিচের)",
    hemoglobin: "হিমোগ্লোবিন",
  },
};

const FINDINGS: Record<Lang, Record<string, string>> = {
  en: {
    normal: "Normal",
    elevated: "Slightly raised",
    prediabetes: "Pre-diabetes range",
    diabetes_range: "Diabetes range",
    hypoglycemia: "Low blood sugar",
    hypertension_stage1: "High blood pressure, stage 1",
    hypertension_stage2: "High blood pressure, stage 2",
    hypertensive_crisis: "Dangerously high blood pressure",
    mild_anemia: "Mild anaemia",
    moderate_anemia: "Moderate anaemia",
    severe_anemia: "Severe anaemia",
  },
  bn: {
    normal: "স্বাভাবিক",
    elevated: "কিছুটা বেশি",
    prediabetes: "প্রি-ডায়াবেটিসের মাত্রা",
    diabetes_range: "ডায়াবেটিসের মাত্রা",
    hypoglycemia: "রক্তে শর্করা কম",
    hypertension_stage1: "উচ্চ রক্তচাপ, ধাপ ১",
    hypertension_stage2: "উচ্চ রক্তচাপ, ধাপ ২",
    hypertensive_crisis: "বিপজ্জনকভাবে উচ্চ রক্তচাপ",
    mild_anemia: "মৃদু রক্তস্বল্পতা",
    moderate_anemia: "মাঝারি রক্তস্বল্পতা",
    severe_anemia: "তীব্র রক্তস্বল্পতা",
  },
};

const CONDITIONS: Record<Lang, Record<string, string>> = {
  en: {
    diabetes: "Diabetes",
    hypertension: "High blood pressure",
    anemia: "Anaemia",
    pregnancy: "Pregnancy",
    chronic_kidney_disease: "Kidney disease",
    knee_osteoarthritis: "Knee osteoarthritis",
  },
  bn: {
    diabetes: "ডায়াবেটিস",
    hypertension: "উচ্চ রক্তচাপ",
    anemia: "রক্তস্বল্পতা",
    pregnancy: "গর্ভাবস্থা",
    chronic_kidney_disease: "কিডনি রোগ",
    knee_osteoarthritis: "হাঁটুর অস্টিওআর্থ্রাইটিস",
  },
};

/* The engine's body mass index categories (src/clinical/bmi.py). */
const BMI_CATEGORIES: Record<Lang, Record<string, string>> = {
  en: { underweight: "Underweight", normal: "Normal", overweight: "Overweight", obese: "Obese" },
  bn: { underweight: "কম ওজন", normal: "স্বাভাবিক ওজন", overweight: "অতিরিক্ত ওজন", obese: "স্থূলতা" },
};

const RISK_LEVELS: Record<Lang, Record<string, string>> = {
  en: {
    none: "Normal",
    low: "Slightly outside the normal range",
    moderate: "Needs attention",
    high: "High",
    critical: "Needs prompt medical attention",
  },
  bn: {
    none: "স্বাভাবিক",
    low: "স্বাভাবিকের সামান্য বাইরে",
    moderate: "মনোযোগ প্রয়োজন",
    high: "বেশি",
    critical: "দ্রুত চিকিৎসা প্রয়োজন",
  },
};

const MEALS: Record<Lang, Record<string, string>> = {
  en: { breakfast: "Breakfast", lunch: "Lunch", dinner: "Dinner", snack: "Snack" },
  bn: { breakfast: "সকালের নাস্তা", lunch: "দুপুরের খাবার", dinner: "রাতের খাবার", snack: "হালকা নাস্তা" },
};

/** Falls back to English, then to the identifier as words, so an engine
 * value we have not translated yet still reads as language. */
function term(table: Record<Lang, Record<string, string>>, lang: Lang, key: string) {
  const text = table[lang][key] ?? table.en[key] ?? key.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export const biomarkerName = (key: string, lang: Lang = "en") => term(BIOMARKERS, lang, key);
export const findingName = (label: string, lang: Lang = "en") => term(FINDINGS, lang, label);
export const conditionName = (key: string, lang: Lang = "en") => term(CONDITIONS, lang, key);
export const bmiCategoryName = (key: string, lang: Lang = "en") => term(BMI_CATEGORIES, lang, key);
export const riskWords = (risk: string, lang: Lang = "en") => term(RISK_LEVELS, lang, risk);
export const mealName = (key: string, lang: Lang = "en") => term(MEALS, lang, key);

export const MEAL_ORDER = ["breakfast", "lunch", "dinner", "snack"] as const;

/* Weekly plans run Saturday to Friday, the Bangladeshi week (engine 0.4.0). */
const WEEKDAYS: Record<Lang, Record<string, string>> = {
  en: {
    saturday: "Saturday", sunday: "Sunday", monday: "Monday", tuesday: "Tuesday",
    wednesday: "Wednesday", thursday: "Thursday", friday: "Friday",
  },
  bn: {
    saturday: "শনিবার", sunday: "রবিবার", monday: "সোমবার", tuesday: "মঙ্গলবার",
    wednesday: "বুধবার", thursday: "বৃহস্পতিবার", friday: "শুক্রবার",
  },
};

const WEEKDAYS_SHORT: Record<Lang, Record<string, string>> = {
  en: {
    saturday: "Sat", sunday: "Sun", monday: "Mon", tuesday: "Tue",
    wednesday: "Wed", thursday: "Thu", friday: "Fri",
  },
  bn: {
    saturday: "শনি", sunday: "রবি", monday: "সোম", tuesday: "মঙ্গল",
    wednesday: "বুধ", thursday: "বৃহঃ", friday: "শুক্র",
  },
};

export const weekdayName = (key: string, lang: Lang = "en", short = false) =>
  term(short ? WEEKDAYS_SHORT : WEEKDAYS, lang, key);

/** Today's weekday key; Date.getDay() counts from Sunday = 0. */
const JS_DAY_KEYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
export const todayWeekday = () => JS_DAY_KEYS[new Date().getDay()];

/** One day of a plan, whatever the plan's age: a week plan's day, or the
 * single "every day" plan of an assessment made before engine 0.4.0. */
export interface PlanDayView extends PlanSalt {
  day: number;
  /** absent for a one-day plan, which applies to every day */
  weekday?: string;
  meals: Record<string, MealItem[]>;
  totals?: Record<string, number>;
}

export function planDays(plan: ({
  days?: PlanDayView[];
  meals?: Record<string, MealItem[]>;
  totals?: Record<string, number>;
} & PlanSalt) | undefined): PlanDayView[] {
  if (!plan) return [];
  if (plan.days?.length) return plan.days;
  return plan.meals
    ? [{ day: 1, meals: plan.meals, totals: plan.totals, salt_g: plan.salt_g, recipe_salt_g: plan.recipe_salt_g }]
    : [];
}

/** How much less cooking salt a day takes than its recipes list, in percent;
 * 0 when the day is cooked as written, or carries no salt figures (plans
 * from before engine 0.6.0). */
export function saltCutPercent(day: PlanSalt): number {
  if (day.salt_g == null || !day.recipe_salt_g || day.salt_g >= day.recipe_salt_g) return 0;
  return Math.round((1 - day.salt_g / day.recipe_salt_g) * 100);
}

/** Which day to open on: today, if the plan has a day for it. */
export function todayIndex(days: PlanDayView[]): number {
  const today = todayWeekday();
  const index = days.findIndex((d) => d.weekday === today);
  return index >= 0 ? index : 0;
}

/** Mirrors src.diet.food_db.display_name: a food-table row as a person says
 * it ("Guava, green, raw" -> "Guava, green"). The engine names plan foods
 * this way; the editor's catalogue keeps the full table names. */
export function foodDisplayName(name: string): string {
  const kept = name
    .replace(/\s*\([^)]*\)/g, "")
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part && part.toLowerCase() !== "raw");
  return kept.length ? kept.join(", ") : name;
}

/** A plan line's identity: dishes carry a recipe_id, single foods a food_id. */
export const mealItemKey = (item: { recipe_id?: string; food_id?: string }) =>
  item.recipe_id ?? item.food_id ?? "";

const FRACTIONS: Record<number, string> = { 0.25: "¼", 0.5: "½", 0.75: "¾" };

/** 1.5 -> "1½", 0.75 -> "¾"; other values to one decimal place. Bangla gets
 * Bangla digits, the fraction signs are shared. */
function servingAmount(servings: number, lang: Lang): string {
  const whole = Math.floor(servings + 1e-9);
  const rest = Math.round((servings - whole) * 100) / 100;
  const digits = (n: number) => n.toLocaleString(lang === "bn" ? "bn-BD" : "en");
  if (rest === 0) return digits(whole);
  if (FRACTIONS[rest]) return `${whole > 0 ? digits(whole) : ""}${FRACTIONS[rest]}`;
  return servings.toLocaleString(lang === "bn" ? "bn-BD" : "en", { maximumFractionDigits: 1 });
}

/** How much of a plan line to eat: a dish in household servings with its
 * weight ("1½ servings, 365 g"), a single food by weight ("130 g"). */
export function portionText(
  item: { servings?: number; qty_g: number; recipe_id?: string },
  lang: Lang = "en"
): string {
  const grams = lang === "bn" ? `${Math.round(item.qty_g).toLocaleString("bn-BD")} গ্রাম` : `${Math.round(item.qty_g)} g`;
  if (!item.recipe_id || item.servings == null) return grams;
  const amount = servingAmount(item.servings, lang);
  const unit = lang === "bn" ? "পরিবেশন" : item.servings > 1 ? "servings" : "serving";
  return `${amount} ${unit}, ${grams}`;
}

/** Food and exercise names in the reader's language, English as fallback. */
export const localName = (item: { name_en: string; name_bn?: string }, lang: Lang) =>
  (lang === "bn" && item.name_bn) || item.name_en;

/** Dates as people say them ("30 Aug 2026"), not as 8/30/2026, which reads
 * as 8 March to most of the app's users. */
export function formatDate(value: string | Date, lang: Lang = "en", withYear = true) {
  const d = typeof value === "string" ? new Date(value) : value;
  return d.toLocaleDateString(lang === "bn" ? "bn-BD" : "en-GB", {
    day: "numeric",
    month: "short",
    ...(withYear ? { year: "numeric" } : {}),
  });
}
