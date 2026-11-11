"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { conditionName } from "@/lib/clinical-terms";
import { useT } from "@/lib/use-t";
import { IconChevronLeft, IconSearch } from "@/components/icons";

/** Keyboard-only focus indicator. `focus-visible` rather than `focus` so a
 * mouse click doesn't leave a ring behind, while Tab stays traceable. Uses
 * `outline` rather than `ring`: outlines follow the border radius and, unlike
 * box-shadow rings, survive Windows forced-colors / high-contrast mode. */
export const focusRing =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-clinical";

/** Focus ring for destructive controls - same geometry, danger colour. */
export const focusRingDanger =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-crit-mark";

/* ---------------------------------------------------------------------------
 * Status vocabulary. Clinical risk and review state use the status families;
 * roles and diagnoses are facts, not findings, so they stay neutral - a
 * patient's "diabetes" chip must not look like an alarm on every screen.
 * ------------------------------------------------------------------------ */
const BADGE_STYLES: Record<string, string> = {
  none: "border-ok-line bg-ok-tint text-ok-ink",
  low: "border-low-line bg-low-tint text-low-ink",
  moderate: "border-watch-line bg-watch-tint text-watch-ink",
  high: "border-high-line bg-high-tint text-high-ink",
  critical: "border-crit-line bg-crit-tint text-crit-ink",
  pending: "border-watch-line bg-watch-tint text-watch-ink",
  approved: "border-ok-line bg-ok-tint text-ok-ink",
  active: "border-ok-line bg-ok-tint text-ok-ink",
  rejected: "border-crit-line bg-crit-tint text-crit-ink",
  flag: "border-watch-line bg-watch-tint text-watch-ink",
  condition: "border-line-strong bg-surface text-ink-strong",
  admin: "border-line bg-surface-soft text-ink-soft",
  doctor: "border-line bg-surface-soft text-ink-soft",
  patient: "border-line bg-surface-soft text-ink-soft",
  info: "border-line bg-surface-soft text-ink-soft",
};

/** Kinds that carry clinical or review status get a leading mark, so the
 * chip differs in shape as well as colour from a neutral fact chip. */
const MARK: Record<string, string> = {
  none: "bg-ok-mark",
  low: "bg-low-mark",
  moderate: "bg-watch-mark",
  high: "bg-high-mark",
  critical: "bg-crit-mark",
  pending: "bg-watch-mark",
  approved: "bg-ok-mark",
  active: "bg-ok-mark",
  rejected: "bg-crit-mark",
  flag: "bg-watch-mark",
};

export function Badge({ kind, children }: { kind: string; children: ReactNode }) {
  const mark = MARK[kind];
  // sentence case for raw engine values ("pending" → "Pending"); ::first-letter
  // can't do this because it doesn't apply to flex containers
  const label =
    typeof children === "string" ? children.charAt(0).toUpperCase() + children.slice(1) : children;
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
        BADGE_STYLES[kind] ?? BADGE_STYLES.info
      }`}
    >
      {mark && <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${mark}`} />}
      {label}
    </span>
  );
}

const SCALE = ["none", "low", "moderate", "high", "critical"] as const;
const SCALE_MARK: Record<string, string> = {
  none: "bg-ok-mark",
  low: "bg-low-mark",
  moderate: "bg-watch-mark",
  high: "bg-high-mark",
  critical: "bg-crit-mark",
};

/** Where a finding sits on the engine's five-step risk scale. The engine's
 * own level is the only input - no thresholds live in the UI - and the
 * accessible name states the level in words, so the bar is a second,
 * faster channel and never the only one. */
export function RiskScale({ risk, label }: { risk: string; label: string }) {
  const at = SCALE.indexOf(risk as (typeof SCALE)[number]);
  return (
    <span role="img" aria-label={label} className="inline-flex items-end gap-0.5">
      {SCALE.map((step, i) => (
        <span
          key={step}
          aria-hidden="true"
          className={`w-3 rounded-xs ${
            i === at ? `h-3.5 ${SCALE_MARK[step]}` : "h-2 bg-line"
          }`}
        />
      ))}
    </span>
  );
}

/** A plain working panel. Flat on purpose: only approved documents (.sheet)
 * get lift, so the eye can tell a record from a tool. A titled panel rules
 * its header off from the body, so every panel reads the same way: what it
 * is, then what is in it. `flush` drops the body padding for lists and
 * tables that run edge to edge. */
