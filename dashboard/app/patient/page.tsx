"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PatientDashboard } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { bmi } from "@/lib/format";
import {
  IconActivity,
  IconChevronRight,
  IconClock,
  IconFileText,
  IconHeartPulse,
  IconLock,
} from "@/components/icons";
import {
  Badge,
  Card,
  EmptyState,
  ErrorNote,
  PageHeader,
  Skeleton,
  StatCard,
} from "@/components/ui";
import { TREND_COLOR_PRIMARY, TREND_COLOR_SECONDARY, TrendPoint } from "@/components/trend-chart";
import { TrendChartCard } from "@/components/trend-chart-card";

export default function PatientHome() {
  const { session } = useAuth();
  const [data, setData] = useState<PatientDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.myDashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  const ready = data?.items.filter((i) => i.report_ready).length ?? 0;
  const inReview = data?.items.filter((i) => i.status === "pending").length ?? 0;
  const patient = data?.patient;
  const age = patient ? new Date().getFullYear() - patient.birth_year : null;

  const chronological = data ? [...data.items].reverse() : [];
  const trendPoints: TrendPoint[] = chronological.map((item) => ({
    date: new Date(item.visit.created_at).toLocaleDateString(undefined, { month: "numeric", day: "numeric" }),
    values: {
      weight: item.visit.weight_kg,
      bmi: patient ? Math.round(bmi(item.visit.weight_kg, patient.height_cm) * 10) / 10 : undefined,
      systolic: item.visit.biomarkers.systolic_bp,
      diastolic: item.visit.biomarkers.diastolic_bp,
    },
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Hello${session ? `, ${session.user.name.split(" ")[0]}` : ""}`}
        subtitle="Your visits and physician-approved reports."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Total visits"
          value={data === null ? <Skeleton className="h-8 w-10" /> : data.items.length}
          icon={<IconActivity className="h-5 w-5" />}
          tone="emerald"
        />
        <StatCard
          label="Reports ready"
          value={data === null ? <Skeleton className="h-8 w-10" /> : ready}
          icon={<IconFileText className="h-5 w-5" />}
          tone="sky"
          hint={
            ready > 0 ? (
              <Link href="/patient/reports" className="font-medium text-emerald-700 hover:underline">
                Read your reports &rarr;
              </Link>
            ) : (
              "Reports appear after your physician approves them."
            )
          }
        />
        <StatCard
          label="Awaiting physician review"
          value={data === null ? <Skeleton className="h-8 w-10" /> : inReview}
          icon={<IconClock className="h-5 w-5" />}
          tone="amber"
        />
      </div>

      {data !== null && data.items.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          <TrendChartCard
            title="Weight"
            unit="kg"
            series={[{ key: "weight", label: "Weight", color: TREND_COLOR_PRIMARY }]}
            points={trendPoints}
            emptyHint="Weight trend appears after your second visit."
          />
          <TrendChartCard
            title="BMI"
            series={[{ key: "bmi", label: "BMI", color: TREND_COLOR_PRIMARY }]}
            points={trendPoints}
            emptyHint="BMI trend appears after your second visit."
          />
          <TrendChartCard
            title="Blood pressure"
            unit="mmHg"
            series={[
              { key: "systolic", label: "Systolic", color: TREND_COLOR_PRIMARY },
              { key: "diastolic", label: "Diastolic", color: TREND_COLOR_SECONDARY },
            ]}
            points={trendPoints}
            emptyHint="Blood pressure trend appears once it's been recorded at two or more visits."
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="My profile">
          {patient === undefined ? (
            <Skeleton className="h-32" />
          ) : (
            <dl className="space-y-2.5 text-sm">
              <div className="flex justify-between">
                <dt className="text-ink-muted">Name</dt>
                <dd className="font-medium text-ink">{patient!.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-ink-muted">Sex / age</dt>
                <dd className="font-medium capitalize text-ink">
                  {patient!.sex} · {age} yrs
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-ink-muted">Height</dt>
                <dd className="font-medium text-ink">{patient!.height_cm} cm</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-ink-muted">Fitness level</dt>
                <dd className="font-medium capitalize text-ink">{patient!.fitness_level}</dd>
              </div>
              {patient!.conditions.length > 0 && (
                <div>
                  <dt className="text-ink-muted">Conditions</dt>
                  <dd className="mt-1 flex flex-wrap gap-1">
                    {patient!.conditions.map((c) => (
                      <Badge key={c} kind="high">
                        {c.replace(/_/g, " ")}
                      </Badge>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          )}
        </Card>

        <Card title="Visit history" className="lg:col-span-2">
          {data === null ? (
            <Skeleton className="h-32" />
          ) : data.items.length === 0 ? (
            <EmptyState
              title="No visits yet"
              hint="Your doctor records visits during consultations — they'll show up here."
              icon={<IconHeartPulse className="h-5 w-5" />}
            />
          ) : (
            <ul className="divide-y divide-line">
              {data.items.map((item) => (
                <li key={item.visit.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="font-medium text-ink">
                      Visit #{item.visit.id}
                    </p>
                    <p className="text-xs text-ink-muted">
                      {new Date(item.visit.created_at).toLocaleDateString()} ·{" "}
                      {item.visit.weight_kg} kg
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <Badge kind={item.status}>
                      {item.status === "pending" ? "in review" : item.status}
                    </Badge>
                    {item.report_ready ? (
                      <Link
                        href={`/patient/reports/${item.visit.id}`}
                        className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700 hover:underline"
                      >
                        View report <IconChevronRight className="h-3.5 w-3.5" />
                      </Link>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-ink-muted">
                        <IconLock className="h-3.5 w-3.5" /> not released
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <p className="text-center text-xs text-ink-muted">
        Every report is generated by a cited clinical rule engine and released only after your
        physician reviews and approves it.
      </p>
    </div>
  );
}
