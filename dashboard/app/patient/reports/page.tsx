"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PatientDashboard } from "@/lib/api";
import { formatDate } from "@/lib/clinical-terms";
import { useLang } from "@/lib/use-lang";
import { IconChevronRight, IconFileText } from "@/components/icons";
import { Badge, EmptyState, ErrorNote, PageHeader, Skeleton, focusRing } from "@/components/ui";

const L = {
  en: {
    title: "Reports",
    subtitle: "Every plan your doctor has approved, newest first. You can print any of them.",
    item: (date: string) => `Health plan from ${date}`,
    latest: "Current plan",
    approved: "Approved",
    emptyTitle: "No reports yet",
    emptyHint: "A report appears here as soon as your doctor approves a visit.",
  },
  bn: {
    title: "রিপোর্ট",
    subtitle: "আপনার চিকিৎসকের অনুমোদিত সব পরিকল্পনা, নতুনটি আগে। যেকোনোটি প্রিন্ট করতে পারবেন।",
    item: (date: string) => `${date} তারিখের স্বাস্থ্য পরিকল্পনা`,
    latest: "বর্তমান পরিকল্পনা",
    approved: "অনুমোদিত",
    emptyTitle: "এখনো কোনো রিপোর্ট নেই",
    emptyHint: "আপনার চিকিৎসক কোনো ভিজিট অনুমোদন করলেই রিপোর্ট এখানে দেখা যাবে।",
  },
} as const;

export default function PatientReportsPage() {
  const [lang] = useLang();
  const t = L[lang];
  const [data, setData] = useState<PatientDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.myDashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  const ready = data?.items.filter((i) => i.report_ready) ?? null;

  return (
    <div lang={lang} className="space-y-6">
      <PageHeader title={t.title} subtitle={t.subtitle} />

      {ready === null ? (
        <Skeleton className="h-48" />
      ) : ready.length === 0 ? (
        <EmptyState title={t.emptyTitle} hint={t.emptyHint} icon={<IconFileText className="h-5 w-5" />} />
      ) : (
        <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
          {ready.map((item, i) => (
            <li key={item.visit.id}>
              <Link
                href={`/patient/reports/${item.visit.id}`}
                className={`group flex items-center gap-4 px-4 py-4 transition-colors duration-150 hover:bg-surface-soft sm:px-5 ${focusRing} focus-visible:-outline-offset-2`}
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-clinical-tint text-clinical">
                  <IconFileText className="h-5 w-5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold text-ink group-hover:text-clinical">
                    {t.item(formatDate(item.visit.created_at, lang))}
                  </span>
                  {i === 0 && <span className="block text-sm text-ink-muted">{t.latest}</span>}
                </span>
                <Badge kind="approved">{t.approved}</Badge>
                <IconChevronRight className="h-5 w-5 shrink-0 text-ink-muted group-hover:text-clinical" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
