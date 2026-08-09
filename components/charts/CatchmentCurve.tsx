"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { PERMEABILITY_SCENARIOS, catchmentRatio } from "@/data/border";

/**
 * Catchment against radius.
 *
 * Three permeability scenarios, each a line, each labelled at its own end so
 * identity never rests on colour alone. The shape is what matters: the closed
 * frontier curve falls away as the radius grows, because a larger disc puts a
 * larger share of itself on the far side of a fixed chord.
 *
 * The practical reading is that the border costs Enschede almost nothing at a
 * five kilometre radius and a great deal at thirty — so it is the regional
 * functions, the ones whose economics need a wide catchment, that the border
 * takes away.
 */
const RADII = [5, 10, 15, 20, 25, 30, 35, 40];
const SHOWN = PERMEABILITY_SCENARIOS.filter((s) => s.id !== "seamless");

const ROWS = SHOWN.flatMap((s) =>
  RADII.map((r) => ({
    scenario: s.label,
    radius: r,
    ratio: Number((catchmentRatio(r, s.value) * 100).toFixed(1)),
  })),
);

const ENDS = SHOWN.map((s) => ({
  scenario: s.label,
  radius: RADII[RADII.length - 1],
  ratio: Number((catchmentRatio(RADII[RADII.length - 1], s.value) * 100).toFixed(1)),
}));

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width: "container",
  height: 280,
  encoding: {
    x: {
      field: "radius",
      type: "quantitative",
      scale: { domain: [5, 40], nice: false },
      axis: {
        title: "travel radius from the city centre, km",
        values: RADII,
        grid: false,
      },
    },
    y: {
      field: "ratio",
      type: "quantitative",
      scale: { domain: [50, 100], nice: false },
      axis: {
        title: "effective catchment as % of a full disc",
        values: [50, 60, 70, 80, 90, 100],
        grid: true,
        gridColor: t.grid,
      },
    },
  },
  layer: [
    {
      data: { values: ROWS },
      mark: { type: "line", strokeWidth: 2, strokeCap: "round", strokeJoin: "round" },
      encoding: {
        // The colour encoding lives on this layer alone. Repeating it across
        // layers produces one legend per layer, drawn on top of each other.
        // The legend sits at the bottom so the top edge is free for the
        // horizontal y-axis title.
        color: {
          field: "scenario",
          type: "nominal",
          sort: SHOWN.map((s) => s.label),
          scale: { domain: SHOWN.map((s) => s.label), range: t.series },
          legend: { orient: "bottom", title: null, offset: 16 },
        },
        tooltip: [
          { field: "scenario", type: "nominal", title: "Scenario" },
          { field: "radius", type: "quantitative", title: "Radius, km" },
          { field: "ratio", type: "quantitative", title: "% of a full disc", format: ".0f" },
        ],
      },
    },
    {
      data: { values: ENDS },
      mark: { type: "point", filled: true, size: 80, stroke: t.surface1, strokeWidth: 2 },
      encoding: {
        color: {
          field: "scenario",
          type: "nominal",
          scale: { domain: SHOWN.map((s) => s.label), range: t.series },
          legend: null,
        },
      },
    },
    {
      data: { values: ENDS },
      mark: { type: "text", align: "right", dy: -14, fontSize: 11 },
      encoding: {
        color: { value: t.textSecondary },
        text: { field: "ratio", type: "quantitative", format: ".0f" },
      },
    },
  ],
});

export function CatchmentCurve() {
  return (
    <VegaChart
      spec={spec}
      minHeight={300}
      ariaLabel="Effective catchment as a percentage of a full disc, against travel radius, for a closed frontier, the permeability observed today, and a working cross-border labour market"
    />
  );
}

export function CatchmentCurveTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Radius, km</th>
          {SHOWN.map((s) => (
            <th key={s.id}>{s.label}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {RADII.map((r) => (
          <tr key={r}>
            <td>{r}</td>
            {SHOWN.map((s) => (
              <td key={s.id}>{(catchmentRatio(r, s.value) * 100).toFixed(0)}%</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
