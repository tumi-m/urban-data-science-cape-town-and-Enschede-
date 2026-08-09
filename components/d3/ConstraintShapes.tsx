"use client";

import { useMemo } from "react";
import { scaleLinear } from "d3-scale";
import { line as d3line, curveMonotoneX } from "d3-shape";
import { useMeasure } from "@/components/useMeasure";

/**
 * Constraint shapes.
 *
 * This is a schematic, and it is worth being blunt about that: the curves are
 * the characteristic *form* of each constraint, not a calibrated model of any
 * particular site. Nothing downstream reads a value off it. What it is for is
 * the one comparison the rest of the platform rests on — that some of these
 * curves can be pushed down and others cannot.
 *
 * Each panel plots intensity as a multiple of that constraint's own threshold
 * against distance from its source, so the horizontal line at 1.0 means the
 * same thing everywhere even though the underlying units do not. The pale
 * second curve is the same constraint after a thirty per cent reduction at
 * source. Where the two curves coincide, there is nothing to reduce.
 */

interface Panel {
  id: string;
  label: string;
  unit: string;
  /** Intensity as a multiple of threshold, at distance d (km) from source. */
  f: (d: number, reduction: number) => number;
  yMax: number;
  /** What the pale curve represents. */
  lever: string;
  reducible: boolean;
}

const PANELS: Panel[] = [
  {
    id: "nitrogen",
    label: "Nitrogen deposition",
    unit: "× critical value",
    f: (d, r) => {
      const background = 4.0 * (1 - 0.7 * r); // regional load; the term that dominates
      const local = (1.1 / Math.pow(1 + d, 1.6)) * (1 - r);
      return background + local;
    },
    yMax: 5.4,
    lever: "Regional ammonia and traffic emissions cut by thirty per cent",
    reducible: true,
  },
  {
    id: "noise",
    label: "Road noise",
    unit: "× preference value",
    f: (d, r) => {
      const lden = 70 - 10 * (1 - r) - 12 * Math.log10(Math.max(d, 0.01) / 0.01);
      return lden / 53;
    },
    yMax: 1.45,
    lever: "Speed reduced and a quiet surface laid: ten decibels at source",
    reducible: true,
  },
  {
    id: "safety",
    label: "External safety",
    unit: "× the 10⁻⁶ per year contour",
    f: (d, r) => (6.5 / Math.pow(1 + d * 9, 1.9)) * (1 - 0.85 * r),
    yMax: 7,
    lever: "Stored quantity reduced, which shrinks every contour at once",
    reducible: true,
  },
  {
    id: "groundwater",
    label: "Groundwater capture",
    unit: "× the twenty-five-year zone",
    f: (d, r) => Math.max(0.05, (2.4 - d * 0.85) * (1 - 0.45 * r)),
    yMax: 2.7,
    lever: "Abstraction rate lowered, which contracts the capture zone",
    reducible: true,
  },
  {
    id: "boundary",
    label: "Designated area boundary",
    unit: "inside or outside",
    f: (d) => (d < 1.6 ? 2 : 0.02),
    yMax: 2.4,
    lever: "No source term exists, so no reduction is available",
    reducible: false,
  },
];

const SAMPLES = 121;
const D_MAX = 3;

export function ConstraintShapes() {
  const [ref, { width }] = useMeasure<HTMLDivElement>();
  const cols = width > 900 ? 5 : width > 640 ? 3 : width > 400 ? 2 : 1;
  const panelW = Math.max(150, Math.floor(((width || 900) - (cols - 1) * 16) / cols));
  const panelH = 132;

  return (
    <div ref={ref} className="w-full">
      <div className="mb-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[0.6875rem] text-ink-2">
        <LegendKey color="var(--series-1)" label="As it stands" />
        <LegendKey color="var(--series-2)" label="After a 30% reduction at source" dashed />
        <span className="text-ink-3">Horizontal rule marks the threshold</span>
      </div>
      <div
        className="grid gap-4"
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
      >
        {PANELS.map((p) => (
          <ShapePanel key={p.id} panel={p} width={panelW} height={panelH} />
        ))}
      </div>
    </div>
  );
}

