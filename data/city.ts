import { q } from "@/lib/provenance";

/**
 * Enschede: municipality in Overijssel, largest city of the Twente region,
 * built on the Saalian ice-pushed ridge that runs north-east from the Dinkel
 * valley. Roughly four kilometres from the German border at its eastern edge.
 *
 * Population and area figures are rounded. This platform never depends on the
 * third significant figure of a population count, and rounding makes that
 * visible rather than implied.
 */
export const CITY = {
  name: "Enschede",
  region: "Twente, Overijssel",

  population: q(161_000, "inhabitants", "official", "cbs", {
    note: "Rounded to the nearest thousand; the analysis is insensitive below that.",
  }),

  dwellings: q(78_000, "dwellings", "official", "cbs", {
    note: "Municipal dwelling stock, rounded.",
  }),

  landArea: q(140, "km²", "official", "cbs", {
    note: "Municipal land area excluding inland water.",
  }),

  builtUpArea: q(43, "km²", "estimate", "pdok", {
    basis: "Continuous urban fabric plus industrial estates, before parcel-level extraction.",
    note: "Replace with a BGT land-use dissolve; the ratio to municipal area is what matters.",
  }),

  distanceToBorder: q(4, "km", "official", "pdok", {
    note: "Centre to the nearest point of the national border at Glanerbrug.",
  }),

  /** The ridge is the reason Enschede is not a flat Dutch city. */
  relief: {
    low: q(28, "m NAP", "official", "ahn", {
      note: "Valley floor toward the Dinkel and the Glanerbeek.",
    }),
    centre: q(45, "m NAP", "official", "ahn", { note: "City centre plateau." }),
    high: q(60, "m NAP", "official", "ahn", {
      note: "Ridge crest inside the municipal boundary.",
    }),
  },
} as const;

/**
 * Facts that set the analytical frame rather than feeding a calculation.
 * Each one is here because it changes what a constraint layer means, not
 * because it is local colour.
 */
export const FRAME: { title: string; body: string }[] = [
  {
    title: "A raised bog inside the city limits",
    body: "Aamsveen, on the south-eastern edge of the municipality and continuous with the German Amtsvenn across the border, is a raised-bog Natura 2000 site. Raised bog carries the lowest nitrogen tolerance of any habitat in the Dutch system. Enschede is therefore one of very few Dutch cities whose own housing programme is tested against the strictest deposition threshold the country has, at a receptor a few kilometres from its centre.",
  },
  {
    title: "A ridge, not a polder",
    body: "The city sits on a Saalian ice-pushed ridge of sands and gravels. Bearing capacity is good and there is no peat subsidence, so the western Dutch cost driver for dense construction is absent. What the ridge does introduce is thirty metres of intra-urban relief — trivial for a motor, not trivial for a person on an unassisted bicycle.",
  },
  {
    title: "Groundwater beneath the built-up area",
    body: "The same permeable ridge sands that carry the city are the aquifer that supplies it. Protection zones around abstraction sites are drawn as travel-time capture areas, not as fences, and the industrial legacy of a century of textile finishing sits inside them as chlorinated-solvent plumes.",
  },
  {
    title: "A rebuilt quarter and a tightened safety regime",
    body: "The May 2000 fireworks depot explosion destroyed roughly forty hectares of the Roombeek district. The reconstruction is one of the more studied exercises in participatory Dutch urbanism, and the national external-safety regime that followed converted hazard into mapped risk contours — another continuous field laid over the city.",
  },
  {
    title: "Half a catchment",
    body: "Every other Dutch city of this size draws labour and custom from a full circle. Enschede's circle is cut by a national border four kilometres from its centre. The land beyond is not empty — Gronau and the Münsterland are there — but it is separated by a labour-market and institutional membrane whose permeability, not the city's land supply, sets its accessible market.",
  },
];
