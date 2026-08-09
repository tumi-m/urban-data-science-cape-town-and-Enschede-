import { q } from "@/lib/provenance";
import { CITY } from "@/data/city";

/**
 * Regional electricity and the land it costs.
 *
 * The regional energy strategy sets a generation target. Debate about it is
 * conducted almost entirely in the language of landscape and consent. This
 * module converts it into the only two quantities that constrain it physically:
 * square kilometres, and square kilometres that are exclusively occupied.
 *
 * The distinction is the whole point. A wind array occupies a large area and
 * withdraws almost none of it. A solar field occupies a smaller area and
 * withdraws all of it.
 */

export const TARGET = q(1.5, "TWh/yr by 2030", "official", "resTwente", {
  note: "Regional renewable electricity commitment across the fourteen Twente municipalities, not Enschede alone.",
});

export interface Technology {
  id: string;
  label: string;
  /** Annual generation per unit, GWh. */
  gwhPerUnit: number;
  unitLabel: string;
  /** Total area associated with a unit, km² — including land that stays in use. */
  grossKm2PerUnit: number;
  /** Area withdrawn from other use, km². */
  exclusiveKm2PerUnit: number;
  basis: string;
  /** What actually stops it being built, which is rarely the land. */
  bindingConstraint: string;
  constraintShape: "field" | "polygon" | "none";
}

export const TECHNOLOGIES: Technology[] = [
  {
    id: "wind",
    label: "Onshore wind",
    gwhPerUnit: 16.8,
    unitLabel: "turbine",
    grossKm2PerUnit: 0.36,
    exclusiveKm2PerUnit: 0.003,
    basis:
      "5.6 MW machine at roughly 3,000 full-load hours inland; array spacing of about five rotor diameters downwind by three across, at a 155 m rotor; foundation and hardstanding of about 0.3 ha.",
    bindingConstraint:
      "Noise and shadow-flicker contours, military and civil radar sightlines, and habitat disturbance. None of these is a land requirement.",
    constraintShape: "field",
  },
  {
    id: "solar-field",
    label: "Ground-mounted solar",
    gwhPerUnit: 0.665,
    unitLabel: "hectare",
    grossKm2PerUnit: 0.01,
    exclusiveKm2PerUnit: 0.01,
    basis:
      "About 950 kWh per installed kWp per year in the eastern Netherlands at a ground-mount density near 0.7 MWp per hectare.",
    bindingConstraint:
      "Land itself, plus a national preference order that puts agricultural land last. The constraint is a boundary that can be redrawn.",
    constraintShape: "polygon",
  },
  {
    id: "solar-roof",
    label: "Rooftop solar",
    gwhPerUnit: 0.665,
    unitLabel: "hectare of roof",
    grossKm2PerUnit: 0,
    exclusiveKm2PerUnit: 0,
    basis: "Same yield per hectare of array, mounted on structure that already exists.",
    bindingConstraint:
      "Grid capacity at the low-voltage transformer, roof structural capacity, and split incentives between owner and occupier. No land at all.",
    constraintShape: "none",
  },
];

export function unitsForTarget(t: Technology, twh = TARGET.value): number {
  return (twh * 1000) / t.gwhPerUnit;
}

export function grossKm2ForTarget(t: Technology, twh = TARGET.value): number {
  return unitsForTarget(t, twh) * t.grossKm2PerUnit;
}

export function exclusiveKm2ForTarget(t: Technology, twh = TARGET.value): number {
  return unitsForTarget(t, twh) * t.exclusiveKm2PerUnit;
}

/** Share of Enschede's municipal land area, for scale rather than for siting. */
export function shareOfMunicipality(km2: number): number {
  return km2 / CITY.landArea.value;
}

/**
 * Roof area available in Enschede. The ceiling on the one option whose land
 * cost is zero, which makes it the number worth knowing before any search area
 * is drawn on a map.
 */
export const ROOFTOP = {
  usableM2PerDwelling: q(25, "m² per dwelling", "estimate", "pdok", {
    basis: "Orientation- and shading-corrected usable area, before structural screening.",
    note: "Derivable properly from BAG footprints crossed with the elevation model; the estimate stands in until that runs.",
  }),
  kwpPerM2: q(0.2, "kWp/m²", "engineering", "physics", {
    basis: "Current module efficiency at commercial packing density.",
  }),
  yieldKwhPerKwp: q(950, "kWh/kWp/yr", "engineering", "physics", {
    basis: "Eastern Netherlands irradiance at typical tilt and orientation.",
  }),
  nonResidentialMultiplier: q(1.6, "×", "estimate", "pdok", {
    basis: "Industrial, retail and institutional roof area relative to residential in a city of this profile.",
    note: "Enschede's inherited industrial estates make this term unusually favourable.",
  }),
};

export function rooftopPotentialTWh(): number {
  const kwp =
    (CITY.dwellings.value * ROOFTOP.usableM2PerDwelling.value * ROOFTOP.kwpPerM2.value) /
    1;
  const residentialTWh = (kwp * ROOFTOP.yieldKwhPerKwp.value) / 1e9;
  return residentialTWh * ROOFTOP.nonResidentialMultiplier.value;
}
