"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api, ApiError, OcrResult, Patient } from "@/lib/api";
import { pid } from "@/lib/format";
import { useT } from "@/lib/use-t";
import { IconCheck, IconFileText, IconSparkles } from "@/components/icons";
import {
  ErrorNote,
  PageHeader,
  PatientBanner,
  Skeleton,
  buttonPrimary,
  buttonSecondary,
  inputClass,
} from "@/components/ui";

/* Reference wording shown next to each field so the cutoffs the engine
 * applies are visible at the moment of entry. Display text only - the
 * engine reads its thresholds from data/reference/*.yaml. */
const BIOMARKERS = [
  {
    key: "fasting_glucose",
    label: "Fasting glucose",
    unit: "mg/dL",
    normal: "70–99 normal, 100–125 prediabetes, 126+ diabetes range (ADA)",
  },
  {
    key: "systolic_bp",
    label: "Systolic blood pressure",
    unit: "mmHg",
    normal: "Under 120 normal, 130–139 stage 1, 140+ stage 2 (ACC/AHA)",
  },
  {
    key: "diastolic_bp",
    label: "Diastolic blood pressure",
    unit: "mmHg",
    normal: "Under 80 normal, 80–89 stage 1, 90+ stage 2 (ACC/AHA)",
  },
  {
    key: "hemoglobin",
    label: "Haemoglobin",
    unit: "g/dL",
    normal: "Normal from 13 (men), 12 (women), 11 (pregnancy) (WHO)",
  },
] as const;

type BiomarkerKey = (typeof BIOMARKERS)[number]["key"];

/** A number field with its unit set inside the box, as on a lab slip. */
function MeasureInput({
  id,
  unit,
  value,
  onChange,
  required,
  min,
  max,
  placeholder,
  prefilled,
}: {
  id: string;
  unit: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  min?: number;
  max?: number;
  placeholder?: string;
  prefilled?: boolean;
}) {
  return (
    <div className="relative mt-1.5">
      <input
        id={id}
        className={`${inputClass} mt-0! pr-16 ${prefilled ? "border-clinical bg-clinical-tint" : ""}`}
        type="number"
        inputMode="decimal"
        step="0.1"
        min={min}
        max={max}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-ink-muted">
        {unit}
      </span>
    </div>
  );
}

