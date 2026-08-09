"use client";

import { useEffect, useRef, useState } from "react";
import { select } from "d3-selection";
import { scaleLinear } from "d3-scale";
import {
  BORDER_DISTANCE_KM,
  DENSITY,
  PERMEABILITY_SCENARIOS,
  accessiblePopulation,
  catchmentRatio,
  discArea,
  effectiveCatchment,
  segmentArea,
} from "@/data/border";
import { sig } from "@/lib/provenance";
import { useMeasure } from "@/components/useMeasure";

/**
 * The cut disc.
 *
 * Drawn imperatively because the figure is not a chart type — it is a piece of
 * geometry with a clip path, a moving fill opacity and a set of rings, and
 * expressing that through a visual grammar would be a longer way round.
 *
 * The reading is direct: the shaded ground is the catchment the city can
 * actually draw on, and the ground east of the line only counts to the extent
 * that the border is permeable. Permeability here is an institutional
 * quantity, not a distance, which is precisely why it is the adjustable one.
 *
 * A note on the class names. They are prefixed because the obvious ones —
 * `ring`, `border`, `outline` — are live utility classes in the stylesheet,
 * and a d3 join that names a node `outline` gets a one-pixel black rectangle
 * drawn around its bounding box by CSS that has nothing to do with this figure.
 * Selector namespaces are shared whether or not the two systems know about
 * each other.
 */
const R_VIEW = 34; // km of ground shown either side of the centre

