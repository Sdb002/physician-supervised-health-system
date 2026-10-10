"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import {
  ErrorNote,
  Field,
  PageHeader,
  buttonPrimary,
  checkboxClass,
  inputClass,
} from "@/components/ui";

const CONDITION_OPTIONS = [
  { key: "hypertension", label: "Hypertension" },
  { key: "diabetes", label: "Diabetes" },
  { key: "anemia", label: "Anaemia" },
  { key: "knee_osteoarthritis", label: "Knee osteoarthritis" },
];

const choiceRow =
  "flex cursor-pointer items-center gap-3 rounded-lg border border-line px-3 py-2.5 text-sm text-ink-strong " +
  "has-[:checked]:border-clinical has-[:checked]:bg-clinical-tint hover:bg-surface-soft";

const sectionClass = "grid gap-x-8 gap-y-4 px-5 py-6 md:grid-cols-[14rem_1fr]";

export default function NewPatientPage() {
  const router = useRouter();
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
    conditions: [] as string[],
    fitness_level: "beginner",
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
        const patient = await api.createPatient(form);
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
          ? `The patient was saved, but the login could not be created: ${(err as Error).message}. ` +
            "Fix the email or password and save again, or untick the login option to continue."
          : (err as Error).message
      );
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="New patient"
        subtitle="After saving, you go straight to their first visit."
        back={{ href: "/doctor/patients", label: "Patients" }}
      />

      {error && <ErrorNote message={error} />}

      <form onSubmit={submit} className="divide-y divide-line rounded-xl border border-line bg-surface">
        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">Identity</h2>
            <p className="mt-0.5 text-sm text-ink-muted">Sex, age and pregnancy change clinical cutoffs.</p>
          </div>
          <div className="space-y-4">
            <Field label="Full name">
              <input
                className={inputClass}
                required
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                placeholder="e.g. Ayesha Rahman"
              />
            </Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Sex">
                <select className={inputClass} value={form.sex} onChange={(e) => set("sex", e.target.value)}>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </Field>
              <Field label="Year of birth">
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
              <Field label="Height (cm)">
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
              <label className={choiceRow}>
                <input
                  type="checkbox"
                  className={checkboxClass}
                  checked={form.pregnant}
                  onChange={(e) => set("pregnant", e.target.checked)}
                />
                <span>
                  Currently pregnant
                  <span className="block text-xs text-ink-muted">
                    Changes anaemia cutoffs, nutrient targets and excluded exercises.
                  </span>
                </span>
              </label>
            )}
          </div>
        </section>

        <section className={sectionClass}>
          <div>
            <h2 className="font-semibold text-ink">Clinical background</h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              The engine also derives conditions from lab values. Tick what is already diagnosed.
            </p>
          </div>
          <div className="space-y-4">
            <fieldset>
              <legend className="text-sm font-semibold text-ink-strong">Diagnosed conditions</legend>
              <div className="mt-1.5 grid gap-2 sm:grid-cols-2">
                {CONDITION_OPTIONS.map((c) => (
                  <label key={c.key} className={choiceRow}>
                    <input
                      type="checkbox"
                      className={checkboxClass}
                      checked={form.conditions.includes(c.key)}
                      onChange={(e) =>
                        set(
                          "conditions",
                          e.target.checked
                            ? [...form.conditions, c.key]
                            : form.conditions.filter((x) => x !== c.key)
                        )
                      }
                    />
                    {c.label}
                  </label>
                ))}
              </div>
            </fieldset>
            <Field label="Fitness level" hint="Scales the starting exercise volume.">
              <select
                className={inputClass}
                value={form.fitness_level}
                onChange={(e) => set("fitness_level", e.target.value)}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </Field>
            <Field label="Notes (optional)">
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
            <h2 className="font-semibold text-ink">Patient login</h2>
            <p className="mt-0.5 text-sm text-ink-muted">Optional. Lets the patient read approved reports online.</p>
          </div>
          <div className="space-y-4">
            <label className={choiceRow}>
              <input
                type="checkbox"
                className={checkboxClass}
                checked={withAccount}
                onChange={(e) => setWithAccount(e.target.checked)}
              />
              Create a login for this patient
            </label>
            {withAccount && (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Patient email">
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
                <Field label="Temporary password" hint="At least 8 characters. Give it to the patient.">
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
            {saving ? "Saving…" : "Save and start visit"}
          </button>
        </div>
      </form>
    </div>
  );
}
