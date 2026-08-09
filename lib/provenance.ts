/**
 * Provenance discipline.
 *
 * Every number rendered anywhere in this platform carries a class and a source.
 * The point is not bureaucracy: an analytical claim is only as strong as the
 * weakest figure feeding it, and the reader must be able to see which figures
 * those are without leaving the chart.
 *
 * The four classes are deliberately coarse. A finer taxonomy invites the author
 * to hide behind it.
 */
export type Class =
  /** Published by a named authority. Reproducible by opening their document. */
  | "official"
  /** Computed here from stated inputs. The formula is given alongside. */
  | "derived"
  /** Standard physics or engineering parameter, quoted with its typical range. */
  | "engineering"
  /** Order-of-magnitude figure held in place until the authoritative layer lands. */
  | "estimate";

export const CLASS_LABEL: Record<Class, string> = {
  official: "official",
  derived: "derived",
  engineering: "engineering",
  estimate: "estimate",
};

/**
 * A single quantity. `note` should say what would change the number, not what
 * the number means — the label already does that.
 */
export interface Quantity {
  value: number;
  unit: string;
  klass: Class;
  source: SourceKey;
  /** For `derived`, the arithmetic. For `engineering`, the assumed range. */
  basis?: string;
  note?: string;
}

export interface Source {
  key: string;
  title: string;
  holder: string;
  /** Landing page for the dataset or document, where one exists publicly. */
  url?: string;
  /** What this platform actually takes from it. */
  takes: string;
}

const SOURCE_ENTRIES = {
  cbs: {
    key: "cbs",
    title: "StatLine — regional population, dwellings and land use",
    holder: "Centraal Bureau voor de Statistiek",
    url: "https://opendata.cbs.nl/statline/",
    takes: "Municipal population, dwelling stock, surface area, commuting flows.",
  },
  pdok: {
    key: "pdok",
    title: "Publieke Dienstverlening Op de Kaart — national geodata services",
    holder: "Kadaster / Ministerie van BZK",
    url: "https://www.pdok.nl/",
    takes:
      "BAG building and address polygons, AHN elevation rasters, BGT topography, administrative boundaries.",
  },
  ahn: {
    key: "ahn",
    title: "Actueel Hoogtebestand Nederland",
    holder: "Waterschappen, Rijkswaterstaat and provinces",
    url: "https://www.ahn.nl/",
    takes: "0.5 m LiDAR elevation model used for the ice-pushed ridge relief profile.",
  },
  aerius: {
    key: "aerius",
    title: "AERIUS Calculator and Monitor — nitrogen deposition model",
    holder: "Rijksinstituut voor Volksgezondheid en Milieu",
    url: "https://www.aerius.nl/",
    takes:
      "Deposition on habitat hexagons, critical deposition values, and the source-receptor relations behind the permit test.",
  },
  natura2000: {
    key: "natura2000",
    title: "Natura 2000 designation orders and habitat maps",
    holder: "Ministerie van Landbouw, Visserij, Voedselzekerheid en Natuur",
    url: "https://www.natura2000.nl/",
    takes: "Site boundaries, designated habitat types and their conservation objectives.",
  },
  provOverijssel: {
    key: "provOverijssel",
    title: "Omgevingsvisie and Omgevingsverordening Overijssel",
    holder: "Provincie Overijssel",
    url: "https://www.overijssel.nl/",
    takes:
      "Nature Network boundaries, groundwater protection zones, and the settlement-boundary policy that governs greenfield development.",
  },
  gemEnschede: {
    key: "gemEnschede",
    title: "Omgevingsvisie, Woonvisie and the municipal open data portal",
    holder: "Gemeente Enschede",
    url: "https://www.enschede.nl/",
    takes: "Housing programme, densification locations, district heating and mobility policy.",
  },
  resTwente: {
    key: "resTwente",
    title: "Regionale Energiestrategie Twente",
    holder: "Fourteen Twente municipalities, Provincie Overijssel and the regional grid operator",
    url: "https://energiestrategietwente.nl/",
    takes: "Regional renewable electricity target and the search areas carrying it.",
  },
  raadVanState: {
    key: "raadVanState",
    title: "Administrative jurisdiction on the nitrogen approach",
    holder: "Raad van State",
    url: "https://www.raadvanstate.nl/",
    takes:
      "The 2019 annulment of the programmatic approach and the 2022 annulment of the construction-phase exemption.",
  },
  ns: {
    key: "ns",
    title: "Network and station data for the Dutch rail system",
    holder: "ProRail and NS",
    url: "https://www.rijdendetreinen.nl/open-data",
    takes: "Station locations and the lines serving them.",
  },
  ctAccess: {
    key: "ctAccess",
    title: "Station-buffer coverage of the Cape Town urban development edge",
    holder: "Third-party analysis, restated as published",
    takes:
      "183 km² of 800 m station buffers against an 895 km² development edge, giving 20 per cent. Quoted here as given and not independently reproduced.",
  },
  clark: {
    key: "clark",
    title: "Negative-exponential urban density gradient",
    holder: "Standard urban-economics form",
    takes:
      "Density falling exponentially with distance from the centre, used to weight access coverage by people rather than by hectares.",
  },
  cctMsdf: {
    key: "cctMsdf",
    title: "Municipal Spatial Development Framework and Spatial Trends Report",
    holder: "City of Cape Town",
    url: "https://resource.capetown.gov.za/",
    takes: "The urban edge, its history since 1996, and land inside it.",
  },
  cctBionet: {
    key: "cctBionet",
    title: "Bioregional Plan and Biodiversity Spatial Plan",
    holder: "City of Cape Town",
    url: "https://resource.capetown.gov.za/",
    takes:
      "Protected areas, critical biodiversity areas, ecological support areas, and the share of natural vegetation already transformed.",
  },
  capeFlats: {
    key: "capeFlats",
    title: "Cape Flats geotechnical and aquifer studies",
    holder: "Published research on the Cape Flats sands and aquifer",
    takes:
      "Depth range of liquefiable sands, aquifer depth and yield, and pollution vulnerability.",
  },
  physics: {
    key: "physics",
    title: "Standard mechanics and powertrain efficiency ranges",
    holder: "Textbook values",
    takes:
      "Gravitational potential energy, human and electrical drivetrain efficiencies, fuel energy densities.",
  },
} as const satisfies Record<string, Source>;

export type SourceKey = keyof typeof SOURCE_ENTRIES;

/**
 * Widened to `Source` on the way out. The literal types are useful for deriving
 * the key union and useless to every consumer, which otherwise has to narrow
 * before it can read an optional field.
 */
export const SOURCES: Record<SourceKey, Source> = SOURCE_ENTRIES;

export function q(
  value: number,
  unit: string,
  klass: Class,
  source: SourceKey,
  extra: { basis?: string; note?: string } = {},
): Quantity {
  return { value, unit, klass, source, ...extra };
}

/** Fixed-significant-figure formatting. Analytical honesty starts at the decimal point. */
export function sig(value: number, digits = 3): string {
  if (value === 0) return "0";
  const mag = Math.floor(Math.log10(Math.abs(value)));
  const decimals = Math.max(0, digits - 1 - mag);
  return value.toLocaleString("en-GB", {
    minimumFractionDigits: Math.min(decimals, 4),
    maximumFractionDigits: Math.min(decimals, 4),
  });
}
