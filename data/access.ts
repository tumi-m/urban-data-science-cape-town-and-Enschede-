import { q } from "@/lib/provenance";
import { CITY } from "@/data/city";

/**
 * Station access sheds.
 *
 * The standard measure of transit access is the share of some administrative
 * area lying within a fixed walking buffer of a station. It is easy to compute,
 * which is most of why it is used, and it carries two assumptions that do the
 * real work while going unstated.
 *
 * The first is that the access radius is a property of the situation. It is
 * not — it is a property of the mode chosen to reach the station, and shed area
 * scales with the square of it. The second is that land is the right thing to
 * count. It is not: a station in an industrial estate books the same hectares
 * as one on a dense corridor, and the question was never how much ground is
 * near a station.
 *
 * This module computes both readings over a stylised Enschede so the gap
 * between them can be seen rather than argued about.
 */

/* ------------------------------------------------------------------ *
 * Geometry
 * ------------------------------------------------------------------ */

/**
 * The built-up area as a disc of equal area, centred on the city centre.
 *
 * This is a stylisation and the honest objection to it is that Enschede's
 * footprint is not circular — it reaches further south-west, into
 * Wesselerbrink and Stroinkslanden, than it does north. A real footprint would
 * change the coverage fractions by a few points. It would not change the ratio
 * between the walking and cycling cases, which is what the section is about,
 * because that ratio is set by r² and not by the shape of the boundary.
 */
export const CITY_DISC = {
  areaKm2: CITY.builtUpArea.value,
  get radiusKm() {
    return Math.sqrt(this.areaKm2 / Math.PI);
  },
};

export interface Station {
  id: string;
  label: string;
  /** km east of the central station. */
  x: number;
  /** km north of the central station. */
  y: number;
  note: string;
}

/**
 * The three stations inside the municipality, at approximate offsets from the
 * central station. Positions are good to a few hundred metres, which is inside
 * the tolerance of everything computed from them.
 */
export const STATIONS: Station[] = [
  {
    id: "centraal",
    label: "Enschede Centraal",
    x: 0,
    y: 0,
    note: "Terminus for services from the west and the interchange to the German regional service. Sits on the density peak.",
  },
  {
    id: "kennispark",
    label: "Enschede Kennispark",
    x: -2.6,
    y: 1.2,
    note: "Serves the university campus and the science park on the Hengelo line.",
  },
  {
    id: "eschmarke",
    label: "Enschede De Eschmarke",
    x: 2.8,
    y: 0.4,
    note: "Eastern suburban stop on the line toward the border.",
  },
];

/* ------------------------------------------------------------------ *
 * Access modes
 * ------------------------------------------------------------------ */

export interface AccessMode {
  id: string;
  label: string;
  /** Nominal planning radius, km. */
  radiusKm: number;
  /**
   * Ratio of network distance to straight-line distance. A buffer drawn as a
   * circle assumes this is 1, which it never is; the effective reach is the
   * nominal radius divided by it.
   */
  circuity: number;
  minutes: number;
  note: string;
}

export const ACCESS_MODES: AccessMode[] = [
  {
    id: "walk",
    label: "Walking",
    radiusKm: 0.8,
    circuity: 1.3,
    minutes: 10,
    note: "The conventional planning buffer, and the one that produces the familiar low coverage numbers.",
  },
  {
    id: "bike",
    label: "Bicycle",
    radiusKm: 3.0,
    circuity: 1.18,
    minutes: 10,
    note: "The same ten minutes at cycling speed. Dutch networks are unusually direct, so little of the radius is lost to circuity.",
  },
  {
    id: "ebike",
    label: "Electric bicycle",
    radiusKm: 5.0,
    circuity: 1.18,
    minutes: 12,
    note: "Assistance buys both speed and, on the ridge, indifference to gradient — which is what converts a nominal radius into a real one here.",
  },
];

export function shedAreaKm2(radiusKm: number): number {
  return Math.PI * radiusKm * radiusKm;
}

/** Straight-line reach once the network's indirectness is taken out. */
export function effectiveRadiusKm(m: AccessMode): number {
  return m.radiusKm / m.circuity;
}

/* ------------------------------------------------------------------ *
 * Density
 * ------------------------------------------------------------------ */

