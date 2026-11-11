"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PatientDashboard, Report } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { bmi } from "@/lib/format";
import { useLang } from "@/lib/use-lang";
import {
  MEAL_ORDER,
  planDays,
  todayIndex,
  weekdayName,
  bmiCategoryName,
  conditionName,
  formatDate,
  localName,
  mealName,
} from "@/lib/clinical-terms";
import { IconChevronRight, IconClock, IconRx } from "@/components/icons";
import { FindingsList } from "@/components/findings";
import { Card, EmptyState, ErrorNote, Note, PageHeader, Skeleton } from "@/components/ui";
import { TREND_COLOR_PRIMARY, TREND_COLOR_SECONDARY, TrendPoint } from "@/components/trend-chart";
import { TrendChartCard } from "@/components/trend-chart-card";
import { StethoscopeArt } from "@/components/stethoscope-art";
import { TodayCard } from "@/components/today-card";

const L = {
  en: {
    hello: (name: string) => `Hello, ${name}`,
    subtitleReady: "Here is the plan your doctor approved, and how your last check-up went.",
    subtitleWaiting: "Your doctor is reviewing your check-up.",
    subtitleNone: "Your plan will appear here after your first check-up.",
    currentPlan: "Your current plan",
    approvedBy: (doc: string, date: string) => `Approved by ${doc} on ${date}`,
    fullReport: "Open full report",
    eat: "Eat",
    eatToday: (day: string) => `Eat today, ${day}`,
    kcalPerDay: (n: number) => `About ${n.toLocaleString("en")} kcal a day`,
    seeMeals: "See meal plan",
    seeWeek: "See the whole week",
    move: "Move",
    aerobic: (min: number, days: number) => `Brisk activity: ${min} min, ${days} days a week`,
    strength: (days: number) => `Strength exercises: ${days} days a week`,
    stretch: (days: number) => `Stretching: ${days} days a week`,
    balance: (days: number) => `Balance exercises: ${days} days a week`,
    seeExercise: "See exercise plan",
    doctorNote: "Note from your doctor",
    results: "Your check-up results",
    resultsFrom: (date: string) => `From your visit on ${date}`,
    bmiLine: "Body mass index",
    newerPending: (date: string) =>
      `Your check-up from ${date} is with your doctor. This plan will update once they approve it.`,
    waitingTitle: "Your doctor is reviewing your check-up",
    waitingHint: (date: string) =>
      `You'll see your plan here as soon as they approve your visit from ${date}.`,
    noVisitsTitle: "No check-ups yet",
    noVisitsHint: "Your doctor records your measurements at your visit. Your plan appears here after they approve it.",
    visits: "Your visits",
    statusApproved: "Plan approved",
    statusPending: "With your doctor",
    statusRejected: "Not approved",
    rejectedHint: "Your doctor will talk to you about this visit.",
    readReport: "Read report",
    details: "Your details",
    age: "Age",
    years: (n: number) => `${n} years`,
    height: "Height",
    conditions: "Diagnosed conditions",
    none: "None recorded",
    trends: "How you're changing",
    weight: "Weight",
    bp: "Blood pressure",
    systolic: "Upper",
    diastolic: "Lower",
    trendHint: "Appears after your second check-up.",
  },
  bn: {
    hello: (name: string) => `স্বাগতম, ${name}`,
    subtitleReady: "আপনার চিকিৎসকের অনুমোদিত পরিকল্পনা এবং আপনার সর্বশেষ চেক-আপের ফলাফল।",
    subtitleWaiting: "আপনার চিকিৎসক আপনার চেক-আপ পর্যালোচনা করছেন।",
    subtitleNone: "প্রথম চেক-আপের পর আপনার পরিকল্পনা এখানে দেখা যাবে।",
    currentPlan: "আপনার বর্তমান পরিকল্পনা",
    approvedBy: (doc: string, date: string) => `${doc} ${date} তারিখে অনুমোদন করেছেন`,
    fullReport: "সম্পূর্ণ রিপোর্ট দেখুন",
    eat: "খাবার",
    eatToday: (day: string) => `আজকের খাবার, ${day}`,
    kcalPerDay: (n: number) => `দিনে প্রায় ${n.toLocaleString("bn-BD")} কিলোক্যালরি`,
    seeMeals: "খাবারের পরিকল্পনা দেখুন",
    seeWeek: "পুরো সপ্তাহ দেখুন",
    move: "ব্যায়াম",
    aerobic: (min: number, days: number) =>
      `দ্রুত হাঁটা বা সমজাতীয়: ${min.toLocaleString("bn-BD")} মিনিট, সপ্তাহে ${days.toLocaleString("bn-BD")} দিন`,
    strength: (days: number) => `শক্তির ব্যায়াম: সপ্তাহে ${days.toLocaleString("bn-BD")} দিন`,
    stretch: (days: number) => `স্ট্রেচিং: সপ্তাহে ${days.toLocaleString("bn-BD")} দিন`,
    balance: (days: number) => `ভারসাম্যের ব্যায়াম: সপ্তাহে ${days.toLocaleString("bn-BD")} দিন`,
    seeExercise: "ব্যায়ামের পরিকল্পনা দেখুন",
    doctorNote: "আপনার চিকিৎসকের মন্তব্য",
    results: "আপনার চেক-আপের ফলাফল",
    resultsFrom: (date: string) => `${date} তারিখের ভিজিট থেকে`,
    bmiLine: "বডি মাস ইনডেক্স",
    newerPending: (date: string) =>
      `${date} তারিখের চেক-আপটি আপনার চিকিৎসক দেখছেন। অনুমোদনের পর এই পরিকল্পনা হালনাগাদ হবে।`,
    waitingTitle: "আপনার চিকিৎসক আপনার চেক-আপ পর্যালোচনা করছেন",
    waitingHint: (date: string) => `${date} তারিখের ভিজিট অনুমোদন হলেই আপনার পরিকল্পনা এখানে দেখা যাবে।`,
    noVisitsTitle: "এখনো কোনো চেক-আপ নেই",
    noVisitsHint: "ভিজিটের সময় আপনার চিকিৎসক আপনার পরিমাপ লিখে রাখেন। অনুমোদনের পর পরিকল্পনা এখানে দেখা যাবে।",
    visits: "আপনার ভিজিট",
    statusApproved: "পরিকল্পনা অনুমোদিত",
    statusPending: "চিকিৎসকের কাছে",
    statusRejected: "অনুমোদিত হয়নি",
    rejectedHint: "এই ভিজিট নিয়ে আপনার চিকিৎসক আপনার সাথে কথা বলবেন।",
    readReport: "রিপোর্ট পড়ুন",
    details: "আপনার তথ্য",
    age: "বয়স",
    years: (n: number) => `${n.toLocaleString("bn-BD")} বছর`,
    height: "উচ্চতা",
    conditions: "নির্ণীত রোগ",
    none: "কিছু লেখা নেই",
    trends: "আপনার পরিবর্তন",
    weight: "ওজন",
    bp: "রক্তচাপ",
    systolic: "উপরের",
    diastolic: "নিচের",
    trendHint: "দ্বিতীয় চেক-আপের পর দেখা যাবে।",
  },
} as const;

