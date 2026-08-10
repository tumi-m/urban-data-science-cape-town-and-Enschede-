"""Cape Town, and the comparison with Enschede.

The other city in this project. It is here because it fails in the opposite
direction: Cape Town has run out of land, Enschede has plenty and still cannot
build. Putting them side by side shows something neither shows alone — what
kind of limit you have decides what you can do about it.

These figures come from the City of Cape Town's published documents and from
research on the Cape Flats. Unlike the Enschede sections, nothing here is
recomputed from source data, and the page says so.
"""

from __future__ import annotations

import pandas as pd

# --- Headline figures -------------------------------------------------
POPULATION = 4_800_000
PROTECTED_HA = 55_697
PROTECTED_SHARE = 22.72          # % of the municipality
URBAN_EDGE_KM2 = 895             # land inside the urban development edge
STATION_BUFFERS_KM2 = 183        # land within 800 m of a station
VEGETATION_LOST_PCT = 61
CBA_SHARE = 23.6                 # critical biodiversity areas, % of regional plan
ESA_SHARE = 13.4                 # ecological support areas, % of regional plan

LIQUEFIABLE_FROM_M = 3.2
LIQUEFIABLE_TO_M = 19.0
AQUIFER_DEPTH_M = 65
AQUIFER_YIELD_MM3 = 18           # million m³ per year

# Worked out from the city's own numbers rather than looked up: 55,697 ha is
# stated as 22.72% of the municipality, so the whole is 245,145 ha. That matches
# the published municipal area, which is a useful sign the two figures agree.
MUNICIPAL_KM2 = round(PROTECTED_HA / (PROTECTED_SHARE / 100) / 100)

PROTECTED_KM2 = PROTECTED_HA / 100
STATION_SHARE = STATION_BUFFERS_KM2 / URBAN_EDGE_KM2
PEOPLE_PER_BUILDABLE_KM2 = POPULATION / URBAN_EDGE_KM2


def land_split() -> pd.DataFrame:
    """How the municipality divides up. The blue block is what can be built on."""
    other = MUNICIPAL_KM2 - PROTECTED_KM2 - URBAN_EDGE_KM2
    return pd.DataFrame([
        {"part": "Protected nature", "km2": round(PROTECTED_KM2), "order": 0,
         "detail": "National parks, nature reserves and marine protected areas."},
        {"part": "Inside the urban edge", "km2": URBAN_EDGE_KM2, "order": 1,
         "detail": "Where building is allowed at all."},
        {"part": "Everything else", "km2": round(other), "order": 2,
         "detail": "Farmland, biodiversity areas short of formal protection, mountain."},
    ])


LIMITS = pd.DataFrame([
    {
        "limit": "The urban edge",
        "kind": "A line",
        "what": "A line drawn in 1996 around how far the city may spread.",
        "does": "Stops building outside it. It worked — sprawl slowed. But it assumed the "
                "city would build upward inside the line instead, and that did not happen "
                "at anything like the rate needed.",
        "fixable": "No. A line can only be moved, and moving it has been a political fight "
                   "for thirty years.",
    },
    {
        "limit": "Protected nature",
        "kind": "A line",
        "what": "Protected areas, critical biodiversity areas and ecological support areas, "
                "mapped as shapes across the city.",
        "does": "Takes roughly a third of the city's land out of play. Cape Town sits in the "
                "smallest and richest plant kingdom on earth, and six vegetation types exist "
                "nowhere else.",
        "fixable": "No. There is nothing underneath to reduce — it is designated land.",
    },
    {
        "limit": "The Cape Flats sand",
        "kind": "A measurement",
        "what": f"Loose windblown sand that can lose its strength in an earthquake, between "
                f"about {LIQUEFIABLE_FROM_M} and {LIQUEFIABLE_TO_M:.0f} metres down.",
        "does": "Makes tall, heavy buildings far more expensive exactly where the city has "
                "flat land available. The place with room to build is the place where "
                "building up costs most.",
        "fixable": "Partly. Ground improvement and different foundations lower the cost, and "
                   "lighter construction avoids it. An engineering problem being treated as a "
                   "location problem.",
    },
    {
        "limit": "The Cape Flats aquifer",
        "kind": "A measurement",
        "what": f"A shallow sandy aquifer under the same flat land, holding about "
                f"{AQUIFER_YIELD_MM3} million cubic metres a year of usable water.",
        "does": "Whatever soaks into the surface reaches the water. Housing without proper "
                "sewerage, built over the recharge area, contaminates the supply the city "
                "fell back on during the drought.",
        "fixable": "Yes. What reaches the groundwater depends on what is done at the "
                   "surface — sanitation, drainage, industrial controls.",
    },
])


