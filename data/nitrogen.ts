import { Class, SourceKey, q } from "@/lib/provenance";

/**
 * Nitrogen.
 *
 * The organising claim of this platform is that Enschede's binding constraints
 * are continuous fields rather than polygons, and nitrogen deposition is the
 * clearest case. It is measured in mol of nitrogen per hectare per year, it
 * varies smoothly across space, it has a per-habitat threshold, and — crucially
 * — it can be reduced, which is something a boundary line can never be.
 */

export interface Habitat {
  code: string;
  label: string;
  /** Critical deposition value: the load above which the habitat degrades. */
  kdw: number;
  klass: Class;
  source: SourceKey;
  note?: string;
}

/**
 * Critical deposition values for habitats present in and around the Twente
 * sites. Raised bog is the reason this page exists: at 400 mol it carries the
 * lowest tolerance in the Dutch system, and Enschede has one on its own edge.
 */
export const HABITATS: Habitat[] = [
  {
    code: "H7110A",
    label: "Active raised bog",
    kdw: 400,
    klass: "official",
    source: "aerius",
    note: "The lowest critical value in the national set. Present at Aamsveen on the south-eastern municipal edge.",
  },
  {
    code: "H7120",
    label: "Regenerating raised bog",
    kdw: 500,
    klass: "official",
    source: "aerius",
    note: "Degraded bog under active restoration; restoration is what the threshold protects.",
  },
  {
    code: "H3160",
    label: "Acid fens",
    kdw: 714,
    klass: "official",
    source: "aerius",
  },
  {
    code: "H4030",
    label: "Dry heath",
    kdw: 1071,
    klass: "official",
    source: "aerius",
  },
  {
    code: "H4010A",
    label: "Wet heath",
    kdw: 1214,
    klass: "official",
    source: "aerius",
  },
  {
    code: "H91E0C",
    label: "Brook-accompanying alluvial forest",
    kdw: 1857,
    klass: "official",
    source: "aerius",
  },
];

/** Regional background load. The number every habitat is measured against. */
export const BACKGROUND_DEPOSITION = q(1600, "mol N/ha/yr", "estimate", "aerius", {
  basis: "Representative Twente background load, pending a hexagon-level pull from the monitor.",
  note: "Eastern Overijssel sits well above the national mean because regional livestock density and prevailing transport of ammonia both work against it.",
});

/**
 * The permit threshold after the 2019 annulment of the programmatic approach.
 *
 * This is the fact that reframes everything. There is no de minimis allowance.
 * A calculated increase of 0.01 mol per hectare per year at a single hexagon
 * of an over-loaded habitat is a legally relevant effect. The model reports to
 * two decimal places, so the practical test is whether a project rounds to
 * zero — a detection limit, not a budget.
 */
export const PERMIT_THRESHOLD = q(0.0, "mol N/ha/yr", "official", "raadVanState", {
  note: "No lower bound below which an increase is disregarded. The reporting precision of the model, 0.01 mol/ha/yr, is what functions as the practical limit.",
});

export const CHRONOLOGY: { date: string; event: string; consequence: string }[] = [
  {
    date: "May 2019",
    event: "The programmatic approach to nitrogen is annulled.",
    consequence:
      "The mechanism that had allowed development to draw against future emission reductions disappears. Consent for projects affecting over-loaded habitats requires an individual demonstration of no significant effect.",
  },
  {
    date: "July 2018",
    event: "The obligation to connect new dwellings to the gas network is removed.",
    consequence:
      "New Dutch housing has essentially no combustion emissions in use. The dwelling's own nitrogen term collapses to construction and to the traffic it attracts.",
  },
  {
    date: "November 2022",
    event: "The construction-phase exemption is annulled.",
    consequence:
      "Machinery emissions during construction re-enter the assessment. The crane is back in the calculation, though it was never the larger term.",
  },
  {
    date: "2023 onward",
    event: "Clean and emission-free construction is written into procurement.",
    consequence:
      "Electrified plant removes the construction term at the point where public bodies specify it, which is precisely where affordable housing is procured.",
  },
];

