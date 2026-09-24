"use client";

import { useState } from "react";
import { useLatestReport } from "@/lib/use-latest-report";
import { IconActivity, IconClock, IconHeartPulse } from "@/components/icons";
import { Card, EmptyState, ErrorNote, InfoNote, PageHeader, Skeleton, StatCard } from "@/components/ui";

const GROUPS = ["aerobic", "strength", "flexibility"] as const;

const LABELS = {
  en: {
    subtitle: "The activity plan your physician recommends for you.",
    recommendedBy: (name: string, date: string) => `Recommended by ${name} on ${date}`,
    targetHr: "Target heart rate",
    weeklyVolume: "Weekly volume",
    aerobicTime: "Aerobic time",
    perWeek: "days/week",
    minPerSession: "min/session",
    progression: "How to progress",
    noPlan: "No exercise plan is available for your latest report.",
    emptyHint: "Your doctor's recommended exercise plan appears here once a visit is approved.",
    groups: { aerobic: "Aerobic", strength: "Strength", flexibility: "Flexibility" },
  },
  bn: {
    subtitle: "আপনার চিকিৎসকের সুপারিশকৃত কার্যক্রম পরিকল্পনা।",
    recommendedBy: (name: string, date: string) => `${name} সুপারিশ করেছেন ${date} তারিখে`,
    targetHr: "লক্ষ্য হৃদস্পন্দন",
    weeklyVolume: "সাপ্তাহিক পরিমাণ",
    aerobicTime: "অ্যারোবিক সময়",
    perWeek: "দিন/সপ্তাহ",
    minPerSession: "মিনিট/সেশন",
    progression: "কীভাবে এগোবেন",
    noPlan: "আপনার সাম্প্রতিক প্রতিবেদনে কোনো ব্যায়াম পরিকল্পনা নেই।",
    emptyHint: "আপনার ডাক্তারের সুপারিশকৃত ব্যায়াম পরিকল্পনা একটি ভিজিট অনুমোদনের পর এখানে দেখা যাবে।",
    groups: { aerobic: "অ্যারোবিক", strength: "শক্তি", flexibility: "নমনীয়তা" },
  },
} as const;

export default function PatientExercisePage() {
  const [lang, setLang] = useState<"en" | "bn">("en");
  const state = useLatestReport(lang);
  const t = LABELS[lang];

  const header = (
    <PageHeader
      title="Exercise"
      subtitle={t.subtitle}
      action={
        <div className="flex overflow-hidden rounded-lg border border-line-strong">
          {(["en", "bn"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={`px-3 py-1.5 text-sm font-medium ${
                lang === l ? "bg-clinical text-on-clinical" : "bg-surface text-ink-soft hover:bg-surface-soft"
              }`}
            >
              {l === "en" ? "English" : "বাংলা"}
            </button>
          ))}
        </div>
      }
    />
  );

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
      <div className="space-y-6">
        {header}
        <EmptyState title="No recommendations yet" hint={t.emptyHint} icon={<IconActivity className="h-5 w-5" />} />
      </div>
    );
  }

  const { report } = state;
  const nameKey = lang === "bn" ? "name_bn" : "name_en";
  const plan = report.result?.exercise_plan;

  if (!plan?.time || !plan.frequency || !plan.intensity) {
    return (
      <div className="space-y-6">
        {header}
        <InfoNote>{plan?.note ?? t.noPlan}</InfoNote>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {header}
      <p className="-mt-4 text-xs text-ink-muted">
        {t.recommendedBy(report.approved_by, new Date(report.approved_at).toLocaleDateString())}
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label={t.targetHr}
          value={`${plan.intensity.target_hr_bpm[0]}–${plan.intensity.target_hr_bpm[1]} bpm`}
          hint={plan.intensity.level}
          icon={<IconHeartPulse className="h-5 w-5" />}
          tone="rose"
        />
        <StatCard
          label={t.aerobicTime}
          value={`${plan.time.aerobic_min_per_week} min/wk`}
          hint={`${plan.frequency.aerobic_days} ${t.perWeek} · ${plan.time.aerobic_min_per_session} ${t.minPerSession}`}
          icon={<IconClock className="h-5 w-5" />}
          tone="sky"
        />
        {plan.volume && (
          <StatCard
            label={t.weeklyVolume}
            value={`${plan.volume.met_min_per_week} MET·min`}
            hint={`${plan.volume.est_kcal_per_week} kcal/week`}
            icon={<IconActivity className="h-5 w-5" />}
            tone="emerald"
          />
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {GROUPS.map((group) => {
          const days =
            group === "aerobic"
              ? plan.frequency!.aerobic_days
              : group === "strength"
                ? plan.frequency!.strength_days
                : plan.frequency!.flexibility_days;
          const exercises = plan.type?.[group] ?? [];
          return (
            <Card key={group} title={t.groups[group]}>
              <p className="text-sm text-ink-soft">
                <strong className="text-ink">{days}</strong> {t.perWeek}
              </p>
              <ul className="mt-2 space-y-1.5 text-sm text-ink-strong">
                {exercises.map((ex) => (
                  <li key={ex.exercise_id}>
                    • {(ex as Record<string, string | number>)[nameKey] || ex.name_en}
                    <span className="ml-1 text-xs text-ink-muted">
                      ({ex.met_value} MET{ex.equipment !== "none" ? `, ${ex.equipment}` : ""})
                    </span>
                  </li>
                ))}
                {exercises.length === 0 && <li className="text-xs text-ink-muted">—</li>}
              </ul>
            </Card>
          );
        })}
      </div>

      {plan.progression && (
        <InfoNote>
          <strong>{t.progression}:</strong> {plan.progression}
        </InfoNote>
      )}
    </div>
  );
}
