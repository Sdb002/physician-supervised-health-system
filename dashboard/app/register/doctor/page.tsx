"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { IconCheck, IconStethoscope } from "@/components/icons";
import { ErrorNote, Field, inputClass } from "@/components/ui";

export default function DoctorRegisterPage() {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    specialty: "",
    license_no: "",
  });

  const set = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.register({ ...form, role: "doctor" });
      setSubmitted(true);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-teal-50 via-slate-50 to-slate-100 dark:from-teal-950 dark:via-slate-900 dark:to-slate-950 p-6">
        <div className="w-full max-w-sm rounded-2xl border border-line bg-surface p-8 text-center shadow-lg shadow-slate-200/60">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
            <IconCheck className="h-6 w-6" />
          </span>
          <h1 className="mt-4 text-xl font-bold text-ink">Application submitted</h1>
          <p className="mt-2 text-sm leading-6 text-ink-muted">
            Your registration was sent to the admin for review. You&apos;ll be able to sign in
            as soon as it&apos;s approved.
          </p>
          <Link
            href="/login/doctor"
            className="mt-6 inline-flex w-full items-center justify-center rounded-lg bg-clinical px-4 py-2.5 text-sm font-medium text-on-clinical hover:bg-clinical-hover"
          >
            Go to doctor sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-teal-50 via-slate-50 to-slate-100 dark:from-teal-950 dark:via-slate-900 dark:to-slate-950 p-6">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-line bg-surface p-7 shadow-lg shadow-slate-200/60">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-100 text-teal-700">
            <IconStethoscope className="h-6 w-6" />
          </span>
          <h1 className="mt-4 text-xl font-bold tracking-tight text-ink">
            Apply for a doctor account
          </h1>
          <p className="mt-1 text-sm text-ink-muted">
            Registrations are reviewed by the admin before activation.
          </p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            {error && <ErrorNote message={error} />}
            <Field label="Full name">
              <input
                className={inputClass}
                required
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                placeholder="Dr. …"
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
              <Field label="Specialty">
                <input
                  className={inputClass}
                  value={form.specialty}
                  onChange={(e) => set("specialty", e.target.value)}
                  placeholder="e.g. Endocrinology"
                />
              </Field>
              <Field label="License / BMDC no.">
                <input
                  className={inputClass}
                  value={form.license_no}
                  onChange={(e) => set("license_no", e.target.value)}
                  placeholder="e.g. BMDC-12345"
                />
              </Field>
            </div>
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-clinical px-4 py-2.5 text-sm font-medium text-on-clinical shadow-sm hover:bg-clinical-hover disabled:opacity-50"
            >
              {busy ? "Submitting…" : "Submit application"}
            </button>
          </form>

          <p className="mt-4 text-center text-xs text-ink-muted">
            Already approved?{" "}
            <Link href="/login/doctor" className="font-medium hover:underline">
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
