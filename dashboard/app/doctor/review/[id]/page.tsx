"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AllowedFood, api, AssessmentResult, MealItem, QueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  conditionName,
  foodDisplayName,
  formatDate,
  mealItemKey,
  mealName,
  planDays,
  portionText,
  weekdayName,
} from "@/lib/clinical-terms";
import { DayPicker, WeekPlan } from "@/components/week-plan";
import { PlanNutrition } from "@/components/plan-nutrition";
import { dietaryRestrictionLabel } from "@/lib/patient-options";
import { pid } from "@/lib/format";
import { riskLabel } from "@/lib/triage";
import { FoodCombobox } from "@/components/FoodCombobox";
import { FindingsList } from "@/components/findings";
import { IconAlert, IconCheck, IconRx, IconX } from "@/components/icons";
import { RecommendedFoodsList, RecommendedRecipesList } from "@/components/recommendations";
import {
  Badge,
  Card,
  ErrorNote,
  Field,
  PageHeader,
  PatientBanner,
  Skeleton,
  buttonDanger,
  buttonPrimary,
  buttonSecondary,
  inputClass,
  linkButton,
} from "@/components/ui";

const MEAL_ORDER = ["breakfast", "lunch", "dinner", "snack"];
const EXERCISE_GROUPS = ["aerobic", "strength", "flexibility"] as const;
const GROUP_NAMES: Record<string, string> = { aerobic: "Aerobic", strength: "Strength", flexibility: "Flexibility" };

interface DraftMealItem {
  /** exactly one of these: a household dish or a single food */
  recipe_id?: string;
  food_id?: string;
  name_en: string;
  name_bn: string;
  qty_g: number;
  /** energy density from the recipe/food data (0 when unknown → kcal shown after apply) */
  kcal_per_100g: number;
  /** a dish's serving weight, so the editor can say how many servings qty_g is */
  serving_size_g?: number;
}

interface DraftDay {
  /** absent for a one-day plan from before weekly plans */
  weekday?: string;
  meals: Record<string, DraftMealItem[]>;
}

const draftServings = (it: DraftMealItem) =>
  it.recipe_id && it.serving_size_g ? it.qty_g / it.serving_size_g : undefined;

const itemKcal = (it: DraftMealItem) => Math.round((it.qty_g * it.kcal_per_100g) / 100);

interface DraftExercise {
  aerobic_days: number;
  strength_days: number;
  flexibility_days: number;
  aerobic_min_per_session: number;
  type: Record<string, { exercise_id: string; name_en: string; name_bn: string }[]>;
}

const removeButton =
  "shrink-0 cursor-pointer rounded-md p-1.5 text-ink-muted hover:bg-crit-tint hover:text-crit-ink " +
  "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-crit-mark";