const STATUS_MARK: Record<string, string> = {
  approved: "bg-ok-mark",
  pending: "bg-watch-mark",
  rejected: "bg-crit-mark",
};

export default function PatientHome() {
  const { session } = useAuth();
  const [lang] = useLang();
  const t = L[lang];
  const [data, setData] = useState<PatientDashboard | null>(null);
  const [fetchedReport, setFetchedReport] = useState<Report | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.myDashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  const latestReady = data?.items.find((i) => i.report_ready) ?? null;
  const latestReadyId = latestReady?.visit.id;
  // null = no approved visit to show; undefined = still loading it
  const report = data !== null && latestReadyId === undefined ? null : fetchedReport;

  useEffect(() => {
    if (latestReadyId === undefined) return;
    let cancelled = false;
    api
      .report(latestReadyId, lang, false)
      .then((r) => !cancelled && setFetchedReport(r))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [latestReadyId, lang]);

  if (error) return <ErrorNote message={error} />;

  const firstName = session?.user.name.split(" ")[0] ?? "";
  const patient = data?.patient;
  const items = data?.items ?? [];
  const newest = items[0];
  const newerPending =
    newest && newest.status === "pending" && latestReady && newest.visit.id !== latestReady.visit.id
      ? newest
      : null;

  const subtitle =
    data === null
      ? undefined
      : latestReady
        ? t.subtitleReady
        : items.some((i) => i.status === "pending")
          ? t.subtitleWaiting
          : t.subtitleNone;

  const chronological = [...items].reverse();
  const trendPoints: TrendPoint[] = chronological.map((item) => ({
    date: formatDate(item.visit.created_at, lang, false),
    values: {
      weight: item.visit.weight_kg,
      bmi: patient ? Math.round(bmi(item.visit.weight_kg, patient.height_cm) * 10) / 10 : undefined,
      systolic: item.visit.biomarkers.systolic_bp,
      diastolic: item.visit.biomarkers.diastolic_bp,
    },
  }));

  return (
    <div lang={lang} className="space-y-8">
      <PageHeader title={t.hello(firstName)} subtitle={subtitle} />

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="space-y-8 lg:col-span-2">
          {data === null || (latestReady && report === undefined) ? (
            <Skeleton className="h-80" />
          ) : items.length === 0 ? (
            <EmptyState
              title={t.noVisitsTitle}
              hint={t.noVisitsHint}
              art={<StethoscopeArt variant="mark" className="mx-auto h-32" />}
            />
          ) : !report ? (
            <div className="flex items-center gap-5 rounded-xl border border-watch-line bg-watch-tint px-5 py-5">
              <StethoscopeArt variant="mark" className="hidden h-24 shrink-0 sm:block" />
              <IconClock className="h-6 w-6 shrink-0 text-watch-ink sm:hidden" />
              <div>
                <p className="font-display text-lg font-bold leading-7 text-ink">{t.waitingTitle}</p>
                <p className="mt-1 text-ink-soft">{t.waitingHint(formatDate(newest.visit.created_at, lang))}</p>
              </div>
            </div>
          ) : (
            <>
              {newerPending && (
                <Note>
                  <span className="flex items-start gap-2.5">
                    <IconClock className="mt-0.5 h-4.5 w-4.5 shrink-0" />
                    {t.newerPending(formatDate(newerPending.visit.created_at, lang))}
                  </span>
                </Note>
              )}
              <TodayCard lang={lang} />
              <PlanSlip report={report} lang={lang} />
              {report.result.risk_flags.length > 0 && (
                <Card
                  title={t.results}
                  description={
                    report.visit_date ? t.resultsFrom(formatDate(report.visit_date, lang)) : undefined
                  }
                >
                  <FindingsList flags={report.result.risk_flags} lang={lang} />
                  <div className="mt-4 flex items-baseline justify-between gap-4 border-t border-line pt-3">
                    <p className="font-semibold text-ink">{t.bmiLine}</p>
                    <p className="text-right">
                      <span className="text-xl font-bold text-ink">
                        {report.result.anthropometrics.bmi}
                      </span>
                      <span className="ml-2 text-sm text-ink-muted">
                        {bmiCategoryName(report.result.anthropometrics.bmi_category, lang)}
                      </span>
                    </p>
                  </div>
                </Card>
              )}
            </>
          )}

          {items.length > 1 && (
            <section>
              <h2 className="font-display mb-3 text-xl font-bold leading-7 text-ink">{t.trends}</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <TrendChartCard
                  title={t.weight}
                  unit="kg"
                  series={[{ key: "weight", label: t.weight, color: TREND_COLOR_PRIMARY }]}
                  points={trendPoints}
                  emptyHint={t.trendHint}
                />
                <TrendChartCard
                  title={t.bp}
                  unit="mmHg"
                  series={[
                    { key: "systolic", label: t.systolic, color: TREND_COLOR_PRIMARY },
                    { key: "diastolic", label: t.diastolic, color: TREND_COLOR_SECONDARY },
                  ]}
                  points={trendPoints}
                  emptyHint={t.trendHint}
                />
              </div>
            </section>
          )}
        </div>

        <aside className="space-y-6">
          <Card title={t.visits}>
            {data === null ? (
              <Skeleton className="h-24" />
            ) : items.length === 0 ? (
              <p className="text-sm text-ink-muted">{t.noVisitsTitle}</p>
            ) : (
              <ol className="relative space-y-5 before:absolute before:bottom-2 before:left-1.25 before:top-2 before:w-px before:bg-line">
                {items.map((item) => (
                  <li key={item.visit.id} className="relative flex gap-3.5">
                    <span
                      aria-hidden="true"
                      className={`relative mt-1.5 h-2.75 w-2.75 shrink-0 rounded-full ring-4 ring-surface ${
                        STATUS_MARK[item.status] ?? "bg-line-strong"
                      }`}
                    />
                    <div className="min-w-0">
                      <p className="font-semibold text-ink">{formatDate(item.visit.created_at, lang)}</p>
                      <p className="text-sm text-ink-soft">
                        {item.status === "approved"
                          ? t.statusApproved
                          : item.status === "pending"
                            ? t.statusPending
                            : t.statusRejected}
                      </p>
                      {item.status === "rejected" && (
                        <p className="mt-0.5 text-sm text-ink-muted">{t.rejectedHint}</p>
                      )}
                      {item.report_ready && (
                        <Link
                          href={`/patient/reports/${item.visit.id}`}
                          className="mt-1 inline-flex items-center gap-0.5 text-sm font-semibold text-clinical hover:underline"
                        >
                          {t.readReport}
                          <IconChevronRight className="h-4 w-4" />
                        </Link>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </Card>

          <Card title={t.details}>
            {!patient ? (
              <Skeleton className="h-28" />
            ) : (
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-muted">{t.age}</dt>
                  <dd className="font-semibold text-ink">
                    {t.years(new Date().getFullYear() - patient.birth_year)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-muted">{t.height}</dt>
                  <dd className="font-semibold text-ink">{patient.height_cm} cm</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-ink-muted">{t.conditions}</dt>
                  <dd className="text-right font-semibold text-ink">
                    {patient.conditions.length === 0
                      ? t.none
                      : patient.conditions.map((c) => conditionName(c, lang)).join(", ")}
                  </dd>
                </div>
              </dl>
            )}
          </Card>
        </aside>
      </div>
    </div>
  );
}

/** The approved plan in brief, set as a signed slip: what to eat, how to
 * move, and who approved it. */
function PlanSlip({ report, lang }: { report: Report; lang: "en" | "bn" }) {
  const t = L[lang];
  const r = report.result;
  const meals = r.nutrition?.meal_plan;
  const plan = r.exercise_plan;
  // a week plan shows today's meals; an older one-day plan shows that day
  const days = meals && !meals.note ? planDays(meals) : [];
  const today = days.length ? days[todayIndex(days)] : null;
  const hasMeals = today !== null;

  return (
    <article className="sheet">
      <header className="sheet-head flex flex-wrap items-start justify-between gap-x-6 gap-y-3 border-b border-line px-5 py-4 sm:px-6">
        <div className="flex items-start gap-3">
          <IconRx className="mt-0.5 h-7 w-7 shrink-0 text-clinical" strokeWidth={2.2} />
          <div>
            <h2 className="font-display text-xl font-bold leading-7 text-ink">{t.currentPlan}</h2>
            <p className="mt-0.5 text-sm text-ink-muted">
              {t.approvedBy(report.approved_by, formatDate(report.approved_at, lang))}
            </p>
          </div>
        </div>
        <Link
          href={`/patient/reports/${report.visit_id}`}
          className="inline-flex items-center gap-0.5 text-sm font-semibold text-clinical hover:underline"
        >
          {t.fullReport}
          <IconChevronRight className="h-4 w-4" />
        </Link>
      </header>

      <div className="grid sm:grid-cols-2">
        <section className="border-b border-line px-5 py-5 sm:border-b-0 sm:border-r sm:px-6">
          <h3 className="text-sm font-semibold text-clinical">
            {today?.weekday ? t.eatToday(weekdayName(today.weekday, lang)) : t.eat}
          </h3>
          {hasMeals ? (
            <>
              <p className="mt-1 text-lg font-bold text-ink">{t.kcalPerDay(meals!.target_kcal)}</p>
              <dl className="mt-3 space-y-2.5">
                {MEAL_ORDER.filter((m) => today.meals[m]?.length).map((m) => (
                  <div key={m}>
                    <dt className="text-sm font-semibold text-ink-strong">{mealName(m, lang)}</dt>
                    <dd className="text-sm leading-6 text-ink-soft">
                      {/* semicolons: the food names carry their own commas ("Rice, bran, raw") */}
                      {today.meals[m].map((it) => localName(it, lang)).join("; ")}
                    </dd>
                  </div>
                ))}
              </dl>
            </>
          ) : (
            <p className="mt-1 text-sm text-ink-soft">{meals?.note}</p>
          )}
          <Link
            href="/patient/foods"
            className="mt-4 inline-flex items-center gap-0.5 text-sm font-semibold text-clinical hover:underline"
          >
            {today?.weekday ? t.seeWeek : t.seeMeals}
            <IconChevronRight className="h-4 w-4" />
          </Link>
        </section>

        <section className="px-5 py-5 sm:px-6">
          <h3 className="text-sm font-semibold text-clinical">{t.move}</h3>
          {plan?.time && plan.frequency ? (
            <ul className="mt-1 space-y-2 text-ink-strong">
              <li className="text-lg font-bold leading-snug text-ink">
                {t.aerobic(plan.time.aerobic_min_per_session, plan.frequency.aerobic_days)}
              </li>
              {plan.frequency.strength_days > 0 && (
                <li className="text-sm">{t.strength(plan.frequency.strength_days)}</li>
              )}
              {plan.frequency.flexibility_days > 0 && (
                <li className="text-sm">{t.stretch(plan.frequency.flexibility_days)}</li>
              )}
              {(plan.frequency.balance_days ?? 0) > 0 && (
                <li className="text-sm">{t.balance(plan.frequency.balance_days!)}</li>
              )}
            </ul>
          ) : (
            <p className="mt-1 text-sm text-ink-soft">{plan?.note}</p>
          )}
          <Link
            href="/patient/exercise"
            className="mt-4 inline-flex items-center gap-0.5 text-sm font-semibold text-clinical hover:underline"
          >
            {t.seeExercise}
            <IconChevronRight className="h-4 w-4" />
          </Link>
        </section>
      </div>

      {report.comment && (
        <footer className="border-t border-line bg-clinical-tint/60 px-5 py-4 sm:px-6">
          <p className="text-sm font-semibold text-clinical">{t.doctorNote}</p>
          <p className="mt-1 text-ink">{report.comment}</p>
        </footer>
      )}
    </article>
  );
}
