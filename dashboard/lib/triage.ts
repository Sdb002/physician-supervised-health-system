import type { QueueItem } from "@/lib/api";

const RISK_RANK: Record<string, number> = { critical: 4, high: 3, moderate: 2, low: 1, none: 0 };

/** Review order for a physician: highest engine risk first, then oldest
 * visit first within a risk level, so nobody urgent waits behind routine
 * follow-ups and nobody routine waits forever. */
export function byTriage(a: QueueItem, b: QueueItem) {
  const risk =
    (RISK_RANK[b.assessment.result.overall_risk] ?? 0) - (RISK_RANK[a.assessment.result.overall_risk] ?? 0);
  if (risk !== 0) return risk;
  return new Date(a.visit.created_at).getTime() - new Date(b.visit.created_at).getTime();
}

export const riskLabel = (risk: string) =>
  risk === "none" ? "No risk flags" : `${risk.charAt(0).toUpperCase()}${risk.slice(1)} risk`;
