"use client";

import { useState } from "react";
import { Card } from "@/components/ui";
import { IconMaximize } from "@/components/icons";
import { Modal } from "@/components/modal";
import { TrendChart, TrendPoint, TrendSeriesDef } from "@/components/trend-chart";

/** A trend chart card that expands into a bigger modal view on click. */
export function TrendChartCard(props: {
  title: string;
  unit?: string;
  series: TrendSeriesDef[];
  points: TrendPoint[];
  emptyHint: string;
  valueFormatter?: (v: number) => string;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasData = props.points.some((p) => props.series.some((s) => p.values[s.key] != null));

  return (
    <>
      <Card>
        <div
          className={`group relative ${hasData ? "cursor-zoom-in" : ""}`}
          onClick={() => hasData && setExpanded(true)}
          role={hasData ? "button" : undefined}
          tabIndex={hasData ? 0 : undefined}
          onKeyDown={(e) => {
            if (hasData && (e.key === "Enter" || e.key === " ")) {
              e.preventDefault();
              setExpanded(true);
            }
          }}
        >
          {hasData && (
            <IconMaximize className="pointer-events-none absolute right-0 top-0 h-3.5 w-3.5 text-ink-muted opacity-0 transition group-hover:opacity-100" />
          )}
          <TrendChart {...props} />
        </div>
      </Card>

      {expanded && (
        <Modal onClose={() => setExpanded(false)}>
          <TrendChart {...props} large />
        </Modal>
      )}
    </>
  );
}
