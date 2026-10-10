"use client";

import { ACTIVITY_OPTIONS, Option, TRIMESTER_OPTIONS } from "@/lib/patient-options";
import { Field, checkboxClass, inputClass } from "@/components/ui";

/* The parts of a patient record every patient form asks for the same way:
 * the staff's new-patient and edit forms, and the patient's own registration. */

/** A row-sized checkbox target: the whole row toggles, not just the 16px box. */
export const choiceRow =
  "flex cursor-pointer items-center gap-3 rounded-lg border border-line px-3 py-2.5 text-sm text-ink-strong " +
  "has-[:checked]:border-clinical has-[:checked]:bg-clinical-tint hover:bg-surface-soft";

/** Tick boxes over a list of keys: conditions, dietary restrictions. */
export function OptionChecks({
  options,
  value,
  onChange,
}: {
  options: Option[];
  value: string[];
  onChange: (next: string[]) => void;
}) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {options.map((o) => (
        <label key={o.key} className={choiceRow}>
          <input
            type="checkbox"
            className={checkboxClass}
            checked={value.includes(o.key)}
            onChange={(e) => onChange(e.target.checked ? [...value, o.key] : value.filter((x) => x !== o.key))}
          />
          <span>
            {o.label}
            {o.hint && <span className="block text-xs text-ink-muted">{o.hint}</span>}
          </span>
        </label>
      ))}
    </div>
  );
}

/** Pregnancy and, once ticked, the trimester: the trimester sets the extra
 * energy the plan adds, and none is added while it is not recorded. */
export function PregnancyFields({
  pregnant,
  trimester,
  onChange,
  label,
  hint,
  trimesterLabel = "Trimester",
  notRecorded = "Not recorded",
}: {
  pregnant: boolean;
  trimester: number | null;
  onChange: (next: { pregnant: boolean; pregnancy_trimester: number | null }) => void;
  label: string;
  hint?: string;
  trimesterLabel?: string;
  notRecorded?: string;
}) {
  return (
    <div className="space-y-3">
      <label className={choiceRow}>
        <input
          type="checkbox"
          className={checkboxClass}
          checked={pregnant}
          onChange={(e) =>
            onChange({ pregnant: e.target.checked, pregnancy_trimester: e.target.checked ? trimester : null })
          }
        />
        <span>
          {label}
          {hint && <span className="block text-xs text-ink-muted">{hint}</span>}
        </span>
      </label>
      {pregnant && (
        <Field label={trimesterLabel} hint="Sets the extra energy the plan adds; none is added until it is recorded.">
          <select
            className={inputClass}
            value={trimester ?? ""}
            onChange={(e) =>
              onChange({ pregnant, pregnancy_trimester: e.target.value ? Number(e.target.value) : null })
            }
          >
            <option value="">{notRecorded}</option>
            {TRIMESTER_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>{o.label}</option>
            ))}
          </select>
        </Field>
      )}
    </div>
  );
}

/** A usual day's activity, for the energy target. */
export function ActivityField({
  value,
  onChange,
  label = "Daily activity",
  hint = "Sets the energy target. Left unrecorded, light activity is assumed and the report says so.",
  notRecorded = "Not recorded",
}: {
  value: string | null;
  onChange: (next: string | null) => void;
  label?: string;
  hint?: string;
  notRecorded?: string;
}) {
  return (
    <Field label={label} hint={hint}>
      <select className={inputClass} value={value ?? ""} onChange={(e) => onChange(e.target.value || null)}>
        <option value="">{notRecorded}</option>
        {ACTIVITY_OPTIONS.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label}: {o.hint}
          </option>
        ))}
      </select>
    </Field>
  );
}
