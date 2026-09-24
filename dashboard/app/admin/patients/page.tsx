"use client";

import { useEffect, useMemo, useState } from "react";
import { api, Patient } from "@/lib/api";
import { pid } from "@/lib/format";
import { IconHeartPulse } from "@/components/icons";
import {
  Avatar,
  Badge,
  EmptyState,
  ErrorNote,
  PageHeader,
  SearchInput,
  Skeleton,
} from "@/components/ui";

interface Row {
  patient: Patient;
  account_email: string | null;
}

export default function AdminPatientsPage() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api.adminPatients().then(setRows).catch((e) => setError(e.message));
  }, []);

  const visible = useMemo(() => {
    if (rows === null) return null;
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(({ patient, account_email }) =>
      [patient.name, account_email ?? "", pid(patient.id), String(patient.id),
       ...patient.conditions]
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [rows, query]);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Patients"
        subtitle={rows ? `${rows.length} registered patients` : "Loading…"}
        action={
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search by name, PID, email…"
          />
        }
      />

      {visible === null ? (
        <Skeleton className="h-48" />
      ) : visible.length === 0 ? (
        <EmptyState
          title={query ? "No patients match your search" : "No patients yet"}
          hint={query ? "Try a different name, PID, or email." : undefined}
          icon={<IconHeartPulse className="h-5 w-5" />}
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-surface shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-ink-muted">
              <tr>
                <th className="px-4 py-3">PID</th>
                <th className="px-4 py-3">Patient</th>
                <th className="px-4 py-3">Sex / age</th>
                <th className="px-4 py-3">Conditions</th>
                <th className="px-4 py-3">Login account</th>
                <th className="px-4 py-3">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map(({ patient, account_email }) => (
                <tr key={patient.id} className="hover:bg-surface-soft">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-emerald-700">
                    {pid(patient.id)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={patient.name} />
                      <span className="font-medium text-ink">
                        {patient.name}
                        {patient.pregnant && (
                          <span className="ml-2">
                            <Badge kind="moderate">pregnant</Badge>
                          </span>
                        )}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 capitalize text-ink-soft">
                    {patient.sex} · {new Date().getFullYear() - patient.birth_year}
                  </td>
                  <td className="px-4 py-3">
                    {patient.conditions.length === 0 ? (
                      <span className="text-ink-muted">—</span>
                    ) : (
                      patient.conditions.map((c) => (
                        <span key={c} className="mr-1">
                          <Badge kind="high">{c.replace(/_/g, " ")}</Badge>
                        </span>
                      ))
                    )}
                  </td>
                  <td className="px-4 py-3 text-ink-soft">
                    {account_email ?? <Badge kind="none">no login</Badge>}
                  </td>
                  <td className="px-4 py-3 text-ink-muted">
                    {new Date(patient.created_at).toLocaleDateString()}
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