export function Card({
  title,
  description,
  children,
  action,
  className,
  flush = false,
}: {
  title?: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
  flush?: boolean;
}) {
  return (
    <section className={`overflow-hidden rounded-xl border border-line bg-surface ${className ?? ""}`}>
      {(title || action) && (
        <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 border-b border-line px-5 py-3.5">
          <div className="min-w-0">
            {title && <h2 className="font-display text-lg font-bold leading-7 text-ink">{title}</h2>}
            {description && <p className="text-sm text-ink-muted">{description}</p>}
          </div>
          {action && <div className="pt-1">{action}</div>}
        </div>
      )}
      <div className={flush ? "" : "p-5"}>{children}</div>
    </section>
  );
}

/** Section heading for content that sits directly on the canvas. */
export function SectionHeading({
  children,
  description,
  action,
}: {
  children: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-3 flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
      <div className="min-w-0">
        <h2 className="font-display text-xl font-bold leading-7 text-ink">{children}</h2>
        {description && <p className="text-sm text-ink-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

/** A row of key numbers in one ruled panel, rather than a card per number.
 * Counts are set in the display face; clinical values never come here. */
export function MetricRow({
  items,
}: {
  items: { label: ReactNode; value: ReactNode; hint?: ReactNode; icon?: ReactNode }[];
}) {
  const cols =
    items.length >= 4 ? "sm:grid-cols-2 lg:grid-cols-4" : items.length === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2";
  return (
    // 1px gaps over a line-coloured ground draw the inner rules at any column count
    <dl className={`grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-line bg-line ${cols}`}>
      {items.map((m, i) => (
        <div key={i} className="relative bg-surface px-5 py-4">
          <dt className={`text-sm font-medium text-ink-muted ${m.icon ? "pr-12" : ""}`}>
            {m.label}
            {m.icon && (
              <span
                aria-hidden="true"
                className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-xl bg-clinical-tint text-clinical"
              >
                {m.icon}
              </span>
            )}
          </dt>
          {/* dd holds a div-safe value: it can be a Skeleton (a div) */}
          <dd className="font-display mt-0.5 text-[2rem] font-bold leading-10 text-ink">{m.value}</dd>
          {m.hint && <dd className="text-sm text-ink-muted">{m.hint}</dd>}
        </div>
      ))}
    </dl>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
  back,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  /** a single "up one level" link, shown above the title */
  back?: { href: string; label: string };
}) {
  return (
    <div>
      {back && (
        <Link
          href={back.href}
          className={`mb-2 inline-flex items-center gap-1 rounded text-sm font-medium text-clinical hover:underline ${focusRing}`}
        >
          <IconChevronLeft className="h-4 w-4" />
          {back.label}
        </Link>
      )}
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-3">
        <div className="min-w-0">
          <h1 className="font-display text-[1.75rem] font-bold leading-9 text-ink sm:text-[2.125rem] sm:leading-11">
            {title}
          </h1>
          {subtitle && <p className="mt-0.5 max-w-2xl text-base text-ink-muted">{subtitle}</p>}
        </div>
        {action}
      </div>
    </div>
  );
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .replace(/^dr\.?\s+/i, "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return (
    <span
      aria-hidden="true"
      className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-clinical-tint text-sm font-bold text-clinical ${className ?? ""}`}
    >
      {initials || "?"}
    </span>
  );
}

/** The identity strip a clinician sees on every patient-specific screen, as
 * in hospital record systems: whose chart this is is never in doubt, and the
 * facts that change clinical cutoffs (sex, age, pregnancy) sit beside the
 * name rather than a scroll away. */
export function PatientBanner({
  name,
  id,
  sex,
  age,
  heightCm,
  weightKg,
  pregnant,
  conditions,
  action,
}: {
  name: string;
  id?: string;
  sex: string;
  age: number;
  heightCm?: number;
  weightKg?: number;
  pregnant?: boolean;
  conditions: string[];
  action?: ReactNode;
}) {
  const { t, lang } = useT();
  const facts: [string, ReactNode][] = [
    [t("Sex"), t(sex === "male" ? "Male" : "Female")],
    [t("Age"), t("{age} y", { age })],
  ];
  if (heightCm) facts.push([t("Height"), t("{value} cm", { value: heightCm })]);
  if (weightKg) facts.push([t("Weight"), t("{value} kg", { value: weightKg })]);
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <Avatar name={name} className="h-11 w-11 text-base" />
          <div className="min-w-0">
            <p className="font-display truncate text-xl font-bold leading-7 text-ink">{name}</p>
            {id && <p className="text-sm font-semibold text-ink-muted">{id}</p>}
          </div>
        </div>
        <dl className="flex flex-wrap gap-x-6 gap-y-1">
          {facts.map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs text-ink-muted">{k}</dt>
              <dd className="text-sm font-semibold text-ink">{v}</dd>
            </div>
          ))}
        </dl>
        {action && <div className="ml-auto">{action}</div>}
      </div>
      {(pregnant || conditions.length > 0) && (
        <div className="flex flex-wrap items-center gap-2 border-t border-line bg-surface-soft px-5 py-2.5">
          <span className="text-xs text-ink-muted">{t("Known conditions")}</span>
          {pregnant && <Badge kind="flag">{t("Pregnant")}</Badge>}
          {conditions.map((c) => (
            <Badge key={c} kind="condition">
              {conditionName(c, lang)}
            </Badge>
          ))}
        </div>
      )}
    </div>
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
  const { t } = useT();
  return (
    <label className="relative block w-full sm:max-w-xs">
      <span className="sr-only">{label ?? placeholder ?? t("Search")}</span>
      <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder ?? t("Search…")}
        className="w-full rounded-lg border border-field bg-surface py-2 pl-9 pr-3 text-base placeholder:text-ink-muted focus:border-clinical focus:outline-none focus:ring-2 focus:ring-clinical/20 sm:text-sm"
      />
    </label>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-md bg-line/70 ${className ?? "h-4 w-full"}`}
    />
  );
}

/** Empty states point at the next step rather than just reporting absence. */
export function EmptyState({
  title,
  hint,
  icon,
  action,
  art,
  inset = false,
}: {
  title: string;
  hint?: string;
  icon?: ReactNode;
  action?: ReactNode;
  /** a spot drawing in place of the icon tile, for patient-facing moments */
  art?: ReactNode;
  /** inside a Card: no frame of its own, so panels don't nest boxes */
  inset?: boolean;
}) {
  return (
    <div className={`text-center ${inset ? "px-2 py-6" : "rounded-xl border border-line bg-surface px-6 py-10"}`}>
      {art ? (
        <div className="mb-3">{art}</div>
      ) : (
        icon && (
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-clinical-tint text-clinical">
            {icon}
          </div>
        )
      )}
      <p className="font-display text-lg font-bold text-ink">{title}</p>
      {hint && <p className="mx-auto mt-1 max-w-md text-sm text-ink-muted">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** A message from the API is shown in the reader's language when the
 * interface has it (the sign-in errors); otherwise as the server wrote it. */
export function ErrorNote({ message }: { message: string }) {
  const { t } = useT();
  return (
    <div
      role="alert"
      className="rounded-lg border border-crit-line bg-crit-tint px-4 py-3 text-sm text-crit-ink"
    >
      {t(message)}
    </div>
  );
}

export function InfoNote({ children }: { children: ReactNode }) {
  return (
    <div
      role="status"
      className="rounded-lg border border-watch-line bg-watch-tint px-4 py-3 text-sm text-watch-ink"
    >
      {children}
    </div>
  );
}

/** Neutral guidance, in ink rather than a status colour. */
export function Note({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-surface-soft px-4 py-3 text-sm text-ink-soft">
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
      <span className="text-sm font-semibold text-ink-strong">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink-muted">{hint}</span>}
    </label>
  );
}

/* 16px text in fields on small screens: below that, iOS zooms the page on
 * focus, which throws a patient filling a form out of position. */
export const inputClass =
  "mt-1.5 block w-full rounded-lg border border-field bg-surface px-3 py-2 text-base text-ink placeholder:text-ink-muted " +
  "focus:border-clinical focus:outline-none focus:ring-2 focus:ring-clinical/20 sm:text-sm";

export const checkboxClass = "h-4 w-4 rounded border-field accent-clinical";

const buttonBase =
  "inline-flex min-h-10 cursor-pointer items-center justify-center gap-1.5 rounded-lg px-4 py-2 text-sm font-semibold " +
  "transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50 ";

export const buttonPrimary =
  buttonBase + "bg-clinical text-on-clinical shadow-[inset_0_-2px_0_rgb(0_0_0/0.18)] hover:bg-clinical-hover " + focusRing;

export const buttonSecondary =
  buttonBase + "border border-line-strong bg-surface text-ink-strong hover:border-field hover:bg-surface-soft " + focusRing;

export const buttonDanger =
  buttonBase + "border border-crit-line bg-surface text-crit-ink hover:bg-crit-tint " + focusRingDanger;

/** Text-style action inside a panel (Edit, Add note). */
export const linkButton =
  "inline-flex cursor-pointer items-center gap-1 rounded text-sm font-semibold text-clinical hover:underline " + focusRing;
