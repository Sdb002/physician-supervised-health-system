"use client";

import Link from "next/link";
import { notFound, useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError, Role } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AuthLayout } from "@/components/auth-layout";
import { ErrorNote, Field, InfoNote, buttonPrimary, inputClass } from "@/components/ui";
import { useT } from "@/lib/use-t";

const ROLE_UI: Record<
  Role,
  {
    title: string;
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
  const { t, rich } = useT();

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
      title={t(ui.title)}
      subtitle={t(ui.blurb)}
      footer={
        ui.register && (
          <>
            {t(ui.register.prompt)}{" "}
            <Link href={ui.register.href} className="font-semibold text-clinical hover:underline">
              {t(ui.register.label)}
            </Link>
          </>
        )
      }
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <ErrorNote message={error} />}
        {pendingNotice && (
          <InfoNote>
            {rich("Your registration is still {waiting}. You can sign in as soon as an admin approves your account.", {
              waiting: <strong>{t("waiting for admin approval")}</strong>,
            })}
          </InfoNote>
        )}
        <Field label={t("Email")}>
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
        <Field label={t("Password")}>
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
          {busy ? t("Signing in…") : t("Sign in")}
        </button>
      </form>
    </AuthLayout>
  );
}
