"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { ACCESS_MODES, CAPE_TOWN, shedAreaKm2 } from "@/data/access";

/**
 * The same stations, three access modes.
 *
 * Summed shed area for Cape Town's published station set against the area of
 * its development edge. The point is the crossing: at the walking radius the
 * network's sheds sum to a fifth of the edge, and at a cycling radius they sum
 * to nearly three times it — with no new track.
 *
 * Summed, not unioned, and the distinction is load-bearing. Overlap means the
 * union is smaller than the sum, so the cycling bars overstate real coverage.
 * What the comparison establishes is that the shortfall at the walking radius
 * is not a shortfall of stations: a network whose sheds sum to 2.9 times the
 * area to be covered is not short of coverage, it is short of a way to reach it.
 */
const EDGE = CAPE_TOWN.developmentEdgeKm2.value;

const ROWS = ACCESS_MODES.map((m) => ({
  mode: `${m.label}, ${m.minutes} min`,
  radius: m.radiusKm,
  shed: Number(shedAreaKm2(m.radiusKm).toFixed(1)),
  summed: Number(CAPE_TOWN.summedShedKm2(m.radiusKm).toFixed(0)),
  ratio: Number((CAPE_TOWN.summedShedKm2(m.radiusKm) / EDGE).toFixed(2)),
}));

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width: "container",
  height: { step: 42 },
  // The band scale lives on the three data layers only. Hoisting it to the top
  // level puts the reference-line layers — whose data has no `mode` — into an
  // "undefined" band of their own, which the axis then dutifully labels.
  encoding: {
    x: {
      field: "summed",
      type: "quantitative",
      scale: { type: "log", domain: [100, 4000], nice: false },
      axis: {
        title: "summed station sheds, km², logarithmic",
        values: [100, 300, 1000, 3000],
        format: "~s",
        grid: true,
        gridColor: t.grid,
      },
    },
  },
  layer: [
    {
      data: { values: ROWS },
      mark: { type: "rule", strokeWidth: 2, opacity: 0.35, strokeCap: "round", color: t.series[0] },
      encoding: {
        y: {
          field: "mode",
          type: "nominal",
          sort: ROWS.map((r) => r.mode),
          axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary, labelLimit: 260 },
        },
        x: { datum: 100 },
        x2: { field: "summed" },
      },
    },
    {
      data: { values: ROWS },
      mark: {
        type: "point",
        filled: true,
        size: 130,
        stroke: t.surface1,
        strokeWidth: 2,
        color: t.series[0],
      },
      encoding: {
        y: {
          field: "mode",
          type: "nominal",
          sort: ROWS.map((r) => r.mode),
          axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary, labelLimit: 260 },
        },
        tooltip: [
          { field: "mode", type: "nominal", title: "Access mode" },
          { field: "shed", type: "quantitative", title: "Shed per station, km²" },
          { field: "summed", type: "quantitative", title: "Summed sheds, km²" },
          { field: "ratio", type: "quantitative", title: "× the development edge" },
        ],
      },
    },
    {
      data: { values: ROWS },
      mark: { type: "text", align: "left", dx: 12, fontSize: 11 },
      encoding: {
        y: {
          field: "mode",
          type: "nominal",
          sort: ROWS.map((r) => r.mode),
          axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary, labelLimit: 260 },
        },
        color: { value: t.textSecondary },
        text: { field: "ratio", type: "quantitative", format: ".2f" },
      },
    },
    {
      data: { values: [{ edge: EDGE }] },
      mark: { type: "rule", strokeWidth: 2, color: t.series[1] },
      encoding: { x: { field: "edge", type: "quantitative" } },
    },
    {
      data: { values: [{ edge: EDGE, note: "development edge, 895 km²" }] },
      mark: {
        type: "text",
        align: "left",
        dx: 8,
        dy: -6,
        baseline: "top",
        fontSize: 11,
      },
      encoding: {
        x: { field: "edge", type: "quantitative" },
        y: { value: 0 },
        text: { field: "note", type: "nominal" },
        color: { value: t.textSecondary },
      },
    },
  ],
});

export function CapeTownSheds() {
  return (
    <VegaChart
      spec={spec}
      minHeight={200}
      ariaLabel="Summed station sheds for Cape Town's rail network at three access radii, against the 895 square kilometre development edge; walking sums to a fifth of it, cycling to nearly three times it"
    />
  );
}

export function CapeTownShedsTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Access mode</th>
          <th>Radius, km</th>
          <th>Shed per station, km²</th>
          <th>Summed, km²</th>
          <th>× the edge</th>
        </tr>
      </thead>
      <tbody>
        {ROWS.map((r) => (
          <tr key={r.mode}>
            <td>{r.mode}</td>
            <td>{r.radius.toFixed(1)}</td>
            <td>{r.shed.toFixed(1)}</td>
            <td>{r.summed.toLocaleString("en-GB")}</td>
            <td>{r.ratio.toFixed(2)}×</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
