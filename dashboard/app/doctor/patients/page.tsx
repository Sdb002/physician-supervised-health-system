"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, Patient } from "@/lib/api";
import { conditionName } from "@/lib/clinical-terms";
import { pid } from "@/lib/format";
import { useT } from "@/lib/use-t";
import { IconPlus, IconUsers } from "@/components/icons";
import {
  Avatar,
  Badge,
  EmptyState,
  ErrorNote,
  PageHeader,
  SearchInput,
  Skeleton,
  buttonPrimary,
  linkButton,
} from "@/components/ui";

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[] | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { t, n, lang } = useT();

  useEffect(() => {
    api.listPatients().then(setPatients).catch((e) => setError(e.message));
  }, []);

  const visible = useMemo(() => {
    if (patients === null) return null;
    const q = query.trim().toLowerCase();
    if (!q) return patients;
    return patients.filter((p) =>
      [p.name, pid(p.id), String(p.id), ...p.conditions.flatMap((c) => [conditionName(c), conditionName(c, "bn")])]
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [patients, query]);

  if (error) return <ErrorNote message={error} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("Patients")}
        subtitle={patients ? t("{count} registered", { count: patients.length }) : undefined}
        action={
          <Link href="/doctor/patients/new" className={buttonPrimary}>
            <IconPlus className="h-4 w-4" /> {t("New patient")}
          </Link>
        }
      />

      {patients !== null && patients.length > 0 && (
        <SearchInput value={query} onChange={setQuery} placeholder={t("Search by name, PID or condition")} />
      )}

      {visible === null ? (
        <Skeleton className="h-48" />
      ) : visible.length === 0 ? (
        <EmptyState
          title={query ? t("No patients match your search") : t("No patients yet")}
          hint={query ? t("Try a different name, PID or condition.") : t("Register your first patient to start an intake.")}
          icon={<IconUsers className="h-5 w-5" />}
          action={
            !query && (
              <Link href="/doctor/patients/new" className={buttonPrimary}>
                <IconPlus className="h-4 w-4" /> {t("New patient")}
              </Link>
            )
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-160 text-left text-sm">
            <thead className="border-b border-line bg-surface-soft text-ink-muted">
              <tr>
                <th scope="col" className="px-5 py-3 font-semibold">{t("Patient")}</th>
                <th scope="col" className="px-4 py-3 font-semibold">{t("Sex, age")}</th>
                <th scope="col" className="px-4 py-3 font-semibold">{t("Known conditions")}</th>
                <th scope="col" className="px-5 py-3"><span className="sr-only">{t("Actions")}</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {visible.map((p) => (
                <tr key={p.id} className="hover:bg-surface-soft">
                  <td className="px-5 py-3">
                    <Link href={`/doctor/patients/${p.id}`} className="group flex items-center gap-3">
                      <Avatar name={p.name} />
                      <span>
                        <span className="block font-semibold text-ink group-hover:text-clinical group-hover:underline">
                          {p.name}
                        </span>
                        <span className="block text-ink-muted">{pid(p.id)}</span>
                      </span>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-ink-soft">
                    {t(p.sex === "male" ? "Male" : "Female")}, {n(new Date().getFullYear() - p.birth_year)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {p.pregnant && <Badge kind="flag">{t("Pregnant")}</Badge>}
                      {p.conditions.length === 0 && !p.pregnant ? (
                        <span className="text-ink-muted">{t("None")}</span>
                      ) : (
                        p.conditions.map((c) => (
                          <Badge key={c} kind="condition">
                            {conditionName(c, lang)}
                          </Badge>
                        ))
                      )}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-5 py-3 text-right">
                    <Link href={`/doctor/patients/${p.id}/intake`} className={linkButton}>
                      {t("New visit")}
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
