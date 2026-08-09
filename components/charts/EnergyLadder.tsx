"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import { MODES, kWhPerPkm, pkmPerKWh } from "@/data/mobility";

/**
 * The ladder.
 *
 * A dot plot rather than bars, because the range spans a factor of fifty and a
 * bar needs a zero baseline that a logarithmic axis cannot give it. Every dot
 * is labelled, which is normally a mistake — here the axis is logarithmic and
 * a reader genuinely cannot recover a value from it, so the labels are doing
 * work rather than decorating.
 *
 * One colour is emphasis, not identity: the assisted bicycle is picked out
 * because it is the argument, and the rest recede.
 */
const ROWS = MODES.map((m) => ({
  mode: m.label,
  pkm: Number(pkmPerKWh(m).toFixed(1)),
  kwh: Number(kWhPerPkm(m).toFixed(4)),
  family: m.family,
  emphasis: m.id === "ebike" ? "yes" : "no",
  basis: m.basis,
}));

const spec = (t: Tokens): VisualizationSpec => ({
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  data: { values: ROWS },
  width: "container",
  height: { step: 30 },
  encoding: {
    y: {
      field: "mode",
      type: "nominal",
      sort: { field: "pkm", order: "descending" },
      axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary },
    },
    x: {
      field: "pkm",
      type: "quantitative",
      scale: { type: "log", domain: [1, 200], nice: false },
      axis: {
        title: "passenger-kilometres per kilowatt-hour, logarithmic",
        values: [1, 2, 5, 10, 20, 50, 100, 200],
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
      mark: { type: "rule", strokeWidth: 2, opacity: 0.35, strokeCap: "round" },
      encoding: { x: { datum: 1 }, x2: { field: "pkm" } },
    },
    {
      mark: { type: "point", filled: true, size: 110, stroke: t.surface1, strokeWidth: 2 },
      encoding: {
        tooltip: [
          { field: "mode", type: "nominal", title: "Mode" },
          { field: "pkm", type: "quantitative", title: "p-km per kWh" },
          { field: "kwh", type: "quantitative", title: "kWh per p-km", format: ".3f" },
          { field: "basis", type: "nominal", title: "Basis" },
        ],
      },
    },
    {
      mark: { type: "text", align: "left", dx: 12, fontSize: 11 },
      encoding: {
        // Values wear a text token. The coloured dot beside them carries the
        // emphasis; a number tinted with the series colour does not.
        color: { value: t.textSecondary },
        text: { field: "pkm", type: "quantitative", format: ".0f" },
      },
    },
  ],
});

export function EnergyLadder() {
  return (
    <VegaChart
      spec={spec}
      minHeight={280}
      ariaLabel="Passenger-kilometres delivered per kilowatt-hour by mode, on a logarithmic scale, ranging from about two for a petrol car to about ninety for an electric bicycle"
    />
  );
}

export function EnergyLadderTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Mode</th>
          <th>p-km per kWh</th>
          <th>kWh per p-km</th>
          <th>Occupancy</th>
        </tr>
      </thead>
      <tbody>
        {[...MODES]
          .sort((a, b) => pkmPerKWh(b) - pkmPerKWh(a))
          .map((m) => (
            <tr key={m.id}>
              <td>{m.label}</td>
              <td>{pkmPerKWh(m).toFixed(1)}</td>
              <td>{kWhPerPkm(m).toFixed(3)}</td>
              <td>{m.occupancy}</td>
            </tr>
          ))}
      </tbody>
    </table>
  );
}
