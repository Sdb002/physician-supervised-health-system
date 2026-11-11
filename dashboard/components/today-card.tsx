"use client";

/** The patient home's way into the daily task list: today's progress and
 * the streak, one tap from the Today page. Shows nothing until there is a
 * plan with tasks (or if the tasks cannot be loaded: the home page has the
 * plan itself). */

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, TodayTasks } from "@/lib/api";
import type { Lang } from "@/lib/use-lang";
import { IconChevronRight, IconFlame, IconListChecks } from "@/components/icons";
import { focusRing } from "@/components/ui";

const L = {
  en: {
    title: "Today's tasks",
    of: (done: string, total: string) => `${done} of ${total} done`,
    allDone: "All done for today",
    streak: (n: string) => `${n} days in a row`,
    streakOne: "1 day in a row",
  },
  bn: {
    title: "আজকের কাজ",
    of: (done: string, total: string) => `${total}টির মধ্যে ${done}টি সম্পন্ন`,
    allDone: "আজকের সব কাজ শেষ",
    streak: (n: string) => `${n} দিন টানা`,
    streakOne: "১ দিন টানা",
  },
} as const;

export function TodayCard({ lang }: { lang: Lang }) {
  const [view, setView] = useState<TodayTasks | null>(null);
  useEffect(() => {
    api.myTasks().then(setView).catch(() => setView(null));
  }, []);
  if (!view?.plan || view.total === 0) return null;

  const t = L[lang];
  const n = (x: number) => x.toLocaleString(lang === "bn" ? "bn-BD" : "en");
  const streak = view.streak.current;
  const allDone = view.done === view.total;
  return (
    <Link
      href="/patient/today"
      className={`flex items-center gap-4 rounded-xl border border-line bg-surface p-4 transition-colors duration-150 hover:border-line-strong active:bg-surface-soft sm:px-5 ${focusRing}`}
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-clinical-tint text-clinical">
        <IconListChecks className="h-5.5 w-5.5" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block font-semibold text-ink">{t.title}</span>
        <span className="block text-sm text-ink-soft">{allDone ? t.allDone : t.of(n(view.done), n(view.total))}</span>
        {/* a bar for the day, under the words */}
        <span className="mt-2 block h-1.5 overflow-hidden rounded-full bg-line" aria-hidden="true">
          <span
            className="block h-full rounded-full bg-clinical transition-[width] duration-300 motion-reduce:transition-none"
            style={{ width: `${(view.done / view.total) * 100}%` }}
          />
        </span>
      </span>
      <span className={`flex shrink-0 items-center gap-1 text-sm font-semibold ${streak ? "text-clinical" : "text-ink-muted"}`}>
        <IconFlame className="h-5 w-5" />
        <span className="hidden sm:inline">{streak === 1 ? t.streakOne : t.streak(n(streak))}</span>
        <span className="sm:hidden">{n(streak)}</span>
      </span>
      <IconChevronRight className="h-5 w-5 shrink-0 text-ink-muted" />
    </Link>
  );
}
