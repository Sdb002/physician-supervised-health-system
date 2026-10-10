"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, User } from "@/lib/api";
import { formatDate } from "@/lib/clinical-terms";
import { did } from "@/lib/format";
import { IconCheck, IconStethoscope, IconX } from "@/components/icons";
import {
  Avatar,
  Badge,
  EmptyState,
  ErrorNote,
  PageHeader,
  SearchInput,
  Skeleton,
  buttonDanger,
  buttonPrimary,
  focusRing,
} from "@/components/ui";

const FILTERS = ["all", "pending", "active", "rejected"] as const;
type Filter = (typeof FILTERS)[number];
const FILTER_LABELS: Record<Filter, string> = {
  all: "All",
  pending: "Waiting",
  active: "Active",
  rejected: "Rejected",
};

export default function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<User[] | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [actioning, setActioning] = useState<number | null>(null);

  const load = useCallback(() => {
    api.adminDoctors().then(setDoctors).catch((e) => setError(e.message));
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

  const pendingCount = doctors?.filter((d) => d.status === "pending").length ?? 0;
  const visible = useMemo(() => {
    if (doctors === null) return null;
    const q = query.trim().toLowerCase();
    return doctors.filter(
      (d) =>
        (filter === "all" || d.status === filter) &&
        (!q ||
          [d.name, d.email, d.specialty, d.license_no, did(d.id), String(d.id)]
            .join(" ")
            .toLowerCase()
            .includes(q))
    );
  }, [doctors, filter, query]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Doctors"
        subtitle={doctors ? `${doctors.length} registered, ${pendingCount} waiting for approval` : undefined}
      />

      {error && <ErrorNote message={error} />}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div role="group" aria-label="Filter by status" className="inline-flex w-fit rounded-lg border border-line-strong bg-surface p-0.5">
          {FILTERS.map((f) => (
            <button
              key={f}
              aria-pressed={filter === f}
              onClick={() => setFilter(f)}
              className={`inline-flex min-h-8 cursor-pointer items-center gap-1.5 rounded-md px-3 text-sm font-semibold transition-colors duration-150 ${focusRing} ${
                filter === f ? "bg-clinical text-on-clinical" : "text-ink-soft hover:bg-surface-soft"
              }`}
            >
              {FILTER_LABELS[f]}
              {f === "pending" && pendingCount > 0 && (
                <span
                  className={`rounded-full px-1.5 text-xs ${
                    filter === f ? "bg-on-clinical/20" : "bg-watch-tint text-watch-ink"
                  }`}
                >
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>
        <SearchInput value={query} onChange={setQuery} placeholder="Search name, DID, specialty" />
      </div>

      {visible === null ? (
        <Skeleton className="h-48" />
      ) : visible.length === 0 ? (
        <EmptyState
          title={filter === "all" ? "No doctors yet" : `No ${FILTER_LABELS[filter].toLowerCase()} doctors`}
          hint="Applications from the doctor registration page appear here."
          icon={<IconStethoscope className="h-5 w-5" />}
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-3xl text-left text-sm">
            <thead className="border-b border-line bg-surface-soft text-ink-muted">
              <tr>
                <th scope="col" className="px-5 py-3 font-semibold">Doctor</th>
                <th scope="col" className="px-4 py-3 font-semibold">Specialty</th>
                <th scope="col" className="px-4 py-3 font-semibold">BMDC no.</th>
                <th scope="col" className="px-4 py-3 font-semibold">Applied</th>
                <th scope="col" className="px-4 py-3 font-semibold">Status</th>
                <th scope="col" className="px-5 py-3"><span className="sr-only">Decision</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map((doc) => (
                <tr key={doc.id} className="hover:bg-surface-soft">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={doc.name} />
                      <div className="min-w-0">
                        <p className="font-semibold text-ink">{doc.name}</p>
                        <p className="text-ink-muted">
                          <span>{did(doc.id)}</span>, {doc.email}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-ink-soft">{doc.specialty || <span className="text-ink-muted">—</span>}</td>
                  <td className="px-4 py-3 text-ink-soft">
                    {doc.license_no || <span className="text-ink-muted">—</span>}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-ink-muted">{formatDate(doc.created_at)}</td>
                  <td className="px-4 py-3">
                    <Badge kind={doc.status}>{doc.status === "pending" ? "Waiting" : doc.status}</Badge>
                  </td>
                  <td className="px-5 py-3 text-right">
                    {doc.status === "pending" && (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => decide(doc.id, "rejected")}
                          disabled={actioning === doc.id}
                          className={`${buttonDanger} min-h-8 px-3`}
                        >
                          <IconX className="h-4 w-4" /> Reject
                        </button>
                        <button
                          onClick={() => decide(doc.id, "approved")}
                          disabled={actioning === doc.id}
                          className={`${buttonPrimary} min-h-8 px-3`}
                        >
                          <IconCheck className="h-4 w-4" /> Approve
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
