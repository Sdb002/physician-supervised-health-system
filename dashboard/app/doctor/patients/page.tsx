"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Patient } from "@/lib/api";
import { IconPlus, IconUsers } from "@/components/icons";
import { Badge, EmptyState, ErrorNote, PageHeader, Skeleton, buttonPrimary } from "@/components/ui";

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listPatients().then(setPatients).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Patients"
        subtitle={patients ? `${patients.length} registered` : "Loading…"}
        action={
          <Link href="/doctor/patients/new" className={buttonPrimary}>
            <IconPlus className="h-4 w-4" /> New patient
          </Link>
        }
      />

      {patients === null && <Skeleton className="h-48" />}

      {patients && patients.length === 0 && (
        <EmptyState
          title="No patients yet"
          hint="Register your first patient to start an intake."
          icon={<IconUsers className="h-5 w-5" />}
        />
      )}

      {patients && patients.length > 0 && (
        <div className="overflow-x-auto rounded-2xl border border-line bg-surface shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-ink-muted">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Sex</th>
                <th className="px-4 py-3">Age</th>
                <th className="px-4 py-3">Known conditions</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {patients.map((p) => (
                <tr key={p.id} className="hover:bg-surface-soft">
                  <td className="px-4 py-3 font-medium">
                    {p.name}
                    {p.pregnant && (
                      <span className="ml-2">
                        <Badge kind="moderate">pregnant</Badge>
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 capitalize">{p.sex}</td>
                  <td className="px-4 py-3">{new Date().getFullYear() - p.birth_year}</td>
                  <td className="px-4 py-3">
                    {p.conditions.length === 0 ? (
                      <span className="text-ink-muted">—</span>
                    ) : (
                      p.conditions.map((c) => (
                        <span key={c} className="mr-1">
                          <Badge kind="high">{c.replace(/_/g, " ")}</Badge>
                        </span>
                      ))
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      href={`/doctor/patients/${p.id}`}
                      className="font-medium text-teal-700 hover:underline"
                    >
                      Open &rarr;
                    </Link>
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