/**
 * Negative-exponential density gradient, D(r) = D₀·exp(−b·r).
 *
 * The standard form, used here for one purpose: to weight coverage by people
 * instead of by hectares. D₀ is solved so the gradient integrates to the city's
 * actual population over the disc, so only the steepness b is a free choice,
 * and 0.35 per km is a gentle gradient appropriate to a compact European city
 * of this size.
 */
export const DENSITY_MODEL = {
  b: 0.35,
  population: CITY.population.value,
  /** Central density, solved rather than assumed. */
  get d0(): number {
    const { b } = this;
    const R = CITY_DISC.radiusKm;
    const integral = (2 * Math.PI * (1 - Math.exp(-b * R) * (1 + b * R))) / (b * b);
    return this.population / integral;
  },
  densityAt(r: number): number {
    return this.d0 * Math.exp(-this.b * r);
  },
};

/* ------------------------------------------------------------------ *
 * Coverage
 * ------------------------------------------------------------------ */

interface Sample {
  x: number;
  y: number;
  /** Population represented by this cell. */
  w: number;
}

/**
 * A grid over the built-up disc, built once.
 *
 * Coverage of a union of overlapping discs has no closed form worth writing,
 * so it is sampled. Everything downstream is a scan over this array, which
 * keeps a slider responsive without caching per-radius results.
 */
const SPACING = 0.025; // km
let grid: Sample[] | null = null;

function samples(): Sample[] {
  if (grid) return grid;
  const R = CITY_DISC.radiusKm;
  const cell = SPACING * SPACING;
  const out: Sample[] = [];
  for (let x = -R; x <= R; x += SPACING) {
    for (let y = -R; y <= R; y += SPACING) {
      const r = Math.hypot(x, y);
      if (r > R) continue;
      out.push({ x, y, w: DENSITY_MODEL.densityAt(r) * cell });
    }
  }
  grid = out;
  return out;
}

export interface Coverage {
  /** Share of built-up land within reach of a station. */
  land: number;
  /** Share of residents within reach of a station. */
  population: number;
  landKm2: number;
  people: number;
}

/**
 * Coverage at a given straight-line reach.
 *
 * Pass the effective radius, not the nominal one, wherever circuity is being
 * taken seriously — the function has no way to know which was meant.
 */
export function coverage(reachKm: number): Coverage {
  const pts = samples();
  const r2 = reachKm * reachKm;
  let landCells = 0;
  let people = 0;
  let totalPeople = 0;

  for (const p of pts) {
    totalPeople += p.w;
    let covered = false;
    for (const s of STATIONS) {
      const dx = p.x - s.x;
      const dy = p.y - s.y;
      if (dx * dx + dy * dy <= r2) {
        covered = true;
        break;
      }
    }
    if (covered) {
      landCells++;
      people += p.w;
    }
  }

  const landKm2 = landCells * SPACING * SPACING;
  return {
    land: landKm2 / CITY_DISC.areaKm2,
    population: people / totalPeople,
    landKm2,
    people,
  };
}

export const CURVE_RADII = [
  0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0,
];

/* ------------------------------------------------------------------ *
 * The comparison case
 * ------------------------------------------------------------------ */

/**
 * Cape Town, as the figures were published.
 *
 * Restated rather than reproduced. They are used here only to make the r²
 * point at a different scale, and that point survives a fair margin of error
 * in either input.
 */
export const CAPE_TOWN = {
  bufferKm2: q(183, "km²", "estimate", "ctAccess", {
    note: "Union of 800 m buffers around the metropolitan rail stations, as published.",
  }),
  developmentEdgeKm2: q(895, "km²", "estimate", "ctAccess", {
    note: "Land inside the urban development edge, as published.",
  }),

  /**
   * Station-equivalents implied by the published buffer area — how many
   * non-overlapping 800 m discs it takes to make 183 km². The real network has
   * more stations than this, and the difference is the overlap.
   */
  get stationEquivalents(): number {
    return this.bufferKm2.value / shedAreaKm2(0.8);
  },

  /** Summed shed area if the same stations were reached by another mode. */
  summedShedKm2(radiusKm: number): number {
    return this.stationEquivalents * shedAreaKm2(radiusKm);
  },

  coverageShare(): number {
    return this.bufferKm2.value / this.developmentEdgeKm2.value;
  },
};
