"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, DailyTask, DayStatus, TodayTasks } from "@/lib/api";
import { useLang } from "@/lib/use-lang";
import type { Lang } from "@/lib/use-lang";
import { localName, mealName, portionText, weekdayName } from "@/lib/clinical-terms";
import { IconActivity, IconCheck, IconChevronRight, IconFlame, IconListChecks, IconUtensils } from "@/components/icons";
import { EmptyState, ErrorNote, Note, PageHeader, Skeleton, focusRing } from "@/components/ui";

const L = {
  en: {
    title: "Today",
    of: (done: string, total: string) => `${done} of ${total} done`,
    keepGoing: "Tick each one off as you go.",
    allDone: "All done for today. Come back tomorrow to keep your streak.",
    streak: "days in a row",
    streakOne: "day in a row",
    best: (n: string) => `Best: ${n}`,
    lastWeek: "The last seven days",
    status: {
      complete: "all done",
      partial: "some done",
      missed: "not done",
      today: "today",
      none: "no plan yet",
    } as Record<DayStatus, string>,
    meals: "Meals",
    mealsHint: "Tick a meal once you have eaten it.",
    exercise: "Exercise",
    exerciseHint: "Tick it once you have done it.",
    restDay: "No exercise is planned for today: it is a rest day.",
    groups: {
      aerobic: "Brisk activity",
      strength: "Strength exercises",
      flexibility: "Stretching",
      balance: "Balance exercises",
    } as Record<string, string>,
    minutes: (n: string) => `${n} min`,
    or: " or ",
    easier: "easier version",
    seeMeals: "See the week's meals",
    seeExercise: "How to do these exercises",
    emptyTitle: "No tasks yet",
    emptyHint: "Your daily tasks appear here once your doctor approves your plan.",
    saveFailed: "That tick was not saved. Check your connection and try again.",
    kcal: "kcal",
  },
  bn: {
    title: "আজকের কাজ",
    of: (done: string, total: string) => `${total}টির মধ্যে ${done}টি সম্পন্ন`,
    keepGoing: "প্রতিটি কাজ শেষ হলে টিক দিন।",
    allDone: "আজকের সব কাজ শেষ। ধারা বজায় রাখতে কাল আবার আসুন।",
    streak: "দিন টানা",
    streakOne: "দিন টানা",
    best: (n: string) => `সর্বোচ্চ: ${n}`,
    lastWeek: "গত সাত দিন",
    status: {
      complete: "সব শেষ",
      partial: "কিছু শেষ",
      missed: "করা হয়নি",
      today: "আজ",
      none: "তখনো পরিকল্পনা ছিল না",
    } as Record<DayStatus, string>,
    meals: "খাবার",
    mealsHint: "খাওয়া হলে টিক দিন।",
    exercise: "ব্যায়াম",
    exerciseHint: "করা হলে টিক দিন।",
    restDay: "আজ কোনো ব্যায়াম নেই: আজ বিশ্রামের দিন।",
    groups: {
      aerobic: "দ্রুত ব্যায়াম",
      strength: "শক্তির ব্যায়াম",
      flexibility: "স্ট্রেচিং",
      balance: "ভারসাম্যের ব্যায়াম",
    } as Record<string, string>,
    minutes: (n: string) => `${n} মিনিট`,
    or: " বা ",
    easier: "সহজ রূপ",
    seeMeals: "সপ্তাহের খাবার দেখুন",
    seeExercise: "ব্যায়ামগুলো কীভাবে করবেন",
    emptyTitle: "এখনো কোনো কাজ নেই",
    emptyHint: "আপনার চিকিৎসক পরিকল্পনা অনুমোদন করলে প্রতিদিনের কাজ এখানে দেখা যাবে।",
    saveFailed: "টিকটি সংরক্ষণ হয়নি। ইন্টারনেট সংযোগ দেখে আবার চেষ্টা করুন।",
    kcal: "কিলোক্যালরি",
  },
} as const;

const num = (n: number, lang: Lang) => n.toLocaleString(lang === "bn" ? "bn-BD" : "en");

/** "2026-11-09" as a local calendar date (new Date("2026-11-09") is UTC
 * midnight, the day before west of Greenwich). */
function calendarDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function longDate(iso: string, lang: Lang): string {
  return calendarDate(iso).toLocaleDateString(lang === "bn" ? "bn-BD" : "en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

/** A ring that fills as the day's tasks are done. */
function ProgressRing({ done, total }: { done: number; total: number }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  const share = total ? done / total : 0;
  return (
    <svg viewBox="0 0 64 64" className="h-16 w-16 shrink-0 -rotate-90" aria-hidden="true">
      <circle cx="32" cy="32" r={r} fill="none" strokeWidth="7" className="stroke-line" />
      <circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        strokeWidth="7"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - share)}
        className="stroke-clinical transition-[stroke-dashoffset] duration-300 motion-reduce:transition-none"
      />
    </svg>
  );
}

