"use client";

import { useEffect, useState } from "react";
import { api, QueueItem } from "@/lib/api";
import { byTriage } from "@/lib/triage";
import { useT } from "@/lib/use-t";
import { IconCheck } from "@/components/icons";
import { QueueList } from "@/components/queue-list";
import { EmptyState, ErrorNote, PageHeader, Skeleton } from "@/components/ui";

export default function ReviewQueuePage() {
  const [queue, setQueue] = useState<QueueItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t } = useT();

  useEffect(() => {
    api
      .reviewQueue()
      .then((q) => setQueue([...q].sort(byTriage)))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("Review queue")}
        subtitle={t("Assessments waiting for your decision, highest risk first. Nothing reaches a patient until you approve it.")}
      />

      {queue === null ? (
        <Skeleton className="h-48" />
      ) : queue.length === 0 ? (
        <EmptyState
          title={t("The queue is empty")}
          hint={t("Every assessment has a decision. New ones appear here when an intake is submitted.")}
          icon={<IconCheck className="h-5 w-5" />}
        />
      ) : (
        <QueueList items={queue} />
      )}
    </div>
  );
}
