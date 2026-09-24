import { useEffect, useState } from "react";
import { api, Report } from "@/lib/api";

export type LatestReportState =
  | { status: "loading" }
  | { status: "empty" }
  | { status: "error"; message: string }
  | { status: "ready"; report: Report };

/** The patient's most recently approved report — backs the Foods/Exercise
 * sidebar shortcuts, which show the current recommendation rather than a
 * printable per-visit document. */
export function useLatestReport(lang: "en" | "bn"): LatestReportState {
  const [state, setState] = useState<LatestReportState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    api
      .myDashboard()
      .then((dashboard) => {
        const latestReady = dashboard.items.find((i) => i.report_ready);
        if (!latestReady) {
          if (!cancelled) setState({ status: "empty" });
          return;
        }
        return api.report(latestReady.visit.id, lang, false).then((report) => {
          if (!cancelled) setState({ status: "ready", report });
        });
      })
      .catch((e) => {
        if (!cancelled) setState({ status: "error", message: (e as Error).message });
      });
    return () => {
      cancelled = true;
    };
  }, [lang]);

  return state;
}
