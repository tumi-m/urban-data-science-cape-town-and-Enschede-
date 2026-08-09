"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { ACCESS_MODES, CURVE_RADII, coverage } from "@/data/access";

/**
 * Coverage against access radius, counted two ways.
 *
 * The gap between the lines is the argument, and it behaves differently
 * depending on how it is read. In percentage points it is widest in the middle
 * of the range, where a growing shed is sweeping through the steep part of the
 * density gradient. In proportional terms it is worst at the short end, where
 * the land metric understates access by about a fifth — the central station
 * stands on the density peak, and hectares out at the edge are nearly empty.
 *
 * Both readings run the same way, and both converge to nothing once the shed is
 * large enough to cover the city, at which point the metric stops carrying
 * information at all.
 */
const ROWS = CURVE_RADII.flatMap((r) => {
  const c = coverage(r);
  return [
    { radius: r, basis: "Share of residents", pct: Number((c.population * 100).toFixed(1)) },
    { radius: r, basis: "Share of built-up land", pct: Number((c.land * 100).toFixed(1)) },
  ];
});

const BASES = ["Share of residents", "Share of built-up land"];
const LAST = CURVE_RADII[CURVE_RADII.length - 1];

/**
 * Direct labels go where the two series are furthest apart, not at the right
 * edge. Both curves saturate at 100 well before the axis runs out, so an
 * end-label would put two identical numbers on top of each other and say
 * nothing; the widest point is where the chart has something to tell you.
 */
const WIDEST = CURVE_RADII.reduce((best, r) => {
  const gap = (rad: number) => {
    const c = coverage(rad);
    return c.population - c.land;
  };
  return gap(r) > gap(best) ? r : best;
}, CURVE_RADII[0]);

const MARKED = ROWS.filter((d) => d.radius === WIDEST);

// The nominal mode radii, marked so the curve can be read against the three
// cases the section discusses. Labels are short and horizontal along the top:
// rotated text inside the plot collides with the curves near saturation and is
// slower to read, and the deck already carries the full mode names.
const SHORT: Record<string, string> = { walk: "walk", bike: "bike", ebike: "e-bike" };

const MARKS = ACCESS_MODES.map((m) => ({
  radius: m.radiusKm,
  label: SHORT[m.id] ?? m.label.toLowerCase(),
  align: m.radiusKm > 4 ? "right" : "left",
  dx: m.radiusKm > 4 ? -5 : 5,
}));

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width: "container",
  height: 300,
  encoding: {
    x: {
      field: "radius",
      type: "quantitative",
      scale: { domain: [0.4, LAST], nice: false },
      axis: {
        title: "access radius from the station, km",
        values: [1, 2, 3, 4, 5, 6],
        grid: false,
      },
    },
    y: {
      field: "pct",
      type: "quantitative",
      // Headroom above 100 so the saturated curves sit clear of the top edge
      // and the mode labels have air. The tick list stops at 100, so the extra
      // space reads as margin rather than as a scale that goes past full.
      scale: { domain: [0, 110], nice: false },
      axis: {
        title: "% within reach of a station",
        values: [0, 25, 50, 75, 100],
        grid: true,
        gridColor: t.grid,
      },
    },
  },
  layer: [
    {
      data: { values: MARKS },
      mark: { type: "rule", strokeWidth: 1, color: t.grid },
      encoding: { x: { field: "radius", type: "quantitative" }, y: { value: 0 }, y2: { value: 300 } },
    },
    {
      data: { values: MARKS.filter((m) => m.align === "left") },
      mark: { type: "text", baseline: "top", align: "left", dx: 5, fontSize: 10 },
      encoding: {
        x: { field: "radius", type: "quantitative" },
        y: { value: 2 },
        text: { field: "label", type: "nominal" },
        color: { value: t.textMuted },
      },
    },
    {
      // The rightmost mark leans the other way so its label stays inside the
      // plot. Two layers rather than an alignment encoding, which the grammar
      // does not offer at this level.
      data: { values: MARKS.filter((m) => m.align === "right") },
      mark: { type: "text", baseline: "top", align: "right", dx: -5, fontSize: 10 },
      encoding: {
        x: { field: "radius", type: "quantitative" },
        y: { value: 2 },
        text: { field: "label", type: "nominal" },
        color: { value: t.textMuted },
      },
    },
    {
      data: { values: ROWS },
      mark: { type: "line", strokeWidth: 2, strokeCap: "round", strokeJoin: "round" },
      encoding: {
        color: {
          field: "basis",
          type: "nominal",
          sort: BASES,
          scale: { domain: BASES, range: [t.series[1], t.series[0]] },
          legend: { orient: "bottom", title: null, offset: 16 },
        },
        tooltip: [
          { field: "basis", type: "nominal", title: "Counted as" },
          { field: "radius", type: "quantitative", title: "Radius, km" },
          { field: "pct", type: "quantitative", title: "% covered", format: ".0f" },
        ],
      },
    },
    {
      data: { values: MARKED },
      mark: { type: "point", filled: true, size: 80, stroke: t.surface1, strokeWidth: 2 },
      encoding: {
        color: {
          field: "basis",
          type: "nominal",
          scale: { domain: BASES, range: [t.series[1], t.series[0]] },
          legend: null,
        },
      },
    },
    {
      data: { values: MARKED },
      mark: { type: "text", align: "left", dx: 10, dy: -2, fontSize: 11 },
      encoding: {
        color: { value: t.textSecondary },
        text: { field: "pct", type: "quantitative", format: ".0f" },
      },
    },
  ],
});

export function CoverageCurve() {
  return (
    <VegaChart
      spec={spec}
      minHeight={330}
      ariaLabel="Coverage against access radius, counted as a share of residents and as a share of built-up land; the residents line runs above the land line at short radii and the two converge as the radius grows"
    />
  );
}

export function CoverageCurveTable() {
  const rows = [0.8, 1.5, 2, 3, 4, 5];
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Radius, km</th>
          <th>Shed per station, km²</th>
          <th>Land covered</th>
          <th>Residents covered</th>
          <th>Gap</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const c = coverage(r);
          return (
            <tr key={r}>
              <td>{r.toFixed(1)}</td>
              <td>{(Math.PI * r * r).toFixed(1)}</td>
              <td>{(c.land * 100).toFixed(0)}%</td>
              <td>{(c.population * 100).toFixed(0)}%</td>
              <td>{((c.population - c.land) * 100).toFixed(0)} pts</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