COMPARISON = [
    {
        "question": "Is land actually scarce?",
        "ct": "Yes. Mountain on one side, ocean on two, and roughly a third of the land "
              f"protected. {URBAN_EDGE_KM2} km² inside the edge for about 4.8 million people.",
        "en": "No. 140 km² of municipal land for 161,000 people, and only about 43 km² of it "
              "built on.",
        "so": "Two cities can both be hard to build in for opposite reasons. Enschede has "
              "plenty of land and still cannot build; Cape Town has almost none and builds "
              "anyway, badly, at the edge.",
    },
    {
        "question": "What is the limit made of?",
        "ct": "Mostly lines on a map: the urban edge, and the protected areas.",
        "en": "Mostly measurements: nitrogen in the air, noise at the window, risk near a "
              "pipeline, travel time to a well.",
        "so": "A line can only be moved or fought over. A measurement can be brought down — "
              "and that frees up every location at once, not just one.",
    },
    {
        "question": "What does the limit push building into?",
        "ct": "The Cape Flats: flat, available, the worst ground to build heavy on, and "
              "sitting directly over the drinking-water aquifer.",
        "en": "The edge of town, where car use per household is highest — which is what "
              "produces the nitrogen that blocks the next permit.",
        "so": "In both cities the limit pushes building to the place that makes the next "
              "problem worse. That is the pattern worth looking for anywhere.",
    },
    {
        "question": "How good is access to a train?",
        "ct": f"{STATION_SHARE * 100:.0f}% of land inside the urban edge is within an 800 m "
              "walk of a station — a large rail network, poorly reached, and in recent years "
              "barely running.",
        "en": "8% of built-up land within a real walk of one of three stations. By bicycle, "
              "the same three stations reach 82% of residents.",
        "so": "Cape Town's problem is not that it lacks stations. Both cities show the same "
              "thing: the walking radius, not the rail network, is what limits the number.",
    },
    {
        "question": "What would actually help?",
        "ct": "Making the trains run, and getting people to the stations that already exist by "
              "something other than walking. Both cheaper than new rail.",
        "en": "Building near the stations and the cycle route, with less parking. That cuts "
              "car use, which cuts nitrogen, which is what is blocking permits.",
        "so": "In both cases the cheapest fix is not construction. It is changing how people "
              "reach what is already built.",
    },
]


SIDE_BY_SIDE = pd.DataFrame([
    {"": "People", "Cape Town": "4.8 million", "Enschede": "161,000",
     "What it means": "Cape Town is about thirty times bigger."},
    {"": "Land you can build on", "Cape Town": f"{URBAN_EDGE_KM2} km²",
     "Enschede": "43 km² built, 140 km² total",
     "What it means": "Twenty times the buildable land for thirty times the people."},
    {"": "People per km² of that land",
     "Cape Town": f"{PEOPLE_PER_BUILDABLE_KM2:,.0f}", "Enschede": f"{161_000 / 43:,.0f}",
     "What it means": "Cape Town is already denser on the land it uses."},
    {"": "Land protected for nature",
     "Cape Town": f"{PROTECTED_SHARE}% formally, about a third once biodiversity areas count",
     "Enschede": "A few per cent, but one bog sets a limit for the whole city",
     "What it means": "Cape Town loses land to protection. Enschede loses permission."},
    {"": "What blocks building",
     "Cape Town": "A line on a map, and land already spoken for",
     "Enschede": "Nitrogen in the air, and noise at the window",
     "What it means": "One is drawn, the other is measured."},
    {"": "Land within a walk of a station",
     "Cape Town": f"{STATION_SHARE * 100:.0f}% of land inside the edge",
     "Enschede": "8% of built-up land, 82% of residents by bicycle",
     "What it means": "Same arithmetic behind both: the walking radius, not the network."},
])


SHARED_LESSONS = [
    ("The limit pushes building to the worst place",
     "Cape Town's edge pushes housing onto sand that is expensive to build on and sits over "
     "the water supply. Enschede's land prices push housing to the edge of town, where people "
     "drive most — and driving produces the nitrogen that blocks the next permit. Neither was "
     "anyone's plan. Both follow from the limit."),
    ("The tool draws maps, so the answer comes back as a map",
     "Planning software holds shapes, so limits get stored as shapes, and the fix always looks "
     "like moving a line. But Cape Town's real problem is that the trains stopped running, and "
     "Enschede's is a chemical measurement. Neither is a shape, and neither is fixed by moving "
     "one."),
    ("The cheapest fix is not construction",
     "In Cape Town it is making the existing trains run and helping people reach the stations "
     "that already exist. In Enschede it is building near the stations with less parking, and "
     "opening the German border to commuting. In both cases the thing that would help most "
     "costs a fraction of what new infrastructure costs."),
]


