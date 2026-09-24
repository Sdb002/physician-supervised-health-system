"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, QueueItem } from "@/lib/api";
import { IconClipboard } from "@/components/icons";
import { Badge, EmptyState, ErrorNote, PageHeader, Skeleton } from "@/components/ui";

export default function ReviewQueuePage() {
  const [queue, setQueue] = useState<QueueItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reviewQueue().then(setQueue).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Review queue"
        subtitle="Assessments waiting for your decision. Nothing reaches a patient until you approve it here."
      />

      {queue === null ? (
        <Skeleton className="h-48" />
      ) : queue.length === 0 ? (
        <EmptyState
          title="Queue is empty"
          hint="All assessments have been reviewed."
          icon={<IconClipboard className="h-5 w-5" />}
        />
      ) : (
        <div className="space-y-3">
          {queue.map((item) => {
            const r = item.assessment.result;
            return (
              <Link
                key={item.assessment.id}
                href={`/doctor/review/${item.assessment.id}`}
                className="block rounded-2xl border border-line bg-surface p-4 shadow-sm transition hover:border-teal-300 hover:shadow"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{item.patient.name}</p>
                    <p className="text-xs text-ink-muted">
                      Visit #{item.visit.id} ·{" "}
                      {new Date(item.visit.created_at).toLocaleString()} · engine v
                      {item.assessment.engine_version}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {r.conditions.map((c) => (
                      <Badge key={c} kind="high">
                        {c.replace(/_/g, " ")}
                      </Badge>
                    ))}
                    <Badge kind={r.overall_risk}>{r.overall_risk} risk</Badge>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
