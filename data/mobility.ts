import { Class, SourceKey } from "@/lib/provenance";

/**
 * The energy ladder.
 *
 * The unit of account is passenger-kilometres per kilowatt-hour. Everything is
 * reduced to that one number so that modes which are normally discussed in
 * incompatible units — litres, calories, watt-hours, seat-kilometres — can be
 * put on a single axis and compared without rhetoric.
 *
 * Two conventions, stated once and applied everywhere:
 *
 *   1. Energy is measured at the point where it enters the vehicle: fuel in the
 *      tank, electricity at the battery or the pantograph, food energy at the
 *      mouth. Upstream chains differ wildly in efficiency and mixing them in
 *      here would bury the comparison in allocation choices. The upstream
 *      multipliers are carried separately, below.
 *
 *   2. Occupancy is the observed average, not the design capacity. A mode is
 *      only as efficient as the way it is actually used, and the gap between
 *      seats offered and seats filled is where most transport energy goes.
 */

export interface Mode {
  id: string;
  label: string;
  /** Energy at the vehicle, per vehicle-kilometre, in kWh. */
  kWhPerVehicleKm: number;
  /** Observed average occupancy, passengers per vehicle. */
  occupancy: number;
  /** Plan-area occupied at operating speed, m² per passenger. */
  m2PerPassenger: number;
  klass: Class;
  source: SourceKey;
  basis: string;
  family: "human" | "assisted" | "collective" | "private";
}

export const MODES: Mode[] = [
  {
    id: "walk",
    label: "Walking",
    kWhPerVehicleKm: 0.049,
    occupancy: 1,
    m2PerPassenger: 1.2,
    klass: "engineering",
    source: "physics",
    basis:
      "Net metabolic cost of walking above rest, ~0.75 kcal per kg per km at 70 kg ⇒ 52 kcal/km ⇒ 0.061 kWh/km gross, taken net of basal metabolism at 0.049.",
    family: "human",
  },
  {
    id: "bike",
    label: "Bicycle",
    kWhPerVehicleKm: 0.029,
    occupancy: 1,
    m2PerPassenger: 6,
    klass: "engineering",
    source: "physics",
    basis:
      "About 25 kcal per km at 18 km/h on level ground, i.e. ~75 W mechanical at ~24% muscular efficiency ⇒ 0.029 kWh/km metabolic.",
    family: "human",
  },
  {
    id: "ebike",
    label: "Electric bicycle",
    kWhPerVehicleKm: 0.011,
    occupancy: 1,
    m2PerPassenger: 7,
    klass: "engineering",
    source: "physics",
    basis:
      "8–15 Wh per km drawn from the battery in mixed use; 11 Wh/km taken as the central case. Rider effort is not counted, which flatters the mode slightly and is stated rather than hidden.",
    family: "assisted",
  },
  {
    id: "escooter",
    label: "Shared e-scooter",
    kWhPerVehicleKm: 0.02,
    occupancy: 1,
    m2PerPassenger: 4,
    klass: "engineering",
    source: "physics",
    basis:
      "20 Wh/km at the battery in service. Operational energy only: rebalancing and short service life dominate the lifecycle figure and are excluded here for consistency with the other modes.",
    family: "assisted",
  },
  {
    id: "train",
    label: "Regional train",
    kWhPerVehicleKm: 12,
    occupancy: 120,
    m2PerPassenger: 1.5,
    klass: "engineering",
    source: "physics",
    basis:
      "Electric multiple unit drawing ~12 kWh per train-km at the pantograph, averaged over the day at 120 passengers per train.",
    family: "collective",
  },
  {
    id: "bus",
    label: "Urban bus, diesel",
    kWhPerVehicleKm: 4.0,
    occupancy: 12,
    m2PerPassenger: 1.8,
    klass: "engineering",
    source: "physics",
    basis:
      "40 litres per 100 km at 10 kWh per litre of diesel ⇒ 4.0 kWh/km, at an all-day average of 12 passengers.",
    family: "collective",
  },
  {
    id: "bev",
    label: "Battery car",
    kWhPerVehicleKm: 0.19,
    occupancy: 1.35,
    m2PerPassenger: 60,
    klass: "engineering",
    source: "physics",
    basis:
      "190 Wh per km at the battery over a mixed urban and interurban cycle, at the Dutch average car occupancy of about 1.35.",
    family: "private",
  },
  {
    id: "ice",
    label: "Petrol car",
    kWhPerVehicleKm: 0.68,
    occupancy: 1.35,
    m2PerPassenger: 60,
    klass: "engineering",
    source: "physics",
    basis:
      "7.0 litres per 100 km at 9.7 kWh per litre of petrol ⇒ 0.68 kWh/km, at the same 1.35 occupancy.",
    family: "private",
  },
];

