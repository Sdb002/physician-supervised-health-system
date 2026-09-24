"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { Card, ErrorNote, Field, PageHeader, buttonPrimary, inputClass } from "@/components/ui";

const CONDITION_OPTIONS = [
  { key: "hypertension", label: "Hypertension (diagnosed)" },
  { key: "diabetes", label: "Diabetes (diagnosed)" },
  { key: "anemia", label: "Anemia (diagnosed)" },
  { key: "knee_osteoarthritis", label: "Knee osteoarthritis" },
];

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
            "Fix the email/password and submit again, or untick the login option to continue."
          : (err as Error).message
      );
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <PageHeader
        title="New patient"
        subtitle="After saving you'll go straight to their first intake."
      />

      {error && <ErrorNote message={error} />}

      <form onSubmit={submit}>
        <Card>
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

            <div className="grid grid-cols-2 gap-4">
              <Field label="Sex">
                <select
                  className={inputClass}
                  value={form.sex}
                  onChange={(e) => set("sex", e.target.value)}
                >
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </Field>
              <Field label="Year of birth">
                <input
                  className={inputClass}
                  type="number"
                  min={1900}
                  max={new Date().getFullYear()}
                  required
                  value={form.birth_year}
                  onChange={(e) => set("birth_year", Number(e.target.value))}
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Height (cm)">
                <input
                  className={inputClass}
                  type="number"
                  min={80}
                  max={230}
                  step="0.5"
                  required
                  value={form.height_cm}
                  onChange={(e) => set("height_cm", Number(e.target.value))}
                />
              </Field>
              <Field label="Fitness level" hint="Used to scale the exercise plan.">
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
            </div>

            {form.sex === "female" && (
              <label className="flex items-center gap-2 text-sm text-ink-strong">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-line-strong text-teal-600"
                  checked={form.pregnant}
                  onChange={(e) => set("pregnant", e.target.checked)}
                />
                Currently pregnant
                <span className="text-xs text-ink-muted">
                  (changes anemia cutoffs, nutrient targets, and excluded exercises)
                </span>
              </label>
            )}

            <fieldset>
              <legend className="text-sm font-medium text-ink-strong">
                Known conditions
              </legend>
              <p className="mb-2 text-xs text-ink-muted">
                The engine also derives conditions from lab values — tick what is
                already diagnosed.
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {CONDITION_OPTIONS.map((c) => (
                  <label key={c.key} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-line-strong text-teal-600"
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

            <Field label="Notes (optional)">
              <textarea
                className={inputClass}
                rows={2}
                value={form.notes}
                onChange={(e) => set("notes", e.target.value)}
              />
            </Field>

            <div className="rounded-xl border border-line bg-surface-soft p-4">
              <label className="flex items-center gap-2 text-sm font-medium text-ink-strong">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-line-strong text-teal-600"
                  checked={withAccount}
                  onChange={(e) => setWithAccount(e.target.checked)}
                />
                Also create a login account for this patient
              </label>
              <p className="mt-1 text-xs text-ink-muted">
                Lets the patient sign in to see their visits and approved reports.
              </p>
              {withAccount && (
                <div className="mt-3 grid gap-4 sm:grid-cols-2">
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
                  <Field label="Temporary password" hint="At least 8 characters — share it with the patient.">
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

            <button type="submit" disabled={saving} className={buttonPrimary + " w-full"}>
              {saving ? "Saving…" : "Save & start intake"}
            </button>
          </div>
        </Card>
      </form>
    </div>
  );
}
