"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { IconHeartPulse } from "@/components/icons";
import { ErrorNote, Field, inputClass } from "@/components/ui";

const CONDITION_OPTIONS = [
  { key: "hypertension", label: "Hypertension" },
  { key: "diabetes", label: "Diabetes" },
  { key: "anemia", label: "Anemia" },
  { key: "knee_osteoarthritis", label: "Knee osteoarthritis" },
];

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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-emerald-50 via-slate-50 to-slate-100 dark:from-emerald-950 dark:via-slate-900 dark:to-slate-950 p-6">
      <div className="w-full max-w-md py-8">
        <div className="rounded-2xl border border-line bg-surface p-7 shadow-lg shadow-slate-200/60">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
            <IconHeartPulse className="h-6 w-6" />
          </span>
          <h1 className="mt-4 text-xl font-bold tracking-tight text-ink">
            Create your patient account
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            Your doctor uses this profile during visits — reports are released to you only after
            physician approval.
          </p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            {error && <ErrorNote message={error} />}
            <Field label="Full name">
              <input
                className={inputClass}
                required
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
              <Field label="Fitness level">
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
                  className="h-4 w-4 rounded border-line-strong text-emerald-600"
                  checked={form.pregnant}
                  onChange={(e) => set("pregnant", e.target.checked)}
                />
                Currently pregnant
              </label>
            )}

            <fieldset>
              <legend className="text-sm font-medium text-ink-strong">
                Diagnosed conditions (if any)
              </legend>
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                {CONDITION_OPTIONS.map((c) => (
                  <label key={c.key} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-line-strong text-emerald-600"
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

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50"
            >
              {busy ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="mt-4 text-center text-xs text-ink-muted">
            Already have an account?{" "}
            <Link href="/login/patient" className="font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
        <p className="mt-4 text-center text-xs text-ink-muted">
          <Link href="/login" className="hover:underline">← Choose a different portal</Link>
        </p>
      </div>
    </div>
  );
}
