import { ReactNode } from "react";
import { IconSearch } from "@/components/icons";

/** Keyboard-only focus indicator. `focus-visible` rather than `focus` so a
 * mouse click doesn't leave a ring behind, while Tab stays traceable. Uses
 * `outline` rather than `ring`: outlines follow the border radius and, unlike
 * box-shadow rings, survive Windows forced-colors / high-contrast mode. */
export const focusRing =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-clinical";

/** Focus ring for destructive controls - same geometry, danger colour. */
export const focusRingDanger =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-600 dark:focus-visible:outline-rose-400";

const RISK_STYLES: Record<string, string> = {
  none: "bg-canvas text-ink-soft",
  low: "bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-200",
  moderate: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  critical: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  approved: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  active: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  rejected: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
  admin: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-200",
  doctor: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-200",
  patient: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200",
};

export function Badge({ kind, children }: { kind: string; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        RISK_STYLES[kind] ?? "bg-canvas text-ink-soft"
      }`}
    >
      {children}
    </span>
  );
}

export function Card({
  title,
  children,
  action,
  className,
}: {
  title?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-line bg-surface p-5 shadow-sm ${className ?? ""}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const STAT_TONES: Record<string, string> = {
  slate: "bg-canvas text-ink-soft",
  teal: "bg-teal-50 text-teal-600 dark:bg-teal-950 dark:text-teal-300",
  indigo: "bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300",
  emerald: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-300",
  amber: "bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-300",
  rose: "bg-rose-50 text-rose-600 dark:bg-rose-950 dark:text-rose-300",
  sky: "bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-300",
};

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = "slate",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  tone?: keyof typeof STAT_TONES;
}) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-ink-muted">{label}</p>
          {/* div, not p: value can be a Skeleton (a div), which a <p> can't legally contain */}
          <div className="mt-1.5 text-3xl font-bold tabular-nums tracking-tight text-ink">{value}</div>
        </div>
        {icon && (
          <div className={`shrink-0 rounded-xl p-2.5 ${STAT_TONES[tone]}`}>{icon}</div>
        )}
      </div>
      {hint && <div className="mt-2 text-xs text-ink-muted">{hint}</div>}
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return (
    <span
      aria-hidden="true"
      className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-line text-sm font-semibold text-ink-soft ${className ?? ""}`}
    >
      {initials || "?"}
    </span>
  );
}

export function SearchInput({
  value,
  onChange,
  placeholder,
  label,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  /** Accessible name. The wrapping <label> holds only an icon, so without
   * this the field's only name is its placeholder - which some screen
   * readers skip, and which disappears as soon as the user types. */
  label?: string;
}) {
  return (
    <label className="relative block w-full max-w-xs">
      <span className="sr-only">{label ?? placeholder ?? "Search"}</span>
      <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder ?? "Search…"}
        className="w-full rounded-lg border border-line-strong bg-surface py-2 pl-9 pr-3 text-sm shadow-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-100"
      />
    </label>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-lg bg-line/70 ${className ?? "h-4 w-full"}`}
    />
  );
}

export function EmptyState({ title, hint, icon }: { title: string; hint?: string; icon?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line-strong bg-surface-soft p-10 text-center">
      {icon && <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-surface text-ink-muted shadow-sm">{icon}</div>}
      <p className="font-medium text-ink-soft">{title}</p>
      {hint && <p className="mt-1 text-sm text-ink-muted">{hint}</p>}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200"
    >
      {message}
    </div>
  );
}

export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <div
      role="status"
      className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200"
    >
      {children}
    </div>
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink-strong">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink-muted">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "mt-1 block w-full rounded-lg border border-line-strong bg-surface px-3 py-2 text-sm shadow-sm " +
  "focus:border-clinical focus:outline-none focus:ring-2 focus:ring-teal-100 dark:focus:ring-teal-900";

export const buttonPrimary =
  "inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-clinical px-4 py-2 text-sm font-medium text-on-clinical " +
  "shadow-sm transition-colors duration-200 hover:bg-clinical-hover " +
  "disabled:cursor-not-allowed disabled:opacity-50 " +
  focusRing;

export const buttonSecondary =
  "inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg border border-line-strong bg-surface px-4 py-2 text-sm " +
  "font-medium text-ink-strong shadow-sm transition-colors duration-200 hover:bg-surface-soft " +
  "disabled:cursor-not-allowed disabled:opacity-50 " +
  focusRing;

export const buttonDanger =
  "inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg border border-rose-200 bg-surface px-4 py-2 text-sm " +
  "font-medium text-rose-700 shadow-sm transition-colors duration-200 hover:bg-rose-50 " +
  "dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950 " +
  "disabled:cursor-not-allowed disabled:opacity-50 " +
  focusRingDanger;
