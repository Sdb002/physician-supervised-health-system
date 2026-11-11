const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

// --- session storage ---------------------------------------------------------

export type Role = "admin" | "doctor" | "patient";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  status: "active" | "pending" | "rejected";
  specialty: string;
  license_no: string;
  patient_id: number | null;
  created_at: string;
}

export interface Session {
  token: string;
  user: User;
}

const SESSION_KEY = "hs_session";

export function loadSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) ?? "null");
  } catch {
    return null;
  }
}

export function saveSession(session: Session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const session = loadSession();
  const auth: Record<string, string> = session ? { Authorization: `Bearer ${session.token}` } : {};
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, {
      ...init,
      headers:
        init?.body instanceof FormData
          ? { ...auth, ...init?.headers }
          : { "Content-Type": "application/json", ...auth, ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "Cannot reach the API — is the backend running on " + API + "?");
  }
  if (!res.ok) {
    // expired/invalid session: drop it and return to the portal chooser
    if (res.status === 401 && session && !path.startsWith("/auth/")) {
      clearSession();
      window.location.href = "/login";
    }
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export interface Biomarkers {
  fasting_glucose?: number | null;
  systolic_bp?: number | null;
  diastolic_bp?: number | null;
  hemoglobin?: number | null;
}

export interface Patient {
  id: number;
  name: string;
  sex: "male" | "female";
  birth_year: number;
  height_cm: number;
  pregnant: boolean;
  /** 1-3 while pregnant; null when not pregnant or not recorded */
  pregnancy_trimester: number | null;
  conditions: string[];
  /** keys of the engine's dietary restrictions, e.g. "no_beef" */
  dietary_restrictions: string[];
  /** the single foods and dishes the patient does not eat, beyond those */
  excluded_foods: ExcludedFood[];
  fitness_level: string;
  /** sedentary | light | moderate | active; null = not recorded */
  activity_level: string | null;
  notes: string;
  created_at: string;
}

/** A food or dish a patient does not eat. A food stands for every form of it
 * in the food table, and takes every dish that uses it along. */
export interface ExcludedFood {
  /** a food-table or recipe id; the forms send it back with the name */
  id: string;
  kind: "food" | "recipe";
  name_en: string;
  name_bn: string;
}

/** Something the patient forms can exclude (GET /foods/catalogue). */
export interface ExcludableFood extends ExcludedFood {
  /** food group, or the dish's recipe category */
  food_group: string;
  /** table rows left out with the food: raw and boiled, each cultivar, and
   * every row named as a form of it */
  forms: number;
  /** dishes left out with it; 1 for a dish */
  dishes: number;
  /** the names of those rows, so a search finds the food by any of them */
  keywords: string;
}

/** A chosen food or dish as the forms send it: the id, with the name it was
 * shown under. After a food-table replacement an id can be another food; the
 * name lets the API tell an entry sent back unchanged from a fresh pick. */
export type ExcludedFoodPick = Pick<ExcludedFood, "id" | "name_en">;

/** A patient as the forms send one: excluded foods go by id and name. */
export type PatientIn = Omit<Patient, "id" | "created_at" | "excluded_foods"> & {
  excluded_foods: ExcludedFoodPick[];
};

/** A change to a patient's record: only the fields sent are changed. */
export type PatientUpdate = Partial<
  Pick<
    PatientIn,
    | "name"
    | "height_cm"
    | "pregnant"
    | "pregnancy_trimester"
    | "conditions"
    | "dietary_restrictions"
    | "excluded_foods"
    | "fitness_level"
    | "activity_level"
    | "notes"
  >
>;

export interface Visit {
  id: number;
  patient_id: number;
  weight_kg: number;
  biomarkers: Record<string, number>;
  created_at: string;
}

export interface RiskFlag {
  biomarker: string;
  value: number;
  unit: string;
  label: string;
  risk: "none" | "low" | "moderate" | "high" | "critical";
}

export interface RecommendedFood {
  food_id: string;
  name_en: string;
  name_bn: string;
  score: number;
  tags: string[];
  // present on assessments generated after kcal was added to the ranking
  food_group?: string;
  kcal_per_100g?: number;
}

/** A food or dish one of the patient's conditions rules out, with the
 * excluded tags it carries (high_sodium, high_sugar, solid_fat, liver...). */
export interface ConditionAvoidItem {
  food_id?: string;
  recipe_id?: string;
  name_en: string;
  name_bn: string;
  food_group?: string;
  category?: string;
  reasons: string[];
}

/** One condition's foods: what to eat for it (real sources of its
 * nutrients, the most often eaten first) and what its rule leaves out
 * (engine 0.13.0 onwards). */
export interface ConditionFoods {
  condition: string;
  nutrients: string[];
  eat: RecommendedFood[];
  avoid_tags: string[];
  avoid_foods: ConditionAvoidItem[];
  avoid_dishes: ConditionAvoidItem[];
}

/** One of today's tasks: a meal of today's plan, or an exercise group the
 * weekly schedule puts on today (src/api/daily_tasks.py). */
export interface DailyTask {
  key: string;
  kind: "meal" | "exercise";
  /** breakfast | lunch | dinner | snack, or aerobic | strength | flexibility | balance */
  group: string;
  items: (Pick<MealItem, "food_id" | "recipe_id" | "name_en" | "name_bn" | "qty_g" | "servings" | "kcal"> & {
    exercise_id?: string;
    dose?: string;
    use_easier_version?: boolean;
    easier_version?: string;
  })[];
  /** a meal's energy */
  kcal?: number;
  /** brisk activity: minutes for the session */
  minutes?: number | null;
  done: boolean;
}

export type DayStatus = "complete" | "partial" | "missed" | "today" | "none";

export interface TodayTasks {
  /** the clinic's calendar day, YYYY-MM-DD */
  date: string;
  weekday: string;
  plan: { visit_id: number; approved_at: string; approved_by: string } | null;
  tasks: DailyTask[];
  done: number;
  total: number;
  streak: { current: number; best: number };
  /** the last seven days, oldest first, today last */
  recent: { date: string; weekday: string; status: DayStatus }[];
}

export interface RecipeIngredient {
  name_en: string;
  name_bn: string;
  household_measure: string;
  qty_g: number;
  optional: boolean;
}

/** A ranked household recipe. Fields beyond per_serving_kcal are present on
 * assessments from engine 0.2.0 onwards (the 250-recipe dataset). */
export interface RecommendedRecipe {
  recipe_id: string;
  name_en: string;
  name_bn: string;
  score: number;
  per_serving_kcal: number;
  tags?: string[];
  category?: string;
  diet_type?: string;
  meal_type?: string[];
  /** 1-10: how commonly the dish is cooked at home (10 = most common) */
  weekly_frequency_score?: number | null;
  frequency_tier?: string;
  servings?: number;
  serving_size_g?: number | null;
  cooking_method?: string;
  total_time_min?: number | null;
  per_serving?: Record<string, number>;
  ingredients?: RecipeIngredient[];
  steps?: string[];
  notes?: string;
}

/** One line of the day's meal plan: a household dish (recipe_id; engine
 * 0.3.0 onwards) or a single food (food_id - every line before 0.3.0, and
 * the snack's fruit after). */
export interface MealItem {
  food_id?: string;
  recipe_id?: string;
  name_en: string;
  name_bn: string;
  qty_g: number;
  kcal: number;
  /** the portion's carbohydrate, fat and sodium (engine 0.5.0 onwards) */
  carb_g?: number;
  fat_g?: number;
  sodium_mg?: number;
  /** dishes only: the oil, ghee or butter the portion is cooked in */
  cooking_fat_g?: number;
  /** dishes only: the salt the portion is cooked with (engine 0.6.0 onwards);
   * sodium_mg counts this much salt, which can be less than the recipe lists */
  salt_g?: number;
  /** staple | dal | main | vegetable | side | fruit (engine-planned lines) */
  course?: string;
  category?: string;
  servings?: number;
  serving_size_g?: number;
}

/** A day's cooking salt (engine 0.6.0 onwards): the grams that keep the day
 * under the sodium limit, beside what the recipes as written would use. */
export interface PlanSalt {
  salt_g?: number;
  recipe_salt_g?: number;
}

export interface AssessmentResult {
  age: number;
  anthropometrics: {
    bmi: number;
    bmi_category: string;
    target_kcal: number;
    ree_kcal: number;
    tdee_kcal: number;
    /** what the target was worked out from (engine 0.5.0 onwards) */
    basis?: {
      weight_kg: number;
      height_cm: number;
      age: number;
      sex: string;
      equation: string;
      activity: string;
      activity_factor: number;
      /** no activity level was given, so the engine's default was used */
      activity_assumed: boolean;
      adjustment_kcal: number;
      floor_kcal: number;
      floor_applied: boolean;
      /** pregnancy only (engine 0.7.0 onwards): the trimester's extra energy */
      pregnancy?: { trimester: number | null; extra_kcal: number };
    };
  };
  risk_flags: RiskFlag[];
  bp_category: string | null;
  overall_risk: string;
  conditions: string[];
  /** what the patient does not eat (engine 0.7.0 onwards) */
  dietary_restrictions?: string[];
  /** the single foods and dishes the patient does not eat (engine 0.11.0 onwards) */
  excluded_foods?: ExcludedFood[];
  /** what the reviewing physician should check before approving (engine
   * 0.7.0 onwards); never sent to the patient */
  cautions?: string[];
  exclusions: {
    food_tags: string[];
    exercise_tags: string[];
    /** every row and dish the patient's excluded foods take out (engine 0.11.0 onwards) */
    food_ids?: string[];
    recipe_ids?: string[];
  };
  nutrition: {
    group: string;
    targets: Record<string, number>;
    limits: Record<string, number>;
    /** the findings behind the emphasis (engine 0.8.0 onwards) */
    findings?: string[];
    emphasize: string[];
    rationales: Record<string, string>;
    /** each finding in the patient's words (engine 0.7.0 onwards) */
    patient_rationales?: Record<string, { en: string; bn: string }>;
    scoring_backend?: "ml" | "linear";
    recipe_scoring_backend?: "ml" | "linear";
    top_foods: RecommendedFood[];
    top_recipes: RecommendedRecipe[];
    /** per condition, what to eat and what to avoid (engine 0.13.0 onwards) */
    condition_foods?: ConditionFoods[];
    meal_plan: {
      /** a week, Saturday to Friday (engine 0.4.0 onwards) */
      days?: ({
        day: number;
        weekday: string;
        meals: Record<string, MealItem[]>;
        totals: Record<string, number>;
      } & PlanSalt)[];
      /** a single day's plan, for every day (assessments before engine 0.4.0) */
      meals?: Record<string, MealItem[]>;
      /** a week plan's average day */
      totals: Record<string, number>;
      /** a week plan's average day; a one-day plan's own salt */
      salt_g?: number;
      recipe_salt_g?: number;
      target_kcal: number;
      coverage: Record<string, number>;
      /** nutrients the food table records for no food (no coverage figure) */
      untracked?: string[];
      note?: string;
    };
  };
  exercise_plan: {
    note?: string;
    /** balance_days only for patients 65 and over (engine 0.12.0 onwards) */
    frequency?: { aerobic_days: number; strength_days: number; flexibility_days: number; balance_days?: number };
    intensity?: { level: string; target_hr_bpm: [number, number] };
    time?: { aerobic_min_per_session: number; aerobic_min_per_week: number };
    type?: Record<string, ExerciseItem[]>;
    volume?: { met_min_per_week: number; est_kcal_per_week: number; volume_factor: number };
    progression?: string;
    /** "ml" when the trained exercise model ranked the plan */
    scoring_backend?: string;
  };
}

/** One exercise of the prescription. Everything after `equipment` comes from
 * the exercise safety dataset (engine 0.12.0); older plans have only a name. */
export interface ExerciseItem {
  exercise_id: string;
  name_en: string;
  name_bn: string;
  /** aerobic exercises only (2024 Compendium) */
  met_value: number | null;
  equipment: string;
  category?: string;
  intensity_level?: string;
  fitness_level?: string;
  /** the dose as a patient reads it (none for an aerobic activity: its
   * minutes are the prescription's) */
  dose?: string;
  /** the dataset's dose text as the source gives it, for staff */
  dose_source?: string;
  how_to?: string;
  easier_version?: string;
  safety_notes?: string;
  /** the dataset's note for each of the patient's conditions it has one for;
   * `modify`: the exercise is allowed with care for that condition */
  condition_notes?: { condition: string; note: string; modify: boolean }[];
  /** 65 and over, and suitable at that age only in its easier version */
  use_easier_version?: boolean;
  video?: { url: string; title: string; channel: string; match: string } | null;
  source?: { name: string; url: string };
}

export interface Assessment {
  id: number;
  visit_id: number;
  status: "pending" | "approved" | "rejected";
  result: AssessmentResult;
  engine_version: string;
  created_at: string;
}

export interface QueueItem {
  assessment: Assessment;
  patient: Patient;
  visit: Visit;
}

export interface DoctorNote {
  id: number;
  visit_id: number;
  physician_name: string;
  note: string;
  created_at: string;
  updated_at: string | null;
}

export interface Report {
  visit_id: number;
  patient_name: string;
  lang: string;
  source: "llm" | "template";
  text: string;
  approved_by: string;
  approved_at: string;
  /** the engine that built this plan, and the one running now */
  engine_version?: string;
  current_engine_version?: string;
  comment: string;
  visit_date: string | null;
  result: AssessmentResult;
  notes: DoctorNote[];
}

export interface OcrResult {
  biomarkers: Biomarkers;
  notes: string;
  /** "PDF text" or "RapidOCR" (read on this server), or "Claude" */
  engine?: string;
  /** the text lines the local reader saw, kept with the visit */
  text?: string[];
}

export interface PatientProfileIn {
  sex: "male" | "female";
  birth_year: number;
  height_cm: number;
  pregnant?: boolean;
  pregnancy_trimester?: number | null;
  conditions?: string[];
  dietary_restrictions?: string[];
  /** picks from the food catalogue */
  excluded_foods?: ExcludedFoodPick[];
  fitness_level?: string;
  activity_level?: string | null;
}

export interface RegisterIn {
  name: string;
  email: string;
  password: string;
  role: "doctor" | "patient";
  specialty?: string;
  license_no?: string;
  profile?: PatientProfileIn;
}

export interface AdminStats {
  patients: number;
  doctors_active: number;
  doctors_pending: number;
  visits: number;
  assessments_pending: number;
  assessments_approved: number;
  assessments_rejected: number;
}

export interface AuditEntry {
  id: number;
  actor: string;
  action: string;
  entity: string;
  entity_id: number | null;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface VisitStatusItem {
  visit: Visit;
  status: "pending" | "approved" | "rejected";
  assessment_id: number | null;
  report_ready: boolean;
}

export interface PatientDashboard {
  patient: Patient;
  items: VisitStatusItem[];
}

/** Something the plan editor can add: a household dish or a single food. */
export interface AllowedFood {
  kind?: "food" | "recipe";
  food_id?: string;
  recipe_id?: string;
  name_en: string;
  name_bn: string;
  /** food group, or the dish's recipe category */
  food_group: string;
  kcal_per_100g: number;
  serving_size_g?: number;
  /** other names a search should find it by */
  keywords?: string;
}

type PlanEditItem = { food_id?: string; recipe_id?: string; qty_g: number; name_en?: string };

export interface PlanEdit {
  /** a week plan, one meals mapping per day in plan order */
  days?: Record<string, PlanEditItem[]>[];
  /** a one-day plan from an assessment made before weekly plans */
  meals?: Record<string, PlanEditItem[]>;
  exercise?: {
    aerobic_days: number;
    strength_days: number;
    flexibility_days: number;
    balance_days?: number;
    aerobic_min_per_session: number;
    type: Record<string, string[]>;
  };
}

export const api = {
  register: (data: RegisterIn) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { email: string; password: string; role?: Role }) =>
    request<Session>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  me: () => request<User>("/auth/me"),

  adminStats: () => request<AdminStats>("/admin/stats"),
  adminDoctors: (status?: "pending" | "active" | "rejected") =>
    request<User[]>(`/admin/doctors${status ? `?status=${status}` : ""}`),
  adminDecideDoctor: (userId: number, decision: "approved" | "rejected") =>
    request<User>(`/admin/doctors/${userId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }),
  adminPatients: () =>
    request<{ patient: Patient; account_email: string | null }[]>("/admin/patients"),
  adminUsers: () => request<User[]>("/admin/users"),
  adminAudit: (limit = 25) => request<AuditEntry[]>(`/admin/audit?limit=${limit}`),

  myDashboard: () => request<PatientDashboard>("/me/dashboard"),
  myTasks: () => request<TodayTasks>("/me/tasks"),
  tickTask: (key: string, done: boolean) =>
    request<TodayTasks>(`/me/tasks/${encodeURIComponent(key)}`, {
      method: "PUT",
      body: JSON.stringify({ done }),
    }),

  health: () =>
    request<{ status: string; llm_configured: boolean; ocr_reader?: "RapidOCR" | "Claude" | null }>("/health"),

  listPatients: () => request<Patient[]>("/patients"),
  getPatient: (id: number | string) => request<Patient>(`/patients/${id}`),
  createPatient: (data: PatientIn) =>
    request<Patient>("/patients", { method: "POST", body: JSON.stringify(data) }),
  /** every dish and everyday food a patient record can exclude; needs no sign-in */
  foodCatalogue: () => request<ExcludableFood[]>("/foods/catalogue"),
  updatePatient: (id: number | string, data: PatientUpdate) =>
    request<Patient>(`/patients/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  listVisits: (patientId: number | string) => request<Visit[]>(`/patients/${patientId}/visits`),

  getPatientAccount: (patientId: number | string) =>
    request<{ email: string | null }>(`/patients/${patientId}/account`),
  createPatientAccount: (patientId: number | string, data: { email: string; password: string }) =>
    request<User>(`/patients/${patientId}/account`, { method: "POST", body: JSON.stringify(data) }),

  createVisit: (patientId: number | string, data: { weight_kg: number; biomarkers: Biomarkers; ocr_raw?: object | null }) =>
    request<Assessment>(`/patients/${patientId}/visits`, { method: "POST", body: JSON.stringify(data) }),

  ocr: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<OcrResult>("/intake/ocr", { method: "POST", body: form });
  },

  reviewFoods: (assessmentId: number | string) =>
    request<AllowedFood[]>(`/review/${assessmentId}/foods`),
  recomputePlan: (assessmentId: number | string, data: PlanEdit) =>
    request<AssessmentResult>(`/review/${assessmentId}/recompute`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  reviewQueue: () => request<QueueItem[]>("/review/queue"),
  getAssessment: (id: number | string) => request<QueueItem>(`/review/${id}`),
  decide: (assessmentId: number | string, data: { decision: "approved" | "rejected"; comment?: string; edited_result?: object | null }) =>
    request(`/review/${assessmentId}/decision`, { method: "POST", body: JSON.stringify(data) }),

  report: (visitId: number | string, lang: "en" | "bn", useLlm: boolean) =>
    request<Report>(`/report/${visitId}?lang=${lang}&use_llm=${useLlm}`),

  listNotes: (visitId: number | string) => request<DoctorNote[]>(`/visits/${visitId}/notes`),
  addNote: (visitId: number | string, data: { note: string }) =>
    request<DoctorNote>(`/visits/${visitId}/notes`, { method: "POST", body: JSON.stringify(data) }),
  updateNote: (visitId: number | string, noteId: number, data: { note: string }) =>
    request<DoctorNote>(`/visits/${visitId}/notes/${noteId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
