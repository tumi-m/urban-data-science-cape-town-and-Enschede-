import { q } from "@/lib/provenance";

/**
 * Cape Town.
 *
 * The other city in this project, and the reason the comparison works: Cape
 * Town's limits are almost all boundaries, and Enschede's are almost all
 * fields. Putting them side by side shows what each kind of limit does to a
 * city, which neither city shows on its own.
 */

export const CT = {
  population: q(4_800_000, "people", "estimate", "cctMsdf", {
    note: "Metropolitan municipality, rounded.",
  }),

  /** Derived from the city's own numbers: 55,697 ha is 22.72% of the municipality. */
  municipalArea: q(2451, "km²", "derived", "cctBionet", {
    basis: "55,697 ha of protected land is stated as 22.72% of the municipality, so the whole is 245,145 ha.",
    note: "Matches the published municipal area, which is a useful check that the two figures agree.",
  }),

  urbanEdgeArea: q(895, "km²", "estimate", "ctAccess", {
    note: "Land inside the urban development edge.",
  }),

  protectedArea: q(55_697, "ha", "official", "cctBionet", {
    note: "Formally protected land: national parks, nature reserves, marine protected areas.",
  }),

  protectedShare: q(22.72, "% of the municipality", "official", "cctBionet"),

  criticalBiodiversityShare: q(23.6, "% of the regional plan", "official", "cctBionet", {
    note: "Critical biodiversity areas, on top of the formally protected land.",
  }),

  ecologicalSupportShare: q(13.4, "% of the regional plan", "official", "cctBionet", {
    note: "Ecological support areas, which keep the protected areas connected.",
  }),

  vegetationLost: q(61, "% of original vegetation", "official", "cctBionet", {
    note: "Already permanently transformed, mostly on the lowlands where building is easiest.",
  }),

  vegetationTypes: q(19, "national vegetation types", "official", "cctBionet", {
    note: "Six of them exist nowhere else but inside the city boundary.",
  }),

  /** Cape Flats. */
  liquefiableFrom: q(3.2, "m depth", "official", "capeFlats"),
  liquefiableTo: q(19, "m depth", "official", "capeFlats", {
    note: "Between these depths the sand can lose strength in an earthquake, which is the depth range foundations for tall buildings sit in.",
  }),

  aquiferDepth: q(65, "m", "official", "capeFlats", {
    note: "Maximum depth before the aquifer meets the basement rock.",
  }),
  aquiferYield: q(18, "million m³ per year", "official", "capeFlats", {
    note: "What the aquifer can supply without being drained. The city turned to it during the 2017–18 drought.",
  }),

  stationBuffers: q(183, "km²", "estimate", "ctAccess", {
    note: "Land within 800 m of a station, as published.",
  }),
} as const;

/** Share of land inside the urban edge that is within a walk of a station. */
export const CT_STATION_SHARE =
  CT.stationBuffers.value / CT.urbanEdgeArea.value;

/**
 * The four limits, in the same shape as the Enschede taxonomy so the two can
 * be compared directly.
 */
export interface CTLimit {
  id: string;
  label: string;
  shape: "boundary" | "field";
  what: string;
  effect: string;
  canItBeLowered: string;
}

export const CT_LIMITS: CTLimit[] = [
  {
    id: "edge",
    label: "The urban edge",
    shape: "boundary",
    what: "A line drawn in 1996 around how far the city may spread.",
    effect:
      "Stops building outside it. It worked: sprawl slowed. But it assumed the city would build upward inside the line instead, and that did not happen at anything like the rate needed.",
    canItBeLowered:
      "No. A line can only be moved, and moving it is a political fight that has been running for thirty years.",
  },
  {
    id: "bionet",
    label: "Protected nature",
    shape: "boundary",
    what:
      "Protected areas, critical biodiversity areas and ecological support areas, mapped as polygons across the city.",
    effect:
      "Takes roughly a third of the city's land out of play for building. Cape Town sits in the smallest and richest plant kingdom on earth, and six vegetation types exist nowhere else.",
    canItBeLowered: "No. There is nothing underneath to reduce — it is designated land.",
  },
  {
    id: "sand",
    label: "The Cape Flats sand",
    shape: "field",
    what:
      "Loose windblown sand that can lose its strength in an earthquake, between about 3 and 19 metres down.",
    effect:
      "Makes tall, heavy buildings far more expensive exactly where the city has flat land available. So the place with room to build is the place where building up costs most.",
    canItBeLowered:
      "Partly. Ground improvement and different foundation types lower the cost, and lighter construction avoids it. This is an engineering problem being treated as a location problem.",
  },
  {
    id: "aquifer",
    label: "The Cape Flats aquifer",
    shape: "field",
    what:
      "A shallow, sandy, unconfined aquifer under the same flat land, holding about 18 million cubic metres a year of usable water.",
    effect:
      "Whatever soaks into the surface reaches the water. Housing without proper sewerage, built over the recharge area, contaminates the water supply the city fell back on during the drought.",
    canItBeLowered:
      "Yes. What reaches the groundwater depends on what is done at the surface — sanitation, drainage, industrial controls.",
  },
];

/**
 * The comparison. This is the point of having both cities in one project.
 */
export interface Comparison {
  question: string;
  capeTown: string;
  enschede: string;
  soWhat: string;
}

export const COMPARISON: Comparison[] = [
  {
    question: "Is land actually scarce?",
    capeTown:
      "Yes. Mountain on one side, ocean on two, and roughly a third of the land protected. 895 km² inside the edge for about 4.8 million people.",
    enschede:
      "No. 140 km² of municipal land for 161,000 people, and only about 43 km² of it built on.",
    soWhat:
      "Two cities can both be hard to build in for opposite reasons. Enschede has plenty of land and still cannot build; Cape Town has almost none and builds anyway, badly, at the edge.",
  },
  {
    question: "What is the limit made of?",
    capeTown:
      "Mostly lines on a map: the urban edge, and the protected-area polygons.",
    enschede:
      "Mostly quantities: nitrogen in the air, noise at the façade, risk near a pipeline, travel time to a well.",
    soWhat:
      "A line can only be moved or fought over. A quantity can be reduced — and reducing it frees up every location at once, not just one.",
  },
  {
    question: "What does the limit push development into?",
    capeTown:
      "The Cape Flats: flat, available, and the worst ground to build heavy on, sitting directly over the drinking-water aquifer.",
    enschede:
      "The edge of town, where car use per household is highest — which is what actually generates the nitrogen that blocks the next permit.",
    soWhat:
      "In both cities the limit pushes building to the place that makes the next problem worse. That is the pattern worth looking for anywhere.",
  },
  {
    question: "How good is access to a train?",
    capeTown:
      "20% of the land inside the urban edge is within an 800 m walk of a station — a large rail network, poorly reached, and in recent years barely running.",
    enschede:
      "8% of built-up land within a real walk of one of three stations. By bicycle, the same three stations reach 82% of residents.",
    soWhat:
      "Cape Town's problem is not that it lacks stations. Both cities show the same thing: the walking radius, not the rail network, is what limits the number.",
  },
  {
    question: "What would actually help?",
    capeTown:
      "Making the trains run, and getting people to the stations that already exist by something other than walking. Both are cheaper than new rail.",
    enschede:
      "Building near the stations and the cycle route, with less parking. That cuts car use, which cuts nitrogen, which is what is blocking permits.",
    soWhat:
      "In both cases the cheapest fix is not construction. It is changing how people reach what is already built.",
  },
];
