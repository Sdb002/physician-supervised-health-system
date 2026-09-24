"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Patient, QueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  IconChevronRight,
  IconClipboard,
  IconPlus,
  IconSparkles,
  IconUsers,
} from "@/components/icons";
import {
  Badge,
  Card,
  EmptyState,
  ErrorNote,
  PageHeader,
  Skeleton,
  StatCard,
  buttonPrimary,
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
        setQueue(q);
        setLlmConfigured(h.llm_configured);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back${session ? `, ${session.user.name}` : ""}`}
        subtitle="Today's workload at a glance."
        action={
          <Link href="/doctor/patients/new" className={buttonPrimary}>
            <IconPlus className="h-4 w-4" /> New patient
          </Link>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Awaiting your review"
          value={queue === null ? <Skeleton className="h-8 w-10" /> : queue.length}
          icon={<IconClipboard className="h-5 w-5" />}
          tone="amber"
          hint={
            <Link href="/doctor/review" className="font-medium text-teal-700 hover:underline">
              Open review queue &rarr;
            </Link>
          }
        />
        <StatCard
          label="Registered patients"
          value={patients === null ? <Skeleton className="h-8 w-10" /> : patients.length}
          icon={<IconUsers className="h-5 w-5" />}
          tone="teal"
          hint={
            <Link href="/doctor/patients" className="font-medium text-teal-700 hover:underline">
              View patients &rarr;
            </Link>
          }
        />
        <StatCard
          label="Lab-report OCR (AI)"
          value={
            llmConfigured === null ? (
              <Skeleton className="h-8 w-24" />
            ) : llmConfigured ? (
              <span className="text-xl font-semibold text-emerald-600">Available</span>
            ) : (
              <span className="text-xl font-semibold text-ink-muted">Not configured</span>
            )
          }
          icon={<IconSparkles className="h-5 w-5" />}
          tone="sky"
          hint={
            llmConfigured
              ? "Images can prefill the intake form — you confirm every value."
              : "Set ANTHROPIC_API_KEY in .env to enable. Manual entry always works."
          }
        />
      </div>

      <Card title="Pending assessments">
        {queue === null ? (
          <Skeleton className="h-24" />
        ) : queue.length === 0 ? (
          <EmptyState
            title="Nothing waiting for review"
            hint="New visits appear here as soon as intake is submitted."
            icon={<IconClipboard className="h-5 w-5" />}
          />
        ) : (
          <ul className="divide-y divide-line">
            {queue.map((item) => (
              <li key={item.assessment.id}>
                <Link
                  href={`/doctor/review/${item.assessment.id}`}
                  className="group flex items-center justify-between gap-3 py-3"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-ink group-hover:text-teal-700">
                      {item.patient.name}
                    </p>
                    <p className="text-xs text-ink-muted">
                      Visit #{item.visit.id} · {new Date(item.visit.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <Badge kind={item.assessment.result.overall_risk}>
                      {item.assessment.result.overall_risk} risk
                    </Badge>
                    <IconChevronRight className="h-4 w-4 text-ink-muted group-hover:text-teal-600" />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