# ---------------------------------------------------------------------
# Live data from the City of Cape Town open data portal
# ---------------------------------------------------------------------
#
# The city publishes its spatial layers through an ArcGIS Open Data portal.
# The fetch below is real code against real endpoints; it returns None when the
# host has no outbound access, and every chart drawn from the fallback says so.
# The sandbox this was written in could not reach the portal, so the fallback
# path is the one that has actually been exercised.

CCT_PORTAL = "https://odp-cctegis.opendata.arcgis.com"
CCT_LAYERS = {
    "rail_stations": "Metrorail stations",
    "urban_edge": "Urban development edge",
    "bionet": "Biodiversity network",
    "suburbs": "Official suburbs",
}


def fetch_cct_layer(layer: str, timeout: int = 8):
    """Try the open data portal. None when it cannot be reached.

    Deliberately failure-tolerant: an unavailable portal should degrade the app
    to a labelled fallback, not break the page.
    """
    try:  # pragma: no cover - depends on host network
        import json
        import urllib.request

        url = f"{CCT_PORTAL}/datasets/{layer}.geojson"
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------
# Further analysis from the published figures
# ---------------------------------------------------------------------

def land_budget() -> pd.DataFrame:
    """How much room per person is left, under three ways of counting.

    The headline "895 km² for 4.8 million people" hides the fact that most of
    that land is already built on. What matters for the next million people is
    what is left, and on the city's own numbers that is a small number.
    """
    built_share = 0.72   # share of the urban edge already developed, estimate
    remaining = URBAN_EDGE_KM2 * (1 - built_share)
    return pd.DataFrame([
        {"measure": "Whole municipality", "km2": MUNICIPAL_KM2,
         "m2_per_person": MUNICIPAL_KM2 * 1e6 / POPULATION,
         "note": "Includes mountain, ocean-front and protected land."},
        {"measure": "Inside the urban edge", "km2": URBAN_EDGE_KM2,
         "m2_per_person": URBAN_EDGE_KM2 * 1e6 / POPULATION,
         "note": "All land where building is permitted at all."},
        {"measure": "Still undeveloped inside the edge", "km2": round(remaining),
         "m2_per_person": remaining * 1e6 / POPULATION,
         "note": "What is actually left to build on. Estimate of the built share."},
    ])


def biodiversity_stack() -> pd.DataFrame:
    """Protection comes in layers, and they add up faster than the headline."""
    return pd.DataFrame([
        {"tier": "Formally protected", "share": PROTECTED_SHARE,
         "what": "Parks, nature reserves and marine protected areas. No development."},
        {"tier": "Critical biodiversity areas", "share": CBA_SHARE,
         "what": "Needed to meet national biodiversity targets. Development must avoid habitat loss."},
        {"tier": "Ecological support areas", "share": ESA_SHARE,
         "what": "Keeps the protected areas connected. Heavy infrastructure is hard to route."},
    ])


def density_comparison() -> pd.DataFrame:
    """Cape Town against other cities, on land people actually occupy.

    Gross municipal density flatters a city with a mountain in it and punishes
    one with farmland. Density over the buildable area is the fairer number and
    it is the one that decides whether transit can work.
    """
    return pd.DataFrame([
        {"city": "Cape Town", "people_per_km2": round(PEOPLE_PER_BUILDABLE_KM2),
         "basis": "Inside the urban development edge."},
        {"city": "Enschede", "people_per_km2": round(161_000 / 43),
         "basis": "Built-up area only."},
        {"city": "Johannesburg", "people_per_km2": 2_900,
         "basis": "Municipal area. Comparative figure, not recomputed here."},
        {"city": "Amsterdam", "people_per_km2": 5_200,
         "basis": "Municipal land area. Comparative figure, not recomputed here."},
        {"city": "Lagos", "people_per_km2": 7_900,
         "basis": "Metropolitan area. Comparative figure, not recomputed here."},
    ])


def water_budget() -> pd.DataFrame:
    """What the aquifer is worth, in days of city supply.

    The 18 million m³ a year figure means nothing on its own. Divided by what
    the city drinks, it becomes a number anyone can hold: roughly how long the
    aquifer alone could carry Cape Town.
    """
    litres_per_person_day = 180          # post-drought consumption, estimate
    daily_demand_m3 = POPULATION * litres_per_person_day / 1000
    annual_demand_m3 = daily_demand_m3 * 365
    return pd.DataFrame([
        {"measure": "Aquifer yield", "m3_per_year": AQUIFER_YIELD_MM3 * 1e6},
        {"measure": "City demand", "m3_per_year": round(annual_demand_m3)},
    ]), round(AQUIFER_YIELD_MM3 * 1e6 / daily_demand_m3)
