"use client";

import { ACTIVITY_OPTIONS, Option, TRIMESTER_OPTIONS } from "@/lib/patient-options";
import { Field, checkboxClass, inputClass } from "@/components/ui";
import { useT } from "@/lib/use-t";

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
  const { t } = useT();
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
            {t(o.label)}
            {o.hint && <span className="block text-xs text-ink-muted">{t(o.hint)}</span>}
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
  trimesterLabel,
  notRecorded,
}: {
  pregnant: boolean;
  trimester: number | null;
  onChange: (next: { pregnant: boolean; pregnancy_trimester: number | null }) => void;
  label: string;
  hint?: string;
  trimesterLabel?: string;
  notRecorded?: string;
}) {
  const { t } = useT();
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
        <Field
          label={trimesterLabel ?? t("Trimester")}
          hint={t("Sets the extra energy the plan adds; none is added until it is recorded.")}
        >
          <select
            className={inputClass}
            value={trimester ?? ""}
            onChange={(e) =>
              onChange({ pregnant, pregnancy_trimester: e.target.value ? Number(e.target.value) : null })
            }
          >
            <option value="">{notRecorded ?? t("Not recorded")}</option>
            {TRIMESTER_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>{t(o.label)}</option>
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
  label,
  hint,
  notRecorded,
}: {
  value: string | null;
  onChange: (next: string | null) => void;
  label?: string;
  hint?: string;
  notRecorded?: string;
}) {
  const { t } = useT();
  return (
    <Field
      label={label ?? t("Daily activity")}
      hint={hint ?? t("Sets the energy target. Left unrecorded, light activity is assumed and the report says so.")}
    >
      <select className={inputClass} value={value ?? ""} onChange={(e) => onChange(e.target.value || null)}>
        <option value="">{notRecorded ?? t("Not recorded")}</option>
        {ACTIVITY_OPTIONS.map((o) => (
          <option key={o.key} value={o.key}>
            {t(o.label)}: {t(o.hint ?? "")}
          </option>
        ))}
      </select>
    </Field>
  );
}
