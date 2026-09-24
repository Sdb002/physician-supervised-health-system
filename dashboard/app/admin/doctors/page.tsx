"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, User } from "@/lib/api";
import { did } from "@/lib/format";
import { IconCheck, IconStethoscope, IconX } from "@/components/icons";
import { Badge, EmptyState, ErrorNote, PageHeader, SearchInput, Skeleton } from "@/components/ui";

const FILTERS = ["all", "pending", "active", "rejected"] as const;
type Filter = (typeof FILTERS)[number];

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
        subtitle={
          doctors
            ? `${doctors.length} registered · ${pendingCount} awaiting approval`
            : "Loading…"
        }
        action={
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search by name, DID, specialty…"
          />
        }
      />

      {error && <ErrorNote message={error} />}

      <div className="flex gap-1 rounded-xl bg-line/60 p-1 text-sm font-medium w-fit">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 capitalize transition ${
              filter === f ? "bg-surface text-ink shadow-sm" : "text-ink-muted hover:text-ink"
            }`}
          >
            {f}
            {f === "pending" && pendingCount > 0 && (
              <span className="ml-1.5 rounded-full bg-amber-100 px-1.5 text-xs text-amber-800">
                {pendingCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {visible === null ? (
        <Skeleton className="h-48" />
      ) : visible.length === 0 ? (
        <EmptyState
          title={filter === "all" ? "No doctors yet" : `No ${filter} doctors`}
          hint="Doctor applications from the registration page appear here."
          icon={<IconStethoscope className="h-5 w-5" />}
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-surface shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-ink-muted">
              <tr>
                <th className="px-4 py-3">DID</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Specialty</th>
                <th className="px-4 py-3">License</th>
                <th className="px-4 py-3">Applied</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map((doc) => (
                <tr key={doc.id} className="hover:bg-surface-soft">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-teal-700">
                    {did(doc.id)}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-ink">{doc.name}</p>
                    <p className="text-xs text-ink-muted">{doc.email}</p>
                  </td>
                  <td className="px-4 py-3 text-ink-soft">
                    {doc.specialty || <span className="text-ink-muted">—</span>}
                  </td>
                  <td className="px-4 py-3 text-ink-soft">
                    {doc.license_no || <span className="text-ink-muted">—</span>}
                  </td>
                  <td className="px-4 py-3 text-ink-muted">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <Badge kind={doc.status}>{doc.status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {doc.status === "pending" && (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => decide(doc.id, "approved")}
                          disabled={actioning === doc.id}
                          className="inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                        >
                          <IconCheck className="h-3.5 w-3.5" /> Approve
                        </button>
                        <button
                          onClick={() => decide(doc.id, "rejected")}
                          disabled={actioning === doc.id}
                          className="inline-flex items-center gap-1 rounded-lg border border-rose-200 px-2.5 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                        >
                          <IconX className="h-3.5 w-3.5" /> Reject
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
