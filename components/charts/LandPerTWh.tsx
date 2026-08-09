"use client";

import type { VisualizationSpec } from "vega-embed";
import { VegaChart } from "@/components/VegaChart";
import type { Tokens } from "@/lib/vegaTheme";
import {
  TARGET,
  TECHNOLOGIES,
  exclusiveKm2ForTarget,
  grossKm2ForTarget,
  shareOfMunicipality,
  unitsForTarget,
} from "@/data/energy";

/**
 * Land for the target, gross against exclusive.
 *
 * A dumbbell, because the story is the distance between two numbers for the
 * same technology rather than the ranking of either one. Wind's two ends are
 * two orders of magnitude apart: it associates with a lot of land and withdraws
 * almost none of it. Ground-mounted solar's two ends coincide.
 *
 * Rooftop solar sits at zero on both, which a logarithmic axis cannot draw. It
 * is stated in the caption instead of being nudged onto the scale, because
 * placing a zero at an arbitrary small value is how a chart starts lying.
 */
const PLOTTED = TECHNOLOGIES.filter((t) => t.exclusiveKm2PerUnit > 0 || t.grossKm2PerUnit > 0);

const ROWS = PLOTTED.flatMap((t) => [
  {
    tech: t.label,
    measure: "Associated land",
    km2: Number(grossKm2ForTarget(t).toFixed(3)),
  },
  {
    tech: t.label,
    measure: "Land withdrawn from other use",
    km2: Number(exclusiveKm2ForTarget(t).toFixed(3)),
  },
]);

const SPANS = PLOTTED.map((t) => ({
  tech: t.label,
  lo: Number(Math.min(grossKm2ForTarget(t), exclusiveKm2ForTarget(t)).toFixed(3)),
  hi: Number(Math.max(grossKm2ForTarget(t), exclusiveKm2ForTarget(t)).toFixed(3)),
}));

const TOOLTIP = [
  { field: "tech", type: "nominal" as const, title: "Technology" },
  { field: "measure", type: "nominal" as const, title: "Measure" },
  { field: "km2", type: "quantitative" as const, title: "km²", format: ".2f" },
];

const spec = (t: Tokens): VisualizationSpec => {
  const MEASURE_COLOR = {
    field: "measure",
    type: "nominal" as const,
    scale: {
      domain: ["Associated land", "Land withdrawn from other use"],
      range: [t.series[0], t.series[1]],
    },
  };

  return {
  $schema: "https://vega.github.io/schema/vega-lite/v6.json",
  width: "container",
  height: { step: 56 },
  encoding: {
    y: {
      field: "tech",
      type: "nominal",
      sort: PLOTTED.map((x) => x.label),
      axis: { title: null, labelFontSize: 12, labelColor: t.textPrimary },
    },
    x: {
      type: "quantitative",
      scale: { type: "log", domain: [0.1, 100], nice: false },
      axis: {
        title: `km² required for the ${TARGET.value} TWh per year regional target, logarithmic`,
        values: [0.1, 1, 10, 100],
        format: "~g",
        grid: true,
        gridColor: t.grid,
      },
    },
  },
  layer: [
    {
      data: { values: SPANS },
      mark: { type: "rule", strokeWidth: 2, color: t.textMuted, opacity: 0.4, strokeCap: "round" },
      encoding: {
        x: { field: "lo", type: "quantitative" },
        x2: { field: "hi" },
      },
    },
    // Two point layers rather than one, sized so the coincident case still
    // reads. Ground-mounted solar withdraws exactly the land it occupies, so
    // its two dots land on the same pixel; drawing the larger one underneath
    // leaves a visible ring, which says "these are equal" rather than "one of
    // these is missing".
    {
      data: { values: ROWS.filter((r) => r.measure === "Associated land") },
      mark: { type: "point", filled: true, size: 220, stroke: t.surface1, strokeWidth: 2 },
      encoding: {
        x: { field: "km2", type: "quantitative" },
        color: { ...MEASURE_COLOR, legend: { orient: "top", title: null } },
        tooltip: TOOLTIP,
      },
    },
    {
      data: { values: ROWS.filter((r) => r.measure !== "Associated land") },
      mark: { type: "point", filled: true, size: 90, stroke: t.surface1, strokeWidth: 2 },
      encoding: {
        x: { field: "km2", type: "quantitative" },
        color: { ...MEASURE_COLOR, legend: null },
        tooltip: TOOLTIP,
      },
    },
  ],
  };
};

export function LandPerTWh() {
  return (
    <VegaChart
      spec={spec}
      minHeight={170}
      ariaLabel="Land needed for the regional renewable target: onshore wind associates with about 32 km² but withdraws under 0.3 km², while ground-mounted solar withdraws all 23 km² it occupies"
    />
  );
}

export function LandPerTWhTable() {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Technology</th>
          <th>Units for the target</th>
          <th>Associated km²</th>
          <th>Withdrawn km²</th>
          <th>Share of Enschede</th>
        </tr>
      </thead>
      <tbody>
        {TECHNOLOGIES.map((t) => (
          <tr key={t.id}>
            <td>{t.label}</td>
            <td>
              {Math.round(unitsForTarget(t)).toLocaleString("en-GB")} {t.unitLabel}
              {Math.round(unitsForTarget(t)) === 1 ? "" : "s"}
            </td>
            <td>{grossKm2ForTarget(t).toFixed(2)}</td>
            <td>{exclusiveKm2ForTarget(t).toFixed(2)}</td>
            <td>{(shareOfMunicipality(exclusiveKm2ForTarget(t)) * 100).toFixed(1)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