export function CatchmentGeometry() {
  const [hostRef, { width }] = useMeasure<HTMLDivElement>();
  const svgRef = useRef<SVGSVGElement>(null);
  const [permeability, setPermeability] = useState(0.15);
  const [radius, setRadius] = useState(20);

  const size = Math.max(240, Math.min(width || 420, 460));

  useEffect(() => {
    const svg = select(svgRef.current);
    if (!svgRef.current || size < 100) return;

    const x = scaleLinear().domain([-R_VIEW, R_VIEW]).range([0, size]);
    const y = scaleLinear().domain([-R_VIEW, R_VIEW]).range([size, 0]);
    const km = (v: number) => x(v) - x(0); // km → px, positive

    svg.attr("viewBox", `0 0 ${size} ${size}`).attr("width", size).attr("height", size);

    let defs = svg.select<SVGDefsElement>("defs");
    if (defs.empty()) defs = svg.append("defs");

    let clip = defs.select<SVGClipPathElement>("#beyond-border");
    if (clip.empty()) clip = defs.append("clipPath").attr("id", "beyond-border");
    clip
      .selectAll("rect")
      .data([0])
      .join("rect")
      .attr("x", x(BORDER_DISTANCE_KM))
      .attr("y", 0)
      .attr("width", Math.max(0, size - x(BORDER_DISTANCE_KM)))
      .attr("height", size);

    let g = svg.select<SVGGElement>("g.map-plot");
    if (g.empty()) g = svg.append("g").attr("class", "map-plot");

    // Reference rings, so the chosen radius is read against a scale.
    g.selectAll<SVGCircleElement, number>("circle.scale-ring")
      .data([10, 20, 30])
      .join("circle")
      .attr("class", "scale-ring")
      .attr("cx", x(0))
      .attr("cy", y(0))
      .attr("r", (d) => km(d))
      .attr("fill", "none")
      .attr("stroke", "var(--grid)")
      .attr("stroke-width", 1);

    // The catchment inside the border: what an interior city would simply have.
    g.selectAll<SVGCircleElement, number>("circle.catch-disc")
      .data([radius])
      .join("circle")
      .attr("class", "catch-disc")
      .attr("cx", x(0))
      .attr("cy", y(0))
      .attr("r", (d) => km(d))
      .attr("fill", "var(--series-1)")
      .attr("fill-opacity", 0.18)
      .attr("stroke", "none");

    // The part beyond the border, faded back in proportion to permeability.
    g.selectAll<SVGCircleElement, number>("circle.catch-beyond")
      .data([radius])
      .join("circle")
      .attr("class", "catch-beyond")
      .attr("clip-path", "url(#beyond-border)")
      .attr("cx", x(0))
      .attr("cy", y(0))
      .attr("r", (d) => km(d))
      .attr("fill", "var(--surface-1)")
      .attr("fill-opacity", 1 - permeability)
      .attr("stroke", "none");

    // The outline goes on top of the fade, so the disc stays legible as a
    // shape whatever the permeability. Fading the outline too would make the
    // geometry harder to read without adding anything to the argument.
    g.selectAll<SVGCircleElement, number>("circle.catch-edge")
      .data([radius])
      .join("circle")
      .attr("class", "catch-edge")
      .attr("cx", x(0))
      .attr("cy", y(0))
      .attr("r", (d) => km(d))
      .attr("fill", "none")
      .attr("stroke", "var(--series-1)")
      .attr("stroke-width", 2);

    g.selectAll<SVGLineElement, number>("line.frontier")
      .data([BORDER_DISTANCE_KM])
      .join("line")
      .attr("class", "frontier")
      .attr("x1", (d) => x(d))
      .attr("x2", (d) => x(d))
      .attr("y1", 0)
      .attr("y2", size)
      .attr("stroke", "var(--series-2)")
      .attr("stroke-width", 2);

    g.selectAll<SVGCircleElement, number>("circle.city-dot")
      .data([0])
      .join("circle")
      .attr("class", "city-dot")
      .attr("cx", x(0))
      .attr("cy", y(0))
      .attr("r", 4)
      .attr("fill", "var(--series-1)")
      .attr("stroke", "var(--surface-1)")
      .attr("stroke-width", 2);

    g.selectAll<SVGTextElement, { t: string; px: number; py: number; anchor: string }>(
      "text.map-label",
    )
      .data([
        { t: "Enschede", px: x(0) + 9, py: y(0) - 6, anchor: "start" },
        { t: "border", px: x(BORDER_DISTANCE_KM) + 6, py: 14, anchor: "start" },
        { t: `${radius} km`, px: x(0), py: y(radius) - 7, anchor: "middle" },
      ])
      .join("text")
      .attr("class", "map-label")
      .attr("x", (d) => d.px)
      .attr("y", (d) => d.py)
      .attr("text-anchor", (d) => d.anchor)
      .attr("font-size", 11)
      .attr("fill", "var(--text-secondary)")
      .text((d) => d.t);
  }, [size, permeability, radius]);

  const ratio = catchmentRatio(radius, permeability);
  const lost = 1 - catchmentRatio(radius, 0);
  const people = accessiblePopulation(radius, permeability);
  const peopleClosed = accessiblePopulation(radius, 0);

  return (
    <div ref={hostRef} className="w-full">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
        <svg ref={svgRef} role="img" aria-label="Travel-radius disc cut by the national border" />

        <div className="min-w-0 flex-1 space-y-6">
          <Control
            label="Travel radius"
            value={`${radius} km`}
            min={5}
            max={30}
            step={5}
            current={radius}
            onChange={setRadius}
          />
          <Control
            label="Border permeability"
            value={permeability.toFixed(2)}
            min={0}
            max={1}
            step={0.05}
            current={permeability}
            onChange={setPermeability}
          />

          <div className="flex flex-wrap gap-2">
            {PERMEABILITY_SCENARIOS.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setPermeability(s.value)}
                aria-pressed={Math.abs(permeability - s.value) < 0.001}
                className={`rounded border px-2 py-1 text-[0.6875rem] transition-colors ${
                  Math.abs(permeability - s.value) < 0.001
                    ? "border-ink-3 text-ink"
                    : "border-rule text-ink-3 hover:text-ink-2"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-[0.8125rem]">
            <Readout
              term="Geometric loss at this radius"
              detail={`${sig(segmentArea(radius, BORDER_DISTANCE_KM), 3)} km² of the ${sig(discArea(radius), 3)} km² disc lies beyond the border`}
            >
              {(lost * 100).toFixed(0)}%
            </Readout>
            <Readout
              term="Effective catchment"
              detail={`${sig(effectiveCatchment(radius, permeability), 3)} km² against a full disc`}
            >
              {(ratio * 100).toFixed(0)}%
            </Readout>
            <Readout
              term="Accessible population"
              detail={`at ${DENSITY.dutchSide} and ${DENSITY.germanSide} inhabitants per km² either side`}
            >
              {Math.round(people / 1000).toLocaleString("en-GB")}k
            </Readout>
            <Readout
              term="Gained over a closed frontier"
              detail="the return on institutional work rather than on construction"
            >
              {Math.round((people - peopleClosed) / 1000).toLocaleString("en-GB")}k
            </Readout>
          </dl>
        </div>
      </div>
    </div>
  );
}

function Control({
  label,
  value,
  min,
  max,
  step,
  current,
  onChange,
}: {
  label: string;
  value: string;
  min: number;
  max: number;
  step: number;
  current: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="block">
      <span className="flex items-baseline justify-between text-[0.6875rem] uppercase tracking-widest text-ink-3">
        {label}
        <span className="tabular-nums text-ink">{value}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={current}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full"
      />
    </label>
  );
}

function Readout({
  term,
  detail,
  children,
}: {
  term: string;
  detail: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-t border-rule pt-2">
      <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">{term}</dt>
      <dd className="mt-1 text-[1.375rem] font-semibold leading-none tabular-nums text-ink">
        {children}
      </dd>
      <dd className="mt-1.5 text-[0.6875rem] leading-relaxed text-ink-3">{detail}</dd>
    </div>
  );
}
