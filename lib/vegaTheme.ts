import type { Config } from "vega-lite";

/**
 * Chart chrome, subtracted.
 *
 * Everything switched off here is ink that is not data: domain lines, tick
 * marks, chart borders, view frames, legend boxes, and — most of all — the
 * default gridlines. What survives is a single hairline grid on the measured
 * axis only, one step off the surface, because a reader estimating a value
 * needs something and estimating from nothing is worse than a faint line.
 *
 * Colours are read from the live stylesheet rather than hard-coded so that a
 * theme change produces the same chart in the other mode, not a chart with one
 * mode's palette on the other mode's surface.
 */
export interface Tokens {
  surface1: string;
  surface2: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  rule: string;
  grid: string;
  series: [string, string, string];
}

const FALLBACK: Tokens = {
  surface1: "#fcfcfb",
  surface2: "#f4f3f0",
  textPrimary: "#0b0b0b",
  textSecondary: "#52514e",
  textMuted: "#78766f",
  rule: "#e2e0da",
  grid: "#eceae4",
  series: ["#2a78d6", "#eb6834", "#1baf7a"],
};

export function readTokens(): Tokens {
  if (typeof window === "undefined") return FALLBACK;
  const s = getComputedStyle(document.documentElement);
  const v = (name: string, fallback: string) => s.getPropertyValue(name).trim() || fallback;
  return {
    surface1: v("--surface-1", FALLBACK.surface1),
    surface2: v("--surface-2", FALLBACK.surface2),
    textPrimary: v("--text-primary", FALLBACK.textPrimary),
    textSecondary: v("--text-secondary", FALLBACK.textSecondary),
    textMuted: v("--text-muted", FALLBACK.textMuted),
    rule: v("--rule", FALLBACK.rule),
    grid: v("--grid", FALLBACK.grid),
    series: [
      v("--series-1", FALLBACK.series[0]),
      v("--series-2", FALLBACK.series[1]),
      v("--series-3", FALLBACK.series[2]),
    ],
  };
}

const FONT =
  'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

export function vegaConfig(t: Tokens): Config {
  return {
    background: "transparent",
    font: FONT,
    padding: 0,
    autosize: { type: "fit", contains: "padding", resize: true },

    view: { stroke: null, continuousWidth: 480, continuousHeight: 260 },

    axis: {
      labelFont: FONT,
      labelFontSize: 11,
      labelColor: t.textMuted,
      labelPadding: 6,
      titleFont: FONT,
      titleFontSize: 11,
      titleFontWeight: 500,
      titleColor: t.textMuted,
      titlePadding: 10,
      domain: false,
      ticks: false,
      grid: false,
      labelOverlap: "greedy",
    },
    axisY: {
      grid: true,
      gridColor: t.grid,
      gridWidth: 1,
      gridDash: [],
      titleAngle: 0,
      titleAlign: "left",
      titleAnchor: "start",
      titleBaseline: "bottom",
      titleY: -8,
      titleX: 0,
    },
    axisX: {
      grid: false,
      labelAngle: 0,
    },

    legend: {
      orient: "top",
      direction: "horizontal",
      title: null,
      labelFont: FONT,
      labelFontSize: 11,
      labelColor: t.textSecondary,
      symbolType: "square",
      symbolSize: 64,
      symbolStrokeWidth: 0,
      offset: 4,
      padding: 0,
      rowPadding: 4,
      columnPadding: 14,
      labelLimit: 240,
    },

    // Mark specs, applied once here so no individual chart restates them.
    bar: { cornerRadiusEnd: 4, color: t.series[0] },
    line: { strokeWidth: 2, strokeJoin: "round", strokeCap: "round", color: t.series[0] },
    point: { size: 64, filled: true, stroke: t.surface1, strokeWidth: 2, color: t.series[0] },
    area: { line: { strokeWidth: 2 }, fillOpacity: 0.1, color: t.series[0] },
    rule: { color: t.textMuted, strokeWidth: 1 },
    text: { font: FONT, fontSize: 11, color: t.textSecondary },

    range: { category: t.series },

    title: { anchor: "start", font: FONT, fontSize: 12, color: t.textSecondary, offset: 8 },
  };
}
