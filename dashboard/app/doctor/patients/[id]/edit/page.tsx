"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ExcludedFood, Patient, PatientUpdate } from "@/lib/api";
import { CONDITION_OPTIONS, DIETARY_RESTRICTION_OPTIONS } from "@/lib/patient-options";
import { ActivityField, OptionChecks, PregnancyFields } from "@/components/patient-fields";
import { ExcludedFoodsField, excludedFoodPicks } from "@/components/excluded-foods";
import { ErrorNote, Field, PageHeader, Skeleton, buttonPrimary, inputClass } from "@/components/ui";
import { useT } from "@/lib/use-t";

const sectionClass = "grid gap-x-8 gap-y-4 px-5 py-6 md:grid-cols-[14rem_1fr]";

/** What the form holds: the editable fields of the record, with the excluded
 * foods as entries (for their names) where the record is sent their ids. */
type EditForm = Omit<Required<PatientUpdate>, "excluded_foods"> & { excluded_foods: ExcludedFood[] };

/** Sex and year of birth are not editable: every past visit was scored on them. */
const editable = (p: Patient): EditForm => ({
  name: p.name,
  height_cm: p.height_cm,
  pregnant: p.pregnant,
  pregnancy_trimester: p.pregnancy_trimester,
  conditions: p.conditions,
  dietary_restrictions: p.dietary_restrictions,
  excluded_foods: p.excluded_foods ?? [],
  fitness_level: p.fitness_level,
  activity_level: p.activity_level,
  notes: p.notes,
});

export default function EditPatientPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { t } = useT();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [form, setForm] = useState<EditForm | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getPatient(id)
      .then((p) => {
        setPatient(p);
        setForm(editable(p));
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const set = (changes: Partial<EditForm>) => setForm((f) => (f ? { ...f, ...changes } : f));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    try {
      await api.updatePatient(id, { ...form, excluded_foods: excludedFoodPicks(form.excluded_foods) });
      router.push(`/doctor/patients/${id}`);
    } catch (err) {
      setError((err as Error).message);
      setSaving(false);
    }
  };

  if (!patient || !form) {
    return error ? <ErrorNote message={error} /> : <Skeleton className="h-96" />;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title={t("Edit patient")}
        subtitle={t("A plan still awaiting review is rebuilt from the saved record. Approved plans stay as signed off.")}
        back={{ href: `/doctor/patients/${id}`, label: patient.name }}
      />

      {error && <ErrorNote message={error} />}

      <form onSubmit={submit} className="divide-y divide-line rounded-xl border border-line bg-surface">
        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">{t("Identity")}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              {t("Sex and year of birth cannot be changed: past visits were scored on them.")}
            </p>
          </div>
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-[1fr_10rem]">
              <Field label={t("Full name")}>
                <input className={inputClass} required value={form.name} onChange={(e) => set({ name: e.target.value })} />
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
                  onChange={(e) => set({ height_cm: Number(e.target.value) })}
                />
              </Field>
            </div>
            {patient.sex === "female" && (
              <PregnancyFields
                pregnant={form.pregnant}
                trimester={form.pregnancy_trimester}
                onChange={set}
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
              {t("A recorded condition shapes the plan even when that day's values are normal.")}
            </p>
          </div>
          <div className="space-y-4">
            <fieldset>
              <legend className="mb-1.5 text-sm font-semibold text-ink-strong">{t("Diagnosed conditions")}</legend>
              <OptionChecks
                options={CONDITION_OPTIONS}
                value={form.conditions}
                onChange={(conditions) => set({ conditions })}
              />
            </fieldset>
            <div className="grid gap-4 sm:grid-cols-2">
              <ActivityField value={form.activity_level} onChange={(activity_level) => set({ activity_level })} />
              <Field label={t("Fitness level")} hint={t("Scales the starting exercise volume.")}>
                <select
                  className={inputClass}
                  value={form.fitness_level}
                  onChange={(e) => set({ fitness_level: e.target.value })}
                >
                  <option value="beginner">{t("Beginner")}</option>
                  <option value="intermediate">{t("Intermediate")}</option>
                  <option value="advanced">{t("Advanced")}</option>
                </select>
              </Field>
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">{t("Food the patient does not eat")}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              {t("For faith, choice or allergy. These foods and any dish containing them are never planned or offered.")}
            </p>
          </div>
          <div className="space-y-4">
            <OptionChecks
              options={DIETARY_RESTRICTION_OPTIONS}
              value={form.dietary_restrictions}
              onChange={(dietary_restrictions) => set({ dietary_restrictions })}
            />
            <fieldset>
              <legend className="text-sm font-semibold text-ink-strong">{t("Other foods and dishes to leave out")}</legend>
              <p className="mb-1.5 text-xs text-ink-muted">
                {t("A single food the patient is allergic to or will not eat, or a dish. A food is left out in every form, with every dish that uses it.")}
              </p>
              <ExcludedFoodsField value={form.excluded_foods} onChange={(excluded_foods) => set({ excluded_foods })} />
            </fieldset>
          </div>
        </section>

        <section className={sectionClass}>
          <h2 className="font-semibold text-ink">{t("Notes")}</h2>
          <Field label={t("Notes (optional)")}>
            <textarea className={inputClass} rows={3} value={form.notes} onChange={(e) => set({ notes: e.target.value })} />
          </Field>
        </section>

        <div className="flex justify-end bg-surface-soft px-5 py-4">
          <button type="submit" disabled={saving} className={buttonPrimary}>
            {saving ? t("Saving…") : t("Save changes")}
          </button>
        </div>
      </form>
    </div>
  );
}
