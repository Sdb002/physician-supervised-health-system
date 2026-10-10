"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { AuthLayout } from "@/components/auth-layout";
import { IconCheck } from "@/components/icons";
import { ErrorNote, Field, buttonPrimary, inputClass } from "@/components/ui";

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
      <AuthLayout
        title={
          <span className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-ok-tint text-ok-ink">
              <IconCheck className="h-5 w-5" />
            </span>
            Application sent
          </span>
        }
        subtitle="An admin will check your registration. You can sign in as soon as it is approved."
      >
        <Link href="/login/doctor" className={`${buttonPrimary} w-full`}>
          Go to doctor sign in
        </Link>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      wide
      title="Apply for a doctor account"
      subtitle="An admin checks every application before the account can sign in."
      footer={
        <>
          Already approved?{" "}
          <Link href="/login/doctor" className="font-semibold text-clinical hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <ErrorNote message={error} />}
        <Field label="Full name">
          <input
            className={inputClass}
            required
            autoComplete="name"
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
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Specialty">
            <input
              className={inputClass}
              value={form.specialty}
              onChange={(e) => set("specialty", e.target.value)}
              placeholder="e.g. Endocrinology"
            />
          </Field>
          <Field label="BMDC registration no.">
            <input
              className={inputClass}
              value={form.license_no}
              onChange={(e) => set("license_no", e.target.value)}
              placeholder="e.g. A-12345"
            />
          </Field>
        </div>
        <button type="submit" disabled={busy} className={`${buttonPrimary} w-full`}>
          {busy ? "Sending…" : "Send application"}
        </button>
      </form>
    </AuthLayout>
  );
}
