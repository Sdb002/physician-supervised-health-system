"use client";

import { useState } from "react";
import { useLatestReport } from "@/lib/use-latest-report";
import { IconClock, IconFlame, IconUtensils } from "@/components/icons";
import {
  Card,
  EmptyState,
  ErrorNote,
  InfoNote,
  PageHeader,
  Skeleton,
  StatCard,
} from "@/components/ui";

const MEAL_ORDER = ["breakfast", "lunch", "dinner", "snack"] as const;

const LABELS = {
  en: {
    subtitle: "The meals your physician recommends for you.",
    recommendedBy: (name: string, date: string) => `Recommended by ${name} on ${date}`,
    dailyTarget: "Daily energy target",
    plannedTotal: "Planned total",
    mealsPlanned: "Meals planned",
    ofTarget: "of target",
    noPlan: "No meal plan is available for your latest report.",
    emptyHint: "Your doctor's recommended foods appear here once a visit is approved.",
    meals: { breakfast: "Breakfast", lunch: "Lunch", dinner: "Dinner", snack: "Snack" },
  },
  bn: {
    subtitle: "আপনার চিকিৎসকের সুপারিশকৃত খাবার।",
    recommendedBy: (name: string, date: string) => `${name} সুপারিশ করেছেন ${date} তারিখে`,
    dailyTarget: "দৈনিক শক্তির লক্ষ্য",
    plannedTotal: "পরিকল্পিত মোট",
    mealsPlanned: "পরিকল্পিত খাবার",
    ofTarget: "লক্ষ্যের",
    noPlan: "আপনার সাম্প্রতিক প্রতিবেদনে কোনো খাবার পরিকল্পনা নেই।",
    emptyHint: "আপনার ডাক্তারের সুপারিশকৃত খাবার একটি ভিজিট অনুমোদনের পর এখানে দেখা যাবে।",
    meals: { breakfast: "সকালের নাস্তা", lunch: "দুপুরের খাবার", dinner: "রাতের খাবার", snack: "হালকা নাস্তা" },
  },
} as const;

export default function PatientFoodsPage() {
  const [lang, setLang] = useState<"en" | "bn">("en");
  const state = useLatestReport(lang);
  const t = LABELS[lang];

  const header = (
    <PageHeader
      title="Foods"
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
        <EmptyState title="No recommendations yet" hint={t.emptyHint} icon={<IconUtensils className="h-5 w-5" />} />
      </div>
    );
  }

  const { report } = state;
  const nameKey = lang === "bn" ? "name_bn" : "name_en";
  const mealPlan = report.result?.nutrition?.meal_plan;

  if (!mealPlan || mealPlan.note || Object.keys(mealPlan.meals ?? {}).length === 0) {
    return (
      <div className="space-y-6">
        {header}
        <InfoNote>{mealPlan?.note ?? t.noPlan}</InfoNote>
      </div>
    );
  }

  const totalKcal = Math.round(Number(mealPlan.totals?.kcal ?? 0));
  const pct = mealPlan.target_kcal ? Math.round((totalKcal / mealPlan.target_kcal) * 100) : null;
  const mealsPlanned = MEAL_ORDER.filter((m) => mealPlan.meals[m]?.length).length;

  return (
    <div className="space-y-6">
      {header}
      <p className="-mt-4 text-xs text-ink-muted">
        {t.recommendedBy(report.approved_by, new Date(report.approved_at).toLocaleDateString())}
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label={t.dailyTarget}
          value={`${mealPlan.target_kcal} kcal`}
          icon={<IconFlame className="h-5 w-5" />}
          tone="amber"
        />
        <StatCard
          label={t.plannedTotal}
          value={`${totalKcal} kcal`}
          hint={pct != null ? `${pct}% ${t.ofTarget}` : undefined}
          icon={<IconUtensils className="h-5 w-5" />}
          tone="emerald"
        />
        <StatCard
          label={t.mealsPlanned}
          value={mealsPlanned}
          icon={<IconClock className="h-5 w-5" />}
          tone="sky"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {MEAL_ORDER.filter((m) => mealPlan.meals[m]?.length).map((meal) => (
          <Card key={meal} title={t.meals[meal]}>
            <ul className="space-y-2">
              {mealPlan.meals[meal].map((item) => (
                <li key={item.food_id} className="flex items-center justify-between text-sm">
                  <span className="text-ink-strong">
                    {(item as Record<string, string | number>)[nameKey] || item.name_en}
                  </span>
                  <span className="shrink-0 text-ink-muted">
                    {item.qty_g} g · <span className="text-ink-muted">{item.kcal} kcal</span>
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  );
}
