"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, PatientDashboard } from "@/lib/api";
import { IconChevronRight, IconFileText } from "@/components/icons";
import { Badge, EmptyState, ErrorNote, PageHeader, Skeleton } from "@/components/ui";

export default function PatientReportsPage() {
  const [data, setData] = useState<PatientDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.myDashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  const ready = data?.items.filter((i) => i.report_ready) ?? null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="My reports"
        subtitle="Reports your physician has approved and released to you."
      />

      {ready === null ? (
        <Skeleton className="h-48" />
      ) : ready.length === 0 ? (
        <EmptyState
          title="No reports released yet"
          hint="A report appears here as soon as your physician approves a visit's assessment."
          icon={<IconFileText className="h-5 w-5" />}
        />
      ) : (
        <div className="space-y-3">
          {ready.map((item) => (
            <Link
              key={item.visit.id}
              href={`/patient/reports/${item.visit.id}`}
              className="group flex items-center justify-between rounded-2xl border border-line bg-surface p-4 shadow-sm transition hover:border-emerald-300 hover:shadow"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
                  <IconFileText className="h-5 w-5" />
                </span>
                <div>
                  <p className="font-medium text-ink group-hover:text-emerald-700">
                    Visit #{item.visit.id} report
                  </p>
                  <p className="text-xs text-ink-muted">
                    {new Date(item.visit.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge kind="approved">approved</Badge>
                <IconChevronRight className="h-4 w-4 text-ink-muted group-hover:text-emerald-600" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
