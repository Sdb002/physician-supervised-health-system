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
  conditions: string[];
  fitness_level: string;
  notes: string;
  created_at: string;
}

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
    };
  };
  risk_flags: RiskFlag[];
  bp_category: string | null;
  overall_risk: string;
  conditions: string[];
  exclusions: { food_tags: string[]; exercise_tags: string[] };
  nutrition: {
    group: string;
    targets: Record<string, number>;
    limits: Record<string, number>;
    emphasize: string[];
    rationales: Record<string, string>;
    scoring_backend?: "ml" | "linear";
    recipe_scoring_backend?: "ml" | "linear";
    top_foods: RecommendedFood[];
    top_recipes: RecommendedRecipe[];
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
    frequency?: { aerobic_days: number; strength_days: number; flexibility_days: number };
    intensity?: { level: string; target_hr_bpm: [number, number] };
    time?: { aerobic_min_per_session: number; aerobic_min_per_week: number };
    type?: Record<string, { exercise_id: string; name_en: string; name_bn: string; met_value: number; equipment: string }[]>;
    volume?: { met_min_per_week: number; est_kcal_per_week: number; volume_factor: number };
    progression?: string;
  };
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
  comment: string;
  visit_date: string | null;
  result: AssessmentResult;
  notes: DoctorNote[];
}

export interface OcrResult {
  biomarkers: Biomarkers;
  notes: string;
}

export interface PatientProfileIn {
  sex: "male" | "female";
  birth_year: number;
  height_cm: number;
  pregnant?: boolean;
  conditions?: string[];
  fitness_level?: string;
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

  health: () => request<{ status: string; llm_configured: boolean }>("/health"),

  listPatients: () => request<Patient[]>("/patients"),
  getPatient: (id: number | string) => request<Patient>(`/patients/${id}`),
  createPatient: (data: Omit<Patient, "id" | "created_at">) =>
    request<Patient>("/patients", { method: "POST", body: JSON.stringify(data) }),
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
