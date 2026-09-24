"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, Patient, Visit } from "@/lib/api";
import { bmi } from "@/lib/format";
import {
  Badge,
  Card,
  EmptyState,
  ErrorNote,
  Field,
  buttonPrimary,
  buttonSecondary,
  inputClass,
} from "@/components/ui";
import { TREND_COLOR_PRIMARY, TREND_COLOR_SECONDARY, TrendPoint } from "@/components/trend-chart";
import { TrendChartCard } from "@/components/trend-chart-card";

const BIOMARKER_LABELS: Record<string, string> = {
  fasting_glucose: "Glucose (mg/dL)",
  systolic_bp: "Systolic (mmHg)",
  diastolic_bp: "Diastolic (mmHg)",
  hemoglobin: "Hb (g/dL)",
};

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
  if (!patient) return <p className="text-sm text-ink-muted">Loading…</p>;

  const age = new Date().getFullYear() - patient.birth_year;

  const chronological = visits ? [...visits].reverse() : [];
  const trendPoints: TrendPoint[] = chronological.map((v) => ({
    date: new Date(v.created_at).toLocaleDateString(undefined, { month: "numeric", day: "numeric" }),
    values: {
      weight: v.weight_kg,
      bmi: Math.round(bmi(v.weight_kg, patient.height_cm) * 10) / 10,
      systolic: v.biomarkers.systolic_bp,
      diastolic: v.biomarkers.diastolic_bp,
    },
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{patient.name}</h1>
          <p className="mt-1 text-sm text-ink-muted">
            {patient.sex === "female" ? "Female" : "Male"} · {age} years ·{" "}
            {patient.height_cm} cm · {patient.fitness_level}
            {patient.pregnant && " · pregnant"}
          </p>
          {patient.conditions.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {patient.conditions.map((c) => (
                <Badge key={c} kind="high">
                  {c.replace(/_/g, " ")}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <Link href={`/doctor/patients/${patient.id}/intake`} className={buttonPrimary}>
          + New visit / intake
        </Link>
      </div>

      {patient.notes && (
        <Card title="Notes">
          <p className="text-sm text-ink-soft">{patient.notes}</p>
        </Card>
      )}

      <Card title="Login account">
        {!accountLoaded ? (
          <p className="text-sm text-ink-muted">Loading…</p>
        ) : accountEmail ? (
          <p className="text-sm text-ink-soft">
            This patient signs in with{" "}
            <strong className="text-ink">{accountEmail}</strong> to see their visits and
            approved reports.
          </p>
        ) : showAccountForm ? (
          <form onSubmit={createAccount} className="space-y-4">
            {accountError && <ErrorNote message={accountError} />}
            <div className="grid gap-4 sm:grid-cols-2">
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
              <Field label="Temporary password" hint="At least 8 characters — share it with the patient.">
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
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={accountSaving} className={buttonPrimary}>
                {accountSaving ? "Creating…" : "Create account"}
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
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-ink-muted">
              No login yet — this patient can&apos;t sign in to see their reports.
            </p>
            <button className={buttonSecondary} onClick={() => setShowAccountForm(true)}>
              + Create login account
            </button>
          </div>
        )}
      </Card>

      {visits !== null && visits.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          <TrendChartCard
            title="Weight"
            unit="kg"
            series={[{ key: "weight", label: "Weight", color: TREND_COLOR_PRIMARY }]}
            points={trendPoints}
            emptyHint="Weight trend appears after a second visit."
          />
          <TrendChartCard
            title="BMI"
            series={[{ key: "bmi", label: "BMI", color: TREND_COLOR_PRIMARY }]}
            points={trendPoints}
            emptyHint="BMI trend appears after a second visit."
          />
          <TrendChartCard
            title="Blood pressure"
            unit="mmHg"
            series={[
              { key: "systolic", label: "Systolic", color: TREND_COLOR_PRIMARY },
              { key: "diastolic", label: "Diastolic", color: TREND_COLOR_SECONDARY },
            ]}
            points={trendPoints}
            emptyHint="Blood pressure trend appears once it's been recorded at two or more visits."
          />
        </div>
      )}

      <Card title="Visit history">
        {visits === null ? (
          <p className="text-sm text-ink-muted">Loading…</p>
        ) : visits.length === 0 ? (
          <EmptyState
            title="No visits yet"
            hint="Start an intake to record biomarkers and generate an assessment."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-line text-xs uppercase tracking-wide text-ink-muted">
                <tr>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Weight</th>
                  {Object.values(BIOMARKER_LABELS).map((label) => (
                    <th key={label} className="px-3 py-2">{label}</th>
                  ))}
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {visits.map((v) => (
                  <tr key={v.id}>
                    <td className="px-3 py-2">{new Date(v.created_at).toLocaleDateString()}</td>
                    <td className="px-3 py-2">{v.weight_kg} kg</td>
                    {Object.keys(BIOMARKER_LABELS).map((key) => (
                      <td key={key} className="px-3 py-2">
                        {v.biomarkers[key] ?? <span className="text-ink-muted">—</span>}
                      </td>
                    ))}
                    <td className="px-3 py-2 text-right">
                      <Link
                        href={`/doctor/reports/${v.id}`}
                        className="font-medium text-teal-700 hover:underline"
                      >
                        Report →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
