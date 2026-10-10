/* What a patient record can hold, as the forms offer it. The keys mirror the
 * engine's reference files - conditions: data/reference/contraindications.yaml,
 * dietary restrictions: data/reference/dietary_restrictions.yaml, activity
 * levels: src/clinical/bmi.py - and tests/test_contraindication.py fails if a
 * key is added there and not here. Labels only; the rules stay in the engine. */

export interface Option {
  key: string;
  label: string;
  /** shown under the label where the choice needs explaining */
  hint?: string;
}

/** Diagnosed conditions a physician records. Pregnancy is its own field. */
export const CONDITION_OPTIONS: Option[] = [
  { key: "hypertension", label: "Hypertension" },
  { key: "diabetes", label: "Diabetes" },
  { key: "anemia", label: "Anaemia" },
  { key: "chronic_kidney_disease", label: "Chronic kidney disease" },
  { key: "knee_osteoarthritis", label: "Knee osteoarthritis" },
];

/** The same conditions in the words a patient uses for them. */
export const CONDITION_OPTIONS_PLAIN: Option[] = [
  { key: "hypertension", label: "High blood pressure" },
  { key: "diabetes", label: "Diabetes" },
  { key: "anemia", label: "Anaemia" },
  { key: "chronic_kidney_disease", label: "Kidney disease" },
  { key: "knee_osteoarthritis", label: "Knee osteoarthritis" },
];

/** What the patient does not eat, for faith, choice or allergy. */
export const DIETARY_RESTRICTION_OPTIONS: Option[] = [
  { key: "vegetarian", label: "Vegetarian", hint: "No meat or fish; eggs and dairy eaten" },
  { key: "vegan", label: "Vegan", hint: "No animal foods" },
  { key: "no_beef", label: "No beef" },
  { key: "no_pork", label: "No pork" },
  { key: "no_egg", label: "No eggs" },
  { key: "no_dairy", label: "No milk or dairy" },
  { key: "no_fish", label: "No fish" },
  { key: "no_shellfish", label: "No prawn, crab or shellfish" },
  { key: "no_nuts", label: "No nuts or peanuts" },
  { key: "no_gluten", label: "No wheat or gluten" },
];

/** A usual day, for the energy target. "" = not recorded: the engine then
 * assumes light activity and the report says it was assumed. */
export const ACTIVITY_OPTIONS: Option[] = [
  { key: "sedentary", label: "Sedentary", hint: "Mostly sitting; little walking" },
  { key: "light", label: "Light", hint: "On the feet part of the day; housework, short walks" },
  { key: "moderate", label: "Moderate", hint: "Walking or manual work most of the day" },
  { key: "active", label: "Active", hint: "Heavy manual work or daily sport" },
];

export const TRIMESTER_OPTIONS: Option[] = [
  { key: "1", label: "First (to week 13)" },
  { key: "2", label: "Second (weeks 14 to 27)" },
  { key: "3", label: "Third (week 28 on)" },
];

const label = (options: Option[], key: string) => options.find((o) => o.key === key)?.label ?? key.replace(/_/g, " ");

export const dietaryRestrictionLabel = (key: string) => label(DIETARY_RESTRICTION_OPTIONS, key);
export const activityLabel = (key: string | null | undefined) => (key ? label(ACTIVITY_OPTIONS, key) : "Not recorded");
