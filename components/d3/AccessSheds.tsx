"use client";

import { useMemo, useState } from "react";
import { scaleLinear } from "d3-scale";
import {
  ACCESS_MODES,
  CITY_DISC,
  DENSITY_MODEL,
  STATIONS,
  coverage,
  effectiveRadiusKm,
  shedAreaKm2,
} from "@/data/access";
import { useMeasure } from "@/components/useMeasure";

/**
 * Sheds over the built-up area.
 *
 * The union of the three discs is drawn as a single translucent group rather
 * than as three translucent circles: group opacity composites once, so overlaps
 * do not darken and the reader sees the union instead of a Venn diagram. The
 * shape on screen is the same shape the coverage figures are computed from.
 *
 * The grey wash underneath is the density gradient, and it is the reason the
 * two readouts differ. Coverage counted in hectares treats the pale outer ring
 * as equal to the dark centre; coverage counted in people does not.
 */
const VIEW_KM = 6.6;

export function AccessSheds() {
  const [hostRef, { width }] = useMeasure<HTMLDivElement>();
  const [radiusKm, setRadiusKm] = useState(0.8);
  const [useCircuity, setUseCircuity] = useState(true);

  const size = Math.max(260, Math.min(width || 420, 440));

  // The mode a nominal radius corresponds to, if any — used to apply the right
  // circuity factor and to light up the matching preset.
  const mode = ACCESS_MODES.find((m) => Math.abs(m.radiusKm - radiusKm) < 0.001);
  const circuity = mode ? mode.circuity : 1.25;
  const reach = useCircuity ? radiusKm / circuity : radiusKm;

  const cov = useMemo(() => coverage(reach), [reach]);

  const x = scaleLinear().domain([-VIEW_KM / 2, VIEW_KM / 2]).range([0, size]);
  const y = scaleLinear().domain([-VIEW_KM / 2, VIEW_KM / 2]).range([size, 0]);
  const km = (v: number) => (v / VIEW_KM) * size;

  return (
    <div ref={hostRef} className="w-full">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={`Station access sheds over Enschede's built-up area at a ${radiusKm.toFixed(1)} kilometre radius, covering ${(cov.land * 100).toFixed(0)} per cent of land and ${(cov.population * 100).toFixed(0)} per cent of residents`}
          className="shrink-0"
        >
          <defs>
            <clipPath id="city-disc">
              <circle cx={x(0)} cy={y(0)} r={km(CITY_DISC.radiusKm)} />
            </clipPath>
            <radialGradient id="density-wash">
              <stop offset="0%" stopColor="var(--text-primary)" stopOpacity={0.22} />
              <stop offset="45%" stopColor="var(--text-primary)" stopOpacity={0.11} />
              <stop offset="100%" stopColor="var(--text-primary)" stopOpacity={0.03} />
            </radialGradient>
          </defs>

          {/* Density, as a backdrop. The gradient stops follow the exponential. */}
          <circle
            cx={x(0)}
            cy={y(0)}
            r={km(CITY_DISC.radiusKm)}
            fill="url(#density-wash)"
          />

          {/* The union, composited once. */}
          <g clipPath="url(#city-disc)" opacity={0.42}>
            {STATIONS.map((s) => (
              <circle
                key={s.id}
                cx={x(s.x)}
                cy={y(s.y)}
                r={km(reach)}
                fill="var(--series-1)"
              />
            ))}
          </g>

          {/* Shed outlines, so the individual radii stay readable in the union. */}
          {STATIONS.map((s) => (
            <circle
              key={`${s.id}-edge`}
              cx={x(s.x)}
              cy={y(s.y)}
              r={km(reach)}
              fill="none"
              stroke="var(--series-1)"
              strokeWidth={1}
              strokeOpacity={0.5}
            />
          ))}

          <circle
            cx={x(0)}
            cy={y(0)}
            r={km(CITY_DISC.radiusKm)}
            fill="none"
            stroke="var(--rule)"
            strokeWidth={2}
          />

          {STATIONS.map((s) => (
            <g key={`${s.id}-dot`}>
              <circle
                cx={x(s.x)}
                cy={y(s.y)}
                r={4}
                fill="var(--series-2)"
                stroke="var(--surface-1)"
                strokeWidth={2}
              >
                <title>{`${s.label} — ${s.note}`}</title>
              </circle>
              <text
                x={x(s.x)}
                y={y(s.y) - 10}
                textAnchor="middle"
                fontSize={10}
                fill="var(--text-secondary)"
              >
                {s.label.replace("Enschede ", "")}
              </text>
            </g>
          ))}

          <text
            x={x(0)}
            y={y(CITY_DISC.radiusKm) - 6}
            textAnchor="middle"
            fontSize={10}
            fill="var(--text-muted)"
          >
            built-up area, {CITY_DISC.areaKm2} km²
          </text>
        </svg>

        <div className="min-w-0 flex-1 space-y-6">
          <label className="block">
            <span className="flex items-baseline justify-between text-[0.6875rem] uppercase tracking-widest text-ink-3">
              Access radius
              <span className="tabular-nums text-ink">{radiusKm.toFixed(1)} km</span>
            </span>
            <input
              type="range"
              min={0.4}
              max={6}
              step={0.1}
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
              className="mt-2 w-full"
            />
          </label>

          <div className="flex flex-wrap items-center gap-2">
            {ACCESS_MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setRadiusKm(m.radiusKm)}
                aria-pressed={mode?.id === m.id}
                className={`rounded border px-2 py-1 text-[0.6875rem] transition-colors ${
                  mode?.id === m.id
                    ? "border-ink-3 text-ink"
                    : "border-rule text-ink-3 hover:text-ink-2"
                }`}
              >
                {m.label}, {m.minutes} min
              </button>
            ))}
          </div>

          <label className="flex items-start gap-2.5 text-[0.8125rem] leading-relaxed text-ink-2">
            <input
              type="checkbox"
              checked={useCircuity}
              onChange={(e) => setUseCircuity(e.target.checked)}
              className="mt-0.5"
            />
            <span>
              Take out network circuity
              <span className="block text-[0.6875rem] text-ink-3">
                Streets do not run straight at the destination. At a factor of{" "}
                {circuity.toFixed(2)} the real reach is {reach.toFixed(2)} km, and the shed
                is {((1 / (circuity * circuity)) * 100).toFixed(0)} per cent of the circle
                a buffer draws.
              </span>
            </span>
          </label>

          <dl className="grid grid-cols-2 gap-x-6 gap-y-4">
            <Readout
              term="Built-up land covered"
              detail={`${cov.landKm2.toFixed(1)} km² of ${CITY_DISC.areaKm2} km²`}
            >
              {(cov.land * 100).toFixed(0)}%
            </Readout>
            <Readout
              term="Residents covered"
              detail={`about ${Math.round(cov.people / 1000).toLocaleString("en-GB")} thousand people`}
              accent
            >
              {(cov.population * 100).toFixed(0)}%
            </Readout>
            <Readout
              term="Shed per station"
              detail={`π r² at a reach of ${reach.toFixed(2)} km`}
            >
              {shedAreaKm2(reach).toFixed(1)}
              <span className="ml-1 text-[0.75rem] font-normal text-ink-2">km²</span>
            </Readout>
            <Readout
              term="People per hectare covered"
              detail="the density of what the network actually reaches"
            >
              {cov.landKm2 > 0 ? (cov.people / cov.landKm2 / 100).toFixed(1) : "—"}
            </Readout>
          </dl>
        </div>
      </div>
    </div>
  );
}

function Readout({
  term,
  detail,
  accent,
  children,
}: {
  term: string;
  detail: string;
  accent?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="border-t border-rule pt-2">
      <dt className="text-[0.6875rem] uppercase tracking-widest text-ink-3">{term}</dt>
      <dd
        className="mt-1 text-[1.375rem] font-semibold leading-none tabular-nums"
        style={accent ? { color: "var(--series-2)" } : { color: "var(--text-primary)" }}
      >
        {children}
      </dd>
      <dd className="mt-1.5 text-[0.6875rem] leading-relaxed text-ink-3">{detail}</dd>
    </div>
  );
}

/** Central density, exposed for the caption so the wash can be read. */
export function centralDensity(): number {
  return DENSITY_MODEL.d0;
}