export default function IntakePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const fileInput = useRef<HTMLInputElement>(null);
  const { t } = useT();

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
  const [prefilled, setPrefilled] = useState<Set<string>>(new Set());
  const [ocrState, setOcrState] = useState<"idle" | "running" | "done" | "unavailable">("idle");
  const [ocrNotes, setOcrNotes] = useState("");
  const [ocrFound, setOcrFound] = useState(0);
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
      const extracted = BIOMARKERS.filter((b) => result.biomarkers[b.key] != null).map((b) => b.key);
      setValues((v) => {
        const next = { ...v };
        for (const key of extracted) next[key] = String(result.biomarkers[key]);
        return next;
      });
      setPrefilled(new Set(extracted));
      setOcrNotes(result.notes);
      setOcrFound(extracted.length);
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
    <div className="space-y-6">
      <PageHeader
        title={t("New visit")}
        subtitle={t("Enter today's measurements. Leave a field empty if it wasn't measured; the assessment scores only what you enter.")}
        back={{ href: `/doctor/patients/${id}`, label: patient ? patient.name : t("Patient record") }}
      />

      {patient ? (
        <PatientBanner
          name={patient.name}
          id={pid(patient.id)}
          sex={patient.sex}
          age={new Date().getFullYear() - patient.birth_year}
          heightCm={patient.height_cm}
          pregnant={patient.pregnant}
          conditions={patient.conditions}
        />
      ) : (
        <Skeleton className="h-20" />
      )}

      {error && <ErrorNote message={error} />}

      <div className="grid items-start gap-6 lg:grid-cols-[1fr_20rem]">
        <form onSubmit={submit} className="rounded-xl border border-line bg-surface">
          <div className="border-b border-line px-5 py-4">
            <h2 className="font-display text-lg font-bold leading-7 text-ink">{t("Measurements")}</h2>
          </div>
          <div className="divide-y divide-line">
            <div className="grid gap-x-6 gap-y-1 px-5 py-4 sm:grid-cols-[1fr_12rem] sm:items-center">
              <label htmlFor="weight" className="font-semibold text-ink">
                {t("Weight")} <span className="font-normal text-ink-muted">{t("(required)")}</span>
              </label>
              <MeasureInput id="weight" unit="kg" value={weight} onChange={setWeight} required min={3} max={350} />
            </div>
            {BIOMARKERS.map((b) => (
              <div key={b.key} className="grid gap-x-6 gap-y-1 px-5 py-4 sm:grid-cols-[1fr_12rem] sm:items-center">
                <div>
                  <label htmlFor={b.key} className="font-semibold text-ink">
                    {t(b.label)}
                  </label>
                  <p className="text-sm text-ink-muted">{t(b.normal)}</p>
                </div>
                <MeasureInput
                  id={b.key}
                  unit={b.unit}
                  value={values[b.key]}
                  onChange={(v) => {
                    setValues((prev) => ({ ...prev, [b.key]: v }));
                    setPrefilled((p) => {
                      const next = new Set(p);
                      next.delete(b.key);
                      return next;
                    });
                  }}
                  placeholder={t("Not measured")}
                  prefilled={prefilled.has(b.key)}
                />
              </div>
            ))}
          </div>
          <div className="flex flex-col gap-3 border-t border-line bg-surface-soft px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-ink-muted">
              {t("The assessment is created instantly and waits for your review. The patient sees nothing until you approve it.")}
            </p>
            <button type="submit" disabled={saving || !weight} className={`${buttonPrimary} shrink-0`}>
              {saving ? t("Creating assessment…") : t("Create assessment")}
            </button>
          </div>
        </form>

        <aside className="rounded-xl border border-line bg-surface p-5">
          <h2 className="flex items-center gap-2 text-base font-semibold text-ink">
            <IconSparkles className="h-4.5 w-4.5 text-clinical" />
            {t("Fill from a lab slip")}
          </h2>
          <p className="mt-1.5 text-sm text-ink-soft">
            {t("Upload a photo of the lab report, or the PDF the lab sent, and the values are read into the form. Check each one against the slip before you submit.")}
          </p>
          <input
            ref={fileInput}
            type="file"
            accept="image/png,image/jpeg,image/webp,application/pdf"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && runOcr(e.target.files[0])}
          />
          <button
            type="button"
            className={`${buttonSecondary} mt-4 w-full`}
            disabled={ocrState === "running"}
            onClick={() => fileInput.current?.click()}
          >
            <IconFileText className="h-4 w-4" />
            {ocrState === "running" ? t("Reading the slip…") : t("Upload lab slip photo or PDF")}
          </button>
          {ocrState === "done" && (
            <div className="mt-3 space-y-2 text-sm">
              {ocrFound > 0 ? (
                <p className="flex items-start gap-1.5 text-ok-ink">
                  <IconCheck className="mt-0.5 h-4 w-4 shrink-0" />
                  {t("Values filled in and highlighted. Check each one against the slip.")}
                </p>
              ) : (
                <p className="text-watch-ink">{t("No values could be read from this photo. Type them in from the slip.")}</p>
              )}
              {ocrNotes && <p className="text-watch-ink">{t("Reader notes: {notes}", { notes: ocrNotes })}</p>}
              {ocrRaw?.engine && (
                <p className="text-xs text-ink-muted">
                  {ocrRaw.engine === "PDF text"
                    ? t("Read from the PDF's own text, on this server.")
                    : ocrRaw.engine === "RapidOCR"
                      ? t("Read by RapidOCR, on this server.")
                      : t("Read by {engine}.", { engine: ocrRaw.engine })}
                </p>
              )}
            </div>
          )}
          {ocrState === "unavailable" && (
            <p className="mt-3 text-sm text-ink-muted">
              {t("Lab-slip reading isn't set up on this server. Typing the values works the same.")}
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
