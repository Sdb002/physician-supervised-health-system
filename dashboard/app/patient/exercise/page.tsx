"use client";

import { useLatestReport } from "@/lib/use-latest-report";
import { useLang } from "@/lib/use-lang";
import { localName } from "@/lib/clinical-terms";
import { IconActivity } from "@/components/icons";
import { ApprovedLine } from "@/components/approved-line";
import { EmptyState, ErrorNote, InfoNote, MetricRow, Note, PageHeader, Skeleton } from "@/components/ui";

const GROUPS = ["aerobic", "strength", "flexibility"] as const;

const LABELS = {
  en: {
    title: "Exercise",
    subtitle: "The activity your doctor recommends each week.",
    targetHr: "Keep your heart rate between",
    bpm: "beats per minute",
    weekly: "Brisk activity each week",
    minutes: "min",
    perWeek: (days: number, min: number) => `${days} days, ${min} minutes each`,
    energy: "Energy this uses",
    kcalWeek: "kcal a week",
    daysAWeek: (n: number) => `${n} ${n === 1 ? "day" : "days"} a week`,
    progression: "How to build up",
    noPlan: "No exercise plan is available in your latest report.",
    emptyTitle: "No exercise plan yet",
    emptyHint: "Your doctor's recommended exercise appears here once a visit is approved.",
    groups: {
      aerobic: { name: "Brisk activity", hint: "Walking, cycling and similar activity that raises your breathing." },
      strength: { name: "Strength", hint: "Builds muscle and keeps joints supported." },
      flexibility: { name: "Stretching", hint: "Slow and gentle. Stop before it hurts." },
    },
    equipment: (e: string) => `Needs: ${e}`,
  },
  bn: {
    title: "ব্যায়াম",
    subtitle: "প্রতি সপ্তাহে কতটা ব্যায়াম করবেন, আপনার চিকিৎসকের সুপারিশ।",
    targetHr: "হৃদস্পন্দন রাখুন",
    bpm: "প্রতি মিনিটে",
    weekly: "সপ্তাহে দ্রুত ব্যায়াম",
    minutes: "মিনিট",
    perWeek: (days: number, min: number) =>
      `${days.toLocaleString("bn-BD")} দিন, প্রতিবার ${min.toLocaleString("bn-BD")} মিনিট`,
    energy: "এতে খরচ হয়",
    kcalWeek: "কিলোক্যালরি/সপ্তাহ",
    daysAWeek: (n: number) => `সপ্তাহে ${n.toLocaleString("bn-BD")} দিন`,
    progression: "কীভাবে বাড়াবেন",
    noPlan: "আপনার সাম্প্রতিক রিপোর্টে কোনো ব্যায়াম পরিকল্পনা নেই।",
    emptyTitle: "এখনো কোনো ব্যায়াম পরিকল্পনা নেই",
    emptyHint: "একটি ভিজিট অনুমোদনের পর আপনার চিকিৎসকের সুপারিশকৃত ব্যায়াম এখানে দেখা যাবে।",
    groups: {
      aerobic: { name: "দ্রুত ব্যায়াম", hint: "হাঁটা, সাইকেল চালানো বা এমন কাজ যাতে শ্বাস একটু দ্রুত হয়।" },
      strength: { name: "শক্তির ব্যায়াম", hint: "পেশি গড়ে ও জয়েন্টকে সাপোর্ট দেয়।" },
      flexibility: { name: "স্ট্রেচিং", hint: "ধীরে ও আলতোভাবে; কখনো ব্যথা পর্যন্ত নয়।" },
    },
    equipment: (e: string) => `লাগবে: ${e}`,
  },
} as const;

export default function PatientExercisePage() {
  const [lang] = useLang();
  const state = useLatestReport(lang);
  const t = LABELS[lang];

  const header = <PageHeader title={t.title} subtitle={t.subtitle} />;

  if (state.status === "error") return <ErrorNote message={state.message} />;

  if (state.status === "loading") {
    return (
      <div className="space-y-6">
        {header}
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (state.status === "empty") {
    return (
      <div lang={lang} className="space-y-6">
        {header}
        <EmptyState title={t.emptyTitle} hint={t.emptyHint} icon={<IconActivity className="h-5 w-5" />} />
      </div>
    );
  }

  const { report } = state;
  const plan = report.result?.exercise_plan;

  if (!plan?.time || !plan.frequency || !plan.intensity) {
    return (
      <div lang={lang} className="space-y-6">
        {header}
        <InfoNote>{plan?.note ?? t.noPlan}</InfoNote>
      </div>
    );
  }

  const muted = "ml-1 text-base font-semibold text-ink-muted";

  return (
    <div lang={lang} className="space-y-8">
      <div className="space-y-3">
        {header}
        <ApprovedLine by={report.approved_by} at={report.approved_at} lang={lang} />
      </div>

      <MetricRow
        items={[
          {
            label: t.weekly,
            value: (
              <>
                {plan.time.aerobic_min_per_week}
                <span className={muted}>{t.minutes}</span>
              </>
            ),
            hint: t.perWeek(plan.frequency.aerobic_days, plan.time.aerobic_min_per_session),
          },
          {
            label: t.targetHr,
            value: (
              <>
                {plan.intensity.target_hr_bpm[0]}–{plan.intensity.target_hr_bpm[1]}
                <span className={muted}>{t.bpm}</span>
              </>
            ),
          },
          ...(plan.volume
            ? [
                {
                  label: t.energy,
                  value: (
                    <>
                      {plan.volume.est_kcal_per_week}
                      <span className={muted}>{t.kcalWeek}</span>
                    </>
                  ),
                },
              ]
            : []),
        ]}
      />

      <div className="grid overflow-hidden rounded-xl border border-line bg-surface md:grid-cols-3">
        {GROUPS.map((group, i) => {
          const days =
            group === "aerobic"
              ? plan.frequency!.aerobic_days
              : group === "strength"
                ? plan.frequency!.strength_days
                : plan.frequency!.flexibility_days;
          const exercises = plan.type?.[group] ?? [];
          return (
            <section
              key={group}
              className={`px-5 py-5 ${i > 0 ? "border-t border-line md:border-l md:border-t-0" : ""}`}
            >
              <h2 className="font-display text-lg font-bold leading-7 text-ink">{t.groups[group].name}</h2>
              <p className="text-sm font-semibold text-clinical">{t.daysAWeek(days)}</p>
              <p className="mt-1 text-sm text-ink-muted">{t.groups[group].hint}</p>
              <ul className="mt-4 space-y-2.5">
                {exercises.map((ex) => (
                  <li key={ex.exercise_id}>
                    <p className="font-medium text-ink">{localName(ex, lang)}</p>
                    {ex.equipment !== "none" && (
                      <p className="text-sm text-ink-muted">{t.equipment(ex.equipment)}</p>
                    )}
                  </li>
                ))}
                {exercises.length === 0 && <li className="text-sm text-ink-muted">—</li>}
              </ul>
            </section>
          );
        })}
      </div>

      {plan.progression && (
        <Note>
          <strong className="font-semibold text-ink">{t.progression}.</strong> {plan.progression}
        </Note>
      )}
    </div>
  );
}