/** The single number the ladder exists to produce. */
export function pkmPerKWh(m: Mode): number {
  return m.occupancy / m.kWhPerVehicleKm;
}

export function kWhPerPkm(m: Mode): number {
  return m.kWhPerVehicleKm / m.occupancy;
}

/**
 * Upstream multipliers, held apart from the ladder rather than folded into it.
 *
 * Folding these in is the single most common way to make an energy comparison
 * unfalsifiable: the reader can no longer tell which of the two numbers moved.
 * They are given here so the reader can apply them deliberately.
 */
export const UPSTREAM: { id: string; label: string; factor: number; note: string }[] = [
  {
    id: "food",
    label: "Food energy",
    factor: 6,
    note: "Industrial food systems spend roughly 6 units of fossil energy per unit of food energy delivered to the plate, with an enormous spread by diet. Applying it moves walking and cycling down the ladder by that factor and changes the ordering against electric modes.",
  },
  {
    id: "grid",
    label: "Electricity at the socket",
    factor: 1.08,
    note: "Distribution and charging losses between the meter and the battery.",
  },
  {
    id: "refinery",
    label: "Liquid fuel to the pump",
    factor: 1.2,
    note: "Extraction, refining and distribution before the fuel reaches the tank.",
  },
];

/**
 * The topographic surcharge.
 *
 * Enschede's ridge gives an intra-urban trip real climb, which is unusual in
 * the Netherlands. This computes what that climb costs, first to a person and
 * then to a motor, so the two can be compared directly.
 */
export const CLIMB = {
  systemMassKg: 90,
  gravity: 9.81,
  humanEfficiency: 0.24,
  motorEfficiency: 0.8,
  typicalClimbM: 30,
  typicalTripKm: 5,
};

/** Mechanical work to raise the system by `metres`, in Wh. */
export function climbWorkWh(metres: number): number {
  return (CLIMB.systemMassKg * CLIMB.gravity * metres) / 3600;
}

/** Food energy a rider must supply for that climb, in Wh. */
export function climbMetabolicWh(metres: number): number {
  return climbWorkWh(metres) / CLIMB.humanEfficiency;
}

/** Battery energy a mid-drive motor must supply for the same climb, in Wh. */
export function climbBatteryWh(metres: number): number {
  return climbWorkWh(metres) / CLIMB.motorEfficiency;
}

/**
 * The elevation profile of a west-to-east traverse of the municipality, from
 * the low ground west of the built-up area, over the ridge through the centre,
 * and down toward the Glanerbeek and the border.
 *
 * Sampled at a coarse spacing sufficient to carry the argument about gradient.
 * Swap for an AHN transect when the raster service is wired in; the shape is
 * what the analysis uses, not the individual samples.
 */
export const RIDGE_TRANSECT: { km: number; m: number }[] = [
  { km: 0, m: 30 },
  { km: 1, m: 33 },
  { km: 2, m: 37 },
  { km: 3, m: 42 },
  { km: 4, m: 46 },
  { km: 5, m: 50 },
  { km: 6, m: 47 },
  { km: 7, m: 51 },
  { km: 8, m: 56 },
  { km: 9, m: 52 },
  { km: 10, m: 46 },
  { km: 11, m: 41 },
  { km: 12, m: 37 },
  { km: 13, m: 33 },
  { km: 14, m: 31 },
];

/** Total ascent along a profile, in metres — the number a rider actually feels. */
export function totalAscent(profile: { km: number; m: number }[]): number {
  let sum = 0;
  for (let i = 1; i < profile.length; i++) {
    const d = profile[i].m - profile[i - 1].m;
    if (d > 0) sum += d;
  }
  return sum;
}