function DayDot({ day, lang }: { day: TodayTasks["recent"][number]; lang: Lang }) {
  const t = L[lang];
  const date = calendarDate(day.date);
  const isToday = day.status === "today";
  const complete = day.status === "complete";
  const style = complete
    ? "bg-clinical text-white"
    : day.status === "partial"
      ? "border-2 border-clinical bg-clinical-tint text-clinical"
      : day.status === "missed"
        ? "border-2 border-dashed border-line-strong text-ink-muted"
        : isToday
          ? "border-2 border-clinical text-clinical"
          : "bg-surface-soft text-ink-muted";
  return (
    <li className="flex min-w-0 flex-1 flex-col items-center gap-1">
      <span
        className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold sm:h-10 sm:w-10 ${style} ${
          isToday ? "ring-2 ring-clinical ring-offset-2 ring-offset-surface" : ""
        }`}
      >
        {complete ? <IconCheck className="h-4.5 w-4.5" strokeWidth={3} /> : num(date.getDate(), lang)}
      </span>
      <span className={`text-xs ${isToday ? "font-bold text-ink" : "text-ink-muted"}`}>
        {weekdayName(day.weekday, lang, true)}
      </span>
      <span className="sr-only">{t.status[day.status]}</span>
    </li>
  );
}

function TaskRow({
  task,
  lang,
  saving,
  onToggle,
}: {
  task: DailyTask;
  lang: Lang;
  saving: boolean;
  onToggle: (task: DailyTask) => void;
}) {
  const t = L[lang];
  const title = task.kind === "meal" ? mealName(task.group, lang) : t.groups[task.group] ?? task.group;
  const meta =
    task.kind === "meal"
      ? task.kcal
        ? `${num(task.kcal, lang)} ${t.kcal}`
        : ""
      : task.minutes
        ? t.minutes(num(task.minutes, lang))
        : "";
  const id = `task-${task.key.replace(/[^a-z0-9]/gi, "-")}`;
  return (
    <li>
      <input
        id={id}
        type="checkbox"
        className="peer sr-only"
        checked={task.done}
        disabled={saving}
        onChange={() => onToggle(task)}
      />
      <label
        htmlFor={id}
        className={`flex min-h-14 cursor-pointer select-none items-start gap-3.5 rounded-xl border px-4 py-3.5 transition-colors duration-150 active:bg-surface-soft peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-clinical ${
          task.done ? "border-clinical/30 bg-clinical-tint/50" : "border-line bg-surface hover:border-line-strong"
        }`}
      >
        <span
          aria-hidden="true"
          className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border-2 transition-colors duration-150 ${
            task.done ? "border-clinical bg-clinical text-white" : "border-line-strong bg-surface"
          }`}
        >
          {task.done && <IconCheck className="h-4.5 w-4.5" strokeWidth={3} />}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-baseline justify-between gap-x-3">
            <span className={`text-base font-semibold ${task.done ? "text-ink-soft" : "text-ink"}`}>{title}</span>
            {meta && <span className="text-sm text-ink-muted">{meta}</span>}
          </span>
          {task.kind === "exercise" && task.group === "aerobic" ? (
            <span className="mt-0.5 block text-sm leading-snug text-ink-soft">
              {task.items.map((item) => localName(item, lang)).join(t.or)}
            </span>
          ) : (
            <span className="mt-1 block space-y-0.5">
              {task.items.map((item, i) => (
                <span key={i} className="block text-sm leading-snug text-ink-soft">
                  {localName(item, lang)}
                  <span className="text-ink-muted">
                    {task.kind === "meal"
                      ? ` · ${portionText(item, lang)}`
                      : item.dose
                        ? ` · ${item.dose}${item.use_easier_version ? ` (${t.easier})` : ""}`
                        : ""}
                  </span>
                </span>
              ))}
            </span>
          )}
        </span>
      </label>
    </li>
  );
}

function Section({
  icon,
  title,
  hint,
  link,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  hint: string;
  link: { href: string; label: string };
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-3 flex items-end justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-display flex items-center gap-2 text-lg font-bold leading-7 text-ink">
            {icon}
            {title}
          </h2>
          <p className="text-sm text-ink-muted">{hint}</p>
        </div>
        <Link
          href={link.href}
          className={`flex min-h-11 min-w-11 shrink-0 items-center justify-center gap-0.5 rounded-md text-sm font-semibold text-clinical hover:underline sm:min-w-0 ${focusRing}`}
        >
          <span className="hidden sm:inline">{link.label}</span>
          <span className="sm:hidden">
            <span className="sr-only">{link.label}</span>
          </span>
          <IconChevronRight className="h-4 w-4" />
        </Link>
      </div>
      {children}
    </section>
  );
}

