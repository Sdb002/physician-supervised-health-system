import { RiskFlag } from "@/lib/api";
import { biomarkerName, findingName, riskWords } from "@/lib/clinical-terms";
import type { Lang } from "@/lib/use-lang";
import { RiskScale } from "@/components/ui";

const RISK_TEXT: Record<string, string> = {
  none: "text-ok-ink",
  low: "text-low-ink",
  moderate: "text-watch-ink",
  high: "text-high-ink",
  critical: "text-crit-ink",
};

/** Measured values as a lab report reads them: name, the number large
 * enough to check against the paper slip, and the finding in words beside a
 * scale mark. Status is carried three ways (words, colour, position) so no
 * reader depends on colour alone. */
export function FindingsList({
  flags,
  lang = "en",
  stacked = false,
}: {
  flags: RiskFlag[];
  lang?: Lang;
  /** narrow-column form (the report's findings margin): value under the name */
  stacked?: boolean;
}) {
  if (stacked) {
    return (
      // printed, the margin becomes a band and each finding a cell of its grid
      <ul className="space-y-4 print:contents print:space-y-0">
        {flags.map((f) => (
          <li key={f.biomarker}>
            <p className="text-sm text-ink-soft">{biomarkerName(f.biomarker, lang)}</p>
            <p className="text-xl font-bold text-ink">
              {f.value}
              <span className="ml-1 text-sm font-normal text-ink-muted">{f.unit}</span>
            </p>
            <p className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 print:flex-col print:items-start">
              <RiskScale risk={f.risk} label={riskWords(f.risk, lang)} />
              <span className={`text-sm font-semibold ${RISK_TEXT[f.risk] ?? "text-ink-soft"}`}>
                {findingName(f.risk === "none" ? "normal" : f.label, lang)}
              </span>
            </p>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <ul className="divide-y divide-line">
      {flags.map((f) => (
        <li key={f.biomarker} className="flex items-start justify-between gap-4 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0">
            <p className="font-semibold text-ink">{biomarkerName(f.biomarker, lang)}</p>
            <p className="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1">
              <RiskScale risk={f.risk} label={riskWords(f.risk, lang)} />
              <span className={`text-sm font-semibold ${RISK_TEXT[f.risk] ?? "text-ink-soft"}`}>
                {findingName(f.risk === "none" ? "normal" : f.label, lang)}
              </span>
            </p>
          </div>
          <p className="shrink-0 whitespace-nowrap text-right text-xl font-bold text-ink">
            {f.value}
            <span className="ml-1 text-sm font-normal text-ink-muted">{f.unit}</span>
          </p>
        </li>
      ))}
    </ul>
  );
}
