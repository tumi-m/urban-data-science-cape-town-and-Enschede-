"use client";

import { useMemo, useState } from "react";
import { scaleLinear } from "d3-scale";
import { area as d3area, line as d3line, curveMonotoneX } from "d3-shape";
import { bisector } from "d3-array";
import { pointer } from "d3-selection";
import {
  CLIMB,
  RIDGE_TRANSECT,
  climbBatteryWh,
  climbMetabolicWh,
  totalAscent,
} from "@/data/mobility";
import { useMeasure } from "@/components/useMeasure";

/**
 * The ridge.
 *
 * Enschede is built on an ice-pushed ridge, which makes it one of the few
 * Dutch cities where a bicycle trip has real climb in it. The profile is here
 * to put a number on that climb, and the readout converts the number into the
 * two currencies that matter: what the rider has to supply, and what a motor
 * has to supply instead.
 *
 * The comparison is the argument. A gradient a rider experiences as effort and
 * as a reason to take the car is, to a motor, less than a kilometre of range.
 */
const bisect = bisector<{ km: number; m: number }, number>((d) => d.km).center;

export function RidgeProfile() {
  const [hostRef, { width }] = useMeasure<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);

  const w = Math.max(300, width || 720);
  const h = 232;
  // Top margin clears the axis title, which sits above the plot rather than
  // rotated beside it; at 16 it collided with the topmost tick label.
  const m = { top: 28, right: 16, bottom: 30, left: 44 };
  const iw = w - m.left - m.right;
  const ih = h - m.top - m.bottom;

  const { x, y, linePath, areaPath, ticksY, crest } = useMemo(() => {
    const xs = scaleLinear()
      .domain([0, RIDGE_TRANSECT[RIDGE_TRANSECT.length - 1].km])
      .range([0, iw]);
    const ys = scaleLinear().domain([20, 60]).range([ih, 0]);
    const ln = d3line<{ km: number; m: number }>()
      .x((d) => xs(d.km))
      .y((d) => ys(d.m))
      .curve(curveMonotoneX);
    const ar = d3area<{ km: number; m: number }>()
      .x((d) => xs(d.km))
      .y0(ih)
      .y1((d) => ys(d.m))
      .curve(curveMonotoneX);
    const peak = RIDGE_TRANSECT.reduce((a, b) => (b.m > a.m ? b : a));
    return {
      x: xs,
      y: ys,
      linePath: ln(RIDGE_TRANSECT) ?? "",
      areaPath: ar(RIDGE_TRANSECT) ?? "",
      ticksY: [20, 30, 40, 50, 60],
      crest: peak,
    };
  }, [iw, ih]);

  const ascent = totalAscent(RIDGE_TRANSECT);
  const point = hover === null ? null : RIDGE_TRANSECT[hover];

  function onMove(event: React.PointerEvent<SVGSVGElement>) {
    const [px] = pointer(event.nativeEvent, event.currentTarget);
    const km = x.invert(px - m.left);
    setHover(bisect(RIDGE_TRANSECT, km));
  }

  return (
    <div ref={hostRef} className="w-full">
      <svg
        width={w}
        height={h}
        onPointerMove={onMove}
        onPointerLeave={() => setHover(null)}
        role="img"
        aria-label="Elevation along a west-to-east traverse of Enschede, from 32 to 52 metres above datum and back"
        className="touch-none"
      >
        <g transform={`translate(${m.left},${m.top})`}>
          {ticksY.map((t) => (
            <g key={t}>
              <line x1={0} y1={y(t)} x2={iw} y2={y(t)} stroke="var(--grid)" strokeWidth={1} />
              <text
                x={-8}
                y={y(t)}
                dy="0.32em"
                textAnchor="end"
                fontSize={11}
                fill="var(--text-muted)"
              >
                {t}
              </text>
            </g>
          ))}

          <path d={areaPath} fill="var(--series-1)" fillOpacity={0.1} />
          <path
            d={linePath}
            fill="none"
            stroke="var(--series-1)"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />

          {/* One direct label, on the extreme. The axis carries the rest. */}
          <circle
            cx={x(crest.km)}
            cy={y(crest.m)}
            r={4}
            fill="var(--series-1)"
            stroke="var(--surface-1)"
            strokeWidth={2}
          />
          <text
            x={x(crest.km)}
            y={y(crest.m) - 12}
            textAnchor="middle"
            fontSize={11}
            fill="var(--text-secondary)"
          >
            {crest.m} m
          </text>

          {point && (
            <g>
              <line
                x1={x(point.km)}
                y1={0}
                x2={x(point.km)}
                y2={ih}
                stroke="var(--rule)"
                strokeWidth={1}
              />
              <circle
                cx={x(point.km)}
                cy={y(point.m)}
                r={4}
                fill="var(--series-2)"
                stroke="var(--surface-1)"
                strokeWidth={2}
              />
            </g>
          )}

          <line x1={0} y1={ih} x2={iw} y2={ih} stroke="var(--rule)" strokeWidth={1} />
          <text x={0} y={ih + 18} fontSize={11} fill="var(--text-muted)">
            west
          </text>
          <text x={iw} y={ih + 18} textAnchor="end" fontSize={11} fill="var(--text-muted)">
            east, toward the border
          </text>
        </g>
        <text x={0} y={11} fontSize={11} fill="var(--text-muted)">
          m above datum
        </text>
      </svg>

      <dl className="mt-6 grid gap-x-8 gap-y-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric
          term={point ? `Elevation at ${point.km} km` : "Total ascent, west to east"}
          value={point ? `${point.m}` : `${ascent}`}
          unit="m"
          note={point ? "hovering the profile" : "the climb a rider actually accumulates"}
        />
        <Metric
          term="Rider's cost for a 30 m climb"
          value={climbMetabolicWh(CLIMB.typicalClimbM).toFixed(0)}
          unit="Wh of food energy"
          note={`at ${(CLIMB.humanEfficiency * 100).toFixed(0)}% muscular efficiency and a ${CLIMB.systemMassKg} kg system`}
        />
        <Metric
          term="Motor's cost for the same climb"
          value={climbBatteryWh(CLIMB.typicalClimbM).toFixed(1)}
          unit="Wh from the battery"
          note={`at ${(CLIMB.motorEfficiency * 100).toFixed(0)}% drivetrain efficiency`}
          accent
        />
        <Metric
          term="Expressed as e-bike range"
          value={(climbBatteryWh(CLIMB.typicalClimbM) / 11).toFixed(1)}
          unit="km of level riding"
          note="at 11 Wh per km — the ridge costs less than a kilometre"
          accent
        />
      </dl>
    </div>
  );
}

function Metric({
  term,
  value,
  unit,
  note,
  accent,
}: {
  term: string;
  value: string;
  unit: string;
  note: string;
  accent?: boolean;
}) {
  return (
    <div className="border-t border-rule pt-2">
      <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">{term}</dt>
      <dd
        className="mt-1.5 text-[1.5rem] font-semibold leading-none tabular-nums"
        style={accent ? { color: "var(--series-2)" } : undefined}
      >
        {value}
        <span className="ml-1.5 text-[0.75rem] font-normal text-ink-2">{unit}</span>
      </dd>
      <dd className="mt-1.5 text-[0.6875rem] leading-relaxed text-ink-3">{note}</dd>
    </div>
  );
}
