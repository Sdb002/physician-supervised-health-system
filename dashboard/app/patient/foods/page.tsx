"use client";

import { useLatestReport } from "@/lib/use-latest-report";
import { useLang } from "@/lib/use-lang";
import { planDays } from "@/lib/clinical-terms";
import { IconUtensils } from "@/components/icons";
import { ApprovedLine } from "@/components/approved-line";
import { RecommendedFoodsList } from "@/components/recommendations";
import { WeekPlan } from "@/components/week-plan";
import { Card, EmptyState, ErrorNote, InfoNote, MetricRow, PageHeader, Skeleton } from "@/components/ui";

const LABELS = {
  en: {
    title: "Meals",
    subtitle: "What your doctor recommends you eat, day by day.",
    subtitleWeek: "What your doctor recommends you eat each day this week. It opens on today.",
    dailyTarget: "Your daily energy target",
    plannedTotal: "This plan adds up to",
    plannedAverage: "An average day of this plan",
    ofTarget: (pct: number) => `${pct}% of your target`,
    kcal: "kcal",
    noPlan: "No meal plan is available in your latest report.",
    emptyTitle: "No meal plan yet",
    emptyHint: "Your doctor's recommended meals appear here once a visit is approved.",
    dayPlan: "Your day of meals",
    weekPlan: "Your week of meals",
    recommendedFoods: "Other foods that suit your plan",
    recommendedHint: "Good choices to swap in, best match first.",
  },
  bn: {
    title: "খাবার",
    subtitle: "দিনে কী খাবেন, আপনার চিকিৎসকের সুপারিশ।",
    subtitleWeek: "এই সপ্তাহে প্রতিদিন কী খাবেন, আপনার চিকিৎসকের সুপারিশ। আজকের দিনটি আগে খোলে।",
    dailyTarget: "দৈনিক শক্তির লক্ষ্য",
    plannedTotal: "এই পরিকল্পনায় মোট",
    plannedAverage: "এই পরিকল্পনার গড় একটি দিন",
    ofTarget: (pct: number) => `লক্ষ্যের ${pct.toLocaleString("bn-BD")}%`,
    kcal: "কিলোক্যালরি",
    noPlan: "আপনার সাম্প্রতিক রিপোর্টে কোনো খাবার পরিকল্পনা নেই।",
    emptyTitle: "এখনো কোনো খাবার পরিকল্পনা নেই",
    emptyHint: "একটি ভিজিট অনুমোদনের পর আপনার চিকিৎসকের সুপারিশকৃত খাবার এখানে দেখা যাবে।",
    dayPlan: "সারাদিনের খাবার",
    weekPlan: "সপ্তাহের খাবার",
    recommendedFoods: "আপনার পরিকল্পনার উপযোগী আরও খাবার",
    recommendedHint: "বদলে খাওয়ার মতো ভালো বিকল্প, সবচেয়ে উপযোগীটি আগে।",
  },
} as const;

export default function PatientFoodsPage() {
  const [lang] = useLang();
  const state = useLatestReport(lang);
  const t = LABELS[lang];

  const days = state.status === "ready" ? planDays(state.report.result?.nutrition?.meal_plan) : [];
  const isWeek = days.some((d) => d.weekday);
  const header = <PageHeader title={t.title} subtitle={isWeek ? t.subtitleWeek : t.subtitle} />;

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
        <EmptyState title={t.emptyTitle} hint={t.emptyHint} icon={<IconUtensils className="h-5 w-5" />} />
      </div>
    );
  }

  const { report } = state;
  const mealPlan = report.result?.nutrition?.meal_plan;

  if (!mealPlan || mealPlan.note || days.length === 0) {
    return (
      <div lang={lang} className="space-y-6">
        {header}
        <InfoNote>{mealPlan?.note ?? t.noPlan}</InfoNote>
      </div>
    );
  }

  const totalKcal = Math.round(Number(mealPlan.totals?.kcal ?? 0));
  const pct = mealPlan.target_kcal ? Math.round((totalKcal / mealPlan.target_kcal) * 100) : null;
  const unit = <span className="ml-1 text-base font-semibold text-ink-muted">{t.kcal}</span>;

  return (
    <div lang={lang} className="space-y-8">
      <div className="space-y-3">
        {header}
        <ApprovedLine by={report.approved_by} at={report.approved_at} lang={lang} />
      </div>

      <MetricRow
        items={[
          { label: t.dailyTarget, value: <>{mealPlan.target_kcal}{unit}</> },
          {
            label: isWeek ? t.plannedAverage : t.plannedTotal,
            value: <>{totalKcal}{unit}</>,
            hint: pct != null ? t.ofTarget(pct) : undefined,
          },
        ]}
      />

      <section>
        <h2 className="font-display mb-3 text-xl font-bold leading-7 text-ink">
          {isWeek ? t.weekPlan : t.dayPlan}
        </h2>
        <WeekPlan days={days} lang={lang} />
      </section>

      {(report.result?.nutrition?.top_foods ?? []).length > 0 && (
        <Card title={t.recommendedFoods} description={t.recommendedHint}>
          <RecommendedFoodsList foods={report.result.nutrition.top_foods} lang={lang} />
        </Card>
      )}
    </div>
  );
}
