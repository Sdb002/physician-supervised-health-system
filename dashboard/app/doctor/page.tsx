"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Patient, QueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { byTriage } from "@/lib/triage";
import { IconAlert, IconCheck, IconClipboard, IconPlus, IconSparkles, IconUsers } from "@/components/icons";
import { QueueList } from "@/components/queue-list";
import {
  EmptyState,
  ErrorNote,
  MetricRow,
  PageHeader,
  SectionHeading,
  Skeleton,
  buttonPrimary,
  linkButton,
} from "@/components/ui";

export default function DoctorOverview() {
  const { session } = useAuth();
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [queue, setQueue] = useState<QueueItem[] | null>(null);
  const [llmConfigured, setLlmConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listPatients(), api.reviewQueue(), api.health()])
      .then(([p, q, h]) => {
        setPatients(p);
        setQueue([...q].sort(byTriage));
        setLlmConfigured(h.llm_configured);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  const today = new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
  const urgent = queue?.filter((q) => ["high", "critical"].includes(q.assessment.result.overall_risk)).length ?? 0;

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Welcome back${session ? `, ${session.user.name}` : ""}`}
        subtitle={today}
        action={
          <Link href="/doctor/patients/new" className={buttonPrimary}>
            <IconPlus className="h-4 w-4" /> New patient
          </Link>
        }
      />

      <MetricRow
        items={[
          {
            label: "Awaiting your review",
            value: queue === null ? <Skeleton className="h-8 w-10" /> : queue.length,
            hint: queue !== null && queue.length === 0 ? "Queue is clear" : undefined,
            icon: <IconClipboard className="h-5 w-5" />,
          },
          {
            label: "High or critical risk",
            value: queue === null ? <Skeleton className="h-8 w-10" /> : urgent,
            hint: queue === null ? undefined : urgent > 0 ? "Open these first" : "None waiting",
            icon: <IconAlert className="h-5 w-5" />,
          },
          {
            label: "Registered patients",
            value: patients === null ? <Skeleton className="h-8 w-10" /> : patients.length,
            hint: (
              <Link href="/doctor/patients" className="font-semibold text-clinical hover:underline">
                View patients
              </Link>
            ),
            icon: <IconUsers className="h-5 w-5" />,
          },
        ]}
      />

      <section>
        <SectionHeading
          description="Highest risk first. Nothing reaches a patient until you approve it."
          action={
            queue && queue.length > 0 ? (
              <Link href="/doctor/review" className={linkButton}>
                Open review queue
              </Link>
            ) : undefined
          }
        >
          Waiting for your approval
        </SectionHeading>
        {queue === null ? (
          <Skeleton className="h-40" />
        ) : queue.length === 0 ? (
          <EmptyState
            title="You're all caught up"
            hint="New assessments appear here as soon as an intake is submitted."
            icon={<IconCheck className="h-5 w-5" />}
          />
        ) : (
          <QueueList items={queue.slice(0, 6)} />
        )}
      </section>

      {llmConfigured !== null && (
        <p className="flex items-start gap-2 border-t border-line pt-4 text-sm text-ink-muted">
          <IconSparkles className="mt-0.5 h-4 w-4 shrink-0" />
          {llmConfigured
            ? "Lab-report reading is on: a photo of a lab slip can prefill the intake form. You confirm every value."
            : "Lab-report reading is off (no ANTHROPIC_API_KEY). Typing values into the intake form works the same."}
        </p>
      )}
    </div>
  );
}
