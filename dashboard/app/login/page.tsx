"use client";

import Link from "next/link";
import {
  IconChevronRight,
  IconHeartPulse,
  IconShield,
  IconStethoscope,
} from "@/components/icons";
import { Brand } from "@/components/brand";
import { StethoscopeArt } from "@/components/stethoscope-art";
import { focusRing } from "@/components/ui";
import { LangSwitch } from "@/components/lang-switch";
import { useT } from "@/lib/use-t";

const PORTALS = [
  {
    role: "patient",
    title: "Patient",
    description: "Read the plan your doctor approved for you.",
    icon: <IconHeartPulse className="h-5 w-5" />,
  },
  {
    role: "doctor",
    title: "Doctor",
    description: "Record check-ups, review plans and approve them.",
    icon: <IconStethoscope className="h-5 w-5" />,
  },
  {
    role: "admin",
    title: "Administrator",
    description: "Approve doctor accounts and oversee the service.",
    icon: <IconShield className="h-5 w-5" />,
  },
] as const;

/* How a plan reaches a patient. A real sequence, so it is numbered. */
const STEPS = [
  "Your doctor records your check-up",
  "They review the plan the system drafts",
  "You get the plan once they approve it",
];

const HEADLINE = {
  en: "Your diet and exercise plan, signed by your doctor.",
  bn: "আপনার খাদ্য ও ব্যায়ামের পরিকল্পনা, চিকিৎসকের অনুমোদনসহ।",
} as const;

export default function PortalChooser() {
  const { t, n, lang } = useT();
  return (
    <div className="relative min-h-screen overflow-x-clip">
      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-5 py-6 sm:px-8 lg:py-8">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <Brand />
          <LangSwitch />
        </header>

        <div className="grid flex-1 items-center gap-6 py-6 lg:grid-cols-[minmax(0,32rem)_1fr] lg:gap-10 lg:py-10">
          {/* phones: the drawing leads the page; desktop: it fills the right half */}
          <div className="relative order-first mx-auto w-64 sm:w-80 lg:order-last lg:mx-0 lg:w-auto lg:self-stretch">
            <StethoscopeArt className="w-full lg:absolute lg:-right-20 lg:top-1/2 lg:w-[min(40rem,46vw)] lg:-translate-y-1/2 xl:-right-28" />
          </div>

          <main className="relative">
            {/* the headline in the reader's language, the other one under it */}
            <h1 className="font-display text-[2.5rem] font-bold leading-[1.1] text-ink sm:text-[3.25rem]">
              {HEADLINE[lang]}
            </h1>
            <p className="font-display mt-3 text-xl font-medium leading-8 text-ink-soft sm:text-2xl">
              {HEADLINE[lang === "bn" ? "en" : "bn"]}
            </p>

            <ol className="mt-6 grid gap-2.5 sm:grid-cols-3 sm:gap-3">
              {STEPS.map((step, i) => (
                <li key={step} className="flex items-start gap-2.5 text-sm leading-5 text-ink-soft">
                  <span
                    aria-hidden="true"
                    className="font-display flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-clinical-tint text-sm font-bold text-clinical"
                  >
                    {n(i + 1)}
                  </span>
                  {t(step)}
                </li>
              ))}
            </ol>

            <section
              aria-labelledby="portal-heading"
              className="mt-8 overflow-hidden rounded-2xl border border-line bg-surface shadow-[0_24px_48px_-32px_rgb(22_35_77/0.45)]"
            >
              <h2
                id="portal-heading"
                className="font-display border-b border-line px-5 pb-2.5 pt-3.5 text-lg font-bold text-ink"
              >
                {t("Sign in as")}
              </h2>
              <ul className="divide-y divide-line">
                {PORTALS.map((portal) => (
                  <li key={portal.role}>
                    <Link
                      href={`/login/${portal.role}`}
                      className={`group flex items-center gap-4 px-5 py-3.5 transition-colors duration-150 hover:bg-clinical-tint/50 ${focusRing} focus-visible:-outline-offset-2`}
                    >
                      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-clinical-tint text-clinical transition-colors duration-150 group-hover:bg-clinical group-hover:text-on-clinical">
                        {portal.icon}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-base font-semibold text-ink">
                          {t(portal.title)}
                        </span>
                        <span className="block text-sm text-ink-muted">{t(portal.description)}</span>
                      </span>
                      <IconChevronRight className="h-5 w-5 shrink-0 text-ink-muted transition-transform duration-150 group-hover:translate-x-0.5 group-hover:text-clinical" />
                    </Link>
                  </li>
                ))}
              </ul>
            </section>

            <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 px-1 text-sm text-ink-muted">
              <p>
                {t("New patient?")}{" "}
                <Link href="/register/patient" className="font-semibold text-clinical hover:underline">
                  {t("Create an account")}
                </Link>
              </p>
              <p>
                {t("Doctor?")}{" "}
                <Link href="/register/doctor" className="font-semibold text-clinical hover:underline">
                  {t("Apply for an account")}
                </Link>
              </p>
            </div>
          </main>
        </div>

        <footer className="relative max-w-xl text-xs leading-5 text-ink-muted">
          {t("Plans come from a rule engine that cites clinical guidelines (ADA, ACC/AHA, WHO, ACSM). They support a consultation and do not replace one.")}
        </footer>
      </div>
    </div>
  );
}
