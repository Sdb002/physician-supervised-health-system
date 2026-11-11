"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Patient, QueueItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { byTriage } from "@/lib/triage";
import { useT } from "@/lib/use-t";
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
  const { t, n, lang } = useT();
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [queue, setQueue] = useState<QueueItem[] | null>(null);
  const [ocrReader, setOcrReader] = useState<string | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listPatients(), api.reviewQueue(), api.health()])
      .then(([p, q, h]) => {
        setPatients(p);
        setQueue([...q].sort(byTriage));
        // servers before the local reader only report the API key
        setOcrReader(h.ocr_reader !== undefined ? h.ocr_reader : h.llm_configured ? "Claude" : null);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  const today = new Date().toLocaleDateString(lang === "bn" ? "bn-BD" : "en-GB", { weekday: "long", day: "numeric", month: "long" });
  const urgent = queue?.filter((q) => ["high", "critical"].includes(q.assessment.result.overall_risk)).length ?? 0;

  return (
    <div className="space-y-8">
      <PageHeader
        title={session ? t("Welcome back, {name}", { name: session.user.name }) : t("Welcome back")}
        subtitle={today}
        action={
          <Link href="/doctor/patients/new" className={buttonPrimary}>
            <IconPlus className="h-4 w-4" /> {t("New patient")}
          </Link>
        }
      />

      <MetricRow
        items={[
          {
            label: t("Awaiting your review"),
            value: queue === null ? <Skeleton className="h-8 w-10" /> : n(queue.length),
            hint: queue !== null && queue.length === 0 ? t("Queue is clear") : undefined,
            icon: <IconClipboard className="h-5 w-5" />,
          },
          {
            label: t("High or critical risk"),
            value: queue === null ? <Skeleton className="h-8 w-10" /> : n(urgent),
            hint: queue === null ? undefined : urgent > 0 ? t("Open these first") : t("None waiting"),
            icon: <IconAlert className="h-5 w-5" />,
          },
          {
            label: t("Registered patients"),
            value: patients === null ? <Skeleton className="h-8 w-10" /> : n(patients.length),
            hint: (
              <Link href="/doctor/patients" className="font-semibold text-clinical hover:underline">
                {t("View patients")}
              </Link>
            ),
            icon: <IconUsers className="h-5 w-5" />,
          },
        ]}
      />

      <section>
        <SectionHeading
          description={t("Highest risk first. Nothing reaches a patient until you approve it.")}
          action={
            queue && queue.length > 0 ? (
              <Link href="/doctor/review" className={linkButton}>
                {t("Open review queue")}
              </Link>
            ) : undefined
          }
        >
          {t("Waiting for your approval")}
        </SectionHeading>
        {queue === null ? (
          <Skeleton className="h-40" />
        ) : queue.length === 0 ? (
          <EmptyState
            title={t("You're all caught up")}
            hint={t("New assessments appear here as soon as an intake is submitted.")}
            icon={<IconCheck className="h-5 w-5" />}
          />
        ) : (
          <QueueList items={queue.slice(0, 6)} />
        )}
      </section>

      {ocrReader !== undefined && (
        <p className="flex items-start gap-2 border-t border-line pt-4 text-sm text-ink-muted">
          <IconSparkles className="mt-0.5 h-4 w-4 shrink-0" />
          {ocrReader === "RapidOCR"
            ? t("Lab-report reading is on, on this server: a photo of a lab slip can prefill the intake form, and the photo never leaves the clinic. You confirm every value.")
            : ocrReader
              ? t("Lab-report reading is on (Claude): a photo of a lab slip can prefill the intake form. You confirm every value.")
              : t("Lab-report reading is off on this server. Typing values into the intake form works the same.")}
        </p>
      )}
    </div>
  );
}
