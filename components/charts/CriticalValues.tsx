"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { BACKGROUND_DEPOSITION, HABITATS } from "@/data/nitrogen";

/**
 * Critical values against the load.
 *
 * The bars are what each habitat can take. The rule is what the region
 * delivers. Five of the six fall short of it, and raised bog falls short by a
 * factor of four — which is Enschede's development problem stated in one
 * figure, at a receptor inside its own municipal boundary.
 *
 * The sixth bar, alluvial forest, clears the rule. It is kept in deliberately:
 * a chart that showed only the habitats supporting the argument would be a
 * weaker chart, and the exception is itself informative — tolerance varies by
 * a factor of nearly five across habitats sharing the same air.
 */
const BG = BACKGROUND_DEPOSITION.value;

const ROWS = HABITATS.map((h) => ({
  habitat: h.label,
  code: h.code,
  kdw: h.kdw,
  factor: Number((BG / h.kdw).toFixed(1)),
  emphasis: h.kdw <= 500 ? "yes" : "no",
}));

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width: "container",
  height: { step: 34 },
  layer: [
    {
      data: { values: ROWS },
      mark: { type: "bar", cornerRadiusEnd: 4, height: 18 },
      encoding: {
        y: {
          field: "habitat",
          type: "nominal",
          sort: { field: "kdw", order: "ascending" },
          axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary, labelLimit: 400 },
        },
        x: {
          field: "kdw",
          type: "quantitative",
          scale: { domain: [0, 2000], nice: false },
          axis: {
            title: "mol nitrogen per hectare per year",
            values: [0, 500, 1000, 1500, 2000],
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
        tooltip: [
          { field: "habitat", type: "nominal", title: "Habitat" },
          { field: "code", type: "nominal", title: "Code" },
          { field: "kdw", type: "quantitative", title: "Critical value, mol N/ha/yr" },
          { field: "factor", type: "quantitative", title: "Regional load ÷ critical value" },
        ],
      },
    },
    {
      data: { values: [{ bg: BG }] },
      mark: { type: "rule", strokeWidth: 2, color: t.textPrimary, opacity: 0.55 },
      encoding: { x: { field: "bg", type: "quantitative" } },
    },
    {
      data: { values: [{ bg: BG, note: `regional load ${BG.toLocaleString("en-GB")}` }] },
      mark: {
        type: "text",
        align: "right",
        dx: -8,
        dy: -8,
        baseline: "top",
        fontSize: 11,
        color: t.textSecondary,
      },
      encoding: {
        x: { field: "bg", type: "quantitative" },
        y: { value: 0 },
        text: { field: "note", type: "nominal" },
      },
    },
  ],
});

export function CriticalValues() {
  return (
    <VegaChart
      spec={spec}
      minHeight={260}
      ariaLabel="Critical nitrogen deposition values by habitat, from 400 for active raised bog to 1857 for alluvial forest, all below the regional load of about 1600 mol per hectare per year"
    />
  );
}

export function CriticalValuesTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Habitat</th>
          <th>Code</th>
          <th>Critical value</th>
          <th>Load ÷ critical value</th>
        </tr>
      </thead>
      <tbody>
        {[...HABITATS]
          .sort((a, b) => a.kdw - b.kdw)
          .map((h) => (
            <tr key={h.code}>
              <td>{h.label}</td>
              <td>{h.code}</td>
              <td>{h.kdw.toLocaleString("en-GB")}</td>
              <td>{(BG / h.kdw).toFixed(1)}×</td>
            </tr>
          ))}
      </tbody>
    </table>
  );
}