function LegendKey({
  color,
  label,
  dashed,
}: {
  color: string;
  label: string;
  dashed?: boolean;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg width="18" height="8" aria-hidden>
        <line
          x1="0"
          y1="4"
          x2="18"
          y2="4"
          stroke={color}
          strokeWidth={2}
          strokeLinecap="round"
          strokeDasharray={dashed ? "4 3" : undefined}
        />
      </svg>
      {label}
    </span>
  );
}

function ShapePanel({
  panel,
  width,
  height,
}: {
  panel: Panel;
  width: number;
  height: number;
}) {
  const m = { top: 8, right: 8, bottom: 22, left: 8 };
  const iw = Math.max(40, width - m.left - m.right);
  const ih = height - m.top - m.bottom;

  const { basePath, cutPath, thresholdY, crossing } = useMemo(() => {
    const x = scaleLinear().domain([0, D_MAX]).range([0, iw]);
    const y = scaleLinear().domain([0, panel.yMax]).range([ih, 0]);
    const gen = d3line<[number, number]>()
      .x((p) => x(p[0]))
      .y((p) => y(p[1]))
      .curve(curveMonotoneX);

    const sample = (r: number): [number, number][] =>
      Array.from({ length: SAMPLES }, (_, i) => {
        const d = (i / (SAMPLES - 1)) * D_MAX;
        return [d, Math.min(panel.f(d, r), panel.yMax)] as [number, number];
      });

    const base = sample(0);
    // Distance at which the untouched constraint drops through its threshold.
    let cross: number | null = null;
    for (let i = 1; i < base.length; i++) {
      if (base[i - 1][1] >= 1 && base[i][1] < 1) {
        cross = base[i][0];
        break;
      }
    }

    return {
      basePath: gen(base) ?? "",
      cutPath: gen(sample(0.3)) ?? "",
      thresholdY: y(1),
      crossing: cross === null ? null : x(cross),
    };
  }, [panel, iw, ih]);

  return (
    <div>
      <svg width={width} height={height} role="img" aria-label={`${panel.label}: ${panel.unit}`}>
        <g transform={`translate(${m.left},${m.top})`}>
          <line
            x1={0}
            y1={thresholdY}
            x2={iw}
            y2={thresholdY}
            stroke="var(--grid)"
            strokeWidth={1}
          />
          {crossing !== null && (
            <line
              x1={crossing}
              y1={thresholdY}
              x2={crossing}
              y2={ih}
              stroke="var(--grid)"
              strokeWidth={1}
            />
          )}
          <path d={cutPath} fill="none" stroke="var(--series-2)" strokeWidth={2} strokeDasharray="4 3" strokeLinecap="round" />
          <path d={basePath} fill="none" stroke="var(--series-1)" strokeWidth={2} strokeLinecap="round" />
          <line x1={0} y1={ih} x2={iw} y2={ih} stroke="var(--rule)" strokeWidth={1} />
        </g>
        <text x={m.left} y={height - 6} className="fill-current text-ink-3" fontSize={10}>
          source
        </text>
        <text
          x={width - m.right}
          y={height - 6}
          textAnchor="end"
          className="fill-current text-ink-3"
          fontSize={10}
        >
          {D_MAX} km
        </text>
      </svg>
      <div className="mt-1">
        <div className="text-[0.8125rem] font-medium leading-snug text-ink">{panel.label}</div>
        <div className="text-[0.6875rem] text-ink-3">{panel.unit}</div>
        <p className="mt-1.5 text-[0.6875rem] leading-relaxed text-ink-2">
          {panel.lever}
          {!panel.reducible && (
            <span className="text-ink-3"> — the two curves are the same curve.</span>
          )}
        </p>
      </div>
    </div>
  );
}
