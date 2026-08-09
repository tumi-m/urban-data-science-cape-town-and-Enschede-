"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import {
  DWELLING,
  LEVERS,
  annualUseNOxKg,
  kgNOxToMolN,
  lifetimeNOxKg,
} from "@/data/nitrogen";

/**
 * Where a dwelling's nitrogen actually goes.
 *
 * Two segments, stacked, over a fifty-year life: the plant that builds it and
 * the traffic it attracts. The construction segment is the one that gets the
 * political attention and it is the smaller of the two by an order of
 * magnitude. The larger segment is set by where the dwelling is put and how
 * much parking is provided with it — decisions taken before any nitrogen
 * calculation is run.
 */
const ROWS = LEVERS.flatMap((l) => {
  const construction = l.electricPlant ? 0 : DWELLING.constructionNOxKg.value;
  const use = annualUseNOxKg() * l.carKmScale * DWELLING.lifetimeYears;
  return [
    { scenario: l.label, phase: "Construction plant", kg: Number(construction.toFixed(1)), order: 0 },
    { scenario: l.label, phase: "Traffic attracted, 50 years", kg: Number(use.toFixed(1)), order: 1 },
  ];
});

const TOTALS = LEVERS.map((l) => ({
  scenario: l.label,
  total: Number(lifetimeNOxKg(l.carKmScale, l.electricPlant).toFixed(0)),
}));

const ORDER = LEVERS.map((l) => l.label);

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width: "container",
  height: { step: 40 },
  encoding: {
    y: {
      field: "scenario",
      type: "nominal",
      sort: ORDER,
      axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary, labelLimit: 420 },
    },
  },
  layer: [
    {
      data: { values: ROWS },
      // A 2px stroke in the surface colour is the gap, not a border: it is how
      // touching segments are separated without adding contrasting ink.
      mark: {
        type: "bar",
        height: 20,
        cornerRadiusEnd: 4,
        stroke: t.surface1,
        strokeWidth: 2,
      },
      encoding: {
        x: {
          field: "kg",
          type: "quantitative",
          stack: "zero",
          scale: { domain: [0, 140], nice: false },
          axis: {
            title: "kg of nitrogen oxides over a fifty-year life",
            values: [0, 25, 50, 75, 100, 125],
            grid: true,
            gridColor: t.grid,
          },
        },
        color: {
          field: "phase",
          type: "nominal",
          sort: ["Construction plant", "Traffic attracted, 50 years"],
          scale: {
            domain: ["Construction plant", "Traffic attracted, 50 years"],
            range: [t.series[1], t.series[0]],
          },
          legend: { orient: "top", title: null },
        },
        order: { field: "order", type: "quantitative" },
        tooltip: [
          { field: "scenario", type: "nominal", title: "Scenario" },
          { field: "phase", type: "nominal", title: "Phase" },
          { field: "kg", type: "quantitative", title: "kg NOx" },
        ],
      },
    },
    {
      data: { values: TOTALS },
      mark: { type: "text", align: "left", dx: 10, fontSize: 11, color: t.textSecondary },
      encoding: {
        x: { field: "total", type: "quantitative" },
        text: { field: "total", type: "quantitative", format: ".0f" },
      },
    },
  ],
});

export function DwellingNitrogen() {
  return (
    <VegaChart
      spec={spec}
      minHeight={280}
      ariaLabel="Lifetime nitrogen oxide emissions per dwelling by scenario, split between construction plant and attracted traffic; traffic dominates in every case"
    />
  );
}

export function DwellingNitrogenTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Scenario</th>
          <th>Construction, kg</th>
          <th>Traffic, kg</th>
          <th>Total, kg</th>
          <th>Total, mol N</th>
          <th>vs baseline</th>
        </tr>
      </thead>
      <tbody>
        {LEVERS.map((l) => {
          const construction = l.electricPlant ? 0 : DWELLING.constructionNOxKg.value;
          const use = annualUseNOxKg() * l.carKmScale * DWELLING.lifetimeYears;
          const total = construction + use;
          const base = lifetimeNOxKg(1, false);
          return (
            <tr key={l.id}>
              <td>{l.label}</td>
              <td>{construction.toFixed(0)}</td>
              <td>{use.toFixed(0)}</td>
              <td>{total.toFixed(0)}</td>
              <td>{Math.round(kgNOxToMolN(total)).toLocaleString("en-GB")}</td>
              <td>{total === base ? "—" : `−${(100 * (1 - total / base)).toFixed(0)}%`}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
