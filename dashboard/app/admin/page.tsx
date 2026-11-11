"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, AdminStats, AuditEntry, User } from "@/lib/api";
import { formatDate } from "@/lib/clinical-terms";
import { did } from "@/lib/format";
import { useT } from "@/lib/use-t";
import { IconCheck, IconX } from "@/components/icons";
import {
  Card,
  EmptyState,
  ErrorNote,
  MetricRow,
  PageHeader,
  Skeleton,
  buttonDanger,
  buttonPrimary,
  linkButton,
} from "@/components/ui";

const actionWords = (action: string) => {
  const s = action.replace(/[._]/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
};

export default function AdminOverview() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [pending, setPending] = useState<User[] | null>(null);
  const [activity, setActivity] = useState<AuditEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actioning, setActioning] = useState<number | null>(null);
  const { t, n, lang } = useT();

  const load = useCallback(() => {
    Promise.all([api.adminStats(), api.adminDoctors("pending"), api.adminAudit(12)])
      .then(([s, p, a]) => {
        setStats(s);
        setPending(p);
        setActivity(a);
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(load, [load]);

  const decide = async (userId: number, decision: "approved" | "rejected") => {
    setActioning(userId);
    setError(null);
    try {
      await api.adminDecideDoctor(userId, decision);
      load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setActioning(null);
    }
  };

  if (error && stats === null) return <ErrorNote message={error} />;

  return (
    <div className="space-y-8">
      <PageHeader title={t("Overview")} subtitle={t("Doctor registrations and the state of the service.")} />

      {stats === null ? (
        <Skeleton className="h-28" />
      ) : (
        <MetricRow
          items={[
            {
              label: t("Patients"),
              value: n(stats.patients),
              hint: t("{count} visits recorded", { count: stats.visits }),
            },
            { label: t("Active doctors"), value: n(stats.doctors_active) },
            {
              label: t("Doctors waiting for approval"),
              value: n(stats.doctors_pending),
              hint: stats.doctors_pending > 0 ? t("Decide below") : t("All caught up"),
            },
            {
              label: t("Assessments awaiting review"),
              value: n(stats.assessments_pending),
              hint: t("{approved} approved, {rejected} rejected", {
                approved: stats.assessments_approved,
                rejected: stats.assessments_rejected,
              }),
            },
          ]}
        />
      )}

      {error && <ErrorNote message={error} />}

      <div className="grid items-start gap-6 lg:grid-cols-5">
        <Card
          title={t("Doctor applications")}
          description={t("Check the BMDC number before approving.")}
          className="lg:col-span-3"
          flush={pending !== null && pending.length > 0}
          action={
            <Link href="/admin/doctors" className={linkButton}>
              {t("All doctors")}
            </Link>
          }
        >
          {pending === null ? (
            <Skeleton className="h-24" />
          ) : pending.length === 0 ? (
            <EmptyState
              title={t("No applications waiting")}
              hint={t("New doctor registrations appear here for your decision.")}
              icon={<IconCheck className="h-5 w-5" />}
              inset
            />
          ) : (
            <ul className="divide-y divide-line">
              {pending.map((doc) => (
                <li key={doc.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5">
                  <div className="min-w-0">
                    <p className="font-semibold text-ink">
                      {doc.name}
                      <span className="ml-2 text-sm font-semibold text-ink-muted">{did(doc.id)}</span>
                    </p>
                    <p className="text-sm text-ink-muted">
                      {[doc.specialty, doc.license_no && t("BMDC {number}", { number: doc.license_no })]
                        .filter(Boolean)
                        .join(", ") || t("No specialty or licence given")}
                    </p>
                    <p className="truncate text-sm text-ink-muted">
                      {t("{email}, applied {date}", { email: doc.email, date: formatDate(doc.created_at, lang) })}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => decide(doc.id, "rejected")}
                      disabled={actioning === doc.id}
                      className={buttonDanger}
                    >
                      <IconX className="h-4 w-4" /> {t("Reject")}
                    </button>
                    <button
                      onClick={() => decide(doc.id, "approved")}
                      disabled={actioning === doc.id}
                      className={buttonPrimary}
                    >
                      <IconCheck className="h-4 w-4" /> {t("Approve")}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title={t("Recent activity")} description={t("From the append-only audit log.")} className="lg:col-span-2">
          {activity === null ? (
            <Skeleton className="h-24" />
          ) : activity.length === 0 ? (
            <p className="text-sm text-ink-muted">{t("No activity yet.")}</p>
          ) : (
            <ol className="relative space-y-4 before:absolute before:bottom-2 before:left-1.25 before:top-2 before:w-px before:bg-line">
              {activity.map((entry) => (
                <li key={entry.id} className="relative flex gap-3.5 text-sm">
                  <span
                    aria-hidden="true"
                    className="relative mt-1.5 h-2.75 w-2.75 shrink-0 rounded-full bg-clinical ring-4 ring-surface"
                  />
                  <div className="min-w-0">
                    <p className="font-semibold text-ink">{t(actionWords(entry.action))}</p>
                    <p className="truncate text-ink-muted">
                      {entry.actor},{" "}
                      {new Date(entry.created_at).toLocaleString(lang === "bn" ? "bn-BD" : "en-GB", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </Card>
      </div>
    </div>
  );
}
