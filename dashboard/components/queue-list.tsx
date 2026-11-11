"use client";

import Link from "next/link";
import { QueueItem } from "@/lib/api";
import { conditionName, formatDate } from "@/lib/clinical-terms";
import { pid } from "@/lib/format";
import { riskLabel } from "@/lib/triage";
import { useT } from "@/lib/use-t";
import { IconChevronRight } from "@/components/icons";
import { Avatar, Badge, focusRing } from "@/components/ui";

/** Assessments waiting for a decision, one row each. The risk badge leads
 * the row's right side because it decides what to open first. */
export function QueueList({ items }: { items: QueueItem[] }) {
  const { t, lang } = useT();
  return (
    <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
      {items.map((item) => {
        const r = item.assessment.result;
        return (
          <li key={item.assessment.id}>
            <Link
              href={`/doctor/review/${item.assessment.id}`}
              className={`group flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3.5 transition-colors duration-150 hover:bg-surface-soft sm:flex-nowrap sm:px-5 ${focusRing} focus-visible:-outline-offset-2`}
            >
              <Avatar name={item.patient.name} />
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-ink group-hover:text-clinical">{item.patient.name}</p>
                <p className="text-sm text-ink-muted">
                  <span>{pid(item.patient.id)}</span>
                  <span className="mx-2 text-line-strong" aria-hidden="true">|</span>
                  {t("Visit {date}", { date: formatDate(item.visit.created_at, lang) })}
                  {r.conditions.length > 0 && (
                    <>
                      <span className="mx-2 text-line-strong" aria-hidden="true">|</span>
                      {r.conditions.map((c) => conditionName(c, lang)).join(", ")}
                    </>
                  )}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3 pl-12 sm:pl-0">
                <Badge kind={r.overall_risk}>{riskLabel(r.overall_risk, t)}</Badge>
                <span className="inline-flex items-center text-sm font-semibold text-clinical">
                  {t("Review")}
                  <IconChevronRight className="h-4 w-4 transition-transform duration-150 group-hover:translate-x-0.5" />
                </span>
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
