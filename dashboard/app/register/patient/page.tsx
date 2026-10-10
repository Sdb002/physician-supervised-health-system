"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AuthLayout } from "@/components/auth-layout";
import { ErrorNote, Field, buttonPrimary, checkboxClass, inputClass } from "@/components/ui";

const CONDITION_OPTIONS = [
  { key: "hypertension", label: "High blood pressure" },
  { key: "diabetes", label: "Diabetes" },
  { key: "anemia", label: "Anaemia" },
  { key: "knee_osteoarthritis", label: "Knee osteoarthritis" },
];

const legendClass = "text-base font-semibold text-ink";

/** A row-sized checkbox target: the whole row toggles, not just the 16px box. */
const choiceRow =
  "flex cursor-pointer items-center gap-3 rounded-lg border border-line px-3 py-2.5 text-sm text-ink-strong " +
  "has-[:checked]:border-clinical has-[:checked]:bg-clinical-tint hover:bg-surface-soft";

export default function PatientRegisterPage() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    sex: "female" as "male" | "female",
    birth_year: 1990,
    height_cm: 160,
    pregnant: false,
    conditions: [] as string[],
    fitness_level: "beginner",
  });

  const set = (key: string, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.register({
        name: form.name,
        email: form.email,
        password: form.password,
        role: "patient",
        profile: {
          sex: form.sex,
          birth_year: form.birth_year,
          height_cm: form.height_cm,
          pregnant: form.sex === "female" ? form.pregnant : false,
          conditions: form.conditions,
          fitness_level: form.fitness_level,
        },
      });
      const session = await api.login({ email: form.email, password: form.password });
      signIn(session);
      router.replace("/patient");
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      wide
      title="Create your patient account"
      subtitle="Your doctor uses these details at your visits. You see a plan only after your doctor approves it."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login/patient" className="font-semibold text-clinical hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-7">
        {error && <ErrorNote message={error} />}

        <fieldset className="space-y-4">
          <legend className={legendClass}>Your account</legend>
          <Field label="Full name">
            <input
              className={inputClass}
              required
              autoComplete="name"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="e.g. Ayesha Rahman"
            />
          </Field>
          <Field label="Email">
            <input
              className={inputClass}
              type="email"
              required
              autoComplete="email"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
            />
          </Field>
          <Field label="Password" hint="At least 8 characters.">
            <input
              className={inputClass}
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
            />
          </Field>
        </fieldset>

        <fieldset className="space-y-4 border-t border-line pt-6">
          <legend className={`${legendClass} float-left mb-4 w-full`}>About you</legend>
          <div className="clear-both" role="radiogroup" aria-label="Sex">
            <span className="text-sm font-semibold text-ink-strong">Sex</span>
            <div className="mt-1.5 grid grid-cols-2 gap-2">
              {(["female", "male"] as const).map((s) => (
                <label key={s} className={choiceRow}>
                  <input
                    type="radio"
                    name="sex"
                    className="h-4 w-4 accent-clinical"
                    checked={form.sex === s}
                    onChange={() => set("sex", s)}
                  />
                  {s === "female" ? "Female" : "Male"}
                </label>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
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
          <Field label="How active are you?" hint="Used to set a safe starting point for exercise.">
            <select
              className={inputClass}
              value={form.fitness_level}
              onChange={(e) => set("fitness_level", e.target.value)}
            >
              <option value="beginner">Not very active</option>
              <option value="intermediate">Somewhat active</option>
              <option value="advanced">Very active</option>
            </select>
          </Field>
          {form.sex === "female" && (
            <label className={choiceRow}>
              <input
                type="checkbox"
                className={checkboxClass}
                checked={form.pregnant}
                onChange={(e) => set("pregnant", e.target.checked)}
              />
              I am currently pregnant
            </label>
          )}
        </fieldset>

        <fieldset className="border-t border-line pt-6">
          <legend className={`${legendClass} float-left w-full`}>Conditions a doctor has diagnosed</legend>
          <p className="clear-both pt-1 text-sm text-ink-muted">Tick any that apply. Leave all unticked if none.</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
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

        <button type="submit" disabled={busy} className={`${buttonPrimary} w-full`}>
          {busy ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
