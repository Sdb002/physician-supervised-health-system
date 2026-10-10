"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Patient, Visit } from "@/lib/api";
import { formatDate } from "@/lib/clinical-terms";
import { bmi, pid } from "@/lib/format";
import { IconPlus } from "@/components/icons";
import {
  Card,
  EmptyState,
  ErrorNote,
  Field,
  PageHeader,
  PatientBanner,
  Skeleton,
  buttonPrimary,
  buttonSecondary,
  inputClass,
  linkButton,
} from "@/components/ui";
import { TREND_COLOR_PRIMARY, TREND_COLOR_SECONDARY, TrendPoint } from "@/components/trend-chart";
import { TrendChartCard } from "@/components/trend-chart-card";

const BIOMARKER_COLUMNS: { key: string; label: string; unit: string }[] = [
  { key: "fasting_glucose", label: "Glucose", unit: "mg/dL" },
  { key: "systolic_bp", label: "Systolic", unit: "mmHg" },
  { key: "diastolic_bp", label: "Diastolic", unit: "mmHg" },
  { key: "hemoglobin", label: "Hb", unit: "g/dL" },
];

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visits, setVisits] = useState<Visit[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accountEmail, setAccountEmail] = useState<string | null>(null);
  const [accountLoaded, setAccountLoaded] = useState(false);
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [accountForm, setAccountForm] = useState({ email: "", password: "" });
  const [accountError, setAccountError] = useState<string | null>(null);
  const [accountSaving, setAccountSaving] = useState(false);

  useEffect(() => {
    Promise.all([api.getPatient(id), api.listVisits(id), api.getPatientAccount(id)])
      .then(([p, v, a]) => {
        setPatient(p);
        setVisits(v);
        setAccountEmail(a.email);
        setAccountLoaded(true);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const createAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setAccountSaving(true);
    setAccountError(null);
    try {
      const user = await api.createPatientAccount(id, accountForm);
      setAccountEmail(user.email);
      setShowAccountForm(false);
    } catch (err) {
      setAccountError((err as Error).message);
    } finally {
      setAccountSaving(false);
    }
  };

  if (error) return <ErrorNote message={error} />;
  if (!patient) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  const age = new Date().getFullYear() - patient.birth_year;
  const latestWeight = visits?.[0]?.weight_kg;

  const chronological = visits ? [...visits].reverse() : [];
  const trendPoints: TrendPoint[] = chronological.map((v) => ({
    date: formatDate(v.created_at, "en", false),
    values: {
      weight: v.weight_kg,
      bmi: Math.round(bmi(v.weight_kg, patient.height_cm) * 10) / 10,
      systolic: v.biomarkers.systolic_bp,
      diastolic: v.biomarkers.diastolic_bp,
    },
  }));

  return (
    <div className="space-y-6">
      <PageHeader title="Patient record" back={{ href: "/doctor/patients", label: "Patients" }} />

      <PatientBanner
        name={patient.name}
        id={pid(patient.id)}
        sex={patient.sex}
        age={age}
        heightCm={patient.height_cm}
        weightKg={latestWeight}
        pregnant={patient.pregnant}
        conditions={patient.conditions}
        action={
          <Link href={`/doctor/patients/${patient.id}/intake`} className={buttonPrimary}>
            <IconPlus className="h-4 w-4" /> New visit
          </Link>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card
            title="Visits"
            description="Newest first. Open a visit's report to read or print it."
            flush={visits !== null && visits.length > 0}
          >
            {visits === null ? (
              <Skeleton className="h-24" />
            ) : visits.length === 0 ? (
              <EmptyState
                title="No visits yet"
                hint="Start an intake to record measurements and generate an assessment."
                inset
                action={
                  <Link href={`/doctor/patients/${patient.id}/intake`} className={buttonPrimary}>
                    Start intake
                  </Link>
                }
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-xl text-left text-sm">
                  <thead className="border-b border-line bg-surface-soft text-ink-muted">
                    <tr>
                      <th scope="col" className="px-5 py-2.5 font-semibold">Date</th>
                      <th scope="col" className="px-3 py-2.5 text-right font-semibold">Weight</th>
                      {BIOMARKER_COLUMNS.map((c) => (
                        <th key={c.key} scope="col" className="px-3 py-2.5 text-right font-semibold">
                          {c.label}
                          <span className="block text-xs font-normal">{c.unit}</span>
                        </th>
                      ))}
                      <th scope="col" className="px-5 py-2.5"><span className="sr-only">Report</span></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {visits.map((v) => (
                      <tr key={v.id} className="hover:bg-surface-soft">
                        <td className="whitespace-nowrap px-5 py-3 font-semibold text-ink">{formatDate(v.created_at)}</td>
                        <td className="px-3 py-3 text-right">{v.weight_kg} kg</td>
                        {BIOMARKER_COLUMNS.map((c) => (
                          <td key={c.key} className="px-3 py-3 text-right">
                            {v.biomarkers[c.key] ?? <span className="text-ink-muted">—</span>}
                          </td>
                        ))}
                        <td className="whitespace-nowrap px-5 py-3 text-right">
                          <Link href={`/doctor/reports/${v.id}`} className={linkButton}>
                            Report
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {visits !== null && visits.length > 1 && (
            <div className="grid gap-4 sm:grid-cols-3">
              <TrendChartCard
                title="Weight"
                unit="kg"
                series={[{ key: "weight", label: "Weight", color: TREND_COLOR_PRIMARY }]}
                points={trendPoints}
                emptyHint="Appears after a second visit."
              />
              <TrendChartCard
                title="BMI"
                series={[{ key: "bmi", label: "BMI", color: TREND_COLOR_PRIMARY }]}
                points={trendPoints}
                emptyHint="Appears after a second visit."
              />
              <TrendChartCard
                title="Blood pressure"
                unit="mmHg"
                series={[
                  { key: "systolic", label: "Systolic", color: TREND_COLOR_PRIMARY },
                  { key: "diastolic", label: "Diastolic", color: TREND_COLOR_SECONDARY },
                ]}
                points={trendPoints}
                emptyHint="Appears once recorded at two or more visits."
              />
            </div>
          )}
        </div>

        <div className="space-y-6">
          <Card title="Patient login">
            {!accountLoaded ? (
              <Skeleton className="h-12" />
            ) : accountEmail ? (
              <p className="text-sm text-ink-soft">
                Signs in as <strong className="break-all font-semibold text-ink">{accountEmail}</strong> to
                read approved reports.
              </p>
            ) : showAccountForm ? (
              <form onSubmit={createAccount} className="space-y-4">
                {accountError && <ErrorNote message={accountError} />}
                <Field label="Patient email">
                  <input
                    className={inputClass}
                    type="email"
                    required
                    autoComplete="off"
                    value={accountForm.email}
                    onChange={(e) => setAccountForm((a) => ({ ...a, email: e.target.value }))}
                    placeholder="patient@example.com"
                  />
                </Field>
                <Field label="Temporary password" hint="At least 8 characters. Give it to the patient.">
                  <input
                    className={inputClass}
                    type="text"
                    required
                    minLength={8}
                    autoComplete="off"
                    value={accountForm.password}
                    onChange={(e) => setAccountForm((a) => ({ ...a, password: e.target.value }))}
                  />
                </Field>
                <div className="flex gap-2">
                  <button type="submit" disabled={accountSaving} className={buttonPrimary}>
                    {accountSaving ? "Creating…" : "Create login"}
                  </button>
                  <button
                    type="button"
                    className={buttonSecondary}
                    onClick={() => {
                      setShowAccountForm(false);
                      setAccountError(null);
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-ink-soft">
                  No login yet, so this patient can&apos;t read their reports online.
                </p>
                <button className={buttonSecondary} onClick={() => setShowAccountForm(true)}>
                  Create login
                </button>
              </div>
            )}
          </Card>

          {patient.notes && (
            <Card title="Notes">
              <p className="whitespace-pre-wrap text-sm text-ink-soft">{patient.notes}</p>
            </Card>
          )}

          <Card title="Profile">
            <dl className="space-y-2.5 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-ink-muted">Year of birth</dt>
                <dd className="font-semibold text-ink">{patient.birth_year}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink-muted">Fitness level</dt>
                <dd className="font-semibold capitalize text-ink">{patient.fitness_level}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-ink-muted">Registered</dt>
                <dd className="font-semibold text-ink">{formatDate(patient.created_at)}</dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>
    </div>
  );
}