/**
 * A dwelling's nitrogen account.
 *
 * Emission-side only. No dispersion is modelled here and none should be
 * inferred: turning emissions into deposition at a named hexagon is what the
 * official calculator is for, and a plausible-looking imitation of it would be
 * worse than useless. What this account establishes is the ratio between the
 * terms, and that ratio is robust to almost any dispersion assumption because
 * both terms disperse from broadly the same place.
 */
export const DWELLING = {
  /** One-off, over the whole build. */
  constructionNOxKg: q(10, "kg NOx per dwelling", "estimate", "aerius", {
    basis: "Diesel plant and site transport for a mid-rise dwelling of roughly 150 m² gross floor area.",
    note: "Wide spread by construction method; timber and prefabricated systems sit at the bottom of the range.",
  }),

  /** Annual, in use. */
  carKmPerYear: q(12_000, "vehicle-km per dwelling per year", "estimate", "cbs", {
    basis: "Around 0.9 cars per household at roughly 13,000 km per car per year.",
  }),

  fleetNOxPerKm: q(0.2, "g NOx per vehicle-km", "estimate", "aerius", {
    basis: "Real-world fleet average across the current petrol and diesel mix.",
    note: "Falls as the fleet electrifies, which is the one term that improves without any planning decision.",
  }),

  lifetimeYears: 50,
};

export const NOX_MOLAR_MASS = 46; // g/mol, expressed as NO2 by convention.

export function annualUseNOxKg(): number {
  return (DWELLING.carKmPerYear.value * DWELLING.fleetNOxPerKm.value) / 1000;
}

export function lifetimeNOxKg(carKmScale = 1, electricPlant = false): number {
  const construction = electricPlant ? 0 : DWELLING.constructionNOxKg.value;
  return construction + annualUseNOxKg() * carKmScale * DWELLING.lifetimeYears;
}

/** Emitted nitrogen in mol, the unit the regulator actually counts in. */
export function kgNOxToMolN(kg: number): number {
  return (kg * 1000) / NOX_MOLAR_MASS;
}

/**
 * The abatement ladder for a single dwelling, ordered by effect rather than by
 * how much attention each option receives in public argument.
 */
export interface Lever {
  id: string;
  label: string;
  carKmScale: number;
  electricPlant: boolean;
  detail: string;
}

export const LEVERS: Lever[] = [
  {
    id: "baseline",
    label: "Edge site, standard parking norm, diesel plant",
    carKmScale: 1,
    electricPlant: false,
    detail:
      "The default greenfield product. Car use is set by the location before a single design decision is taken.",
  },
  {
    id: "plant",
    label: "Same site, emission-free construction plant",
    carKmScale: 1,
    electricPlant: true,
    detail:
      "Removes the construction term outright. It is the intervention with the clearest public profile and the smallest lifetime effect.",
  },
  {
    id: "location",
    label: "Corridor site, reduced parking norm, diesel plant",
    carKmScale: 0.5,
    electricPlant: false,
    detail:
      "A dwelling within reach of the regional cycle route and the rail station, with parking provision cut from roughly 1.2 to 0.4 spaces. Halving car-kilometres is a conservative reading of the observed elasticity.",
  },
  {
    id: "both",
    label: "Corridor site, reduced parking norm, emission-free plant",
    carKmScale: 0.5,
    electricPlant: true,
    detail: "The two levers together, which is how they are actually available.",
  },
  {
    id: "carlight",
    label: "Corridor site, car-free covenant, emission-free plant",
    carKmScale: 0.2,
    electricPlant: true,
    detail:
      "Achievable only where the alternative genuinely reaches the destinations residents need, which in Enschede means the ridge crossing has to work on a bicycle.",
  },
];
