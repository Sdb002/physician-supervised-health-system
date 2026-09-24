"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, AdminStats, AuditEntry, User } from "@/lib/api";
import { did } from "@/lib/format";
import {
  IconArrowRight,
  IconCheck,
  IconClipboard,
  IconClock,
  IconStethoscope,
  IconUsers,
  IconX,
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

export default function AdminOverview() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [pending, setPending] = useState<User[] | null>(null);
  const [activity, setActivity] = useState<AuditEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actioning, setActioning] = useState<number | null>(null);

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
    <div className="space-y-6">
      <PageHeader
        title="Admin overview"
        subtitle="Platform health and doctor registrations at a glance."
      />

      {stats === null ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Registered patients"
            value={stats.patients}
            icon={<IconUsers className="h-5 w-5" />}
            tone="emerald"
            hint={`${stats.visits} visits recorded`}
          />
          <StatCard
            label="Active doctors"
            value={stats.doctors_active}
            icon={<IconStethoscope className="h-5 w-5" />}
            tone="teal"
          />
          <StatCard
            label="Doctor approvals waiting"
            value={stats.doctors_pending}
            icon={<IconClock className="h-5 w-5" />}
            tone="amber"
            hint={stats.doctors_pending > 0 ? "Action needed below" : "All caught up"}
          />
          <StatCard
            label="Assessments pending review"
            value={stats.assessments_pending}
            icon={<IconClipboard className="h-5 w-5" />}
            tone="sky"
            hint={`${stats.assessments_approved} approved · ${stats.assessments_rejected} rejected`}
          />
        </div>
      )}

      {error && <ErrorNote message={error} />}

      <div className="grid gap-6 lg:grid-cols-5">
        <Card
          title="Doctor registration requests"
          className="lg:col-span-3"
          action={
            <Link href="/admin/doctors" className="text-sm font-medium text-indigo-600 hover:underline">
              All doctors <IconArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          }
        >
          {pending === null ? (
            <Skeleton className="h-24" />
          ) : pending.length === 0 ? (
            <EmptyState
              title="No pending requests"
              hint="New doctor registrations will appear here for your approval."
              icon={<IconCheck className="h-5 w-5" />}
            />
          ) : (
            <ul className="divide-y divide-line">
              {pending.map((doc) => (
                <li key={doc.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="font-medium text-ink">
                      {doc.name}{" "}
                      <span className="font-mono text-xs font-semibold text-teal-700">
                        {did(doc.id)}
                      </span>
                    </p>
                    <p className="truncate text-xs text-ink-muted">
                      {doc.email}
                      {doc.specialty && <> · {doc.specialty}</>}
                      {doc.license_no && <> · {doc.license_no}</>}
                      {" · applied "}
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => decide(doc.id, "approved")}
                      disabled={actioning === doc.id}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                    >
                      <IconCheck className="h-3.5 w-3.5" /> Approve
                    </button>
                    <button
                      onClick={() => decide(doc.id, "rejected")}
                      disabled={actioning === doc.id}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-surface px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                    >
                      <IconX className="h-3.5 w-3.5" /> Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Recent activity" className="lg:col-span-2">
          {activity === null ? (
            <Skeleton className="h-24" />
          ) : activity.length === 0 ? (
            <p className="text-sm text-ink-muted">No activity yet.</p>
          ) : (
            <ul className="space-y-3">
              {activity.map((entry) => (
                <li key={entry.id} className="flex items-start gap-3 text-sm">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-indigo-400" />
                  <div className="min-w-0">
                    <p className="text-ink-strong">
                      <Badge kind="info">{entry.action}</Badge>
                    </p>
                    <p className="mt-0.5 truncate text-xs text-ink-muted">
                      {entry.actor} · {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
