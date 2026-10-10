"use client";

import { useLatestReport } from "@/lib/use-latest-report";
import { useLang } from "@/lib/use-lang";
import { IconCookingPot } from "@/components/icons";
import { ApprovedLine } from "@/components/approved-line";
import { RecommendedRecipesList } from "@/components/recommendations";
import { EmptyState, ErrorNote, InfoNote, PageHeader, Skeleton } from "@/components/ui";

const LABELS = {
  en: {
    title: "Recipes",
    subtitle: "Home dishes that suit your plan. Open any dish for its ingredients and method.",
    hint: "Dishes that suit you best come first. Among them, everyday home cooking ranks above dishes made only now and then.",
    noRecipes: "No recipes were recommended in your latest report.",
    emptyTitle: "No recipes yet",
    emptyHint: "Your doctor's recommended recipes appear here once a visit is approved.",
  },
  bn: {
    title: "রান্না",
    subtitle: "আপনার পরিকল্পনার উপযোগী ঘরোয়া রান্না। উপকরণ ও পদ্ধতি দেখতে যেকোনো রান্না খুলুন।",
    hint: "আপনার জন্য সবচেয়ে উপযোগী রান্না আগে। এর মধ্যে প্রতিদিনের ঘরোয়া রান্না মাঝে মাঝে হওয়া রান্নার আগে।",
    noRecipes: "আপনার সাম্প্রতিক রিপোর্টে কোনো রান্না সুপারিশ করা হয়নি।",
    emptyTitle: "এখনো কোনো রান্না নেই",
    emptyHint: "একটি ভিজিট অনুমোদনের পর আপনার চিকিৎসকের সুপারিশকৃত রান্না এখানে দেখা যাবে।",
  },
} as const;

export default function PatientRecipesPage() {
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
        <EmptyState title={t.emptyTitle} hint={t.emptyHint} icon={<IconCookingPot className="h-5 w-5" />} />
      </div>
    );
  }

  const { report } = state;
  const recipes = report.result?.nutrition?.top_recipes ?? [];

  return (
    <div lang={lang} className="space-y-8">
      <div className="space-y-3">
        {header}
        <ApprovedLine by={report.approved_by} at={report.approved_at} lang={lang} />
      </div>
      {recipes.length === 0 ? (
        <InfoNote>{t.noRecipes}</InfoNote>
      ) : (
        <section>
          <p className="mb-4 max-w-2xl text-sm text-ink-muted">{t.hint}</p>
          <RecommendedRecipesList recipes={recipes} lang={lang} />
        </section>
      )}
    </div>
  );
}
