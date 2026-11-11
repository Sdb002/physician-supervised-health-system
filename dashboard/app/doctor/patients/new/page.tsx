"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ExcludedFood, api } from "@/lib/api";
import { CONDITION_OPTIONS, DIETARY_RESTRICTION_OPTIONS } from "@/lib/patient-options";
import { ActivityField, OptionChecks, PregnancyFields, choiceRow } from "@/components/patient-fields";
import { ExcludedFoodsField, excludedFoodPicks } from "@/components/excluded-foods";
import {
  ErrorNote,
  Field,
  PageHeader,
  buttonPrimary,
  checkboxClass,
  inputClass,
} from "@/components/ui";
import { useT } from "@/lib/use-t";

const sectionClass = "grid gap-x-8 gap-y-4 px-5 py-6 md:grid-cols-[14rem_1fr]";

export default function NewPatientPage() {
  const router = useRouter();
  const { t } = useT();
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [createdId, setCreatedId] = useState<number | null>(null);
  const [withAccount, setWithAccount] = useState(false);
  const [account, setAccount] = useState({ email: "", password: "" });
  const [form, setForm] = useState({
    name: "",
    sex: "female" as "male" | "female",
    birth_year: 1990,
    height_cm: 160,
    pregnant: false,
    pregnancy_trimester: null as number | null,
    conditions: [] as string[],
    dietary_restrictions: [] as string[],
    excluded_foods: [] as ExcludedFood[],
    fitness_level: "beginner",
    activity_level: null as string | null,
    notes: "",
  });

  const set = (key: string, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      // don't create the patient twice if a previous attempt failed only on the account step
      let patientId = createdId;
      if (patientId === null) {
        // the record keeps the excluded foods by id; the name goes with it
        const record = { ...form, excluded_foods: excludedFoodPicks(form.excluded_foods) };
        const patient = await api.createPatient(
          form.sex === "female" ? record : { ...record, pregnant: false, pregnancy_trimester: null }
        );
        patientId = patient.id;
        setCreatedId(patientId);
      }
      if (withAccount) {
        await api.createPatientAccount(patientId, account);
      }
      router.push(`/doctor/patients/${patientId}/intake`);
    } catch (err) {
      setError(
        createdId !== null
          ? t(
              "The patient was saved, but the login could not be created: {reason}. Fix the email or password and save again, or untick the login option to continue.",
              { reason: t((err as Error).message) }
            )
          : (err as Error).message
      );
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title={t("New patient")}
        subtitle={t("After saving, you go straight to their first visit.")}
        back={{ href: "/doctor/patients", label: t("Patients") }}
      />

      {error && <ErrorNote message={error} />}

      <form onSubmit={submit} className="divide-y divide-line rounded-xl border border-line bg-surface">
        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">{t("Identity")}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">{t("Sex, age and pregnancy change clinical cutoffs.")}</p>
          </div>
          <div className="space-y-4">
            <Field label={t("Full name")}>
              <input
                className={inputClass}
                required
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                placeholder={t("e.g. Ayesha Rahman")}
              />
            </Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label={t("Sex")}>
                <select className={inputClass} value={form.sex} onChange={(e) => set("sex", e.target.value)}>
                  <option value="female">{t("Female")}</option>
                  <option value="male">{t("Male")}</option>
                </select>
              </Field>
              <Field label={t("Year of birth")}>
                <input
                  className={inputClass}
                  type="number"
                  inputMode="numeric"
                  min={1900}
                  max={new Date().getFullYear()}
                  required
                  value={form.birth_year}
                  onChange={(e) => set("birth_year", Number(e.target.value))}
                />
              </Field>
              <Field label={t("Height (cm)")}>
                <input
                  className={inputClass}
                  type="number"
                  inputMode="decimal"
                  min={80}
                  max={230}
                  step="0.5"
                  required
                  value={form.height_cm}
                  onChange={(e) => set("height_cm", Number(e.target.value))}
                />
              </Field>
            </div>
            {form.sex === "female" && (
              <PregnancyFields
                pregnant={form.pregnant}
                trimester={form.pregnancy_trimester}
                onChange={(next) => setForm((f) => ({ ...f, ...next }))}
                label={t("Currently pregnant")}
                hint={t("Changes anaemia cutoffs, nutrient targets, excluded foods and exercises; no weight-loss deficit is applied.")}
              />
            )}
          </div>
        </section>

        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">{t("Clinical background")}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              {t("The engine also derives conditions from lab values. Tick what is already diagnosed.")}
            </p>
          </div>
          <div className="space-y-4">
            <fieldset>
              <legend className="mb-1.5 text-sm font-semibold text-ink-strong">{t("Diagnosed conditions")}</legend>
              <OptionChecks
                options={CONDITION_OPTIONS}
                value={form.conditions}
                onChange={(conditions) => set("conditions", conditions)}
              />
            </fieldset>
            <fieldset>
              <legend className="text-sm font-semibold text-ink-strong">{t("Food the patient does not eat")}</legend>
              <p className="mb-1.5 text-xs text-ink-muted">
                {t("For faith, choice or allergy. These foods and any dish containing them are never planned or offered.")}
              </p>
              <OptionChecks
                options={DIETARY_RESTRICTION_OPTIONS}
                value={form.dietary_restrictions}
                onChange={(restrictions) => set("dietary_restrictions", restrictions)}
              />
            </fieldset>
            <fieldset>
              <legend className="text-sm font-semibold text-ink-strong">{t("Other foods and dishes to leave out")}</legend>
              <p className="mb-1.5 text-xs text-ink-muted">
                {t("A single food the patient is allergic to or will not eat, or a dish. A food is left out in every form, with every dish that uses it.")}
              </p>
              <ExcludedFoodsField value={form.excluded_foods} onChange={(foods) => set("excluded_foods", foods)} />
            </fieldset>
            <div className="grid gap-4 sm:grid-cols-2">
              <ActivityField value={form.activity_level} onChange={(level) => set("activity_level", level)} />
              <Field label={t("Fitness level")} hint={t("Scales the starting exercise volume.")}>
                <select
                  className={inputClass}
                  value={form.fitness_level}
                  onChange={(e) => set("fitness_level", e.target.value)}
                >
                  <option value="beginner">{t("Beginner")}</option>
                  <option value="intermediate">{t("Intermediate")}</option>
                  <option value="advanced">{t("Advanced")}</option>
                </select>
              </Field>
            </div>
            <Field label={t("Notes (optional)")}>
              <textarea
                className={inputClass}
                rows={3}
                value={form.notes}
                onChange={(e) => set("notes", e.target.value)}
              />
            </Field>
          </div>
        </section>

        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">{t("Patient login")}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">{t("Optional. Lets the patient read approved reports online.")}</p>
          </div>
          <div className="space-y-4">
            <label className={choiceRow}>
              <input
                type="checkbox"
                className={checkboxClass}
                checked={withAccount}
                onChange={(e) => setWithAccount(e.target.checked)}
              />
              {t("Create a login for this patient")}
            </label>
            {withAccount && (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label={t("Patient email")}>
                  <input
                    className={inputClass}
                    type="email"
                    required={withAccount}
                    autoComplete="off"
                    value={account.email}
                    onChange={(e) => setAccount((a) => ({ ...a, email: e.target.value }))}
                    placeholder="patient@example.com"
                  />
                </Field>
                <Field label={t("Temporary password")} hint={t("At least 8 characters. Give it to the patient.")}>
                  <input
                    className={inputClass}
                    type="text"
                    required={withAccount}
                    minLength={8}
                    autoComplete="off"
                    value={account.password}
                    onChange={(e) => setAccount((a) => ({ ...a, password: e.target.value }))}
                  />
                </Field>
              </div>
            )}
          </div>
        </section>

        <div className="flex justify-end bg-surface-soft px-5 py-4">
          <button type="submit" disabled={saving} className={buttonPrimary}>
            {saving ? t("Saving…") : t("Save and start visit")}
          </button>
        </div>
      </form>
    </div>
  );
}
