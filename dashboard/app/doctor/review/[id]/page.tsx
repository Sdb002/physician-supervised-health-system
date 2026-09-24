"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AllowedFood, api, AssessmentResult, QueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { FoodCombobox } from "@/components/FoodCombobox";
import { IconX } from "@/components/icons";
import {
  Badge,
  Card,
  ErrorNote,
  Field,
  buttonPrimary,
  buttonSecondary,
  inputClass,
} from "@/components/ui";

const MEAL_ORDER = ["breakfast", "lunch", "dinner", "snack"];
const EXERCISE_GROUPS = ["aerobic", "strength", "flexibility"] as const;

interface DraftMealItem {
  food_id: string;
  name_en: string;
  name_bn: string;
  qty_g: number;
  /** energy density from the food DB (0 when unknown → kcal shown after apply) */
  kcal_per_100g: number;
}

const itemKcal = (it: DraftMealItem) => Math.round((it.qty_g * it.kcal_per_100g) / 100);

interface DraftExercise {
  aerobic_days: number;
  strength_days: number;
  flexibility_days: number;
  aerobic_min_per_session: number;
  type: Record<string, { exercise_id: string; name_en: string; name_bn: string }[]>;
}

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
  const [draftMeals, setDraftMeals] = useState<Record<string, DraftMealItem[]>>({});
  const [draftEx, setDraftEx] = useState<DraftExercise | null>(null);
  // live, contraindication-filtered food list (never the stale copy stored in
  // the assessment — the dataset may have changed since it was generated)
  const [foods, setFoods] = useState<AllowedFood[] | null>(null);

  const foodIndex = useMemo(
    () => new Map((foods ?? []).map((f) => [f.food_id, f])),
    [foods]
  );
  // this patient's ranked picks, restricted to the live gate-filtered list
  // (a recommendation can go stale the same way a stored meal item can)
  const recommendedFoods = useMemo(() => {
    const topFoods = item?.assessment.result.nutrition.top_foods ?? [];
    return topFoods
      .map((f) => foodIndex.get(f.food_id))
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
    const liveIndex = new Map(liveFoods.map((f) => [f.food_id, f]));
    const meals: Record<string, DraftMealItem[]> = {};
    for (const [meal, items] of Object.entries(result.nutrition.meal_plan.meals ?? {})) {
      meals[meal] = items.map((i) => ({
        food_id: i.food_id, name_en: i.name_en, name_bn: i.name_bn, qty_g: i.qty_g,
        kcal_per_100g:
          i.qty_g > 0 && i.kcal > 0
            ? (i.kcal / i.qty_g) * 100
            : liveIndex.get(i.food_id)?.kcal_per_100g ?? 0,
      }));
    }
    setDraftMeals(meals);
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
      const result = await api.recomputePlan(id, {
        meals: Object.fromEntries(
          Object.entries(draftMeals).map(([meal, items]) => [
            meal,
            items.map((i) => ({ food_id: i.food_id, qty_g: i.qty_g, name_en: i.name_en })),
          ])
        ),
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
  if (!item) return <p className="text-sm text-ink-muted">Loading…</p>;

  const original = item.assessment.result;
  const r = edited ?? original;
  const decided = item.assessment.status !== "pending";
  const meals = r.nutrition.meal_plan.meals ?? {};
  const plan = r.exercise_plan;
  const canEdit = !decided && !editing;

  const setQty = (meal: string, index: number, qty: number) =>
    setDraftMeals((d) => ({
      ...d,
      [meal]: d[meal].map((it, i) => (i === index ? { ...it, qty_g: qty } : it)),
    }));

  const removeItem = (meal: string, index: number) =>
    setDraftMeals((d) => ({ ...d, [meal]: d[meal].filter((_, i) => i !== index) }));

  const addItem = (meal: string, food: AllowedFood) => {
    setDraftMeals((d) => ({
      ...d,
      [meal]: [
        ...(d[meal] ?? []),
        {
          food_id: food.food_id, name_en: food.name_en, name_bn: food.name_bn,
          qty_g: 100, kcal_per_100g: food.kcal_per_100g,
        },
      ],
    }));
  };

  const draftTotalKcal = Object.values(draftMeals)
    .flat()
    .reduce((sum, it) => sum + itemKcal(it), 0);
  const targetKcal = r.nutrition.meal_plan.target_kcal || r.anthropometrics.target_kcal;
  const draftPct = targetKcal ? Math.round((draftTotalKcal / targetKcal) * 100) : 0;

  const removeExercise = (group: string, index: number) =>
    setDraftEx((d) =>
      d ? { ...d, type: { ...d.type, [group]: d.type[group].filter((_, i) => i !== index) } } : d
    );

  const setExField = (key: keyof Omit<DraftExercise, "type">, value: number) =>
    setDraftEx((d) => (d ? { ...d, [key]: value } : d));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-ink-muted">
            <Link href="/doctor/review" className="hover:underline">Review queue</Link> / assessment #{item.assessment.id}
          </p>
          <h1 className="text-2xl font-bold">{item.patient.name}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Visit {new Date(item.visit.created_at).toLocaleString()} ·{" "}
            {item.visit.weight_kg} kg · engine v{item.assessment.engine_version}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {edited && <Badge kind="moderate">edited plan</Badge>}
          <Badge kind={item.assessment.status}>{item.assessment.status}</Badge>
        </div>
      </div>

      <Card title="Findings">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-ink-muted">
              BMI{" "}
              <span className="font-semibold text-ink">
                {r.anthropometrics.bmi}
              </span>{" "}
              ({r.anthropometrics.bmi_category}, Asian cutoffs) · energy target{" "}
              <span className="font-semibold text-ink">
                {r.anthropometrics.target_kcal} kcal/day
              </span>
            </p>
            <div className="mt-3 space-y-2">
              {r.risk_flags.length === 0 && (
                <p className="text-sm text-ink-muted">No biomarkers recorded.</p>
              )}
              {r.risk_flags.map((f) => (
                <div key={f.biomarker} className="flex items-center justify-between text-sm">
                  <span className="text-ink-soft">
                    {f.biomarker.replace(/_/g, " ")}: <strong>{f.value}</strong> {f.unit}
                  </span>
                  <Badge kind={f.risk}>{f.label.replace(/_/g, " ")}</Badge>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-ink-strong">Derived conditions</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {r.conditions.length === 0 ? (
                <span className="text-sm text-ink-muted">none</span>
              ) : (
                r.conditions.map((c) => (
                  <Badge key={c} kind="high">{c.replace(/_/g, " ")}</Badge>
                ))
              )}
            </div>
            <p className="mt-4 text-sm font-medium text-ink-strong">
              Safety exclusions applied
            </p>
            <p className="mt-1 text-xs text-ink-muted">
              Foods tagged{" "}
              {r.exclusions.food_tags.length
                ? r.exclusions.food_tags.join(", ")
                : "(none)"}{" "}
              and exercises tagged{" "}
              {r.exclusions.exercise_tags.length
                ? r.exclusions.exercise_tags.join(", ")
                : "(none)"}{" "}
              were removed before ranking.
            </p>
            {Object.entries(r.nutrition.rationales).map(([finding, why]) => (
              <p key={finding} className="mt-2 text-xs text-ink-muted">
                <strong className="text-ink-soft">{finding}:</strong> {why}
              </p>
            ))}
          </div>
        </div>
      </Card>

      <Card
        title="Diet plan"
        action={
          canEdit && !r.nutrition.meal_plan.note ? (
            edited ? (
              <div className="flex gap-3">
                <button
                  className="text-sm font-medium text-ink-muted hover:underline"
                  onClick={() => setEdited(null)}
                >
                  Discard edits
                </button>
                <button
                  className="text-sm font-medium text-teal-700 hover:underline"
                  onClick={() => startEdit(r)}
                >
                  Edit again
                </button>
              </div>
            ) : (
              <button
                className="text-sm font-medium text-teal-700 hover:underline"
                onClick={() => startEdit(r)}
              >
                Edit plan
              </button>
            )
          ) : undefined
        }
      >
        {r.nutrition.meal_plan.note ? (
          <p className="text-sm text-amber-700">{r.nutrition.meal_plan.note}</p>
        ) : editing ? (
          <div className="space-y-4">
            {MEAL_ORDER.filter((m) => draftMeals[m] !== undefined).map((meal) => (
              <div key={meal} className="rounded-lg bg-surface-soft p-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    {meal}
                  </p>
                  <p className="text-xs font-medium text-ink-muted">
                    ≈{draftMeals[meal].reduce((sum, it) => sum + itemKcal(it), 0)} kcal
                  </p>
                </div>
                <ul className="mt-2 space-y-2">
                  {draftMeals[meal].map((it, index) => {
                    const live = foodIndex.get(it.food_id);
                    const outdated = foods !== null && (!live || live.name_en !== it.name_en);
                    return (
                    <li
                      key={`${it.food_id}-${index}`}
                      className={`flex items-center gap-2 rounded-lg text-sm ${
                        outdated ? "bg-amber-50 px-2 py-1 -mx-2" : ""
                      }`}
                    >
                      <span className="min-w-0 flex-1 truncate text-ink-strong">
                        {it.name_en}
                        {it.name_bn && <span className="text-ink-muted"> · {it.name_bn}</span>}
                        {outdated && (
                          <span
                            className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800"
                            title="This item comes from an older version of the food database — remove it and add its replacement from the list."
                          >
                            outdated — replace
                          </span>
                        )}
                      </span>
                      <input
                        type="number"
                        min={5}
                        max={2000}
                        step={5}
                        value={it.qty_g}
                        onChange={(e) => setQty(meal, index, Number(e.target.value))}
                        className="w-20 rounded-lg border border-line-strong px-2 py-1 text-right text-sm"
                      />
                      <span className="text-xs text-ink-muted">g</span>
                      <span className="w-16 text-right text-xs tabular-nums text-ink-muted">
                        {it.kcal_per_100g > 0 ? `${itemKcal(it)} kcal` : "—"}
                      </span>
                      <button
                        type="button"
                        title="Remove"
                        onClick={() => removeItem(meal, index)}
                        className="rounded p-1 text-ink-muted hover:bg-rose-50 hover:text-rose-600"
                      >
                        <IconX className="h-3.5 w-3.5" />
                      </button>
                    </li>
                    );
                  })}
                  {draftMeals[meal].length === 0 && (
                    <li className="text-xs text-ink-muted">No items — add one below.</li>
                  )}
                </ul>
                <div className="mt-2">
                  <FoodCombobox
                    foods={foods ?? []}
                    recommended={recommendedFoods}
                    onSelect={(food) => addItem(meal, food)}
                  />
                </div>
              </div>
            ))}
            <div
              className={`flex items-center justify-between rounded-lg px-4 py-2.5 text-sm font-medium ${
                draftPct >= 85 && draftPct <= 115
                  ? "bg-emerald-50 text-emerald-800"
                  : draftPct >= 60 && draftPct <= 140
                    ? "bg-amber-50 text-amber-800"
                    : "bg-rose-50 text-rose-800"
              }`}
            >
              <span>
                Planned total ≈<strong>{draftTotalKcal} kcal</strong> · target{" "}
                {targetKcal} kcal
              </span>
              <span>{draftPct}% of target</span>
            </div>
            <p className="text-xs text-ink-muted">
              Live estimates from the food database — exact totals and nutrient coverage
              are recomputed server-side when you apply the changes.
            </p>
          </div>
        ) : (
          <>
            {(() => {
              const total = Number(r.nutrition.meal_plan.totals?.kcal ?? 0);
              const target = r.nutrition.meal_plan.target_kcal;
              if (!total || !target) return null;
              const pct = Math.round((total / target) * 100);
              if (pct >= 85 && pct <= 115) return null;
              return (
                <p className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
                  This plan totals <strong>{Math.round(total)} kcal</strong> — {pct}% of
                  the {target} kcal daily target. Adjust quantities before approving if
                  this is unintended.
                </p>
              );
            })()}
            <div className="grid gap-3 sm:grid-cols-2">
              {Object.entries(meals).map(([meal, items]) => (
                <div key={meal} className="rounded-lg bg-surface-soft p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    {meal}
                  </p>
                  <ul className="mt-1 space-y-0.5 text-sm text-ink-strong">
                    {items.map((it) => (
                      <li key={it.food_id}>
                        {it.name_en}
                        {it.name_bn && <span className="text-ink-muted"> · {it.name_bn}</span>}{" "}
                        — {it.qty_g} g ({it.kcal} kcal)
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>

      <Card title="Exercise plan (ACSM FITT-VP)">
        {plan.note ? (
          <p className="text-sm text-amber-700">{plan.note}</p>
        ) : editing && draftEx ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Field label="Aerobic days/wk">
                <input
                  type="number" min={1} max={7} className={inputClass}
                  value={draftEx.aerobic_days}
                  onChange={(e) => setExField("aerobic_days", Number(e.target.value))}
                />
              </Field>
              <Field label="Min/session">
                <input
                  type="number" min={5} max={180} step={5} className={inputClass}
                  value={draftEx.aerobic_min_per_session}
                  onChange={(e) => setExField("aerobic_min_per_session", Number(e.target.value))}
                />
              </Field>
              <Field label="Strength days/wk">
                <input
                  type="number" min={0} max={7} className={inputClass}
                  value={draftEx.strength_days}
                  onChange={(e) => setExField("strength_days", Number(e.target.value))}
                />
              </Field>
              <Field label="Flexibility days/wk">
                <input
                  type="number" min={0} max={7} className={inputClass}
                  value={draftEx.flexibility_days}
                  onChange={(e) => setExField("flexibility_days", Number(e.target.value))}
                />
              </Field>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {EXERCISE_GROUPS.map((group) => (
                <div key={group} className="rounded-lg bg-surface-soft p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    {group}
                  </p>
                  <ul className="mt-2 space-y-1">
                    {draftEx.type[group].map((e, index) => (
                      <li key={e.exercise_id} className="flex items-center justify-between gap-2 text-sm text-ink-strong">
                        <span className="min-w-0 truncate">
                          {e.name_en}
                          {e.name_bn && <span className="text-ink-muted"> · {e.name_bn}</span>}
                        </span>
                        <button
                          type="button"
                          title="Remove"
                          onClick={() => removeExercise(group, index)}
                          className="rounded p-1 text-ink-muted hover:bg-rose-50 hover:text-rose-600"
                        >
                          <IconX className="h-3.5 w-3.5" />
                        </button>
                      </li>
                    ))}
                    {draftEx.type[group].length === 0 && (
                      <li className="text-xs text-ink-muted">none</li>
                    )}
                  </ul>
                </div>
              ))}
            </div>
            <p className="text-xs text-ink-muted">
              Weekly volume (MET·min and kcal) is recomputed when you apply the changes.
              Target heart rate stays as prescribed by the engine.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1 text-sm text-ink-soft">
              <p>
                <strong>{plan.time!.aerobic_min_per_week} min/week</strong> aerobic —{" "}
                {plan.time!.aerobic_min_per_session} min ×{" "}
                {plan.frequency!.aerobic_days} days at {plan.intensity!.level} intensity
              </p>
              <p>
                Target heart rate {plan.intensity!.target_hr_bpm[0]}–
                {plan.intensity!.target_hr_bpm[1]} bpm
              </p>
              <p>
                Strength {plan.frequency!.strength_days}×/week · flexibility{" "}
                {plan.frequency!.flexibility_days}×/week
              </p>
              <p className="text-xs text-ink-muted">
                ≈{plan.volume!.met_min_per_week} MET·min/week ·{" "}
                {plan.volume!.est_kcal_per_week} kcal/week · start volume ×
                {plan.volume!.volume_factor}
              </p>
              <p className="text-xs text-ink-muted">{plan.progression}</p>
            </div>
            <div>
              {EXERCISE_GROUPS.map((group) => (
                <div key={group} className="mb-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    {group}
                  </p>
                  <ul className="text-sm text-ink-strong">
                    {(plan.type?.[group] ?? []).map((ex) => (
                      <li key={ex.exercise_id}>
                        {ex.name_en}
                        {ex.name_bn && <span className="text-ink-muted"> · {ex.name_bn}</span>}{" "}
                        <span className="text-xs text-ink-muted">
                          ({ex.met_value} MET{ex.equipment !== "none" ? `, ${ex.equipment}` : ""})
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {editing && (
        <Card>
          {editError && <div className="mb-3"><ErrorNote message={editError} /></div>}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-ink-muted">
              Applying re-checks every item against this patient&apos;s safety exclusions
              and recomputes all derived numbers server-side.
            </p>
            <div className="flex gap-3">
              <button className={buttonSecondary} onClick={() => setEditing(false)} disabled={applying}>
                Cancel
              </button>
              <button className={buttonPrimary} onClick={applyEdits} disabled={applying}>
                {applying ? "Recomputing…" : "Apply changes"}
              </button>
            </div>
          </div>
        </Card>
      )}

      {decided ? (
        <Card title="Decision">
          <p className="text-sm text-ink-soft">
            This assessment was <Badge kind={item.assessment.status}>{item.assessment.status}</Badge>.
            {item.assessment.status === "approved" && (
              <Link
                href={`/doctor/reports/${item.visit.id}`}
                className="ml-2 font-medium text-teal-700 hover:underline"
              >
                View report →
              </Link>
            )}
          </p>
        </Card>
      ) : (
        <Card title="Your decision">
          {error && <div className="mb-3"><ErrorNote message={error} /></div>}
          {edited && (
            <p className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
              You are approving the <strong>edited</strong> plan — your changes are recorded
              on the audit trail and are what the patient&apos;s report will contain.
            </p>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Approving as" hint="Recorded on the immutable audit trail — tied to your signed-in account.">
              <div className={`${inputClass} bg-surface-soft text-ink-strong`}>{session?.user.name}</div>
            </Field>
            <Field label="Comment (optional)">
              <input
                className={inputClass}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="e.g. re-check hemoglobin in 4 weeks"
              />
            </Field>
          </div>
          <div className="mt-4 flex gap-3">
            <button
              className="inline-flex flex-1 items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={submitting || editing}
              onClick={() => decide("approved")}
            >
              Approve — release report
            </button>
            <button
              className="inline-flex flex-1 items-center justify-center rounded-lg border border-rose-200 bg-surface px-4 py-2 text-sm font-medium text-rose-700 shadow-sm hover:bg-rose-50 disabled:opacity-50"
              disabled={submitting || editing}
              onClick={() => decide("rejected")}
            >
              Reject
            </button>
          </div>
          {editing && (
            <p className="mt-2 text-center text-xs text-ink-muted">
              Apply or cancel your plan edits before recording a decision.
            </p>
          )}
        </Card>
      )}
    </div>
  );
}
