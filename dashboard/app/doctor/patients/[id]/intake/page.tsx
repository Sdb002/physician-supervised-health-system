"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, OcrResult, Patient } from "@/lib/api";
import {
  Card,
  ErrorNote,
  Field,
  buttonPrimary,
  buttonSecondary,
  inputClass,
} from "@/components/ui";

const BIOMARKERS = [
  {
    key: "fasting_glucose",
    label: "Fasting glucose",
    unit: "mg/dL",
    normal: "70–99 normal · 100–125 prediabetes · ≥126 diabetes range (ADA)",
  },
  {
    key: "systolic_bp",
    label: "Systolic blood pressure",
    unit: "mmHg",
    normal: "<120 normal · 130–139 stage 1 · ≥140 stage 2 (ACC/AHA)",
  },
  {
    key: "diastolic_bp",
    label: "Diastolic blood pressure",
    unit: "mmHg",
    normal: "<80 normal · 80–89 stage 1 · ≥90 stage 2 (ACC/AHA)",
  },
  {
    key: "hemoglobin",
    label: "Hemoglobin",
    unit: "g/dL",
    normal: "normal ≥13 (men) / ≥12 (women) / ≥11 (pregnancy) (WHO)",
  },
] as const;

type BiomarkerKey = (typeof BIOMARKERS)[number]["key"];

export default function IntakePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);

  const [patient, setPatient] = useState<Patient | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [weight, setWeight] = useState("");
  const [values, setValues] = useState<Record<BiomarkerKey, string>>({
    fasting_glucose: "",
    systolic_bp: "",
    diastolic_bp: "",
    hemoglobin: "",
  });
  const [ocrState, setOcrState] = useState<"idle" | "running" | "done" | "unavailable">("idle");
  const [ocrNotes, setOcrNotes] = useState("");
  const [ocrRaw, setOcrRaw] = useState<OcrResult | null>(null);

  useEffect(() => {
    api.getPatient(id).then(setPatient).catch((e) => setError(e.message));
  }, [id]);

  const runOcr = async (file: File) => {
    setOcrState("running");
    setError(null);
    try {
      const result = await api.ocr(file);
      setOcrRaw(result);
      setValues((v) => {
        const next = { ...v };
        for (const b of BIOMARKERS) {
          const extracted = result.biomarkers[b.key];
          if (extracted != null) next[b.key] = String(extracted);
        }
        return next;
      });
      setOcrNotes(result.notes);
      setOcrState("done");
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setOcrState("unavailable");
      } else {
        setOcrState("idle");
        setError((err as Error).message);
      }
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const biomarkers = Object.fromEntries(
        Object.entries(values)
          .filter(([, v]) => v !== "")
          .map(([k, v]) => [k, Number(v)])
      );
      const assessment = await api.createVisit(id, {
        weight_kg: Number(weight),
        biomarkers,
        ocr_raw: ocrRaw,
      });
      router.push(`/doctor/review/${assessment.id}`);
    } catch (err) {
      setError((err as Error).message);
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <p className="text-sm text-ink-muted">
          <Link href={`/doctor/patients/${id}`} className="hover:underline">
            {patient ? patient.name : `Patient #${id}`}
          </Link>{" "}
          / new visit
        </p>
        <h1 className="text-2xl font-bold">Intake</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Enter today&apos;s measurements. Leave a field empty if it wasn&apos;t
          measured — the assessment scores only what you enter.
        </p>
      </div>

      {error && <ErrorNote message={error} />}

      <Card title="Prefill from lab report (optional)">
        <p className="mb-3 text-sm text-ink-muted">
          Upload a photo of the lab report and AI will read the values into the
          form. <strong>You confirm every value before submitting</strong> —
          nothing is scored until you do.
        </p>
        <input
          ref={fileInput}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && runOcr(e.target.files[0])}
        />
        <button
          type="button"
          className={buttonSecondary}
          disabled={ocrState === "running"}
          onClick={() => fileInput.current?.click()}
        >
          {ocrState === "running" ? "Reading report…" : "Upload lab report image"}
        </button>
        {ocrState === "done" && (
          <p className="mt-2 text-sm text-emerald-700">
            Values prefilled below — please verify each one against the report.
            {ocrNotes && (
              <span className="mt-1 block text-amber-700">OCR notes: {ocrNotes}</span>
            )}
          </p>
        )}
        {ocrState === "unavailable" && (
          <p className="mt-2 text-sm text-ink-muted">
            OCR is not configured on the server (no API key). Manual entry below
            works exactly the same.
          </p>
        )}
      </Card>

      <form onSubmit={submit}>
        <Card title="Measurements">
          <div className="space-y-4">
            <Field label="Weight (kg)">
              <input
                className={inputClass}
                type="number"
                step="0.1"
                min={3}
                max={350}
                required
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
              />
            </Field>

            {BIOMARKERS.map((b) => (
              <Field key={b.key} label={`${b.label} (${b.unit})`} hint={b.normal}>
                <input
                  className={inputClass}
                  type="number"
                  step="0.1"
                  value={values[b.key]}
                  onChange={(e) =>
                    setValues((v) => ({ ...v, [b.key]: e.target.value }))
                  }
                  placeholder="not measured"
                />
              </Field>
            ))}

            <button type="submit" disabled={saving || !weight} className={buttonPrimary + " w-full"}>
              {saving ? "Generating assessment…" : "Submit & generate assessment"}
            </button>
            <p className="text-center text-xs text-ink-muted">
              A deterministic assessment is generated instantly and waits for
              your review — the patient sees nothing until you approve it.
            </p>
          </div>
        </Card>
      </form>
    </div>
  );
}
