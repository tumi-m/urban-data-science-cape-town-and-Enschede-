import { SourceKey } from "@/lib/provenance";

/**
 * The constraint taxonomy.
 *
 * A geographic information system stores what its file formats can hold, and
 * the dominant format holds polygons. So constraints arrive as polygons: a
 * settlement boundary, a nature network, a protection zone. The habit of
 * thought that follows is that a constraint is a place, and that planning is
 * the business of moving development relative to places.
 *
 * Most of the constraints that actually bind in Enschede are not places. They
 * are scalar fields with thresholds — a quantity defined everywhere, mapped as
 * a polygon only because someone drew the contour where the quantity crosses a
 * number. The distinction is not pedantic. A polygon can only be moved or
 * fought. A field can be reduced, and reducing it moves every contour at once.
 */

export type Shape = "field" | "polygon";

export interface Constraint {
  id: string;
  label: string;
  shape: Shape;
  /** The quantity, where there is one. */
  quantity: string;
  unit: string;
  /** The number at which the contour gets drawn. */
  threshold: string;
  /** What the constraint does to development. */
  effect: string;
  /** What reduces it — empty for polygons, which is the point. */
  reducedBy: string;
  source: SourceKey;
}

export const CONSTRAINTS: Constraint[] = [
  {
    id: "nitrogen",
    label: "Nitrogen deposition",
    shape: "field",
    quantity: "Deposited reactive nitrogen on protected habitat",
    unit: "mol N/ha/yr",
    threshold:
      "The habitat's critical value — 400 for active raised bog — with no allowance for increases once it is exceeded",
    effect:
      "Consent for any project whose calculated contribution does not round to zero at an over-loaded hexagon must be individually justified or offset.",
    reducedBy:
      "Emission-free construction plant, lower induced car traffic per dwelling, fleet electrification, and reduced agricultural ammonia across the region.",
    source: "aerius",
  },
  {
    id: "noise",
    label: "Noise",
    shape: "field",
    quantity: "Day-evening-night sound level at the façade",
    unit: "dB Lden",
    threshold: "Statutory preference values, with a bounded discretion to exceed them",
    effect:
      "Sets how close housing can sit to the ring roads, the rail corridor and the industrial estates — which is to say, it prices exactly the locations densification depends on.",
    reducedBy:
      "Quieter road surfaces, lower speeds, façade construction, and mode shift. Every one of these is an engineering decision rather than a land-use one.",
    source: "gemEnschede",
  },
  {
    id: "safety",
    label: "External safety",
    shape: "field",
    quantity: "Individual fatality probability from hazardous installations and transport",
    unit: "per year",
    threshold: "The 10⁻⁶ per year contour, with a separate account for group risk",
    effect:
      "Withholds development capacity along transport routes and pipelines and around installations. Enschede's regime was reshaped by the 2000 fireworks depot explosion.",
    reducedBy:
      "Relocating or removing the hazard, reducing the quantity stored, or rerouting the transport. The contour follows the source, not the map.",
    source: "gemEnschede",
  },
  {
    id: "groundwater",
    label: "Groundwater protection",
    shape: "field",
    quantity: "Travel time of infiltrating water to the abstraction well",
    unit: "years",
    threshold: "Nested one-year, twenty-five-year and hundred-year capture zones",
    effect:
      "Restricts activities and subsurface works above the aquifer that supplies the city. The permeable ridge sands that make abstraction viable also make the aquifer vulnerable.",
    reducedBy:
      "Changing what is done at the surface. The zone geometry itself follows from the abstraction rate, so it moves when pumping does.",
    source: "provOverijssel",
  },
  {
    id: "radar",
    label: "Radar and obstacle limitation",
    shape: "field",
    quantity: "Structure height intruding on a radar or approach surface",
    unit: "m above the surface",
    threshold: "Interference criteria assessed case by case",
    effect:
      "Caps turbine tip height across large parts of Twente, which removes the technology with by far the lowest land intensity from consideration.",
    reducedBy:
      "Radar mitigation and signal processing. This is a technical problem that is treated as a spatial one.",
    source: "resTwente",
  },
  {
    id: "nnn",
    label: "Nature Network and Natura 2000 boundaries",
    shape: "polygon",
    quantity: "Designated area",
    unit: "hectares",
    threshold: "Inside or outside",
    effect:
      "Withdraws land from development and requires compensation where the network is impaired.",
    reducedBy:
      "Nothing. This one really is a boundary, which is why it is the constraint planners find easiest to reason about and the one that explains least about why Enschede cannot build.",
    source: "natura2000",
  },
  {
    id: "contour",
    label: "Settlement boundary and the sequencing test",
    shape: "polygon",
    quantity: "Designated urban area",
    unit: "hectares",
    threshold: "Inside or outside, with a demonstration of need for anything outside",
    effect:
      "Directs growth into the existing urban fabric before greenfield land can be considered.",
    reducedBy:
      "Nothing directly, though the demonstration of need is where the argument is actually had.",
    source: "provOverijssel",
  },
];

/** What the taxonomy adds up to. */
export const THESIS = {
  claim:
    "Most of what stops Enschede building is a measurement, not a line on a map — and a measurement can be brought down.",
  corollaries: [
    "If you treat every limit as a boundary, all you can do is move development somewhere else. If you recognise the measurements, you can lower them — and that frees up every location at once.",
    "Most of a home's nitrogen comes from the driving it causes over fifty years, not from building it. So where you put housing, and how much parking you give it, is nitrogen policy — whatever the plan calls it.",
    "The renewable option that uses the least land is the one the rules block, so the search for sites keeps landing on the one that uses the most. The scarce thing is being spent to avoid the fixable one.",
    "When a limit has no minimum allowance, the cost of complying is mostly modelling and legal risk rather than actually cutting emissions. That favours big developers, who can afford both.",
  ],
};
