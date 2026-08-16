"""One record per city, so both get the same analysis.

The report had a real asymmetry in it: Enschede had a population history, seven
forecasting models, a development classifier and a growth simulation, and Cape
Town had one section of description. That is not a finding about the two
cities, it is a finding about which one got built first.

This module fixes it by making the city a parameter. Everything the machine
learning sections need — the population series, the geometry the grid is cut
from, the constraint that binds — lives in a `City` record, and the pages take
one of these rather than importing Enschede's constants directly.

The two cities are genuinely different and the record is where that difference
is stated, once, instead of being scattered through the pages:

  - Enschede is a small city with plenty of land that cannot build because of a
    chemical measurement. Its population series has three regimes and a
    thirty-year plateau.
  - Cape Town is a large city with almost no land left, growing fast. Its
    population series is one long curve with no plateau at all, which is why
    the same seven models behave completely differently on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .provenance import OFFICIAL, RECONSTRUCTED, Series

# ---------------------------------------------------------------------
# Geometry the grid is cut from
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Geometry:
    """The shape of a city, reduced to what a cell grid needs.

    Deliberately crude. A ring model with a couple of masks is not a map, and
    the development sections say so. What it has to get right is the *kind* of
    constraint each city faces, because that is the report's argument: Enschede
    is stopped by a scalar field it cannot see, Cape Town by polygons it can.
    """

    extent_km: float           # half-width of the modelled square
    radius_km: float           # radius of the currently built-up area
    spacing_km: float          # cell size
    stations: tuple[tuple[float, float], ...]
    density_decay: float       # how fast built density falls with distance
    # A hard edge running north-south: nothing may be built beyond it. The
    # German border for Enschede, the coastline for Cape Town.
    hard_edge_x: float | None = None
    # A circular protected mass: the Aamsveen bog, or Table Mountain.
    protected_centre: tuple[float, float] | None = None
    protected_radius_km: float = 0.0
    edge_margin_km: float = 1.6      # how far past the built area building is allowed
    # Land already built on, km². The built radius is solved to hit this so the
    # grid agrees with the land ledger instead of being tuned by hand.
    built_km2: float = 0.0


# ---------------------------------------------------------------------
# Population histories
# ---------------------------------------------------------------------

# Cape Town, City of Cape Town metropolitan municipality. The four census
# figures are Statistics South Africa and are exact. Everything before 1996 is
# the urban agglomeration under boundaries that no longer exist — Cape Town was
# amalgamated into a single metropolitan council in 2000, and comparing across
# that change is comparing two different areas. They are kept because the shape
# of the growth matters and dropping forty years would hide it, but they are
# labelled reconstructed and the forecasting section is told where the reliable
# part starts.
_CAPE_TOWN_ANCHORS = {
    1950: 618_000,
    1960: 803_000,
    1970: 1_096_000,
    1980: 1_491_000,
    1991: 2_350_000,
    1996: 2_563_095,      # census
    2001: 2_893_251,      # census
    2011: 3_740_026,      # census
    2016: 4_004_793,      # community survey
    2022: 4_772_846,      # census
    2024: 4_800_000,      # municipal estimate
}

CAPE_TOWN_OFFICIAL_FROM = 1996


def _interpolate(anchors: dict[int, int], wobble_scale: float) -> pd.DataFrame:
    """Anchors onto every year, with a small deterministic wobble.

    Same treatment as the Enschede series and for the same reason: straight
    lines between anchors give a series with no year-to-year variation, which
    flatters every forecasting model that touches it. A model that cannot be
    wrong about noise looks better than it is. The wobble is deterministic, so
    every run gives the same answer.
    """
    years = np.arange(min(anchors), max(anchors) + 1)
    ay = np.array(sorted(anchors))
    av = np.array([anchors[y] for y in ay], dtype=float)
    base = np.interp(years, ay, av)
    wobble = wobble_scale * (np.sin(years * 1.7) + 0.55 * np.sin(years * 0.6 + 1.3))
    return pd.DataFrame({"year": years,
                         "population": np.round(base + wobble).astype(int)})


def cape_town_population() -> tuple[pd.DataFrame, Series]:
    frame = _interpolate(_CAPE_TOWN_ANCHORS, wobble_scale=9_000)
    series = Series(
        "Cape Town population, 1950–2024", RECONSTRUCTED,
        "Stats SA censuses 1996, 2001, 2011, 2022 and the 2016 Community Survey; "
        "pre-1996 figures are the urban agglomeration under former boundaries",
        "Exact at the census years. Interpolated between them, and the years before 1996 "
        "describe a different area from the one the later figures describe — Cape Town became "
        "a single metropolitan municipality in 2000.",
    )
    return frame, series


# Johannesburg, City of Johannesburg metropolitan municipality. The census
# figures are Statistics South Africa. The 2001 jump of over a million people
# in five years is not a birth rate; it is the 2000 amalgamation redrawing the
# boundary around areas the 1996 count left out. The dip in 1996 is the same
# artefact seen from the other side. Pre-1996 figures are the urban
# agglomeration under boundaries that no longer exist, kept because the
# seventy-year climb matters, labelled reconstructed.
_JOHANNESBURG_ANCHORS = {
    1950: 900_000,
    1960: 1_250_000,
    1970: 1_700_000,
    1980: 2_150_000,
    1991: 2_600_000,
    1996: 2_062_000,       # census, transitional boundaries
    2001: 3_225_608,       # census, metropolitan boundary
    2011: 4_434_827,       # census
    2022: 6_060_952,       # census
    2024: 6_200_000,       # municipal estimate
}


def johannesburg_population() -> tuple[pd.DataFrame, Series]:
    frame = _interpolate(_JOHANNESBURG_ANCHORS, wobble_scale=9_000)
    series = Series(
        "Johannesburg population, 1950–2024", RECONSTRUCTED,
        "Stats SA censuses 1996, 2001, 2011, 2022; pre-1996 figures are the urban "
        "agglomeration under former boundaries",
        "Exact at the census years. Interpolated between them. The 1996 dip and the 2001 "
        "leap are the same event seen twice: the 2000 amalgamation moved the boundary, not "
        "the people. The 2022 census figure is Stats SA's, published with an undercount "
        "adjustment that has been publicly contested.",
    )
    return frame, series


# Amsterdam, gemeente Amsterdam. Every figure is the municipal population
# register (bevolkingsregister, later the GBA/CBS counts) — this is the best
# documented series in the project, and the only one that goes down as well as
# up. The boundary has been stable since the 1966 annexation of the Bijlmer,
# which is why this series can be labelled official where the South African
# ones cannot.
_AMSTERDAM_ANCHORS = {
    1950: 846_000,
    1959: 872_000,         # the post-war peak
    1970: 807_000,
    1980: 715_000,
    1985: 676_000,         # the trough
    1990: 695_000,
    2000: 727_000,
    2010: 767_000,
    2015: 822_000,
    2020: 873_000,
    2024: 938_000,
}


def amsterdam_population() -> tuple[pd.DataFrame, Series]:
    frame = _interpolate(_AMSTERDAM_ANCHORS, wobble_scale=700)
    series = Series(
        "Amsterdam population, 1950–2024", OFFICIAL,
        "CBS / municipal population register; 1950 figure before the 1966 Bijlmer "
        "annexation, so the pre-1966 years describe a slightly smaller municipality",
        "Exact at the anchor years, interpolated between. The only series here with a "
        "genuine decline: the city lost a fifth of its people between 1959 and 1985 — "
        "suburbanisation, deindustrialisation and the Bijlmer's failed start — and then "
        "regained all of it by 2022.",
    )
    return frame, series


# ---------------------------------------------------------------------
# The land ledger
# ---------------------------------------------------------------------

# Every square kilometre a city has, and what happens to it on the way to being
# somewhere you could actually put a house. Both cities are run through the
# same ledger and they fail in different places, which is the whole argument of
# this report reduced to one arithmetic:
#
#   Cape Town runs out of LAND.        It reaches the bottom with 251 km² left.
#   Enschede runs out of PERMISSION.   It reaches the bottom with 97 km² of land
#                                      and an allowance of zero to build on it.
#
# A ledger that stopped at "land physically available" would score Enschede as
# the healthier of the two, which is exactly backwards, and that is why the last
# row of each is a legal quantity rather than a physical one.

_ENSCHEDE_LEDGER = [
    ("Municipal area", 140.0, "total", "Everything inside the municipal boundary."),
    ("Already built on", -43.0, "used", "The existing urban fabric."),
    ("Water and infrastructure", -7.0, "used",
     "Rivers, canals, motorway and rail land."),
    ("Nature and forest", -25.0, "hard",
     "Including the Aamsveen raised bog, which is what makes the nitrogen test bite."),
]

_CAPE_TOWN_LEDGER = [
    ("Municipal area", 2451.0, "total", "Everything inside the metropolitan boundary."),
    ("Formally protected", -557.0, "hard",
     "Table Mountain National Park, nature reserves and marine protected areas. "
     "22.7% of the city, and none of it is available."),
    ("Outside the urban edge", -999.0, "hard",
     "Mountain, agricultural and rural land beyond the development edge."),
    ("Already built on", -644.0, "used",
     "About 72% of the land inside the edge is already developed."),
]

_JOHANNESBURG_LEDGER = [
    ("Municipal area", 1645.0, "total", "The City of Johannesburg, west to east."),
    ("Already built on", -1180.0, "used",
     "The urban footprint — townships, suburbs, mines-turned-industry, "
     "and a CBD that emptied and refilled."),
    ("Mining land and tailings", -80.0, "hard",
     "Gold-reef sand dumps and mine-leased land. Technically developable; "
     "in practice nobody finances it."),
    ("Dolomitic ground", -60.0, "hard",
     "Sinkhole-prone limestone in the west. Buildings need raft foundations "
     "and insurers need persuading."),
]

_AMSTERDAM_LEDGER = [
    ("Municipal area", 219.0, "total", "The municipality, water included."),
    ("Water", -55.0, "hard",
     "The IJ, the canals, the Amstel and the polder ditches. IJburg proves "
     "water is a barrier you can pay to move, not one you can ignore."),
    ("Parks and the Amsterdamse Bos", -25.0, "hard",
     "The Bos is a twentieth-century plantation the city built for itself "
     "and is not about to build over."),
    ("Already built on", -95.0, "used",
     "The seventeenth-century core, the nineteenth-century ring and the "
     "post-war extensions, already carrying 940,000 people."),
]


def _ledger_frame(rows, city_name: str, permitted: float | None = None) -> pd.DataFrame:
    """Waterfall rows with running totals, ready to plot."""
    out, running = [], 0.0
    for label, value, kind, note in rows:
        start = running
        running = value if kind == "total" else running + value
        out.append({
            "city": city_name, "step": label, "value": value, "kind": kind,
            "start": 0.0 if kind == "total" else running,
            "end": value if kind == "total" else start,
            "running": running, "note": note,
        })
    out.append({
        "city": city_name, "step": "Land physically left", "value": running,
        "kind": "result", "start": 0.0, "end": running, "running": running,
        "note": "What remains after everything above. Farmland and vacant plots — "
                "convertible in principle.",
    })
    if permitted is not None:
        out.append({
            "city": city_name, "step": "…that may actually be built on", "value": permitted,
            "kind": "permitted", "start": 0.0, "end": permitted, "running": permitted,
            "note": "The same land, after the law is applied.",
        })
    return pd.DataFrame(out)


# ---------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------


@dataclass
class City:
    key: str
    name: str
    country: str
    accent: str
    land_area_km2: float          # the area growth is allowed to happen in
    buildable_km2: float          # what is actually available to build on
    geometry: Geometry
    binding_constraint: str       # the one-line answer to "what stops building"
    population_note: str          # what the series does, in plain words
    forecast_note: str            # why the models behave the way they do here
    # What the ledger ends on: the legal quantity, not the physical one.
    permitted_note: str = ""
    permitted_km2: float | None = None
    _population: object = field(repr=False, default=None)
    _sites: object = field(repr=False, default=None)
    _ledger: object = field(repr=False, default=None)

    def population(self) -> tuple[pd.DataFrame, Series]:
        return self._population()

    def ledger(self) -> pd.DataFrame:
        """The land ledger for this city, as waterfall rows."""
        return _ledger_frame(self._ledger, self.name, self.permitted_km2)

    def sites(self) -> pd.DataFrame:
        """Recognisable places, in this city's own coordinate frame.

        Each city carries its own. Drawing Enschede's hospital and science park
        on a map of Cape Town would put eight labels within a kilometre of the
        Foreshore and call it a legend.
        """
        from . import spatial as sp
        return sp.KNOWN_SITES if self._sites is None else self._sites()


def _enschede_population():
    from . import demography as dem
    data = dem.load_population()
    return data.frame, data.series


ENSCHEDE = City(
    key="enschede",
    name="Enschede",
    country="Netherlands",
    accent="#2a78d6",
    land_area_km2=140.0,
    buildable_km2=43.0,
    geometry=Geometry(
        extent_km=6.5,
        radius_km=float(np.sqrt(43 / np.pi)),
        spacing_km=0.2,
        stations=((0.0, 0.0), (-2.6, 1.2), (2.8, 0.4)),
        density_decay=0.35,
        hard_edge_x=4.0,                      # the German border
        protected_centre=(4.2, -3.0),         # standing in for the Aamsveen bog
        protected_radius_km=1.8,
        built_km2=43.0,
    ),
    binding_constraint="Nitrogen. There is land, and the allowance to emit onto it is zero.",
    permitted_km2=0.0,
    permitted_note=(
        "Enschede reaches the bottom of the ledger with 97 km² of land and permission to "
        "build on none of it. Since 2019 a project that adds any nitrogen to an over-loaded "
        "habitat gets no allowance at all, and the raised bog on the city's own edge is four "
        "times over its limit. The land is there. The permission is zero."
    ),
    population_note=(
        "Three regimes, not one: fast growth on textiles to the early 1960s, thirty years flat "
        "while that industry collapsed, then slow growth from students and international "
        "migration."
    ),
    forecast_note=(
        "The plateau is what makes this hard. A model that fits the recent slow growth "
        "extrapolates one thing; a model that fits the whole series extrapolates another."
    ),
)

CAPE_TOWN = City(
    key="cape_town",
    name="Cape Town",
    country="South Africa",
    accent="#eb6834",
    land_area_km2=2_451.0,
    buildable_km2=895.0,
    geometry=Geometry(
        extent_km=26.0,
        radius_km=float(np.sqrt(895 / np.pi)),   # ≈16.9 km
        spacing_km=0.8,
        # The rail spine: CBD, Bellville, Khayelitsha, Mitchells Plain, Muizenberg.
        stations=((0.0, 0.0), (8.0, 2.0), (15.0, -6.0), (11.0, -9.0), (3.0, -12.0)),
        density_decay=0.08,
        hard_edge_x=-6.0,                        # the Atlantic, to the west
        protected_centre=(-2.5, -4.0),           # Table Mountain National Park
        protected_radius_km=6.0,
        edge_margin_km=3.0,
        built_km2=644.0,
    ),
    binding_constraint=(
        "Land. A mountain, two oceans and a protected-area network leave 895 km² for "
        "4.8 million people."
    ),
    permitted_km2=251.0,
    permitted_note=(
        "Cape Town reaches the bottom of the ledger with about 251 km² — roughly 10% of the "
        "municipality, for a city adding a Enschede-sized population every three years. The "
        "permission exists. The land does not."
    ),
    population_note=(
        "One long curve and no plateau anywhere: 618,000 in 1950 to 4.8 million today. The "
        "city added more people in the last thirty years than Enschede has ever had."
    ),
    forecast_note=(
        "The opposite problem from Enschede. Nothing in the history tells a model when the "
        "curve should bend, so the models agree on the past and disagree enormously about 2050 "
        "— which is the honest state of the question, not a defect of the models."
    ),
)

def _cape_town_sites():
    from . import spatial as sp
    return sp.KNOWN_SITES_CAPE_TOWN


JOHANNESBURG = City(
    key="johannesburg",
    name="Johannesburg",
    country="South Africa",
    accent="#d4a017",
    land_area_km2=1_645.0,
    buildable_km2=1_500.0,
    geometry=Geometry(
        extent_km=26.0,
        radius_km=float(np.sqrt(1_500 / np.pi)),   # ≈21.9 km
        spacing_km=1.0,
        # The Gautrain spine and the rail commuters' lines: Park Station,
        # Rosebank, Sandton, Midrand — and Soweto, a metro away from its jobs.
        stations=((0.0, 0.0), (5.0, 5.0), (9.0, 8.0), (16.0, 15.0), (-8.0, -13.0)),
        density_decay=0.05,
        hard_edge_x=None,                      # nothing stops this city. that is the point
        protected_centre=(-4.0, -2.0),         # Melville Koppies, the rocky ridge
        protected_radius_km=1.0,
        edge_margin_km=3.0,
        built_km2=1_180.0,
    ),
    binding_constraint=(
        "Nothing physical. No mountain, no sea, no urban edge — growth is stopped by "
        "the price of the land and the geography of where work is, not by the land itself."
    ),
    permitted_km2=300.0,
    permitted_note=(
        "Johannesburg reaches the bottom of the ledger with about 300 km² of genuinely "
        "serviceable land — and unlike the other cities here, that is not the constraint "
        "anyone names. The city has always had room; the question the other cities do not "
        "face is room for whom, and where, at what price."
    ),
    population_note=(
        "A seventy-year climb with one artefact in it: the dip in 1996 and the leap in "
        "2001 are the 2000 amalgamation moving a boundary, not people leaving and "
        "returning. Six million people on a gold reef nobody was supposed to live on."
    ),
    forecast_note=(
        "The series that most tempts a model to be confident: nearly exponential for "
        "seventy years. But the last two census intervals disagree about the rate, and "
        "the 2022 count itself is contested — the honest forecast is a wide band with "
        "a warning label."
    ),
)

AMSTERDAM = City(
    key="amsterdam",
    name="Amsterdam",
    country="Netherlands",
    accent="#b5446e",
    land_area_km2=219.0,
    buildable_km2=120.0,
    geometry=Geometry(
        extent_km=8.5,
        radius_km=float(np.sqrt(120 / np.pi)),    # ≈6.2 km
        spacing_km=0.3,
        # Centraal, Zuid, Sloterdijk, Bijlmer ArenA, Noord — five nodes of a
        # metro region pretending to be one medium-sized municipality.
        stations=((0.0, 0.5), (1.8, -2.8), (-1.6, 1.8), (5.2, -3.8), (0.2, 3.8)),
        density_decay=0.22,
        hard_edge_x=None,                      # the municipal border is on every side
        protected_centre=(-3.2, -3.5),         # the Amsterdamse Bos
        protected_radius_km=1.9,
        edge_margin_km=1.2,
        built_km2=95.0,
    ),
    binding_constraint=(
        "A municipal border it cannot move. The last annexation was 1966; since then "
        "the city has grown by densifying and by building into its own water."
    ),
    permitted_km2=10.0,
    permitted_note=(
        "Amsterdam reaches the bottom of the ledger with about 10 km² — the housing "
        "pipeline: Haven-Stad's docks, the last Zuidas plots and whatever the city "
        "decides it can fill the IJ with next. The land is nearly gone, the demand is "
        "not, and the price of a house says so."
    ),
    population_note=(
        "The only U-shape in the project. A fifth of the city left between 1959 and "
        "1985 — for Purmerend and Almere, for the car — and the whole loss was "
        "recovered by 2022. Both halves are real and a model must explain both."
    ),
    forecast_note=(
        "The test the other cities do not set: a model trained on the recovery alone "
        "sees steep growth forever; a model that remembers the decline refuses to "
        "believe it. The truth is that a municipality this size is full when policy "
        "says it is full, not when a curve bends."
    ),
)


def _johannesburg_sites():
    from . import spatial as sp
    return sp.KNOWN_SITES_JOHANNESBURG


def _amsterdam_sites():
    from . import spatial as sp
    return sp.KNOWN_SITES_AMSTERDAM


CAPE_TOWN._population = cape_town_population
CAPE_TOWN._sites = _cape_town_sites
CAPE_TOWN._ledger = _CAPE_TOWN_LEDGER
ENSCHEDE._population = _enschede_population
ENSCHEDE._ledger = _ENSCHEDE_LEDGER
JOHANNESBURG._population = johannesburg_population
JOHANNESBURG._sites = _johannesburg_sites
JOHANNESBURG._ledger = _JOHANNESBURG_LEDGER
AMSTERDAM._population = amsterdam_population
AMSTERDAM._sites = _amsterdam_sites
AMSTERDAM._ledger = _AMSTERDAM_LEDGER

CITIES: dict[str, City] = {c.name: c for c in
                           (ENSCHEDE, CAPE_TOWN, JOHANNESBURG, AMSTERDAM)}


def pick(name: str) -> City:
    return CITIES[name]
