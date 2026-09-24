"use client";

import Link from "next/link";
import { notFound, useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError, Role } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { IconHeartPulse, IconShield, IconStethoscope } from "@/components/icons";
import { ErrorNote, Field, InfoNote, inputClass } from "@/components/ui";

const ROLE_UI: Record<
  Role,
  {
    title: string;
    blurb: string;
    icon: React.ReactNode;
    iconBg: string;
    button: string;
    gradient: string;
    register: { href: string; label: string } | null;
  }
> = {
  admin: {
    title: "Admin sign in",
    blurb: "Approve doctor registrations and oversee the platform.",
    icon: <IconShield className="h-6 w-6" />,
    iconBg: "bg-indigo-100 text-indigo-700",
    button: "bg-indigo-600 hover:bg-indigo-700",
    gradient: "from-indigo-50 via-slate-50 to-slate-100 dark:from-indigo-950 dark:via-slate-900 dark:to-slate-950",
    register: null,
  },
  doctor: {
    title: "Doctor sign in",
    blurb: "Run intake, review assessments, and approve reports.",
    icon: <IconStethoscope className="h-6 w-6" />,
    iconBg: "bg-teal-100 text-teal-700",
    button: "bg-clinical hover:bg-clinical-hover",
    gradient: "from-teal-50 via-slate-50 to-slate-100 dark:from-teal-950 dark:via-slate-900 dark:to-slate-950",
    register: { href: "/register/doctor", label: "New here? Apply for a doctor account" },
  },
  patient: {
    title: "Patient sign in",
    blurb: "See your visits and physician-approved reports.",
    icon: <IconHeartPulse className="h-6 w-6" />,
    iconBg: "bg-emerald-100 text-emerald-700",
    button: "bg-emerald-700 hover:bg-emerald-800",
    gradient: "from-emerald-50 via-slate-50 to-slate-100 dark:from-emerald-950 dark:via-slate-900 dark:to-slate-950",
    register: { href: "/register/patient", label: "New here? Create a patient account" },
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
    <div className={`flex min-h-screen items-center justify-center bg-gradient-to-b p-6 ${ui.gradient}`}>
      <div className="w-full max-w-sm">
        <div className="rounded-2xl border border-line bg-surface p-7 shadow-lg shadow-slate-200/60">
          <span className={`flex h-12 w-12 items-center justify-center rounded-xl ${ui.iconBg}`}>
            {ui.icon}
          </span>
          <h1 className="mt-4 text-xl font-bold tracking-tight text-ink">{ui.title}</h1>
          <p className="mt-1 text-sm text-ink-muted">{ui.blurb}</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            {error && <ErrorNote message={error} />}
            {pendingNotice && (
              <InfoNote>
                Your registration is still <strong>awaiting admin approval</strong>. You&apos;ll be
                able to sign in once an admin approves your account.
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
                placeholder="••••••••"
              />
            </Field>
            <button
              type="submit"
              disabled={busy}
              className={`w-full rounded-lg px-4 py-2.5 text-sm font-medium text-white shadow-sm disabled:opacity-50 ${ui.button}`}
            >
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          {ui.register && (
            <p className="mt-4 text-center text-xs text-ink-muted">
              <Link href={ui.register.href} className="font-medium hover:underline">
                {ui.register.label}
              </Link>
            </p>
          )}
        </div>
        <p className="mt-4 text-center text-xs text-ink-muted">
          <Link href="/login" className="hover:underline">← Choose a different portal</Link>
        </p>
      </div>
    </div>
  );
}
