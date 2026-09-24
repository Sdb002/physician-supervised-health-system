"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";
import { Role } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  IconActivity,
  IconClipboard,
  IconDashboard,
  IconFileText,
  IconHeartPulse,
  IconLogout,
  IconShield,
  IconStethoscope,
  IconUsers,
  IconUtensils,
} from "@/components/icons";
import { Avatar, Badge, Skeleton } from "@/components/ui";
import { ThemeToggle } from "@/components/theme-toggle";

interface NavItem {
  href: string;
  label: string;
  icon: ReactNode;
}

const ROLE_CONFIG: Record<
  Role,
  {
    title: string;
    subtitle: string;
    mark: ReactNode;
    markBg: string;
    active: string;
    nav: NavItem[];
  }
> = {
  admin: {
    title: "স্বাস্থ্য পরিকল্পনা",
    subtitle: "Admin console",
    mark: <IconShield className="h-5 w-5" />,
    markBg: "bg-indigo-500",
    active: "bg-indigo-500/20 text-indigo-200",
    nav: [
      { href: "/admin", label: "Overview", icon: <IconDashboard className="h-4.5 w-4.5" /> },
      { href: "/admin/doctors", label: "Doctors", icon: <IconStethoscope className="h-4.5 w-4.5" /> },
      { href: "/admin/patients", label: "Patients", icon: <IconHeartPulse className="h-4.5 w-4.5" /> },
      { href: "/admin/users", label: "Users", icon: <IconUsers className="h-4.5 w-4.5" /> },
    ],
  },
  doctor: {
    title: "স্বাস্থ্য পরিকল্পনা",
    subtitle: "Physician dashboard",
    mark: <IconStethoscope className="h-5 w-5" />,
    markBg: "bg-teal-500",
    active: "bg-teal-500/20 text-teal-200",
    nav: [
      { href: "/doctor", label: "Overview", icon: <IconDashboard className="h-4.5 w-4.5" /> },
      { href: "/doctor/patients", label: "Patients", icon: <IconUsers className="h-4.5 w-4.5" /> },
      { href: "/doctor/review", label: "Review queue", icon: <IconClipboard className="h-4.5 w-4.5" /> },
    ],
  },
  patient: {
    title: "স্বাস্থ্য পরিকল্পনা",
    subtitle: "My health",
    mark: <IconHeartPulse className="h-5 w-5" />,
    markBg: "bg-emerald-500",
    active: "bg-emerald-500/20 text-emerald-200",
    nav: [
      { href: "/patient", label: "My dashboard", icon: <IconDashboard className="h-4.5 w-4.5" /> },
      { href: "/patient/reports", label: "My reports", icon: <IconFileText className="h-4.5 w-4.5" /> },
      { href: "/patient/foods", label: "Foods", icon: <IconUtensils className="h-4.5 w-4.5" /> },
      { href: "/patient/exercise", label: "Exercise", icon: <IconActivity className="h-4.5 w-4.5" /> },
    ],
  },
};

function isActive(pathname: string, href: string, home: string) {
  if (href === home) return pathname === home;
  return pathname === href || pathname.startsWith(href + "/");
}

export function Shell({ role, children }: { role: Role; children: ReactNode }) {
  const { session, ready, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const config = ROLE_CONFIG[role];
  const home = config.nav[0].href;

  useEffect(() => {
    if (ready && (session === null || session.user.role !== role)) {
      router.replace(`/login/${role}`);
    }
  }, [ready, session, role, router]);

  if (!ready || session === null || session.user.role !== role) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 p-6">
        <Skeleton className="h-8 w-56" />
        <div className="grid gap-4 sm:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const user = session.user;

  return (
    <div className="flex min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-slate-900 focus:shadow-lg focus:outline-2 focus:outline-offset-2 focus:outline-teal-600"
      >
        Skip to main content
      </a>
      <aside className="hidden w-64 shrink-0 flex-col bg-slate-900 p-4 text-slate-300 md:flex print:hidden!">
        <Link href={home} className="flex items-center gap-3 rounded-xl px-2 py-2">
          <span className={`flex h-9 w-9 items-center justify-center rounded-xl text-white ${config.markBg}`}>
            {config.mark}
          </span>
          <span>
            <span className="block text-sm font-bold text-white">{config.title}</span>
            <span className="block text-xs text-slate-400">{config.subtitle}</span>
          </span>
        </Link>

        <nav aria-label="Main" className="mt-6 flex-1 space-y-1">
          {config.nav.map((item) => {
            const active = isActive(pathname, item.href, home);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  active ? config.active : "text-slate-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </nav>

        <ThemeToggle />

        <div className="rounded-xl bg-white/5 p-3">
          <div className="flex items-center gap-3">
            <Avatar name={user.name} className="bg-slate-700! text-slate-200!" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-white">{user.name}</p>
              <p className="truncate text-xs text-slate-400">{user.email}</p>
            </div>
          </div>
          <button
            onClick={signOut}
            className="mt-3 flex w-full cursor-pointer items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors duration-200 hover:bg-white/10 hover:text-white"
          >
            <IconLogout className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-surface/90 px-4 py-2.5 backdrop-blur md:hidden print:hidden!">
          <nav aria-label="Main (compact)" className="flex gap-1 overflow-x-auto text-sm font-medium">
            {config.nav.map((item) => {
              const active = isActive(pathname, item.href, home);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`whitespace-nowrap rounded-lg px-3 py-1.5 ${
                    active
                      ? "bg-clinical text-on-clinical"
                      : "text-ink-soft hover:bg-surface-soft"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <button
            onClick={signOut}
            aria-label="Sign out"
            className="ml-2 cursor-pointer rounded-lg p-2 text-ink-muted transition-colors duration-200 hover:bg-surface-soft"
          >
            <IconLogout className="h-4 w-4" />
          </button>
        </header>

        <div className="hidden items-center justify-end gap-3 border-b border-line bg-surface px-6 py-2.5 md:flex print:hidden!">
          <Badge kind={user.role}>{user.role}</Badge>
          <span className="text-sm text-ink-muted">{user.name}</span>
        </div>

        <main id="main-content" className="mx-auto max-w-6xl p-4 md:p-6 print:max-w-none print:p-0">
          {children}
        </main>
      </div>
    </div>
  );
}
