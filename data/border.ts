import { CITY } from "@/data/city";

/**
 * The half-disc problem.
 *
 * Infrastructure economics assume a city sits at the centre of its catchment.
 * Fixed costs — a rail terminus, a hospital, a university, a district heating
 * spine — are recovered from the population inside some travel radius, and that
 * population is normally proportional to the area of a disc.
 *
 * Enschede's disc is cut. The national border runs roughly four kilometres from
 * the centre, and beyond it the land is not empty but institutionally separate:
 * different labour law, different qualifications recognition, different health
 * insurance, different telephone tariffs until recently, and a rail service
 * that changes operator at the frontier.
 *
 * The correct model is not a wall and not open ground. It is a membrane with a
 * permeability coefficient, and the interesting question is what that
 * coefficient is worth per point of improvement.
 */

/** Distance from the city centre to the border, in km. */
export const BORDER_DISTANCE_KM = CITY.distanceToBorder.value;

/**
 * Area of the circular segment lying beyond a chord at perpendicular distance
 * `d` from the centre of a circle of radius `r`. In km² when inputs are km.
 */
export function segmentArea(r: number, d: number): number {
  if (d >= r) return 0;
  if (d <= -r) return Math.PI * r * r;
  return r * r * Math.acos(d / r) - d * Math.sqrt(r * r - d * d);
}

export function discArea(r: number): number {
  return Math.PI * r * r;
}

/** Fraction of a travel disc of radius `r` that lies beyond the border. */
export function fractionBeyond(r: number, d = BORDER_DISTANCE_KM): number {
  return segmentArea(r, d) / discArea(r);
}

/**
 * Effective catchment area at radius `r` given a membrane permeability in
 * [0, 1]. Permeability 0 is a closed frontier; 1 is a border that has no
 * economic existence at all.
 */
export function effectiveCatchment(r: number, permeability: number, d = BORDER_DISTANCE_KM): number {
  const beyond = segmentArea(r, d);
  const within = discArea(r) - beyond;
  return within + permeability * beyond;
}

/**
 * Ratio of effective catchment to the full disc an interior city of the same
 * size would enjoy. This is the number that multiplies straight through into
 * the unit economics of every piece of fixed infrastructure in the city.
 */
export function catchmentRatio(r: number, permeability: number, d = BORDER_DISTANCE_KM): number {
  return effectiveCatchment(r, permeability, d) / discArea(r);
}

export const RADII_KM = [5, 10, 15, 20, 25, 30, 40, 50];

/**
 * Permeability scenarios. These are judgements about institutional friction,
 * not measurements, and they are labelled as such wherever they are shown. The
 * defensible part of this analysis is the geometry; the permeability value is
 * the reader's to argue with, which is why the interface makes it adjustable.
 */
export const PERMEABILITY_SCENARIOS: {
  id: string;
  label: string;
  value: number;
  detail: string;
}[] = [
  {
    id: "closed",
    label: "Closed frontier",
    value: 0,
    detail: "The counterfactual. Included to show what the geometry alone costs.",
  },
  {
    id: "current",
    label: "Observed today",
    value: 0.15,
    detail:
      "Cross-border commuting into and out of the Twente–Münsterland zone remains a small share of either labour market despite forty kilometres of shared frontier and an hourly rail link.",
  },
  {
    id: "integrated",
    label: "Working cross-border labour market",
    value: 0.5,
    detail:
      "Qualifications recognised in both directions, a single ticketing and tariff regime, and social insurance portability. Nothing here requires new construction.",
  },
  {
    id: "seamless",
    label: "No institutional friction",
    value: 1,
    detail: "The upper bound. A border that costs a commuter nothing but distance.",
  },
];

/**
 * Population density beyond the border, used to convert catchment area into
 * accessible people rather than accessible hectares. Gronau, Ahaus and the
 * western Münsterland are less densely settled than urban Twente, which
 * moderates the prize.
 */
export const DENSITY = {
  dutchSide: 500, // inhabitants per km², Twente urban region average
  germanSide: 220, // inhabitants per km², western Münsterland average
};

export function accessiblePopulation(r: number, permeability: number): number {
  const beyond = segmentArea(r, BORDER_DISTANCE_KM);
  const within = discArea(r) - beyond;
  return within * DENSITY.dutchSide + permeability * beyond * DENSITY.germanSide;
}
