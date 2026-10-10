import { formatDate } from "@/lib/clinical-terms";
import type { Lang } from "@/lib/use-lang";
import { IconRx } from "@/components/icons";

/** Provenance under a patient page title: who approved what they're reading,
 * and when. Every recommendation in the portal traces to one signature. */
export function ApprovedLine({ by, at, lang }: { by: string; at: string; lang: Lang }) {
  const date = formatDate(at, lang);
  return (
    <p className="flex items-center gap-1.5 text-sm text-ink-muted">
      <IconRx className="h-4 w-4 shrink-0 text-clinical" strokeWidth={2.2} />
      {lang === "bn" ? (
        <span>
          <strong className="font-semibold text-ink-strong">{by}</strong> {date} তারিখে অনুমোদন করেছেন
        </span>
      ) : (
        <span>
          Approved by <strong className="font-semibold text-ink-strong">{by}</strong> on {date}
        </span>
      )}
    </p>
  );
}
