"use client";

import Link from "next/link";
import { IconChevronRight, IconHeartPulse, IconShield, IconStethoscope } from "@/components/icons";

const PORTALS = [
  {
    role: "patient",
    title: "Patient",
    description: "See your visits, review status, and physician-approved reports.",
    icon: <IconHeartPulse className="h-6 w-6" />,
    iconBg: "bg-emerald-100 text-emerald-700",
    ring: "hover:border-emerald-300",
    register: { href: "/register/patient", label: "Create a patient account" },
  },
  {
    role: "doctor",
    title: "Doctor",
    description: "Run intake, review assessments, and approve patient reports.",
    icon: <IconStethoscope className="h-6 w-6" />,
    iconBg: "bg-teal-100 text-teal-700",
    ring: "hover:border-teal-300",
    register: { href: "/register/doctor", label: "Apply for a doctor account" },
  },
  {
    role: "admin",
    title: "Admin",
    description: "Approve doctor registrations and oversee the platform.",
    icon: <IconShield className="h-6 w-6" />,
    iconBg: "bg-indigo-100 text-indigo-700",
    ring: "hover:border-indigo-300",
    register: null,
  },
] as const;

export default function PortalChooser() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-100 via-slate-50 to-teal-50 dark:from-slate-950 dark:via-slate-900 dark:to-teal-950 p-6">
      <div className="w-full max-w-3xl">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-ink">স্বাস্থ্য পরিকল্পনা</h1>
          <p className="mt-2 text-sm text-ink-muted">
            Physician-supervised diet &amp; lifestyle recommendations. Choose your portal to sign in.
          </p>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {PORTALS.map((portal) => (
            <div
              key={portal.role}
              className={`flex flex-col rounded-2xl border border-line bg-surface p-5 shadow-sm transition ${portal.ring}`}
            >
              <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${portal.iconBg}`}>
                {portal.icon}
              </span>
              <h2 className="mt-3 font-semibold text-ink">{portal.title}</h2>
              <p className="mt-1 flex-1 text-xs leading-5 text-ink-muted">{portal.description}</p>
              <Link
                href={`/login/${portal.role}`}
                className="mt-4 inline-flex items-center justify-center gap-1 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
              >
                Sign in <IconChevronRight className="h-4 w-4" />
              </Link>
              {portal.register && (
                <Link
                  href={portal.register.href}
                  className="mt-2 text-center text-xs font-medium text-ink-muted hover:text-ink hover:underline"
                >
                  {portal.register.label}
                </Link>
              )}
            </div>
          ))}
        </div>

        <p className="mt-8 text-center text-xs text-ink-muted">
          Every recommendation comes from a deterministic, cited rule engine and is released only
          after a physician approves it.
        </p>
      </div>
    </div>
  );
}
