"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { CT } from "@/data/capetown";

/**
 * How Cape Town's land splits up.
 *
 * One bar, broken into parts, because the question is "how much of the whole
 * is left" and that is a part-to-whole question. The order runs from most
 * restricted to least, so the reader accumulates the restriction left to right
 * and lands on what is actually available.
 */
const MUNICIPAL = CT.municipalArea.value;
const PROTECTED_KM2 = CT.protectedArea.value / 100;
const EDGE = CT.urbanEdgeArea.value;

const ROWS = [
  {
    part: "Formally protected",
    km2: Math.round(PROTECTED_KM2),
    order: 0,
    detail: "National parks, nature reserves and marine protected areas.",
  },
  {
    part: "Inside the urban edge",
    km2: EDGE,
    order: 1,
    detail: "Where building is allowed at all.",
  },
  {
    part: "Everything else",
    km2: Math.round(MUNICIPAL - PROTECTED_KM2 - EDGE),
    order: 2,
    detail:
      "Farmland, biodiversity areas short of formal protection, and mountain outside the edge.",
  },
];

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  data: { values: ROWS },
  width: "container",
  height: 90,
  layer: [
    {
      // A 2px stroke in the surface colour is the gap, not a border.
      mark: { type: "bar", stroke: t.surface1, strokeWidth: 2, cornerRadiusEnd: 4 },
      encoding: {
        x: {
          field: "km2",
          type: "quantitative",
          stack: "zero",
          title: `km² of Cape Town's ${MUNICIPAL.toLocaleString("en-GB")} km²`,
          axis: { grid: true, gridColor: t.grid, format: "~s" },
        },
        color: {
          field: "part",
          type: "nominal",
          sort: ROWS.map((r) => r.part),
          scale: {
            domain: ROWS.map((r) => r.part),
            range: [t.series[2], t.series[0], t.textMuted],
          },
          legend: { orient: "top", title: null },
        },
        order: { field: "order", type: "quantitative" },
        tooltip: [
          { field: "part", type: "nominal", title: "Land" },
          { field: "km2", type: "quantitative", title: "km²", format: "," },
          { field: "detail", type: "nominal", title: "What it is" },
        ],
      },
    },
  ],
});

export function CapeTownLand() {
  return (
    <VegaChart
      spec={spec}
      minHeight={120}
      ariaLabel="How Cape Town's 2,451 square kilometres split between protected land, land inside the urban edge, and everything else"
    />
  );
}

export function CapeTownLandTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Land</th>
          <th>km²</th>
          <th>Share</th>
        </tr>
      </thead>
      <tbody>
        {ROWS.map((r) => (
          <tr key={r.part}>
            <td>{r.part}</td>
            <td>{r.km2.toLocaleString("en-GB")}</td>
            <td>{((r.km2 / MUNICIPAL) * 100).toFixed(0)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