export default function PatientTodayPage() {
  const [lang] = useLang();
  const t = L[lang];
  const [view, setView] = useState<TodayTasks | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState(false);
  const [saving, setSaving] = useState<Set<string>>(new Set());

  useEffect(() => {
    api.myTasks().then(setView).catch((e) => setLoadError((e as Error).message));
  }, []);

  const toggle = async (task: DailyTask) => {
    if (!view) return;
    const next = !task.done;
    const before = view;
    // show the tick at once; the server's answer (with the streak) follows
    setView({
      ...view,
      tasks: view.tasks.map((x) => (x.key === task.key ? { ...x, done: next } : x)),
      done: view.done + (next ? 1 : -1),
    });
    setSaveError(false);
    setSaving((s) => new Set(s).add(task.key));
    try {
      setView(await api.tickTask(task.key, next));
    } catch {
      setView(before);
      setSaveError(true);
    } finally {
      setSaving((s) => {
        const copy = new Set(s);
        copy.delete(task.key);
        return copy;
      });
    }
  };

  if (loadError) return <ErrorNote message={loadError} />;

  if (!view) {
    return (
      <div className="space-y-5">
        <PageHeader title={t.title} />
        <Skeleton className="h-40" />
        <Skeleton className="h-56" />
      </div>
    );
  }

  const header = <PageHeader title={t.title} subtitle={longDate(view.date, lang)} />;

  if (!view.plan) {
    return (
      <div lang={lang} className="space-y-6">
        {header}
        <EmptyState title={t.emptyTitle} hint={t.emptyHint} icon={<IconListChecks className="h-5 w-5" />} />
      </div>
    );
  }

  const meals = view.tasks.filter((x) => x.kind === "meal");
  const exercise = view.tasks.filter((x) => x.kind === "exercise");
  const allDone = view.total > 0 && view.done === view.total;
  const streak = view.streak.current;

  return (
    // a checklist reads best at a comfortable line length, not full width
    <div lang={lang} className="max-w-3xl space-y-7">
      {header}

      {/* the day at a glance: progress, streak, the last week */}
      <section className="rounded-xl border border-line bg-surface p-4 sm:p-5">
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-4">
          <div className="flex min-w-0 items-center gap-3.5">
            <ProgressRing done={view.done} total={view.total} />
            <div className="min-w-0">
              <p className="text-lg font-bold leading-tight text-ink" aria-live="polite">
                {t.of(num(view.done, lang), num(view.total, lang))}
              </p>
              <p className="text-sm text-ink-muted">{allDone ? t.allDone : t.keepGoing}</p>
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <span
              className={`flex h-11 w-11 items-center justify-center rounded-full ${
                streak > 0 ? "bg-clinical-tint text-clinical" : "bg-surface-soft text-ink-muted"
              }`}
            >
              <IconFlame className="h-6 w-6" />
            </span>
            <div>
              <p className="text-lg font-bold leading-tight text-ink">
                {num(streak, lang)} <span className="text-sm font-semibold text-ink-soft">{streak === 1 ? t.streakOne : t.streak}</span>
              </p>
              <p className="text-sm text-ink-muted">{t.best(num(view.streak.best, lang))}</p>
            </div>
          </div>
        </div>
        <div className="mt-5 border-t border-line pt-4">
          <h2 className="sr-only">{t.lastWeek}</h2>
          <ol className="flex justify-between gap-1">
            {view.recent.map((day) => (
              <DayDot key={day.date} day={day} lang={lang} />
            ))}
          </ol>
        </div>
      </section>

      {saveError && (
        <p role="alert" className="rounded-lg border border-high-line bg-high-tint px-4 py-3 text-sm text-high-ink">
          {t.saveFailed}
        </p>
      )}

      {meals.length > 0 && (
        <Section
          icon={<IconUtensils className="h-5 w-5 text-clinical" />}
          title={t.meals}
          hint={t.mealsHint}
          link={{ href: "/patient/foods", label: t.seeMeals }}
        >
          <ul className="space-y-2.5">
            {meals.map((task) => (
              <TaskRow key={task.key} task={task} lang={lang} saving={saving.has(task.key)} onToggle={toggle} />
            ))}
          </ul>
        </Section>
      )}

      <Section
        icon={<IconActivity className="h-5 w-5 text-clinical" />}
        title={t.exercise}
        hint={exercise.length ? t.exerciseHint : ""}
        link={{ href: "/patient/exercise", label: t.seeExercise }}
      >
        {exercise.length > 0 ? (
          <ul className="space-y-2.5">
            {exercise.map((task) => (
              <TaskRow key={task.key} task={task} lang={lang} saving={saving.has(task.key)} onToggle={toggle} />
            ))}
          </ul>
        ) : (
          <Note>{t.restDay}</Note>
        )}
      </Section>
    </div>
  );
}
