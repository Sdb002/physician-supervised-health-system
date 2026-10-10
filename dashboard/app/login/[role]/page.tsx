"use client";

import Link from "next/link";
import { notFound, useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError, Role } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AuthLayout } from "@/components/auth-layout";
import { ErrorNote, Field, InfoNote, buttonPrimary, inputClass } from "@/components/ui";

const ROLE_UI: Record<
  Role,
  {
    title: string;
    titleBn?: string;
    blurb: string;
    register: { href: string; prompt: string; label: string } | null;
  }
> = {
  admin: {
    title: "Administrator sign in",
    blurb: "Approve doctor accounts and oversee the service.",
    register: null,
  },
  doctor: {
    title: "Doctor sign in",
    blurb: "Record check-ups, review plans and approve them.",
    register: { href: "/register/doctor", prompt: "New here?", label: "Apply for a doctor account" },
  },
  patient: {
    title: "Patient sign in",
    titleBn: "রোগী হিসেবে সাইন ইন",
    blurb: "Read the plan your doctor approved for you.",
    register: { href: "/register/patient", prompt: "New here?", label: "Create a patient account" },
  },
};

export default function LoginPage() {
  const { role } = useParams<{ role: string }>();
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pendingNotice, setPendingNotice] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!(role in ROLE_UI)) notFound();
  const ui = ROLE_UI[role as Role];

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setPendingNotice(false);
    try {
      const session = await api.login({ email, password, role: role as Role });
      signIn(session);
      router.replace(`/${session.user.role}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403 && err.message.includes("awaiting")) {
        setPendingNotice(true);
      } else {
        setError((err as Error).message);
      }
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title={
        <>
          {ui.title}
          {ui.titleBn && (
            <span lang="bn" className="mt-0.5 block text-base font-medium text-ink-muted">
              {ui.titleBn}
            </span>
          )}
        </>
      }
      subtitle={ui.blurb}
      footer={
        ui.register && (
          <>
            {ui.register.prompt}{" "}
            <Link href={ui.register.href} className="font-semibold text-clinical hover:underline">
              {ui.register.label}
            </Link>
          </>
        )
      }
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <ErrorNote message={error} />}
        {pendingNotice && (
          <InfoNote>
            Your registration is still <strong>waiting for admin approval</strong>. You can sign in
            as soon as an admin approves your account.
          </InfoNote>
        )}
        <Field label="Email">
          <input
            className={inputClass}
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </Field>
        <Field label="Password">
          <input
            className={inputClass}
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <button type="submit" disabled={busy} className={`${buttonPrimary} w-full`}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </AuthLayout>
  );
}
