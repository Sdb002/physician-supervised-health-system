import { useEffect, useState } from "react";
import { api, Report } from "@/lib/api";

export type LatestReportState =
  | { status: "loading" }
  | { status: "empty" }
  | { status: "error"; message: string }
  | { status: "ready"; report: Report };

const LOADING: LatestReportState = { status: "loading" };

/** The patient's most recently approved report — backs the Foods/Exercise
 * sidebar shortcuts, which show the current recommendation rather than a
 * printable per-visit document. */
export function useLatestReport(lang: "en" | "bn"): LatestReportState {
  // the answer is kept with the language it was fetched in, so a language
  // switch reads as loading until its own report arrives
  const [answer, setAnswer] = useState<{ lang: string; state: LatestReportState } | null>(null);

  useEffect(() => {
    let cancelled = false;
    const settle = (state: LatestReportState) => {
      if (!cancelled) setAnswer({ lang, state });
    };
    api
      .myDashboard()
      .then((dashboard) => {
        const latestReady = dashboard.items.find((i) => i.report_ready);
        if (!latestReady) {
          settle({ status: "empty" });
          return;
        }
        return api.report(latestReady.visit.id, lang, false).then((report) => {
          settle({ status: "ready", report });
        });
      })
      .catch((e) => {
        settle({ status: "error", message: (e as Error).message });
      });
    return () => {
      cancelled = true;
    };
  }, [lang]);

  return answer?.lang === lang ? answer.state : LOADING;
}