export default function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { session } = useAuth();
  const [item, setItem] = useState<QueueItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // physician plan edits: draft state while editing, recomputed result after apply
  const [edited, setEdited] = useState<AssessmentResult | null>(null);
  const [editing, setEditing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  // the plan being edited, one entry per day (a single entry for a one-day
  // plan from before weekly plans), and the day on screen
  const [draftDays, setDraftDays] = useState<DraftDay[]>([]);
  const [editDay, setEditDay] = useState(0);
  const draftIsWeek = draftDays.some((day) => day.weekday);
  const [draftEx, setDraftEx] = useState<DraftExercise | null>(null);
  // live, contraindication-filtered food list (never the stale copy stored in
  // the assessment — the dataset may have changed since it was generated)
  const [foods, setFoods] = useState<AllowedFood[] | null>(null);

  const foodIndex = useMemo(
    () => new Map((foods ?? []).map((f) => [mealItemKey(f), f])),
    [foods]
  );
  // this patient's ranked dishes and foods, restricted to the live
  // gate-filtered list (a recommendation can go stale the same way a stored
  // meal item can)
  const recommendedFoods = useMemo(() => {
    const nutrition = item?.assessment.result.nutrition;
    const keys = [
      ...(nutrition?.top_recipes ?? []).map((r) => r.recipe_id),
      ...(nutrition?.top_foods ?? []).map((f) => f.food_id),
    ];
    return keys
      .map((key) => foodIndex.get(key))
      .filter((f): f is AllowedFood => f !== undefined);
  }, [item, foodIndex]);

  useEffect(() => {
    api.getAssessment(id).then(setItem).catch((e) => setError(e.message));
  }, [id]);

  const decide = async (decision: "approved" | "rejected") => {
    setSubmitting(true);
    setError(null);
    try {
      await api.decide(id, {
        decision,
        comment,
        edited_result: edited ?? null,
      });
      if (decision === "approved" && item) {
        router.push(`/doctor/reports/${item.visit.id}`);
      } else {
        router.push("/doctor/review");
      }
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  };

  const startEdit = async (result: AssessmentResult) => {
    let liveFoods = foods;
    if (liveFoods === null) {
      try {
        liveFoods = await api.reviewFoods(id);
        setFoods(liveFoods);
      } catch {
        liveFoods = [];
      }
    }
    const liveIndex = new Map(liveFoods.map((f) => [mealItemKey(f), f]));
    const toDraft = (items: MealItem[]): DraftMealItem[] =>
      items.map((i) => {
        const live = liveIndex.get(mealItemKey(i));
        return {
          recipe_id: i.recipe_id, food_id: i.recipe_id ? undefined : i.food_id,
          name_en: i.name_en, name_bn: i.name_bn, qty_g: i.qty_g,
          kcal_per_100g:
            i.qty_g > 0 && i.kcal > 0 ? (i.kcal / i.qty_g) * 100 : live?.kcal_per_100g ?? 0,
          serving_size_g: i.serving_size_g ?? live?.serving_size_g,
        };
      });
    setDraftDays(
      planDays(result.nutrition.meal_plan).map((day) => ({
        weekday: day.weekday,
        meals: Object.fromEntries(Object.entries(day.meals).map(([meal, items]) => [meal, toDraft(items)])),
      }))
    );
    setEditDay(0);
    const plan = result.exercise_plan;
    setDraftEx(
      plan.time
        ? {
            aerobic_days: plan.frequency!.aerobic_days,
            strength_days: plan.frequency!.strength_days,
            flexibility_days: plan.frequency!.flexibility_days,
            aerobic_min_per_session: plan.time.aerobic_min_per_session,
            type: Object.fromEntries(
              EXERCISE_GROUPS.map((g) => [
                g,
                (plan.type?.[g] ?? []).map((e) => ({
                  exercise_id: e.exercise_id, name_en: e.name_en, name_bn: e.name_bn,
                })),
              ])
            ),
          }
        : null
    );
    setEditError(null);
    setEditing(true);
  };

  const applyEdits = async () => {
    setApplying(true);
    setEditError(null);
    try {
      const payload = (meals: Record<string, DraftMealItem[]>) =>
        Object.fromEntries(
          Object.entries(meals).map(([meal, items]) => [
            meal,
            items.map((i) =>
              i.recipe_id
                ? { recipe_id: i.recipe_id, qty_g: i.qty_g, name_en: i.name_en }
                : { food_id: i.food_id, qty_g: i.qty_g, name_en: i.name_en }
            ),
          ])
        );
      const result = await api.recomputePlan(id, {
        ...(draftIsWeek
          ? { days: draftDays.map((day) => payload(day.meals)) }
          : { meals: payload(draftDays[0]?.meals ?? {}) }),
        exercise: draftEx
          ? {
              aerobic_days: draftEx.aerobic_days,
              strength_days: draftEx.strength_days,
              flexibility_days: draftEx.flexibility_days,
              aerobic_min_per_session: draftEx.aerobic_min_per_session,
              type: Object.fromEntries(
                Object.entries(draftEx.type).map(([g, list]) => [
                  g,
                  list.map((e) => e.exercise_id),
                ])
              ),
            }
          : undefined,
      });
      setEdited(result);
      setEditing(false);
    } catch (err) {
      setEditError((err as Error).message);
    } finally {
      setApplying(false);
    }
  };

  if (error && !item) return <ErrorNote message={error} />;
  if (!item) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  const original = item.assessment.result;
  const r = edited ?? original;
  const decided = item.assessment.status !== "pending";
  const planIsWeek = (r.nutrition.meal_plan.days?.length ?? 0) > 0;
  const plan = r.exercise_plan;
  const canEdit = !decided && !editing;

  const draftMeals = draftDays[editDay]?.meals ?? {};
  // edits apply to the day on screen
  const updateDay = (change: (meals: Record<string, DraftMealItem[]>) => Record<string, DraftMealItem[]>) =>
    setDraftDays((days) => days.map((day, i) => (i === editDay ? { ...day, meals: change(day.meals) } : day)));

  const setQty = (meal: string, index: number, qty: number) =>
    updateDay((d) => ({
      ...d,
      [meal]: d[meal].map((it, i) => (i === index ? { ...it, qty_g: qty } : it)),
    }));

  const removeItem = (meal: string, index: number) =>
    updateDay((d) => ({ ...d, [meal]: d[meal].filter((_, i) => i !== index) }));

  const addItem = (meal: string, food: AllowedFood) => {
    updateDay((d) => ({
      ...d,
      [meal]: [
        ...(d[meal] ?? []),
        {
          recipe_id: food.recipe_id, food_id: food.recipe_id ? undefined : food.food_id,
          name_en: food.name_en, name_bn: food.name_bn,
          // a dish starts at one serving, a single food at 100 g
          qty_g: food.kind === "recipe" && food.serving_size_g ? food.serving_size_g : 100,
          kcal_per_100g: food.kcal_per_100g, serving_size_g: food.serving_size_g,
        },
      ],
    }));
  };

  const dayKcal = (meals: Record<string, DraftMealItem[]>) =>
    Object.values(meals).flat().reduce((sum, it) => sum + itemKcal(it), 0);
  const draftTotalKcal = dayKcal(draftMeals);
  const draftWeekAverage = draftDays.length
    ? Math.round(draftDays.reduce((sum, day) => sum + dayKcal(day.meals), 0) / draftDays.length)
    : 0;
  const editDayName = draftDays[editDay]?.weekday ? weekdayName(draftDays[editDay].weekday!) : null;
  const targetKcal = r.nutrition.meal_plan.target_kcal || r.anthropometrics.target_kcal;
  const draftPct = targetKcal ? Math.round((draftTotalKcal / targetKcal) * 100) : 0;

  const removeExercise = (group: string, index: number) =>
    setDraftEx((d) =>
      d ? { ...d, type: { ...d.type, [group]: d.type[group].filter((_, i) => i !== index) } } : d
    );

  const setExField = (key: keyof Omit<DraftExercise, "type">, value: number) =>
    setDraftEx((d) => (d ? { ...d, [key]: value } : d));

  const planTotal = Number(r.nutrition.meal_plan.totals?.kcal ?? 0);
  const planTarget = r.nutrition.meal_plan.target_kcal;
  const planPct = planTotal && planTarget ? Math.round((planTotal / planTarget) * 100) : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Assessment ${item.assessment.id}`}
        subtitle={`Visit on ${formatDate(item.visit.created_at)}, engine v${item.assessment.engine_version}`}
        back={{ href: "/doctor/review", label: "Review queue" }}
        action={
          <div className="flex flex-wrap items-center gap-2">
            {edited && <Badge kind="flag">Plan edited</Badge>}
            <Badge kind={item.assessment.status}>{item.assessment.status}</Badge>
          </div>
        }
      />

      <PatientBanner
        name={item.patient.name}
        id={pid(item.patient.id)}
        sex={item.patient.sex}
        age={r.age}
        heightCm={item.patient.height_cm}
        weightKg={item.visit.weight_kg}
        pregnant={item.patient.pregnant}
        conditions={item.patient.conditions}
        action={<Badge kind={r.overall_risk}>{riskLabel(r.overall_risk)}</Badge>}
      />

      <div className="grid items-start gap-6 lg:grid-cols-[22rem_1fr]">
        {/* the engine's reasoning: what it found and what it excluded */}
        <div className="space-y-6 lg:sticky lg:top-6">
          <Card title="Findings">
            <dl className="mb-4 grid grid-cols-2 gap-3 border-b border-line pb-4">
              <div>
                <dt className="text-sm text-ink-muted">BMI (Asian cutoffs)</dt>
                <dd className="text-xl font-bold text-ink">
                  {r.anthropometrics.bmi}
                  <span className="ml-1.5 text-sm font-normal capitalize text-ink-muted">
                    {r.anthropometrics.bmi_category}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-sm text-ink-muted">Energy target</dt>
                <dd className="text-xl font-bold text-ink">
                  {r.anthropometrics.target_kcal}
                  <span className="ml-1 text-sm font-normal text-ink-muted">kcal/day</span>
                </dd>
              </div>
            </dl>
            {r.risk_flags.length === 0 ? (
              <p className="text-sm text-ink-muted">No biomarkers recorded.</p>
            ) : (
              <FindingsList flags={r.risk_flags} />
            )}
          </Card>

          {(r.cautions ?? []).length > 0 && (
            <div role="note" className="rounded-xl border border-watch-line bg-watch-tint px-5 py-4">
              <h2 className="flex items-center gap-2 font-semibold text-watch-ink">
                <IconAlert className="h-4 w-4 shrink-0" />
                Check before approving
              </h2>
              <ul className="mt-2 space-y-2 text-sm text-watch-ink">
                {r.cautions!.map((caution) => (
                  <li key={caution}>{caution}</li>
                ))}
              </ul>
            </div>
          )}

          <Card title="Why this plan">
            <h3 className="text-sm font-semibold text-ink-strong">Derived conditions</h3>
            <p className="mt-1 text-sm text-ink">
              {r.conditions.length === 0 ? (
                <span className="text-ink-muted">None</span>
              ) : (
                r.conditions.map((c) => conditionName(c)).join(", ")
              )}
            </p>
            {(r.dietary_restrictions ?? []).length > 0 && (
              <>
                <h3 className="mt-4 text-sm font-semibold text-ink-strong">Does not eat</h3>
                <p className="mt-1 text-sm text-ink">
                  {r.dietary_restrictions!.map(dietaryRestrictionLabel).join(", ")}
                </p>
              </>
            )}
            <h3 className="mt-4 text-sm font-semibold text-ink-strong">Safety exclusions applied</h3>
            <p className="mt-1 text-sm text-ink-soft">
              Removed before ranking: foods tagged{" "}
              <strong className="font-semibold text-ink">
                {r.exclusions.food_tags.length ? r.exclusions.food_tags.join(", ") : "none"}
              </strong>
              ; exercises tagged{" "}
              <strong className="font-semibold text-ink">
                {r.exclusions.exercise_tags.length ? r.exclusions.exercise_tags.join(", ") : "none"}
              </strong>
              .
            </p>
            {Object.keys(r.nutrition.rationales).length > 0 && (
              <ul className="mt-4 space-y-2.5 border-t border-line pt-4">
                {Object.entries(r.nutrition.rationales).map(([finding, why]) => (
                  <li key={finding} className="text-sm text-ink-soft">
                    <strong className="font-semibold text-ink">{conditionName(finding)}.</strong> {why}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        {/* the plan the physician is signing */}
        <div className="min-w-0 space-y-6">
          <Card
            title="Diet plan"
            description={
              r.nutrition.meal_plan.note
                ? undefined
                : `${planIsWeek ? "Seven days, Saturday to Friday. " : ""}Target ${targetKcal} kcal/day${
                    planTotal ? `, planned ${Math.round(planTotal)} kcal${planIsWeek ? " on an average day" : ""}` : ""
                  }`
            }
            action={
              canEdit && !r.nutrition.meal_plan.note ? (
                edited ? (
                  <div className="flex gap-4">
                    <button className={linkButton + " text-ink-muted!"} onClick={() => setEdited(null)}>
                      Discard edits
                    </button>
                    <button className={linkButton} onClick={() => startEdit(r)}>
                      Edit again
                    </button>
                  </div>
                ) : (
                  <button className={linkButton} onClick={() => startEdit(r)}>
                    Edit plan
                  </button>
                )
              ) : undefined
            }
          >
            {r.nutrition.meal_plan.note ? (
              <p className="text-sm text-watch-ink">{r.nutrition.meal_plan.note}</p>
            ) : editing ? (
              <div className="space-y-4">
                {draftIsWeek && (
                  <div className="space-y-2">
                    <DayPicker
                      days={draftDays.map((day, i) => ({ day: i + 1, weekday: day.weekday, meals: {} }))}
                      selected={editDay}
                      onSelect={setEditDay}
                      lang="en"
                      panelId="plan-editor-day"
                    />
                    <p className="font-display text-lg font-bold text-ink">Editing {editDayName}</p>
                  </div>
                )}
                {MEAL_ORDER.filter((m) => draftMeals[m] !== undefined).map((meal) => (
                  <div key={meal} className="rounded-md border border-line">
                    <div className="flex items-center justify-between border-b border-line bg-surface-soft px-3 py-2">
                      <p className="font-semibold text-ink">{mealName(meal)}</p>
                      <p className="text-sm text-ink-muted">
                        ≈{draftMeals[meal].reduce((sum, it) => sum + itemKcal(it), 0)} kcal
                      </p>
                    </div>
                    <ul className="divide-y divide-line">
                      {draftMeals[meal].map((it, index) => {
                        const live = foodIndex.get(mealItemKey(it));
                        const outdated =
                          foods !== null &&
                          (!live || (live.name_en !== it.name_en && foodDisplayName(live.name_en) !== it.name_en));
                        const servings = draftServings(it);
                        return (
                          <li
                            key={`${mealItemKey(it)}-${index}`}
                            className={`flex items-center gap-2 px-3 py-2 text-sm ${outdated ? "bg-watch-tint" : ""}`}
                          >
                            <span className="min-w-0 flex-1">
                              <span className="block truncate text-ink-strong">
                                {it.name_en}
                                {it.name_bn && <span lang="bn" className="text-ink-muted"> {it.name_bn}</span>}
                              </span>
                              {servings !== undefined && !outdated && (
                                <span className="block text-xs text-ink-muted">
                                  {portionText({ recipe_id: it.recipe_id, servings, qty_g: it.qty_g })}
                                </span>
                              )}
                              {outdated && (
                                <span className="mt-0.5 flex items-center gap-1 text-xs font-semibold text-watch-ink">
                                  <IconAlert className="h-3.5 w-3.5" />
                                  From an older database. Remove it and add its replacement.
                                </span>
                              )}
                            </span>
                            <label className="sr-only" htmlFor={`qty-${meal}-${index}`}>
                              Grams of {it.name_en}
                            </label>
                            <input
                              id={`qty-${meal}-${index}`}
                              type="number"
                              min={5}
                              max={2000}
                              step={5}
                              value={it.qty_g}
                              onChange={(e) => setQty(meal, index, Number(e.target.value))}
                              className="w-20 rounded-md border border-field bg-surface px-2 py-1 text-right text-sm focus:border-clinical focus:outline-none focus:ring-2 focus:ring-clinical/20"
                            />
                            <span className="text-xs text-ink-muted">g</span>
                            <span className="w-16 text-right text-xs text-ink-muted">
                              {it.kcal_per_100g > 0 ? `${itemKcal(it)} kcal` : "—"}
                            </span>
                            <button
                              type="button"
                              aria-label={`Remove ${it.name_en}`}
                              onClick={() => removeItem(meal, index)}
                              className={removeButton}
                            >
                              <IconX className="h-4 w-4" />
                            </button>
                          </li>
                        );
                      })}
                      {draftMeals[meal].length === 0 && (
                        <li className="px-3 py-2 text-sm text-ink-muted">No items. Add one below.</li>
                      )}
                    </ul>
                    <div className="border-t border-line px-3 py-2">
                      <FoodCombobox
                        foods={foods ?? []}
                        recommended={recommendedFoods}
                        onSelect={(food) => addItem(meal, food)}
                      />
                    </div>
                  </div>
                ))}
                <div
                  className={`flex flex-wrap items-center justify-between gap-2 rounded-md border px-4 py-2.5 text-sm font-semibold ${
                    draftPct >= 85 && draftPct <= 115
                      ? "border-ok-line bg-ok-tint text-ok-ink"
                      : draftPct >= 60 && draftPct <= 140
                        ? "border-watch-line bg-watch-tint text-watch-ink"
                        : "border-crit-line bg-crit-tint text-crit-ink"
                  }`}
                >
                  <span>
                    {editDayName ? `${editDayName}: planned` : "Planned"} ≈{draftTotalKcal} kcal of a {targetKcal} kcal
                    target
                  </span>
                  <span>{draftPct}%</span>
                </div>
                {draftIsWeek && (
                  <p className="text-sm text-ink-soft">
                    Week average ≈{draftWeekAverage} kcal a day. Each day is edited on its own; pick a day above.
                  </p>
                )}
                <p className="text-sm text-ink-muted">
                  Live estimates from the recipe and food data. Exact totals and nutrient coverage are recomputed
                  when you apply the changes.
                </p>
              </div>
            ) : (
              <>
                {planPct !== null && (planPct < 85 || planPct > 115) && (
                  <p className="mb-4 flex items-start gap-2 rounded-md border border-watch-line bg-watch-tint px-4 py-2.5 text-sm text-watch-ink">
                    <IconAlert className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>
                      {planIsWeek ? "An average day of this plan totals" : "This plan totals"}{" "}
                      <strong>{Math.round(planTotal)} kcal</strong>, {planPct}% of the {planTarget} kcal target. Adjust
                      quantities before approving if this is unintended.
                    </span>
                  </p>
                )}
                <WeekPlan days={planDays(r.nutrition.meal_plan)} lang="en" showItemKcal />
                <div className="mt-6 space-y-6">
                  <PlanNutrition
                    plan={r.nutrition.meal_plan}
                    limits={r.nutrition.limits}
                    anthropometrics={r.anthropometrics}
                    lang="en"
                    staff
                  />
                </div>
              </>
            )}
          </Card>

          <Card title="Exercise plan" description="ACSM FITT-VP prescription">
            {plan.note ? (
              <p className="text-sm text-watch-ink">{plan.note}</p>
            ) : editing && draftEx ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <Field label="Aerobic days/week">
                    <input
                      type="number" min={1} max={7} className={inputClass}
                      value={draftEx.aerobic_days}
                      onChange={(e) => setExField("aerobic_days", Number(e.target.value))}
                    />
                  </Field>
                  <Field label="Minutes/session">
                    <input
                      type="number" min={5} max={180} step={5} className={inputClass}
                      value={draftEx.aerobic_min_per_session}
                      onChange={(e) => setExField("aerobic_min_per_session", Number(e.target.value))}
                    />
                  </Field>
                  <Field label="Strength days/week">
                    <input
                      type="number" min={0} max={7} className={inputClass}
                      value={draftEx.strength_days}
                      onChange={(e) => setExField("strength_days", Number(e.target.value))}
                    />
                  </Field>
                  <Field label="Flexibility days/week">
                    <input
                      type="number" min={0} max={7} className={inputClass}
                      value={draftEx.flexibility_days}
                      onChange={(e) => setExField("flexibility_days", Number(e.target.value))}
                    />
                  </Field>
                </div>
                <div className="grid divide-y divide-line rounded-md border border-line sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                  {EXERCISE_GROUPS.map((group) => (
                    <div key={group} className="px-3 py-3">
                      <p className="font-semibold text-ink">{GROUP_NAMES[group]}</p>
                      <ul className="mt-2 space-y-1">
                        {draftEx.type[group].map((e, index) => (
                          <li key={e.exercise_id} className="flex items-center justify-between gap-2 text-sm text-ink-strong">
                            <span className="min-w-0 truncate">{e.name_en}</span>
                            <button
                              type="button"
                              aria-label={`Remove ${e.name_en}`}
                              onClick={() => removeExercise(group, index)}
                              className={removeButton}
                            >
                              <IconX className="h-4 w-4" />
                            </button>
                          </li>
                        ))}
                        {draftEx.type[group].length === 0 && <li className="text-sm text-ink-muted">None</li>}
                      </ul>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-ink-muted">
                  Weekly volume (MET-min and kcal) is recomputed when you apply the changes. Target heart rate stays
                  as the engine prescribed.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
                  <div>
                    <dt className="text-sm text-ink-muted">Aerobic</dt>
                    <dd className="font-semibold text-ink">
                      {plan.time!.aerobic_min_per_week} min/week
                    </dd>
                    <dd className="text-sm text-ink-muted">
                      {plan.frequency!.aerobic_days} × {plan.time!.aerobic_min_per_session} min
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-ink-muted">Intensity</dt>
                    <dd className="font-semibold capitalize text-ink">{plan.intensity!.level}</dd>
                    <dd className="text-sm text-ink-muted">
                      {plan.intensity!.target_hr_bpm[0]}–{plan.intensity!.target_hr_bpm[1]} bpm
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-ink-muted">Strength, flexibility</dt>
                    <dd className="font-semibold text-ink">
                      {plan.frequency!.strength_days}×, {plan.frequency!.flexibility_days}× a week
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-ink-muted">Volume</dt>
                    <dd className="font-semibold text-ink">≈{plan.volume!.met_min_per_week} MET-min</dd>
                    <dd className="text-sm text-ink-muted">
                      {plan.volume!.est_kcal_per_week} kcal/week, start ×{plan.volume!.volume_factor}
                    </dd>
                  </div>
                </dl>
                <div className="grid divide-y divide-line rounded-md border border-line sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                  {EXERCISE_GROUPS.map((group) => (
                    <div key={group} className="px-3 py-3">
                      <p className="font-semibold text-ink">{GROUP_NAMES[group]}</p>
                      <ul className="mt-1.5 space-y-1.5 text-sm">
                        {(plan.type?.[group] ?? []).map((ex) => (
                          <li key={ex.exercise_id}>
                            <span className="text-ink-strong">{ex.name_en}</span>
                            <span className="block text-xs text-ink-muted">
                              {ex.met_value} MET{ex.equipment !== "none" ? `, ${ex.equipment}` : ""}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
                {plan.progression && <p className="text-sm text-ink-muted">{plan.progression}</p>}
              </div>
            )}
          </Card>

          {editing && (
            <div className="rounded-lg border border-clinical bg-clinical-tint p-4">
              {editError && <div className="mb-3"><ErrorNote message={editError} /></div>}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="max-w-lg text-sm text-ink-soft">
                  Applying re-checks every item against this patient&apos;s safety exclusions and recomputes all
                  derived numbers on the server.
                </p>
                <div className="flex gap-2">
                  <button className={buttonSecondary} onClick={() => setEditing(false)} disabled={applying}>
                    Cancel
                  </button>
                  <button className={buttonPrimary} onClick={applyEdits} disabled={applying}>
                    {applying ? "Recomputing…" : "Apply changes"}
                  </button>
                </div>
              </div>
            </div>
          )}

          <Card
            title="Recommended foods"
            description={`${
              // engine 0.3.0 ranks foods households eat, by what a usual portion supplies
              item.assessment.engine_version >= "0.3.0"
                ? "Everyday foods ranked by what a usual portion supplies, at most three per food group"
                : "Ranked per 100 g"
            } after the safety gate, ${
              r.nutrition.scoring_backend === "ml" ? "trained food model" : "deterministic formula"
            }`}
          >
            {r.nutrition.top_foods.length > 0 ? (
              <RecommendedFoodsList foods={r.nutrition.top_foods} lang="en" />
            ) : (
              <p className="text-sm text-ink-muted">No foods ranked.</p>
            )}
          </Card>

          <section>
            <div className="mb-3">
              <h2 className="font-display text-lg font-bold leading-7 text-ink">Recommended recipes</h2>
              <p className="mt-0.5 text-sm text-ink-muted">
                Ranked per serving after the safety gate; among suitable dishes the most commonly cooked at home
                rank first.{" "}
                {item.assessment.engine_version >= "0.3.0" &&
                  "Sweets, drinks and dishes over the vitamin A upper limit are left out; you can still add them to the plan. "}
                {r.nutrition.recipe_scoring_backend === "ml" ? "Trained recipe model." : "Deterministic formula."}
              </p>
            </div>
            {(r.nutrition.top_recipes ?? []).length > 0 ? (
              <RecommendedRecipesList recipes={r.nutrition.top_recipes} lang="en" showNotes />
            ) : (
              <p className="text-sm text-ink-muted">No recipes ranked.</p>
            )}
          </section>
        </div>
      </div>

      {decided ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface px-5 py-4">
          <p className="flex items-center gap-2 text-ink-soft">
            This assessment was <Badge kind={item.assessment.status}>{item.assessment.status}</Badge>
          </p>
          {item.assessment.status === "approved" && (
            <Link href={`/doctor/reports/${item.visit.id}`} className={buttonSecondary}>
              View report
            </Link>
          )}
        </div>
      ) : (
        /* The decision stays in reach however far down the plan the physician has read. */
        <div className="sticky bottom-[calc(4.25rem+env(safe-area-inset-bottom))] z-10 md:bottom-4">
          <div className="rounded-lg border border-line-strong bg-surface px-4 py-4 shadow-[0_12px_32px_-12px_rgb(27_36_51/0.35)] sm:px-5">
            {error && <div className="mb-3"><ErrorNote message={error} /></div>}
            {edited && (
              <p className="mb-3 flex items-start gap-2 text-sm text-watch-ink">
                <IconAlert className="mt-0.5 h-4 w-4 shrink-0" />
                You are approving the edited plan. Your changes go on the audit trail and into the patient&apos;s
                report.
              </p>
            )}
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
              <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row sm:items-end">
                <p className="flex shrink-0 items-center gap-1.5 text-sm text-ink-muted sm:block">
                  <span className="sm:block sm:text-xs">Signing as</span>
                  <span className="flex items-center gap-1.5 font-semibold text-ink sm:text-base">
                    <IconRx className="h-4 w-4 text-clinical" strokeWidth={2.2} />
                    {session?.user.name}
                  </span>
                </p>
                <label className="block min-w-0 flex-1">
                  <span className="sr-only">Comment for the patient (optional)</span>
                  <input
                    className={`${inputClass} mt-0!`}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Comment for the patient (optional), e.g. re-check haemoglobin in 4 weeks"
                  />
                </label>
              </div>
              <div className="flex gap-2">
                <button
                  className={`${buttonDanger} shrink-0 px-3 sm:px-4`}
                  disabled={submitting || editing}
                  onClick={() => decide("rejected")}
                >
                  <IconX className="h-4 w-4" />
                  Reject
                </button>
                <button
                  className={`${buttonPrimary} flex-1 whitespace-nowrap lg:flex-none`}
                  disabled={submitting || editing}
                  onClick={() => decide("approved")}
                >
                  <IconCheck className="h-4 w-4" />
                  Approve and release
                </button>
              </div>
            </div>
            {editing && (
              <p className="mt-2 text-sm text-ink-muted">Apply or cancel your plan edits before recording a decision.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
