"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";
import { Role } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Lang, useLang } from "@/lib/use-lang";
import {
  IconActivity,
  IconClipboard,
  IconCookingPot,
  IconDashboard,
  IconFileText,
  IconHeartPulse,
  IconHome,
  IconLogout,
  IconStethoscope,
  IconUsers,
  IconUtensils,
} from "@/components/icons";
import { Avatar, Skeleton, focusRing } from "@/components/ui";
import { ThemeToggle } from "@/components/theme-toggle";
import { LangSwitch } from "@/components/lang-switch";
import { Brand, BrandMark } from "@/components/brand";

interface NavItem {
  href: string;
  label: string | Record<Lang, string>;
  icon: (cls: string) => ReactNode;
}

const ROLE_CONFIG: Record<Role, { portal: string | Record<Lang, string>; nav: NavItem[] }> = {
  admin: {
    portal: "Administration",
    nav: [
      { href: "/admin", label: "Overview", icon: (c) => <IconDashboard className={c} /> },
      { href: "/admin/doctors", label: "Doctors", icon: (c) => <IconStethoscope className={c} /> },
      { href: "/admin/patients", label: "Patients", icon: (c) => <IconHeartPulse className={c} /> },
      { href: "/admin/users", label: "Users", icon: (c) => <IconUsers className={c} /> },
    ],
  },
  doctor: {
    portal: "Physician",
    nav: [
      { href: "/doctor", label: "Today", icon: (c) => <IconHome className={c} /> },
      { href: "/doctor/review", label: "Review queue", icon: (c) => <IconClipboard className={c} /> },
      { href: "/doctor/patients", label: "Patients", icon: (c) => <IconUsers className={c} /> },
    ],
  },
  patient: {
    portal: { en: "Patient", bn: "রোগী" },
    nav: [
      { href: "/patient", label: { en: "Home", bn: "হোম" }, icon: (c) => <IconHome className={c} /> },
      { href: "/patient/reports", label: { en: "Reports", bn: "রিপোর্ট" }, icon: (c) => <IconFileText className={c} /> },
      { href: "/patient/foods", label: { en: "Meals", bn: "খাবার" }, icon: (c) => <IconUtensils className={c} /> },
      { href: "/patient/recipes", label: { en: "Recipes", bn: "রান্না" }, icon: (c) => <IconCookingPot className={c} /> },
      { href: "/patient/exercise", label: { en: "Exercise", bn: "ব্যায়াম" }, icon: (c) => <IconActivity className={c} /> },
    ],
  },
};

const SIGN_OUT: Record<Lang, string> = { en: "Sign out", bn: "সাইন আউট" };

const text = (value: string | Record<Lang, string>, lang: Lang) =>
  typeof value === "string" ? value : value[lang];

function isActive(pathname: string, href: string, home: string) {
  if (href === home) return pathname === home;
  return pathname === href || pathname.startsWith(href + "/");
}

export function Shell({ role, children }: { role: Role; children: ReactNode }) {
  const { session, ready, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [storedLang] = useLang();
  const config = ROLE_CONFIG[role];
  const home = config.nav[0].href;
  // Only the patient portal is bilingual; staff screens stay in English.
  const lang: Lang = role === "patient" ? storedLang : "en";

  useEffect(() => {
    if (ready && (session === null || session.user.role !== role)) {
      router.replace(`/login/${role}`);
    }
  }, [ready, session, role, router]);

  if (!ready || session === null || session.user.role !== role) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 p-6">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-24" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const user = session.user;

  return (
    <div className="flex min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-surface focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-ink focus:shadow-lg focus:outline-2 focus:outline-offset-2 focus:outline-clinical"
      >
        Skip to main content
      </a>

      {/* desktop rail */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-line bg-surface md:flex print:hidden!">
        <Link href={home} className={`mx-3 mt-4 rounded-lg px-2 py-1.5 ${focusRing}`}>
          <Brand caption={text(config.portal, lang)} lang={lang} />
        </Link>

        <nav aria-label="Main" className="mt-6 flex-1 space-y-1 overflow-y-auto px-3">
          {config.nav.map((item) => {
            const active = isActive(pathname, item.href, home);
            return (
              <Link
                key={item.href}
                href={item.href}
                lang={lang}
                aria-current={active ? "page" : undefined}
                className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-[15px] transition-colors duration-150 ${focusRing} ${
                  active
                    ? "bg-clinical-tint font-semibold text-clinical before:absolute before:-left-3 before:top-2 before:bottom-2 before:w-1 before:rounded-r-full before:bg-clinical"
                    : "font-medium text-ink-soft hover:bg-surface-soft hover:text-ink"
                }`}
              >
                {item.icon("h-5 w-5 shrink-0")}
                {text(item.label, lang)}
              </Link>
            );
          })}
        </nav>

        <div className="space-y-2 border-t border-line p-3">
          {role === "patient" && <LangSwitch className="flex w-full" />}
          <ThemeToggle />
          <div className="flex items-center gap-3 rounded-xl bg-surface-soft p-2.5">
            <Avatar name={user.name} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink">{user.name}</p>
              <p className="truncate text-xs text-ink-muted">{user.email}</p>
            </div>
            <button
              onClick={signOut}
              aria-label={SIGN_OUT[lang]}
              title={SIGN_OUT[lang]}
              className={`shrink-0 cursor-pointer rounded-lg p-2 text-ink-muted transition-colors duration-150 hover:bg-surface hover:text-ink ${focusRing}`}
            >
              <IconLogout className="h-4.5 w-4.5" />
            </button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        {/* compact top bar */}
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-surface/95 px-4 py-2.5 backdrop-blur md:hidden print:hidden!">
          <Link href={home} className={`flex min-w-0 items-center gap-2.5 rounded-md ${focusRing}`}>
            <BrandMark className="h-9 w-9" />
            <span lang="bn" className="font-display truncate text-[17px] font-bold text-ink">
              স্বাস্থ্য পরিকল্পনা
            </span>
          </Link>
          <div className="flex shrink-0 items-center gap-1.5">
            {role === "patient" && <LangSwitch />}
            <button
              onClick={signOut}
              aria-label={SIGN_OUT[lang]}
              className={`cursor-pointer rounded-lg p-2 text-ink-muted hover:bg-surface-soft ${focusRing}`}
            >
              <IconLogout className="h-5 w-5" />
            </button>
          </div>
        </header>

        <main
          id="main-content"
          className="mx-auto max-w-6xl px-4 pb-28 pt-5 sm:px-6 md:px-8 md:pb-14 md:pt-9 print:max-w-none print:p-0"
        >
          {children}
        </main>

        {/* bottom tab bar: thumb-reachable, labels always visible */}
        <nav
          aria-label="Main (compact)"
          className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden print:hidden!"
        >
          <ul className="mx-auto flex max-w-lg">
            {config.nav.map((item) => {
              const active = isActive(pathname, item.href, home);
              return (
                <li key={item.href} className="flex-1">
                  <Link
                    href={item.href}
                    lang={lang}
                    aria-current={active ? "page" : undefined}
                    className={`flex flex-col items-center gap-0.5 px-1 pb-2 pt-2.5 text-[11px] leading-tight ${focusRing} ${
                      active ? "font-bold text-clinical" : "font-medium text-ink-muted"
                    }`}
                  >
                    <span
                      className={`flex h-7 w-12 items-center justify-center rounded-full ${
                        active ? "bg-clinical-tint" : ""
                      }`}
                    >
                      {item.icon("h-5 w-5")}
                    </span>
                    {text(item.label, lang)}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </div>
  );
}
