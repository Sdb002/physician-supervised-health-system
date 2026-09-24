"use client";

import { useState } from "react";

export interface TrendSeriesDef {
  key: string;
  label: string;
  /** validated categorical hex — see the constants below */
  color: string;
}

export interface TrendPoint {
  /** short display label, e.g. "7/31" */
  date: string;
  values: Partial<Record<string, number>>;
}

// Categorical slots 1 (blue) and 8 (red) from the validated default palette —
// passes CVD/contrast checks as a pair (worst adjacent normal-vision ΔE 32.3,
// CVD ΔE 21.6). Chart chrome (axis/text) uses the app's own slate tokens
// instead, since only data-identity color needs the validated palette.
export const TREND_COLOR_PRIMARY = "#2a78d6";
export const TREND_COLOR_SECONDARY = "#e34948";

const WIDTH = 600;
const BAR_GAP = 3; // surface-color gap between bars within a group

/** Path for a rectangle with rounded top corners, square at the baseline —
 * the bar/column mark spec (never a plain rect with all four corners rounded). */
function roundedTopRect(x: number, y: number, w: number, h: number, r: number) {
  const radius = Math.min(r, w / 2, h);
  if (h <= 0) return "";
  return `M ${x} ${y + h}
    L ${x} ${y + radius}
    Q ${x} ${y} ${x + radius} ${y}
    L ${x + w - radius} ${y}
    Q ${x + w} ${y} ${x + w} ${y + radius}
    L ${x + w} ${y + h}
    Z`;
}

/** Grouped/single column chart: 1–2 series, categorical color, value labeled
 * on every bar's cap (few visits, so labeling all of them — not just the
 * endpoint — reads as data, not clutter). Value/date text renders as real
 * HTML overlaid on the SVG (percentage-positioned), not scaled SVG <text>,
 * so it stays legible at whatever width the card actually renders at — a
 * fixed SVG font-size shrinks along with everything else once the chart is
 * squeezed into a ~300px card. Built inline (no chart library) to match this
 * app's existing hand-rolled icon/UI kit. */
export function TrendChart({
  title,
  unit,
  series,
  points,
  emptyHint,
  valueFormatter = (v) => `${Math.round(v * 10) / 10}`,
  large = false,
}: {
  title: string;
  unit?: string;
  series: TrendSeriesDef[];
  points: TrendPoint[];
  emptyHint: string;
  valueFormatter?: (v: number) => string;
  /** the expanded-in-a-modal rendering: taller plot, bigger bars/labels */
  large?: boolean;
}) {
  const [hoverGroup, setHoverGroup] = useState<number | null>(null);

  const HEIGHT = large ? 340 : 220;
  const PAD = large
    ? { top: 44, right: 20, bottom: 36, left: 20 }
    : { top: 30, right: 12, bottom: 26, left: 12 };
  const PLOT_W = WIDTH - PAD.left - PAD.right;
  const PLOT_H = HEIGHT - PAD.top - PAD.bottom;
  const MAX_BAR_W = large ? 48 : 28;
  const valueTextClass = large ? "text-base" : "text-xs";
  const dateTextClass = large ? "text-sm" : "text-xs";

  const allValues = points.flatMap((p) =>
    series.map((s) => p.values[s.key]).filter((v): v is number => v != null)
  );

  if (allValues.length === 0) {
    return (
      <div>
        <p className="text-sm font-semibold text-ink-strong">{title}</p>
        <p className="mt-8 text-center text-sm text-ink-muted">{emptyHint}</p>
      </div>
    );
  }

  // bars grow from a zero baseline (the honest bar-chart contract — the
  // number above each cap carries the precision, the bar carries the magnitude)
  const domainMax = Math.max(...allValues) * 1.2;

  const groupW = PLOT_W / points.length;
  const barW = Math.min(MAX_BAR_W, (groupW - BAR_GAP * (series.length + 1)) / series.length);
  const groupContentW = barW * series.length + BAR_GAP * (series.length - 1);

  const yFor = (v: number) => PAD.top + (1 - v / domainMax) * PLOT_H;
  const baselineY = PAD.top + PLOT_H;

  const barX = (groupIndex: number, seriesIndex: number) => {
    const groupStart = PAD.left + groupIndex * groupW + (groupW - groupContentW) / 2;
    return groupStart + seriesIndex * (barW + BAR_GAP);
  };

  const pct = (v: number, of: number) => `${(v / of) * 100}%`;

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className={`font-semibold text-ink-strong ${large ? "text-lg" : "text-sm"}`}>{title}</p>
        {series.length > 1 && (
          <div className="flex items-center gap-3">
            {series.map((s) => (
              <span key={s.key} className={`flex items-center gap-1.5 text-ink-muted ${dateTextClass}`}>
                <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: s.color }} />
                {s.label}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="relative mt-1">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          style={{ width: "100%", height: "auto", display: "block" }}
          role="img"
          aria-label={`${title} across ${points.length} visits`}
        >
          <line x1={PAD.left} x2={WIDTH - PAD.right} y1={baselineY} y2={baselineY} stroke="#cbd5e1" strokeWidth={1} />

          {points.map((p, gi) => (
            <g
              key={p.date + gi}
              onPointerEnter={() => setHoverGroup(gi)}
              onPointerLeave={() => setHoverGroup(null)}
            >
              {series.map((s, si) => {
                const v = p.values[s.key];
                if (v == null) return null;
                const x = barX(gi, si);
                const y = yFor(v);
                const h = baselineY - y;
                return (
                  <path
                    key={s.key}
                    d={roundedTopRect(x, y, barW, h, 4)}
                    fill={s.color}
                    opacity={hoverGroup === null || hoverGroup === gi ? 1 : 0.45}
                  />
                );
              })}
              <rect
                x={PAD.left + gi * groupW}
                y={PAD.top}
                width={groupW}
                height={PLOT_H}
                fill="transparent"
              />
            </g>
          ))}
        </svg>

        {/* value labels: real HTML text, so it stays crisp at any card width */}
        {points.map((p, gi) =>
          series.map((s, si) => {
            const v = p.values[s.key];
            if (v == null) return null;
            const x = barX(gi, si) + barW / 2;
            const y = yFor(v);
            return (
              <span
                key={`${gi}-${s.key}`}
                className={`pointer-events-none absolute -translate-x-1/2 -translate-y-full whitespace-nowrap font-semibold text-ink-strong ${valueTextClass}`}
                style={{ left: pct(x, WIDTH), top: pct(y - 4, HEIGHT) }}
              >
                {valueFormatter(v)}
              </span>
            );
          })
        )}

        {/* date labels below the baseline */}
        {points.map((p, gi) => (
          <span
            key={`date-${gi}`}
            className={`pointer-events-none absolute -translate-x-1/2 whitespace-nowrap text-ink-muted ${dateTextClass}`}
            style={{ left: pct(PAD.left + gi * groupW + groupW / 2, WIDTH), top: pct(baselineY + 6, HEIGHT) }}
          >
            {p.date}
          </span>
        ))}
      </div>
      {unit && <p className="mt-1 text-right text-xs text-ink-muted">values in {unit}</p>}
    </div>
  );
}
