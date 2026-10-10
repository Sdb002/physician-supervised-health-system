"use client";

import { useEffect, useMemo, useState } from "react";
import { api, Patient } from "@/lib/api";
import { conditionName, formatDate } from "@/lib/clinical-terms";
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
        subtitle={rows ? `${rows.length} registered patients` : undefined}
        action={
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search name, PID, email"
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
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-surface-soft text-ink-muted">
              <tr>
                <th scope="col" className="px-5 py-3 font-semibold">Patient</th>
                <th scope="col" className="px-4 py-3 font-semibold">Sex, age</th>
                <th scope="col" className="px-4 py-3 font-semibold">Conditions</th>
                <th scope="col" className="px-4 py-3 font-semibold">Login</th>
                <th scope="col" className="px-4 py-3 font-semibold">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map(({ patient, account_email }) => (
                <tr key={patient.id} className="hover:bg-surface-soft">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={patient.name} />
                      <span>
                        <span className="block font-semibold text-ink">{patient.name}</span>
                        <span className="block text-ink-muted">{pid(patient.id)}</span>
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 capitalize text-ink-soft">
                    {patient.sex}, {new Date().getFullYear() - patient.birth_year}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {patient.pregnant && <Badge kind="flag">Pregnant</Badge>}
                      {patient.conditions.length === 0 && !patient.pregnant ? (
                        <span className="text-ink-muted">None</span>
                      ) : (
                        patient.conditions.map((c) => (
                          <Badge key={c} kind="condition">
                            {conditionName(c)}
                          </Badge>
                        ))
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-ink-soft">
                    {account_email ?? <span className="text-ink-muted">No login</span>}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-ink-muted">
                    {formatDate(patient.created_at)}
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
