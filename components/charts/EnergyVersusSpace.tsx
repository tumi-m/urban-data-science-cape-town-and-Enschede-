"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { MODES, kWhPerPkm } from "@/data/mobility";

/**
 * Two scarcities, one plot.
 *
 * Energy per passenger-kilometre against plan area per passenger, both
 * logarithmic. The modes fall along a diagonal, which is the finding: in a
 * city with a settlement boundary and a nature network on three sides, the
 * mode that wastes energy is the same mode that wastes the land there is none
 * of. They are not separate problems being traded off against each other.
 */
const ROWS = MODES.map((m) => ({
  mode: m.label,
  kwh: Number(kWhPerPkm(m).toFixed(4)),
  m2: m.m2PerPassenger,
  emphasis: m.family === "private" ? "yes" : "no",
}));

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  data: { values: ROWS },
  width: "container",
  height: 300,
  encoding: {
    x: {
      field: "kwh",
      type: "quantitative",
      scale: { type: "log", domain: [0.008, 1], nice: false },
      axis: {
        title: "kilowatt-hours per passenger-kilometre, logarithmic",
        values: [0.01, 0.03, 0.1, 0.3, 1],
        format: ".2~f",
        grid: true,
        gridColor: t.grid,
      },
    },
    y: {
      field: "m2",
      type: "quantitative",
      scale: { type: "log", domain: [1, 100], nice: false },
      axis: {
        title: "m² of plan area per passenger, logarithmic",
        values: [1, 3, 10, 30, 100],
        format: "~s",
        grid: true,
        gridColor: t.grid,
      },
    },
    color: {
      field: "emphasis",
      type: "nominal",
      scale: { domain: ["no", "yes"], range: [t.series[0], t.series[1]] },
      legend: null,
    },
  },
  layer: [
    {
      mark: { type: "point", filled: true, size: 120, stroke: t.surface1, strokeWidth: 2 },
      encoding: {
        tooltip: [
          { field: "mode", type: "nominal", title: "Mode" },
          { field: "kwh", type: "quantitative", title: "kWh per p-km", format: ".3f" },
          { field: "m2", type: "quantitative", title: "m² per passenger" },
        ],
      },
    },
    {
      mark: { type: "text", align: "left", dx: 11, dy: -1, fontSize: 11 },
      encoding: {
        color: { value: t.textSecondary },
        text: { field: "mode", type: "nominal" },
      },
    },
  ],
});

export function EnergyVersusSpace() {
  return (
    <VegaChart
      spec={spec}
      minHeight={320}
      ariaLabel="Energy per passenger-kilometre plotted against plan area per passenger; the modes fall along a rising diagonal, with cars at the top right and bicycles at the bottom left"
    />
  );
}
