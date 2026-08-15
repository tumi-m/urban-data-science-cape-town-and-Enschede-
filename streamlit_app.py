"""
Enschede — spatial constraints.

A Streamlit deployment of the same constraint analysis the Next.js application
serves. Streamlit Cloud runs Python, so this is a port rather than a wrapper:
the analytical constants are restated here in Python and the figures are rebuilt
in Altair, which is Vega-Lite under a different surface and therefore carries
the same grammar the TypeScript charts are written in.

The duplication is worth naming rather than hiding. There are now two statements
of the same numbers, and they can drift. Everything that could drift lives in the
CONSTANTS block below, in the same order as the `data/*.ts` modules it mirrors, so
a change on one side has one obvious place to land on the other. Nothing outside
that block hard-codes a quantity.

Run locally:      streamlit run streamlit_app.py
Deploy:           point Streamlit Cloud at this file; requirements.txt does the rest.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# =====================================================================
# Presentation
# =====================================================================
#
# Tokens and the shared Altair configuration live in urban/theme.py so the
# charting helpers can use them without importing this module, and so there is
# one definition of each colour rather than two that drift.

from urban.theme import (  # noqa: E402
    DIVERGING, FONT, GRID, INK, INK_2, INK_3, RULE, SEQUENTIAL, SERIES,
    SHED_PX, SURFACE, SURFACE_2, style,
)
from urban.ui import (  # noqa: E402
    begin_section as ui_begin_section, caveat, figure, header, note, provenance,
    stats, values_table,
)
from urban.pages import (  # noqa: E402
    page_cape_town, page_compare, page_development, page_population,
    page_projection, page_simulation,
)
from urban.pages_behaviour import page_behaviour, page_scaling  # noqa: E402
from urban.pages_simulator import page_simulator  # noqa: E402
from urban.pages_open import page_opening  # noqa: E402
from urban import chrome, geo  # noqa: E402
from urban import gravity  # noqa: E402


# =====================================================================
# CONSTANTS — mirrors data/*.ts. The only place a quantity is written down.
# =====================================================================

# --- data/city.ts ----------------------------------------------------
POPULATION = 161_000
DWELLINGS = 78_000
LAND_AREA_KM2 = 140
BUILT_UP_KM2 = 43
BORDER_DISTANCE_KM = 4
RELIEF = {"low": 28, "centre": 45, "high": 60}

FRAME = [
    (
        "A raised bog inside the city limits",
        "Aamsveen, on the south-eastern edge of the municipality and continuous with the German "
        "Amtsvenn across the border, is a raised-bog Natura 2000 site. Raised bog carries the "
        "lowest nitrogen tolerance of any habitat in the Dutch system. Enschede is therefore one "
        "of very few Dutch cities whose own housing programme is tested against the strictest "
        "deposition threshold the country has, at a receptor a few kilometres from its centre.",
    ),
    (
        "A ridge, not a polder",
        "The city sits on a Saalian ice-pushed ridge of sands and gravels. Bearing capacity is "
        "good and there is no peat subsidence, so the western Dutch cost driver for dense "
        "construction is absent. What the ridge does introduce is thirty metres of intra-urban "
        "relief — trivial for a motor, not trivial for a person on an unassisted bicycle.",
    ),
    (
        "Groundwater beneath the built-up area",
        "The same permeable ridge sands that carry the city are the aquifer that supplies it. "
        "Protection zones around abstraction sites are drawn as travel-time capture areas, not as "
        "fences, and the industrial legacy of a century of textile finishing sits inside them as "
        "chlorinated-solvent plumes.",
    ),
    (
        "A rebuilt quarter and a tightened safety regime",
        "The May 2000 fireworks depot explosion destroyed roughly forty hectares of the Roombeek "
        "district. The reconstruction is one of the more studied exercises in participatory Dutch "
        "urbanism, and the national external-safety regime that followed converted hazard into "
        "mapped risk contours — another continuous field laid over the city.",
    ),
    (
        "Half a catchment",
        "Every other Dutch city of this size draws labour and custom from a full circle. "
        "Enschede's circle is cut by a national border four kilometres from its centre. The land "
        "beyond is not empty — Gronau and the Münsterland are there — but it is separated by a "
        "labour-market and institutional membrane whose permeability, not the city's land supply, "
        "sets its accessible market.",
    ),
]

# --- data/constraints.ts ---------------------------------------------
CONSTRAINTS = pd.DataFrame(
    [
        {
            "label": "Nitrogen deposition",
            "shape": "field",
            "quantity": "Deposited reactive nitrogen on protected habitat (mol N/ha/yr)",
            "threshold": "The habitat's critical value — 400 for active raised bog — with no allowance for increases once it is exceeded",
            "effect": "Consent for any project whose calculated contribution does not round to zero at an over-loaded hexagon must be individually justified or offset.",
            "reduced_by": "Emission-free construction plant, lower induced car traffic per dwelling, fleet electrification, and reduced agricultural ammonia across the region.",
        },
        {
            "label": "Noise",
            "shape": "field",
            "quantity": "Day-evening-night sound level at the façade (dB Lden)",
            "threshold": "Statutory preference values, with a bounded discretion to exceed them",
            "effect": "Sets how close housing can sit to the ring roads, the rail corridor and the industrial estates — which is to say, it prices exactly the locations densification depends on.",
            "reduced_by": "Quieter road surfaces, lower speeds, façade construction, and mode shift. Every one of these is an engineering decision rather than a land-use one.",
        },
        {
            "label": "External safety",
            "shape": "field",
            "quantity": "Individual fatality probability from hazardous installations and transport (per year)",
            "threshold": "The 10⁻⁶ per year contour, with a separate account for group risk",
            "effect": "Withholds development capacity along transport routes and pipelines and around installations. Enschede's regime was reshaped by the 2000 fireworks depot explosion.",
            "reduced_by": "Relocating or removing the hazard, reducing the quantity stored, or rerouting the transport. The contour follows the source, not the map.",
        },
        {
            "label": "Groundwater protection",
            "shape": "field",
            "quantity": "Travel time of infiltrating water to the abstraction well (years)",
            "threshold": "Nested one-year, twenty-five-year and hundred-year capture zones",
            "effect": "Restricts activities and subsurface works above the aquifer that supplies the city. The permeable ridge sands that make abstraction viable also make the aquifer vulnerable.",
            "reduced_by": "Changing what is done at the surface. The zone geometry itself follows from the abstraction rate, so it moves when pumping does.",
        },
        {
            "label": "Radar and obstacle limitation",
            "shape": "field",
            "quantity": "Structure height intruding on a radar or approach surface (m)",
            "threshold": "Interference criteria assessed case by case",
            "effect": "Caps turbine tip height across large parts of Twente, which removes the technology with by far the lowest land intensity from consideration.",
            "reduced_by": "Radar mitigation and signal processing. This is a technical problem that is treated as a spatial one.",
        },
        {
            "label": "Nature Network and Natura 2000 boundaries",
            "shape": "polygon",
            "quantity": "Designated area (hectares)",
            "threshold": "Inside or outside",
            "effect": "Withdraws land from development and requires compensation where the network is impaired.",
            "reduced_by": "Nothing. This one really is a boundary, which is why it is the constraint planners find easiest to reason about and the one that explains least about why Enschede cannot build.",
        },
        {
            "label": "Settlement boundary and the sequencing test",
            "shape": "polygon",
            "quantity": "Designated urban area (hectares)",
            "threshold": "Inside or outside, with a demonstration of need for anything outside",
            "effect": "Directs growth into the existing urban fabric before greenfield land can be considered.",
            "reduced_by": "Nothing directly, though the demonstration of need is where the argument is actually had.",
        },
    ]
)

THESIS_CLAIM = (
    "Enschede's binding constraints are scalar fields, not polygons, and they are therefore "
    "reducible rather than merely negotiable."
)

COROLLARIES = [
    "A city that treats every constraint as a boundary can only relocate development. A city that "
    "recognises the fields can lower them, and lowering a field relaxes every location at once.",
    "The dwelling's dominant nitrogen term is the traffic it attracts over fifty years, not the "
    "plant that builds it over eighteen months. Location and parking provision are therefore "
    "nitrogen policy, whatever they are called in the plan.",
    "The renewable technology with the lowest land intensity is the one the field constraints "
    "exclude, so the search-area process selects for land consumption. The scarce resource is "
    "being spent to avoid the reducible one.",
    "Where a field constraint has no de minimis threshold, compliance cost is dominated by "
    "modelling and legal exposure rather than by abatement, which favours developers large enough "
    "to carry both.",
]

# --- data/nitrogen.ts ------------------------------------------------
HABITATS = pd.DataFrame(
    [
        {"code": "H7110A", "label": "Active raised bog", "kdw": 400},
        {"code": "H7120", "label": "Regenerating raised bog", "kdw": 500},
        {"code": "H3160", "label": "Acid fens", "kdw": 714},
        {"code": "H4030", "label": "Dry heath", "kdw": 1071},
        {"code": "H4010A", "label": "Wet heath", "kdw": 1214},
        {"code": "H91E0C", "label": "Brook-accompanying alluvial forest", "kdw": 1857},
    ]
)

BACKGROUND_DEPOSITION = 1600  # mol N/ha/yr, regional

CONSTRUCTION_NOX_KG = 10.0  # one-off, per dwelling
CAR_KM_PER_DWELLING_YEAR = 12_000
FLEET_NOX_G_PER_KM = 0.2
DWELLING_LIFETIME_YEARS = 50
NOX_MOLAR_MASS = 46.0  # g/mol, expressed as NO2 by convention

CHRONOLOGY = [
    (
        "May 2019",
        "The programmatic approach to nitrogen is annulled.",
        "The mechanism that had allowed development to draw against future emission reductions "
        "disappears. Consent for projects affecting over-loaded habitats requires an individual "
        "demonstration of no significant effect.",
    ),
    (
        "July 2018",
        "The obligation to connect new dwellings to the gas network is removed.",
        "New Dutch housing has essentially no combustion emissions in use. The dwelling's own "
        "nitrogen term collapses to construction and to the traffic it attracts.",
    ),
    (
        "November 2022",
        "The construction-phase exemption is annulled.",
        "Machinery emissions during construction re-enter the assessment. The crane is back in the "
        "calculation, though it was never the larger term.",
    ),
    (
        "2023 onward",
        "Clean and emission-free construction is written into procurement.",
        "Electrified plant removes the construction term at the point where public bodies specify "
        "it, which is precisely where affordable housing is procured.",
    ),
]

LEVERS = [
    {
        "label": "Edge site, standard parking norm, diesel plant",
        "car_scale": 1.0,
        "electric_plant": False,
        "detail": "The default greenfield product. Car use is set by the location before a single design decision is taken.",
    },
    {
        "label": "Same site, emission-free construction plant",
        "car_scale": 1.0,
        "electric_plant": True,
        "detail": "Removes the construction term outright. It is the intervention with the clearest public profile and the smallest lifetime effect.",
    },
    {
        "label": "Corridor site, reduced parking norm, diesel plant",
        "car_scale": 0.5,
        "electric_plant": False,
        "detail": "A dwelling within reach of the regional cycle route and the rail station, with parking provision cut from roughly 1.2 to 0.4 spaces. Halving car-kilometres is a conservative reading of the observed elasticity.",
    },
    {
        "label": "Corridor site, reduced parking norm, emission-free plant",
        "car_scale": 0.5,
        "electric_plant": True,
        "detail": "The two levers together, which is how they are actually available.",
    },
    {
        "label": "Corridor site, car-free covenant, emission-free plant",
        "car_scale": 0.2,
        "electric_plant": True,
        "detail": "Achievable only where the alternative genuinely reaches the destinations residents need, which in Enschede means the ridge crossing has to work on a bicycle.",
    },
]

# --- data/mobility.ts ------------------------------------------------
MODES = pd.DataFrame(
    [
        {"id": "walk", "label": "Walking", "kwh_per_vkm": 0.049, "occupancy": 1, "m2": 1.2,
         "family": "human",
         "basis": "Net metabolic cost above rest, ~0.75 kcal per kg per km at 70 kg."},
        {"id": "bike", "label": "Bicycle", "kwh_per_vkm": 0.029, "occupancy": 1, "m2": 6,
         "family": "human",
         "basis": "About 25 kcal per km at 18 km/h, i.e. ~75 W mechanical at ~24% muscular efficiency."},
        {"id": "ebike", "label": "Electric bicycle", "kwh_per_vkm": 0.011, "occupancy": 1, "m2": 7,
         "family": "assisted",
         "basis": "8–15 Wh per km at the battery in mixed use; 11 Wh/km as the central case."},
        {"id": "escooter", "label": "Shared e-scooter", "kwh_per_vkm": 0.020, "occupancy": 1, "m2": 4,
         "family": "assisted",
         "basis": "20 Wh/km at the battery in service. Operational energy only."},
        {"id": "train", "label": "Regional train", "kwh_per_vkm": 12.0, "occupancy": 120, "m2": 1.5,
         "family": "collective",
         "basis": "~12 kWh per train-km at the pantograph, averaged over the day at 120 passengers."},
        {"id": "bus", "label": "Urban bus, diesel", "kwh_per_vkm": 4.0, "occupancy": 12, "m2": 1.8,
         "family": "collective",
         "basis": "40 litres per 100 km at 10 kWh per litre, at an all-day average of 12 passengers."},
        {"id": "bev", "label": "Battery car", "kwh_per_vkm": 0.19, "occupancy": 1.35, "m2": 60,
         "family": "private",
         "basis": "190 Wh per km at the battery, at the Dutch average car occupancy of about 1.35."},
        {"id": "ice", "label": "Petrol car", "kwh_per_vkm": 0.68, "occupancy": 1.35, "m2": 60,
         "family": "private",
         "basis": "7.0 litres per 100 km at 9.7 kWh per litre, at the same 1.35 occupancy."},
    ]
)
MODES["pkm_per_kwh"] = MODES["occupancy"] / MODES["kwh_per_vkm"]
MODES["kwh_per_pkm"] = MODES["kwh_per_vkm"] / MODES["occupancy"]

UPSTREAM = [
    ("Food energy", 6.0,
     "Industrial food systems spend roughly 6 units of fossil energy per unit of food energy "
     "delivered to the plate, with an enormous spread by diet."),
    ("Electricity at the socket", 1.08,
     "Distribution and charging losses between the meter and the battery."),
    ("Liquid fuel to the pump", 1.2,
     "Extraction, refining and distribution before the fuel reaches the tank."),
]

CLIMB_SYSTEM_MASS_KG = 90
GRAVITY = 9.81
HUMAN_EFFICIENCY = 0.24
MOTOR_EFFICIENCY = 0.80
TYPICAL_CLIMB_M = 30
EBIKE_WH_PER_KM = 11

RIDGE_TRANSECT = pd.DataFrame(
    {
        "km": list(range(15)),
        "m": [30, 33, 37, 42, 46, 50, 47, 51, 56, 52, 46, 41, 37, 33, 31],
    }
)

# --- data/border.ts --------------------------------------------------
DENSITY_DUTCH = 500  # inhabitants per km²
DENSITY_GERMAN = 220

PERMEABILITY_SCENARIOS = [
    ("Closed frontier", 0.0, "The counterfactual. Included to show what the geometry alone costs."),
    ("Observed today", 0.15,
     "Cross-border commuting remains a small share of either labour market despite forty "
     "kilometres of shared frontier and an hourly rail link."),
    ("Working cross-border labour market", 0.5,
     "Qualifications recognised in both directions, a single ticketing and tariff regime, and "
     "social insurance portability. Nothing here requires new construction."),
    ("No institutional friction", 1.0, "The upper bound. A border that costs a commuter nothing but distance."),
]

# --- data/energy.ts --------------------------------------------------
RES_TARGET_TWH = 1.5

TECHNOLOGIES = pd.DataFrame(
    [
        {
            "id": "wind", "label": "Onshore wind", "gwh_per_unit": 16.8, "unit": "turbine",
            "gross_km2": 0.36, "exclusive_km2": 0.003, "constraint_shape": "field",
            "basis": "5.6 MW machine at roughly 3,000 full-load hours inland; array spacing of about five rotor diameters downwind by three across, at a 155 m rotor; foundation and hardstanding of about 0.3 ha.",
            "binding": "Noise and shadow-flicker contours, military and civil radar sightlines, and habitat disturbance. None of these is a land requirement.",
        },
        {
            "id": "solar-field", "label": "Ground-mounted solar", "gwh_per_unit": 0.665, "unit": "hectare",
            "gross_km2": 0.01, "exclusive_km2": 0.01, "constraint_shape": "polygon",
            "basis": "About 950 kWh per installed kWp per year in the eastern Netherlands at a ground-mount density near 0.7 MWp per hectare.",
            "binding": "Land itself, plus a national preference order that puts agricultural land last. The constraint is a boundary that can be redrawn.",
        },
        {
            "id": "solar-roof", "label": "Rooftop solar", "gwh_per_unit": 0.665, "unit": "hectare of roof",
            "gross_km2": 0.0, "exclusive_km2": 0.0, "constraint_shape": "none",
            "basis": "Same yield per hectare of array, mounted on structure that already exists.",
            "binding": "Grid capacity at the low-voltage transformer, roof structural capacity, and split incentives between owner and occupier. No land at all.",
        },
    ]
)

ROOF_M2_PER_DWELLING = 25
ROOF_KWP_PER_M2 = 0.2
ROOF_YIELD_KWH_PER_KWP = 950
ROOF_NONRESIDENTIAL_MULTIPLIER = 1.6

# --- data/access.ts --------------------------------------------------
STATIONS = pd.DataFrame(
    [
        {"id": "centraal", "label": "Enschede Centraal", "x": 0.0, "y": 0.0,
         "note": "Terminus for services from the west and the interchange to the German regional service. Sits on the density peak."},
        {"id": "kennispark", "label": "Enschede Kennispark", "x": -2.6, "y": 1.2,
         "note": "Serves the university campus and the science park on the Hengelo line."},
        {"id": "eschmarke", "label": "Enschede De Eschmarke", "x": 2.8, "y": 0.4,
         "note": "Eastern suburban stop on the line toward the border."},
    ]
)

ACCESS_MODES = [
    {"id": "walk", "label": "Walking", "radius_km": 0.8, "circuity": 1.30, "minutes": 10,
     "note": "The conventional planning buffer, and the one that produces the familiar low coverage numbers."},
    {"id": "bike", "label": "Bicycle", "radius_km": 3.0, "circuity": 1.18, "minutes": 10,
     "note": "The same ten minutes at cycling speed. Dutch networks are unusually direct, so little of the radius is lost to circuity."},
    {"id": "ebike", "label": "Electric bicycle", "radius_km": 5.0, "circuity": 1.18, "minutes": 12,
     "note": "Assistance buys both speed and, on the ridge, indifference to gradient — which is what converts a nominal radius into a real one here."},
]

DENSITY_GRADIENT_B = 0.35  # per km

# Cape Town, restated as published and not independently reproduced.
CT_BUFFER_KM2 = 183
CT_EDGE_KM2 = 895


# =====================================================================
# Derived quantities
# =====================================================================

def annual_use_nox_kg() -> float:
    return CAR_KM_PER_DWELLING_YEAR * FLEET_NOX_G_PER_KM / 1000


def lifetime_nox_kg(car_scale: float = 1.0, electric_plant: bool = False) -> float:
    construction = 0.0 if electric_plant else CONSTRUCTION_NOX_KG
    return construction + annual_use_nox_kg() * car_scale * DWELLING_LIFETIME_YEARS


def kg_nox_to_mol_n(kg: float) -> float:
    return kg * 1000 / NOX_MOLAR_MASS


def total_ascent(profile: pd.DataFrame) -> int:
    diffs = profile["m"].diff().dropna()
    return int(diffs[diffs > 0].sum())


def climb_work_wh(metres: float) -> float:
    return CLIMB_SYSTEM_MASS_KG * GRAVITY * metres / 3600


def segment_area(r: float, d: float) -> float:
    """Area of the circular segment beyond a chord at perpendicular distance d."""
    if d >= r:
        return 0.0
    if d <= -r:
        return math.pi * r * r
    return r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)


def disc_area(r: float) -> float:
    return math.pi * r * r


def catchment_ratio(r: float, permeability: float, d: float = BORDER_DISTANCE_KM) -> float:
    beyond = segment_area(r, d)
    within = disc_area(r) - beyond
    return (within + permeability * beyond) / disc_area(r)


def accessible_population(r: float, permeability: float) -> float:
    beyond = segment_area(r, BORDER_DISTANCE_KM)
    within = disc_area(r) - beyond
    return within * DENSITY_DUTCH + permeability * beyond * DENSITY_GERMAN


def units_for_target(row: pd.Series, twh: float = RES_TARGET_TWH) -> float:
    return twh * 1000 / row["gwh_per_unit"]


def rooftop_potential_twh() -> float:
    kwp = DWELLINGS * ROOF_M2_PER_DWELLING * ROOF_KWP_PER_M2
    residential = kwp * ROOF_YIELD_KWH_PER_KWP / 1e9
    return residential * ROOF_NONRESIDENTIAL_MULTIPLIER


def shed_area_km2(r: float) -> float:
    return math.pi * r * r


CITY_RADIUS_KM = math.sqrt(BUILT_UP_KM2 / math.pi)


@st.cache_data
def access_grid(spacing: float = 0.05) -> pd.DataFrame:
    """Sample points inside the stylised built-up disc, with a population weight.

    Coverage of a union of overlapping discs has no closed form worth writing,
    so it is sampled. Cached because the grid never changes; only the radius
    scanned against it does.
    """
    R = CITY_RADIUS_KM
    axis = np.arange(-R, R + spacing, spacing)
    xx, yy = np.meshgrid(axis, axis)
    r = np.hypot(xx, yy)
    inside = r <= R
    x, y, r = xx[inside], yy[inside], r[inside]

    # D(r) = D0 exp(-b r), with D0 solved so the gradient integrates to the
    # actual population. Only the steepness b is a free choice.
    b = DENSITY_GRADIENT_B
    integral = 2 * math.pi * (1 - math.exp(-b * R) * (1 + b * R)) / (b * b)
    d0 = POPULATION / integral
    weight = d0 * np.exp(-b * r) * spacing * spacing

    return pd.DataFrame({"x": x, "y": y, "r": r, "w": weight})


def coverage(reach_km: float, spacing: float = 0.05) -> dict:
    """Share of land and of residents within `reach_km` of any station."""
    g = access_grid(spacing)
    covered = np.zeros(len(g), dtype=bool)
    for _, s in STATIONS.iterrows():
        covered |= (g["x"] - s["x"]) ** 2 + (g["y"] - s["y"]) ** 2 <= reach_km**2
    land_km2 = covered.sum() * spacing * spacing
    people = g.loc[covered, "w"].sum()
    return {
        "land": land_km2 / BUILT_UP_KM2,
        "population": people / g["w"].sum(),
        "land_km2": land_km2,
        "people": people,
    }


def effective_radius(mode: dict) -> float:
    return mode["radius_km"] / mode["circuity"]


CT_STATION_EQUIVALENTS = CT_BUFFER_KM2 / shed_area_km2(0.8)


# =====================================================================
# Element identity
# =====================================================================
#
# Every st.altair_chart call carries an explicit `key`. Streamlit reconciles
# elements by their position in the tree, so a chart sitting at the same
# position on two different sections gets handed the previous section's
# rendered spec until it re-renders — which shows the reader the wrong figure
# under the right caption. A stable key gives each figure its own identity.


# =====================================================================
# Pages
# =====================================================================

def page_constraints() -> None:
    header("The seven things limiting building",
           "Planning software stores shapes. So limits get stored as shapes, and everyone "
           "starts thinking a limit is a place. Most of the things actually stopping "
           "building in Enschede are not places. They are measurements — nitrogen, noise, "
           "risk, travel time — that exist everywhere and only look like a shape because "
           "someone drew a line where the number crosses a threshold.")

    figure("Measurements fade with distance; lines do not",
           "The same five limits, before and after cutting their cause by thirty per cent.",
           "Where the two lines separate, the limit can be reduced. In the last panel they "
           "sit on top of each other.")
    st.altair_chart(chart_constraint_shapes(), width="stretch", key="shapes_constraints")
    provenance("derived", "RIVM, Provincie Overijssel")

    st.divider()
    for shape, heading, blurb in [
        ("field", "The five that are fields",
         "Each of these is a quantity with a source, a decay, and a threshold. Each has a lever "
         "that moves the whole surface rather than one location on it."),
        ("polygon", "The two that really are boundaries",
         "These two are genuine polygons: inside or outside, with nothing underneath to reduce. "
         "They are also the two that dominate public argument about growth in the city."),
    ]:
        st.subheader(heading)
        st.caption(blurb)
        for _, c in CONSTRAINTS[CONSTRAINTS["shape"] == shape].iterrows():
            with st.expander(f"{c['label']}  ·  {c['shape']}"):
                st.markdown(f"**Quantity** — {c['quantity']}")
                st.markdown(f"**Threshold** — {c['threshold']}")
                st.markdown(f"**Effect on development** — {c['effect']}")
                st.markdown(
                    f"**{'Reduced by' if shape == 'field' else 'Reducible?'}** — {c['reduced_by']}")
        st.write("")

    st.divider()
    st.subheader("The consequence")
    for i, c in enumerate(COROLLARIES, 1):
        st.markdown(f"`{i:02d}`  {c}")


def page_nitrogen() -> None:
    bog = HABITATS.iloc[0]
    baseline = lifetime_nox_kg()
    construction_share = CONSTRUCTION_NOX_KG / baseline
    location_only = 1 - lifetime_nox_kg(0.5, False) / baseline
    best_case = lifetime_nox_kg(0.2, True)

    header("Nitrogen: why the allowance is zero",
           "Since a 2019 court ruling, a project that adds nitrogen to a nature area already "
           "over its limit gets no allowance at all. Not a small one — none. So what limits "
           "building in Enschede is not hectares of land, it is a chemical measurement. And "
           "most of that measurement comes from something nobody files under environmental "
           "policy: how much driving each new home causes.")

    stats([
        ("What a raised bog can take", f"{bog['kdw']:,}",
         "Units of nitrogen per hectare per year — the lowest limit in the country, at a bog on Enschede's own edge."),
        ("What the region actually delivers", f"{BACKGROUND_DEPOSITION:,}",
         "Same units. The bog is four times over its limit before anyone proposes anything."),
        ("Allowance for a new project", "0.00",
         "None at all. A project has to round to zero on the official calculator to be allowed."),
        ("Share that comes from building it", f"{construction_share * 100:.0f}%",
         "All the rest is the driving the home causes over the next fifty years."),
    ])

    st.divider()
    figure("Five of six habitats get more nitrogen than they can take",
           "Each bar is how much nitrogen a habitat can tolerate. The vertical line is how "
           "much the region actually delivers.",
           "Any bar shorter than the line is a habitat already over its limit. The orange "
           "bar is raised bog — over by a factor of four, and it sits on Enschede's own "
           "edge.")
    st.altair_chart(chart_critical_values(), width="stretch", key="critical_values")
    values_table(HABITATS.assign(**{
        "load ÷ critical value": (BACKGROUND_DEPOSITION / HABITATS["kdw"]).round(1)
    }))
    note("Once a habitat is over its critical value, the legal question stops being how much a "
         "project adds and becomes whether it adds anything at all. That is a categorical test, "
         "and categorical tests do not respond to being slightly better.")
    provenance("official", "RIVM, Ministerie van LVVN")

    st.divider()
    st.subheader("How the rule got this shape")
    for date, event, consequence in CHRONOLOGY:
        st.markdown(f"**{date}** — {event}")
        st.caption(consequence)
    note("The 2018 change matters more than it looks. A new Dutch dwelling has no combustion in "
         "use, so its heating contributes nothing. That leaves two terms in the account — the "
         "plant that builds it and the traffic it attracts — and it makes the second one almost "
         "the whole of the answer.")

    st.divider()
    figure("Most of a home's nitrogen comes from driving, not building",
           "Nitrogen from one home over fifty years. Orange is the machinery that builds it; "
           "blue is the traffic it causes afterwards.",
           "The blue is about twelve times the orange. Where you put the home, and how much "
           "parking you give it, matters far more than how cleanly you build it.")
    st.altair_chart(chart_dwelling_nitrogen(), width="stretch", key="dwelling_nitrogen")
    values_table(dwelling_nitrogen_table())
    note("Emission side only: no dispersion is modelled here and none should be read into it. "
         "Turning emissions into deposition at a named receptor is what the official calculator "
         "does, and an imitation of it would be worse than nothing. What survives any dispersion "
         "assumption is the ratio between the two segments, because both disperse from broadly "
         "the same place.")
    provenance("derived", "CBS, RIVM")

    st.divider()
    st.subheader("What this means")
    st.markdown(
        f"Electrifying the construction plant is the intervention with the clearest public profile "
        f"and it removes {construction_share * 100:.0f} per cent of the lifetime total. Putting "
        f"the same dwelling where its residents drive half as much removes "
        f"{location_only * 100:.0f} per cent — nearly {location_only / construction_share:.0f} "
        f"times as much — and the two together take a dwelling from {baseline:.0f} kg to "
        f"{best_case:.0f} kg, a reduction of {(1 - best_case / baseline) * 100:.0f} per cent, with "
        f"no change to the building itself."
    )
    st.markdown(
        "The conclusion is not that nitrogen policy should be relaxed. It is that in Enschede the "
        "nitrogen decision and the parking decision are the same decision, and only one of them is "
        "currently made by people who think they are working on nitrogen. A parking norm is an "
        "emissions instrument. So is the choice between an edge site and a site on the regional "
        "cycle route."
    )
    st.markdown(
        "There is a second-order effect worth naming. Where a threshold has no lower bound, "
        "compliance cost is dominated by modelling and by legal exposure rather than by abatement, "
        "because the marginal kilogram avoided does not change the answer to a categorical "
        "question. That structure favours applicants large enough to carry a specialist and a "
        "litigation reserve — and the housing that most needs to be built is precisely the housing "
        "whose promoters can least carry that overhead."
    )


def page_mobility() -> None:
    m = MODES.set_index("id")
    ratio = m.loc["ebike", "pkm_per_kwh"] / m.loc["ice", "pkm_per_kwh"]
    bev_ratio = m.loc["ebike", "pkm_per_kwh"] / m.loc["bev", "pkm_per_kwh"]
    ascent = total_ascent(RIDGE_TRANSECT)
    metabolic = climb_work_wh(TYPICAL_CLIMB_M) / HUMAN_EFFICIENCY
    battery = climb_work_wh(TYPICAL_CLIMB_M) / MOTOR_EFFICIENCY

    header("How much energy each way of travelling uses",
           "Traffic is normally counted in vehicles per hour. That measures what is being "
           "managed, not what is being used up. Measure instead the energy each way of "
           "travelling spends moving one person one kilometre, and the options stop being a "
           "matter of taste: the best is about fifty times better than the worst.")

    stats([
        ("Electric bicycle", f"{m.loc['ebike', 'pkm_per_kwh']:.0f}",
         "p-km per kWh, at 11 Wh per kilometre from the battery."),
        ("Petrol car", f"{m.loc['ice', 'pkm_per_kwh']:.1f}",
         "p-km per kWh, at 7 l/100 km and 1.35 occupancy."),
        ("Ratio between them", f"{ratio:.0f}×",
         "A different order of magnitude, available today, at a fraction of the capital cost."),
        ("Against a battery car", f"{bev_ratio:.0f}×",
         "Electrifying the car closes part of the gap, not the part from moving a tonne and a half."),
    ])

    st.divider()
    figure("Energy used per person per kilometre",
           "How far one kilowatt-hour moves one person. Longer is better. The scale is "
           "logarithmic — each gridline is a multiple, not an addition.",
           "The top of this list is about fifty times better than the bottom. Not a tuning "
           "difference — a different order of magnitude, available today.")
    st.altair_chart(chart_energy_ladder(), width="stretch", key="energy_ladder")
    values_table(
        MODES.sort_values("pkm_per_kwh", ascending=False)[
            ["label", "pkm_per_kwh", "kwh_per_pkm", "occupancy"]
        ].round(3)
    )
    note("Every dot is labelled, which is normally a fault. Here the axis is logarithmic and a "
         "reader cannot recover a value from it, so the labels are carrying information the axis "
         "cannot.")
    provenance("engineering", "Textbook values, CBS")

    st.divider()
    st.subheader("What the ladder deliberately leaves out")
    note("Upstream chains are held apart from the ladder rather than folded into it. Folding them "
         "in is the commonest way to make an energy comparison unfalsifiable: once two multipliers "
         "are inside one number, a reader can no longer tell which of them moved.")
    for label, factor, blurb in UPSTREAM:
        st.markdown(f"**{label}** ×{factor}")
        st.caption(blurb)
    note("Applying the food multiplier is the honest stress test of the whole argument, and it "
         "costs the unassisted bicycle its position: at a factor of six, cycling falls below the "
         "electric bicycle rather than sitting above it. Two caveats belong with that result. The "
         "multiplier assumes food intake rises in proportion to effort, which for most riders it "
         "does not. And the assisted rider is still pedalling, so a like-for-like accounting would "
         "add part of a metabolic term back. Both corrections narrow the gap; neither reverses it.")

    st.divider()
    figure("The modes that waste energy also waste space",
           "Energy used across the bottom, road space used up the side. Both scales "
           "logarithmic.",
           "The dots fall along a diagonal. Energy and space are not two problems to trade "
           "off against each other — they are one problem measured twice.")
    st.altair_chart(chart_energy_versus_space(), width="stretch", key="energy_space")
    note("The modes fall along a diagonal. In a city with a settlement boundary on one side, a "
         "nature network on another and a national border on a third, the mode that wastes energy "
         "is the same mode that wastes the land there is none of. These are not two constraints to "
         "be traded against one another; they are one constraint measured twice.")
    provenance("engineering", "Textbook values")

    st.divider()
    st.subheader("The ridge")
    st.markdown(
        f"Enschede sits on a Saalian ice-pushed ridge, which makes it one of the few Dutch cities "
        f"where a bicycle trip contains real climb. A west-to-east traverse of the built-up area "
        f"accumulates about {ascent} metres of ascent. In a country whose cycling policy is written "
        f"for flat ground, this is the local variable that policy does not account for — and it is "
        f"the specific thing electrical assistance removes."
    )
    figure("The hill across Enschede, west to east",
           "Height above sea level along a line across the city.",
           "About thirty metres of climb. Trivial in a car, and the reason a three-kilometre "
           "cycle trip to the station turns into a car trip instead.")
    st.altair_chart(chart_ridge(), width="stretch", key="ridge")

    stats([
        ("Total ascent, west to east", f"{ascent} m", "The climb a rider actually accumulates."),
        ("Rider's cost for a 30 m climb", f"{metabolic:.0f} Wh",
         f"Food energy at {HUMAN_EFFICIENCY:.0%} muscular efficiency and a {CLIMB_SYSTEM_MASS_KG} kg system."),
        ("Motor's cost for the same climb", f"{battery:.1f} Wh",
         f"From the battery, at {MOTOR_EFFICIENCY:.0%} drivetrain efficiency."),
        ("Expressed as e-bike range", f"{battery / EBIKE_WH_PER_KM:.1f} km",
         "Of level riding at 11 Wh per km — the ridge costs less than a kilometre."),
    ])
    provenance("official", "AHN")
    note("The gradient a person experiences as a reason to take the car is, to the motor, a "
         "rounding error. This is why the assisted bicycle is a different proposition in Enschede "
         "than in the west of the country: elsewhere it buys speed on ground that was already "
         "ridable, and here it removes a barrier that exists.")


def page_access() -> None:
    walk, bike, ebike = ACCESS_MODES
    walk_cov = coverage(effective_radius(walk))
    bike_cov = coverage(effective_radius(bike))

    header("How many people can reach a station",
           "The usual measure is the share of an area within an 800 metre walk of a station. "
           "It is easy to work out, which is most of why it gets used, and it hides two "
           "assumptions. First, that 800 metres is a fact about the place rather than a "
           "choice about how people get there. Second, that land is the right thing to "
           "count. Both are wrong.")

    stats([
        ("Reach on foot", f"{shed_area_km2(walk['radius_km']):.1f} km²",
         "Area one station covers at an 800 m walk — the usual planning assumption."),
        ("Reach by bicycle", f"{shed_area_km2(bike['radius_km']):.1f} km²",
         f"The same ten minutes on a bike covers {shed_area_km2(bike['radius_km']) / shed_area_km2(walk['radius_km']):.0f} times "
         "the area, because area grows with the square of the distance."),
        ("Reach by e-bike", f"{shed_area_km2(ebike['radius_km']):.0f} km²",
         f"{shed_area_km2(ebike['radius_km']) / shed_area_km2(walk['radius_km']):.0f} times the walking figure, from twelve minutes of pedalling."),
        ("Stations in Enschede", f"{len(STATIONS)}",
         "Poor coverage on foot — and it turns out that is not the real problem."),
    ])

    st.divider()
    st.subheader("Why the distance assumption matters so much")
    st.markdown(
        "An access shed is a disc, and the area of a disc goes as the square of its radius. "
        "Tripling the reach does not triple the catchment, it multiplies it by nine. This is "
        "arithmetic rather than a finding, but it is arithmetic that a coverage percentage hides "
        "completely: the percentage is reported as though it described the rail network, when most "
        "of what it describes is the decision to measure at 800 metres."
    )

    st.divider()
    figure("Enschede's three stations on the map",
           "The real stations, with a real catchment circle around each one. Change the travel "
           "mode to change the radius.",
           "The circles are drawn in metres on the ground. Switch from walking to cycling and "
           "watch them swallow most of the city — the stations have not moved and no track has "
           "been laid.")
    map_mode = st.radio("Travel mode to the station",
                        [m["label"] for m in ACCESS_MODES], horizontal=True, key="osm_mode")
    map_radius = next(m["radius_km"] for m in ACCESS_MODES if m["label"] == map_mode) * 1000
    st.pydeck_chart(geo.station_catchment_map(map_radius), height=470)
    st.markdown(
        geo.legend_html([("Station", SERIES[1]), ("Area within reach", SERIES[0])]),
        unsafe_allow_html=True)
    st.caption(
        f"{map_mode} radius drawn at {map_radius / 1000:.1f} km. {geo.OSM_ATTRIBUTION} "
        "Station positions are hand-placed to about ten metres."
    )

    st.divider()
    figure("How much of Enschede each station reaches",
           "Grey shading is where people live — darker is denser. Blue is what is within "
           "reach of a station at the radius you pick.",
           "Switch between walking, bicycle and e-bike in the controls. The stations do not "
           "move and no track is built; only the assumed radius changes, and the blue area "
           "changes enormously.")

    c1, c2 = st.columns([1, 1])
    with c1:
        preset = st.radio("Access mode", [m["label"] for m in ACCESS_MODES] + ["Custom"],
                          horizontal=False, key="access_preset")
        if preset == "Custom":
            radius = st.slider("Access radius, km", 0.4, 6.0, 1.5, 0.1)
            circuity = 1.25
        else:
            mode = next(m for m in ACCESS_MODES if m["label"] == preset)
            radius, circuity = mode["radius_km"], mode["circuity"]
            st.caption(mode["note"])
        take_circuity = st.checkbox("Take out network circuity", value=True)

    reach = radius / circuity if take_circuity else radius
    cov = coverage(reach)

    with c2:
        st.altair_chart(chart_access_sheds(reach), width="content", key="access_sheds")

    stats([
        ("Built-up land covered", f"{cov['land'] * 100:.0f}%",
         f"{cov['land_km2']:.1f} km² of {BUILT_UP_KM2} km²."),
        ("Residents covered", f"{cov['population'] * 100:.0f}%",
         f"About {cov['people'] / 1000:.0f} thousand people."),
        ("Shed per station", f"{shed_area_km2(reach):.1f} km²",
         f"π r² at a reach of {reach:.2f} km."),
        ("People per hectare covered",
         f"{cov['people'] / cov['land_km2'] / 100:.1f}" if cov["land_km2"] else "—",
         "The density of what the network actually reaches."),
    ])
    note(f"The built-up area is stylised as a disc of equal area — {BUILT_UP_KM2} km², radius "
         f"{CITY_RADIUS_KM:.2f} km — centred on the city centre. Enschede's real footprint reaches "
         f"further south-west than north, so a true boundary would move the coverage fractions by "
         f"a few points. It would not move the ratio between the walking and cycling cases, which "
         f"is set by r² and not by the shape of the edge.")
    provenance("derived", "ProRail/NS, CBS, standard urban-economics form")

    st.divider()
    st.subheader("Circuity, or why a buffer flatters itself")
    st.markdown(
        "A circle drawn around a station assumes streets run straight at it. They do not. The "
        "ratio of network distance to straight-line distance is typically between 1.2 and 1.4, and "
        "because the shed goes as r², the real catchment is the circle divided by the square of "
        "that factor — somewhere between 51 and 69 per cent of what the buffer claims. The factor "
        "is not a constant of nature either: superblock layouts, severance by motorways and rail "
        "reserves, and cul-de-sac estates all push it up."
    )
    st.dataframe(
        pd.DataFrame([{
            "Mode": m["label"],
            "Nominal radius, km": m["radius_km"],
            "Circuity": m["circuity"],
            "Real reach, km": round(effective_radius(m), 2),
            "Shed as % of the circle": f"{100 / m['circuity'] ** 2:.0f}%",
        } for m in ACCESS_MODES]),
        hide_index=True, width="stretch",
    )

    st.divider()
    figure("Counting land instead of people",
           "The same coverage counted two ways: share of residents in orange, share of land "
           "in blue, as the radius grows.",
           "The orange line sits above the blue one. Counting land undercounts access, "
           "because the central station stands where most people are and the hectares at the "
           "edge are nearly empty.")
    st.altair_chart(chart_coverage_curve(), width="stretch", key="coverage_curve")
    values_table(coverage_table())
    note(f"The gap behaves in two ways worth separating. In proportional terms it is worst at the "
         f"short end: at a real walk the land metric reports {walk_cov['land'] * 100:.1f} per cent "
         f"where {walk_cov['population'] * 100:.1f} per cent of people are covered, understating "
         f"access by about a fifth. In percentage points it is widest in the middle of the range. "
         f"Either way it runs the same direction, because the central station stands on the "
         f"density peak while hectares out at the edge are nearly empty.")
    provenance("derived", "Standard urban-economics form, CBS, ProRail/NS")

    st.divider()
    st.subheader("What Enschede's three stations actually reach")
    st.markdown(
        f"Measured the conventional way, Enschede's rail access is poor: "
        f"{walk_cov['land'] * 100:.0f} per cent of built-up land within a real walk of a station. "
        f"Measured in residents it is {walk_cov['population'] * 100:.0f} per cent. Shift the access "
        f"mode to the bicycle and the same three stations reach "
        f"{bike_cov['population'] * 100:.0f} per cent of residents. Nothing was built. The trains "
        f"did not change, the timetable did not change, and the stations stayed where they were. "
        f"What changed was the assumed radius, and the radius was never a property of the rail "
        f"network."
    )
    st.markdown(
        "This is the specific reason the mobility section matters to this one. The bicycle only "
        "delivers that radius if the ridge is not in the way, and thirty metres of climb is "
        "precisely the thing that turns a three-kilometre feeder trip into a car trip. Assistance "
        "removes it for about nine watt-hours."
    )

    st.divider()
    figure("Cape Town's stations, if people cycled instead of walked",
           "Cape Town's existing stations under three assumptions about how far people will "
           "travel to reach one. The orange line is the whole buildable area.",
           "At walking distance the stations cover a fifth of the city. At cycling distance "
           "the same stations cover nearly three times it. This is a sum not a union, so the "
           "real figure is lower — but Cape Town is clearly not short of stations.")
    st.altair_chart(chart_cape_town(), width="stretch", key="cape_town")
    values_table(cape_town_table())
    note(f"The published figure is that {CT_BUFFER_KM2} km² of 800 m buffers cover "
         f"{CT_BUFFER_KM2 / CT_EDGE_KM2 * 100:.0f} per cent of the {CT_EDGE_KM2} km² development "
         f"edge. Restated as given and not independently reproduced. Divide by one 800 m disc and "
         f"the network is worth about {CT_STATION_EQUIVALENTS:.0f} non-overlapping "
         f"station-equivalents; at a cycling radius their sheds sum to "
         f"{CT_STATION_EQUIVALENTS * shed_area_km2(3.0) / CT_EDGE_KM2:.1f} times the entire edge. "
         f"Summed, not unioned, and the distinction is load-bearing — overlap means the real union "
         f"is smaller. What the comparison establishes is narrower and still worth having: a "
         f"network whose sheds sum to nearly three times the area to be covered is not short of "
         f"stations, it is short of a way to reach them.")
    provenance("estimate", "Third-party analysis, restated as published")

    st.divider()
    st.subheader("Where this reading has to stop")
    st.markdown(
        "Summed sheds are not a union, so the metropolitan figures are an upper bound. The density "
        "gradient is a modelled exponential rather than a measured surface, solved so it integrates "
        "to the actual population — it will misplace people at the neighbourhood scale even where "
        "the aggregate is right. And a shed is not a service: coverage says nothing about whether "
        "trains run."
    )
    st.markdown(
        "That last one deserves more than a caveat. Metrorail ridership on the worst corridors fell "
        "by roughly an order of magnitude over the past decade through vandalism, cable theft and "
        "service withdrawal. Twenty per cent coverage is moot when the trains do not come. A "
        "reliability constraint was measured as a spatial one, and the instrument returned a "
        "spatial answer — the same failure this platform documents in nitrogen, in noise and in "
        "renewable siting. The tool draws polygons, so the problem arrives shaped like a polygon."
    )


def page_border() -> None:
    header("The border cuts the city's market",
           "A hospital, a university, a station or a heat network pays for itself out of the "
           "people who live within travelling distance. That area is normally a circle. "
           "Enschede's circle is cut four kilometres from the centre by the German border. "
           "The land on the other side is not empty — Gronau is right there — but it is a "
           "different country, which is a different problem with a different fix.")

    stats([
        ("Lost within 20 km", f"{(1 - catchment_ratio(20, 0)) * 100:.0f}%",
         "Share of the circle that falls on the German side. Pure geometry."),
        ("Lost within 30 km", f"{(1 - catchment_ratio(30, 0)) * 100:.0f}%",
         "The further out you look, the more of the circle is on the wrong side of the line."),
        ("What Enschede actually has", f"{catchment_ratio(30, 0.15) * 100:.0f}%",
         "Of what a city the same size inland would have, at 30 km, at today's border openness."),
        ("Gained by opening the border",
         f"{(accessible_population(30, 0.5) - accessible_population(30, 0.15)) / 1000:.0f}k",
         "From a working cross-border labour market. Nothing has to be built."),
    ])

    st.divider()
    figure("How much of the city's market the border removes",
           "The circle is everyone within travelling distance. The orange line is the German "
           "border. Ground east of it fades out as the border gets harder to cross.",
           "Drag the two sliders. The radius is geography and cannot change; the border's "
           "openness is a policy choice and can. Watch which one moves the numbers more.")

    c1, c2 = st.columns([1, 1])
    with c1:
        radius = st.slider("Travel radius, km", 5, 30, 20, 5)
        labels = [s[0] for s in PERMEABILITY_SCENARIOS]
        chosen = st.select_slider("Border permeability", options=labels, value=labels[1])
        permeability = next(v for lbl, v, _ in PERMEABILITY_SCENARIOS if lbl == chosen)
        st.caption(next(d for lbl, _, d in PERMEABILITY_SCENARIOS if lbl == chosen))
    with c2:
        st.altair_chart(chart_catchment_geometry(radius, permeability), width="content", key="catchment_geom")

    beyond = segment_area(radius, BORDER_DISTANCE_KM)
    stats([
        ("Geometric loss at this radius", f"{(1 - catchment_ratio(radius, 0)) * 100:.0f}%",
         f"{beyond:.0f} km² of the {disc_area(radius):.0f} km² disc lies beyond the border."),
        ("Effective catchment", f"{catchment_ratio(radius, permeability) * 100:.0f}%",
         "Against a full disc."),
        ("Accessible population",
         f"{accessible_population(radius, permeability) / 1000:.0f}k",
         f"At {DENSITY_DUTCH} and {DENSITY_GERMAN} inhabitants per km² either side."),
        ("Gained over a closed frontier",
         f"{(accessible_population(radius, permeability) - accessible_population(radius, 0)) / 1000:.0f}k",
         "The return on institutional work rather than on construction."),
    ])
    note("Permeability here is an institutional quantity, not a distance — recognition of "
         "qualifications, portability of social insurance, a single tariff and ticket, a rail "
         "service that does not change character at the frontier. It is the only term in this "
         "figure that policy can move without moving earth.")
    provenance("derived", "CBS, Kadaster")

    st.divider()
    st.subheader("The arithmetic")
    st.latex(r"A_{\text{beyond}} = r^2 \arccos\!\left(\frac{d}{r}\right) - d\sqrt{r^2 - d^2}")
    st.markdown(
        f"Effective catchment is the near area plus permeability times the far area. That is the "
        f"whole model, and its transparency is the point. The behaviour worth noticing is that the "
        f"loss *grows* with radius: at five kilometres the border costs Enschede almost nothing, "
        f"and at thirty it costs {(1 - catchment_ratio(30, 0)) * 100:.0f} per cent. So the border "
        f"does not take away the corner shop's market; it takes away the market for exactly those "
        f"functions whose economics require a wide catchment — the specialist hospital department, "
        f"the concert hall, the regional distribution centre, the university's non-residential "
        f"intake. A city can lose its regional tier while its local tier looks perfectly healthy, "
        f"and that is a failure mode that per-capita statistics do not show."
    )

    st.divider()
    figure("How the loss grows with distance",
           "How much of a normal city's catchment Enschede actually has, as the travel "
           "radius grows.",
           "All three lines fall as you go right. The border costs Enschede almost nothing "
           "locally, and a great deal for anything needing a wide catchment — a hospital "
           "department, a concert hall.")
    st.altair_chart(chart_catchment_curve(), width="stretch", key="catchment_curve")
    provenance("derived", "CBS")

    _gravity_section()

    st.divider()
    st.subheader("What this reframes")
    st.markdown(
        "Enschede's development capacity is limited by nitrogen, by noise, by safety contours and "
        "by groundwater — all supply-side constraints on building. The border is a demand-side "
        "constraint, and it is the one nobody is required to model. It caps the catchment that "
        "would justify the density that the supply-side constraints make expensive."
    )
    st.markdown(
        "The two interact in a way that is easy to miss. A city with a full disc can justify paying "
        "the regulatory premium for dense, well-connected development, because the catchment is "
        "there to fill it. A city with two-thirds of a disc has a thinner case, so it builds at the "
        "edge instead, which raises the traffic term, which raises the nitrogen term, which further "
        "restricts what can be consented. The border is upstream of the constraint that binds."
    )
    st.markdown(
        "That gives an unusual conclusion for a spatial analysis: Enschede's highest-return "
        "investment may not be spatial at all."
    )


@st.fragment
def _gravity_section() -> None:
    """The same border question, answered with the real settlement pattern.

    The disc model above assumes population is spread evenly. This one places
    the dozen actual towns around Enschede at their real distances and lets a
    gravity model discount each by distance — with the border multiplying the
    effective distance of every German town. It is wrapped in a fragment so the
    permeability slider reruns only this block, not the page around it.
    """
    st.divider()
    st.subheader("The same border, town by town")
    note(
        "The disc above is honest but abstract: real people live in real towns at real "
        "distances, and the border falls on some of them. This is a gravity model — each "
        "town pulls in proportion to its population divided by the square of its distance, "
        "and the frontier stretches the effective distance of every town on the German side. "
        "Drag the permeability and watch the cross-border arcs thicken and thin."
    )

    perm = st.slider(
        "Border permeability", 0.0, 1.0, 0.15, 0.05, key="gravity_perm",
        help="0 = a closed frontier; 1 = a border that costs a commuter nothing but "
             "distance. 0.15 is roughly today's observed cross-border share.")

    open_a = gravity.accessibility(1.0)
    now_a = gravity.accessibility(perm)
    closed_a = gravity.accessibility(0.0)
    working_a = gravity.accessibility(0.5)

    stats([
        ("Regional market, open border", f"{open_a:,.0f}",
         "Gravity accessibility to the surrounding towns, border free (the reference)."),
        ("Lost to a closed frontier", f"{(1 - closed_a / open_a) * 100:.0f}%",
         "How much of the regional market sits across the border. Compare the disc's 37%."),
        ("At today's openness", f"{now_a / open_a * 100:.0f}%",
         f"Of the open-border market, at a permeability of {perm:.2f}."),
        ("Returned by a working border", f"+{(working_a - now_a) / open_a * 100:.0f} pts",
         "Going from the current setting to a permeability of 0.5. Policy, not construction."),
    ])

    figure("Which towns the border is holding back",
           "One arc per town, weighted by the pull the model assigns to that link at the "
           "permeability you set. Warm arcs cross the frontier.",
           "Gronau's arc is the one to watch. It is close and mid-sized, so when the border "
           "opens it becomes one of the strongest links on the map; when the border hardens it "
           "all but vanishes. Münster is big enough to matter but far enough away that "
           "distance has already done most of the discounting before the border adds any.")
    flows = gravity.flow_frame(perm)
    st.pydeck_chart(geo.gravity_flow_map(flows), width="stretch", height=520)
    st.markdown(
        geo.legend_html([
            ("Enschede (origin)", "#0b0b0b"),
            ("Dutch town", "#2a78d6"),
            ("German town — crosses the border", "#eb6834"),
        ]),
        unsafe_allow_html=True)
    st.caption(geo.OSM_ATTRIBUTION)

    contrib = gravity.contribution_table(perm)
    contrib = contrib[contrib["name"] != gravity.ORIGIN].copy()
    contrib["lost to border"] = contrib["open"] - contrib["at_permeability"]
    shown = contrib[["name", "side", "population", "distance_km",
                     "open", "at_permeability", "lost to border"]].copy()
    shown.columns = ["Town", "Side", "Population", "Distance, km",
                     "Pull, open border", "Pull at this setting", "Withheld by the border"]
    shown = shown.sort_values("Pull, open border", ascending=False)
    values_table(
        shown.assign(**{
            "Population": shown["Population"].map("{:,.0f}".format),
            "Distance, km": shown["Distance, km"].map("{:.1f}".format),
            "Pull, open border": shown["Pull, open border"].map("{:.1f}".format),
            "Pull at this setting": shown["Pull at this setting"].map("{:.1f}".format),
            "Withheld by the border": shown["Withheld by the border"].map("{:.1f}".format),
        }).reset_index(drop=True))
    provenance(
        "derived",
        "Populations are published municipal figures (CBS for the Dutch towns, Destatis / "
        "IT.NRW / LDS for the German ones); distances are straight-line between town centres. "
        "The gravity form, the decay exponent of 2 and the town-as-a-point abstraction are "
        "modelling choices, stated in urban/gravity.py.")


def page_energy() -> None:
    t = TECHNOLOGIES.set_index("id")
    wind_excl = units_for_target(t.loc["wind"]) * t.loc["wind", "exclusive_km2"]
    wind_gross = units_for_target(t.loc["wind"]) * t.loc["wind", "gross_km2"]
    solar_excl = units_for_target(t.loc["solar-field"]) * t.loc["solar-field", "exclusive_km2"]
    rooftop = rooftop_potential_twh()

    header("How much land renewable energy needs",
           "The regional renewable target gets argued about in terms of landscape and "
           "objections. Convert it instead into the two things that really limit it — how "
           "much land is involved, and how much land is actually taken out of use — and an "
           "awkward result appears. The option that uses the least land is the one the rules "
           "block. The one that gets built uses the most.")

    stats([
        ("Regional target", f"{RES_TARGET_TWH} TWh a year",
         "Across the fourteen Twente municipalities together, not Enschede alone."),
        ("Land wind actually takes", f"{wind_excl:.2f} km²",
         f"{units_for_target(t.loc['wind']):.0f} turbines, spread over {wind_gross:.0f} km² — but farming carries on "
         "under almost all of it."),
        ("Land solar actually takes", f"{solar_excl:.0f} km²",
         f"All of it, permanently — about {solar_excl / LAND_AREA_KM2 * 100:.0f}% of Enschede's whole area, "
         "quoted for scale rather than as a proposal."),
        ("Solar versus wind", f"{solar_excl / wind_excl:.0f}× more land",
         "For the same amount of energy. That gap is the whole comparison."),
    ])

    st.divider()
    figure("Land used up, versus land merely nearby",
           "Land needed for the regional renewable target. Blue is land the technology is "
           "spread across; orange is land actually taken out of use. Logarithmic scale.",
           "For wind the two dots are far apart — a wind farm covers a lot of ground and the "
           "farming carries on underneath. For solar they sit on top of each other: a solar "
           "field takes all of it.")
    st.altair_chart(chart_land_per_twh(), width="stretch", key="land_per_twh")
    values_table(land_table())
    note("Rooftop solar sits at zero on both measures, which a logarithmic axis cannot draw, so it "
         "is stated here rather than nudged onto the scale — putting a zero at an arbitrary small "
         "value is how a chart starts to lie.")
    provenance("derived", "RES Twente, textbook values")

    st.divider()
    st.subheader("Why the process selects the land-hungry option")
    for _, tech in TECHNOLOGIES.iterrows():
        shape = "no spatial constraint" if tech["constraint_shape"] == "none" else tech["constraint_shape"]
        with st.expander(f"{tech['label']}  ·  {shape}"):
            st.markdown(f"**What stops it** — {tech['binding']}")
            st.caption(tech["basis"])
    st.markdown(
        "Wind is stopped by fields — noise, shadow flicker, radar sightlines, habitat disturbance — "
        "none of which is a land requirement, and several of which are tractable engineering "
        "problems being handled as spatial ones. Radar interference in particular is a signal "
        "processing question that has been converted into a map. Ground-mounted solar is stopped by "
        "a polygon, and a polygon can be redrawn. So a search-area process genuinely trying to find "
        "consentable capacity will reliably converge on solar, not because it is the better answer "
        "but because its obstacle is the negotiable kind."
    )

    st.divider()
    st.subheader("The option with no land cost at all")
    st.markdown(
        f"Enschede's roofs are worth roughly {rooftop:.2f} TWh per year — about "
        f"{rooftop / RES_TARGET_TWH * 100:.0f} per cent of the whole regional target, from one "
        f"municipality, on structure that already exists. What stops it is not land and not "
        f"consent. It is transformer capacity at the low-voltage end of the network, roof "
        f"structural capacity on older stock, and the split incentive between whoever owns a roof "
        f"and whoever pays the electricity bill underneath it. Two of those three are capital "
        f"problems and the third is a contract problem. None is a spatial problem, and none is what "
        f"the regional search-area process is set up to solve."
    )


def page_method() -> None:
    header("Where the numbers come from",
           "An argument is only as good as its weakest number, so every figure carries a "
           "label saying how solid it is, right next to the figure. There are only a few "
           "labels on purpose — more categories would just give the author somewhere to "
           "hide.")

    st.subheader("Classes")
    for name, body in [
        ("official", "Published by a named authority and reproducible by opening their document. "
                     "Rounding is applied where the analysis is insensitive below a digit."),
        ("derived", "Computed here from stated inputs, with the arithmetic given alongside. If you "
                    "disagree with a derived number, the disagreement is with an input."),
        ("engineering", "A standard physics or engineering parameter quoted with its typical range. "
                        "These carry real spread."),
        ("estimate", "An order-of-magnitude figure held in place until the authoritative layer is "
                     "wired in. Every conclusion resting on one is written to survive its "
                     "replacement, or it is not drawn."),
    ]:
        st.markdown(f"**{name}** — {body}")

    st.divider()
    st.subheader("Sources")
    st.dataframe(
        pd.DataFrame([
            ("Centraal Bureau voor de Statistiek", "StatLine", "Population, dwellings, area, commuting."),
            ("Kadaster / PDOK", "National geodata services", "Building footprints, elevation, topography, boundaries."),
            ("Waterschappen / Rijkswaterstaat", "Actueel Hoogtebestand Nederland", "Elevation model behind the ridge profile."),
            ("RIVM", "AERIUS Calculator and Monitor", "Deposition, critical values, source-receptor relations."),
            ("Ministerie van LVVN", "Natura 2000 designations", "Site boundaries and habitat types."),
            ("Provincie Overijssel", "Omgevingsvisie and Omgevingsverordening", "Nature network, groundwater zones, settlement policy."),
            ("Gemeente Enschede", "Omgevingsvisie and Woonvisie", "Housing programme, densification, mobility policy."),
            ("RES Twente", "Regionale Energiestrategie", "Regional renewable target and search areas."),
            ("Raad van State", "Nitrogen jurisprudence", "The 2019 and 2022 annulments."),
            ("ProRail / NS", "Open network data", "Station locations and lines."),
            ("Third-party analysis", "Cape Town station-buffer coverage", "183 km² of buffers against an 895 km² edge, as published."),
        ], columns=["Holder", "Dataset or document", "What is taken from it"]),
        hide_index=True, width="stretch",
    )

    st.divider()
    st.subheader("Modelling methods")
    for title, body in [
        ("Conformal forecast bands",
         "Each family's 2050 interval is a split-conformal band: the half-width is the (1 − α) "
         "quantile of that model's own absolute errors on the withheld tail, with the finite-sample "
         "correction, widened with distance ahead by a square-root factor. It is calibrated to how "
         "wrong the model was about the recent past, and needs no assumption that the functional "
         "form is correctly specified — a family that has been wrong lately gets a wide band "
         "whatever it believes about itself. What it cannot carry is uncertainty about whether the "
         "form keeps holding at all, which is the larger error and the reason the comparison table "
         "still matters more than any single band."),
        ("The error-weighted ensemble",
         "The single planning figure is the inverse-backtest-MAE-weighted mean of the families that "
         "can extrapolate. Tree ensembles are excluded rather than allowed to vote for a flat line. "
         "The band around it is the conformal half-width plus the between-model standard deviation, "
         "so it widens where the families genuinely disagree and not only where each is unsure of "
         "itself. It is the one number the registry will defend; it is not a claim that the answer "
         "is right, only that it is arrived at by arithmetic the reader can check."),
        ("The gravity model of the border",
         "Each town's pull on Enschede is its population divided by the square of its distance, with "
         "a floor so the origin city does not dominate by sitting at zero. The frontier multiplies "
         "the effective distance of every German town by the inverse of the permeability. "
         "Populations are published municipal figures (CBS, Destatis / IT.NRW / LDS) and distances "
         "are straight-line between town centres; the gravity form, the exponent of 2 and the "
         "town-as-a-point abstraction are modelling choices, stated in urban/gravity.py. It "
         "reproduces the disc model's ~37% loss from the real settlement pattern and shows which "
         "towns the border falls hardest on."),
    ]:
        st.markdown(f"**{title}** — {body}")

    st.divider()
    st.subheader("Limits")
    for title, body in [
        ("No dispersion model",
         "The nitrogen section works entirely on the emission side. Converting emissions to "
         "deposition at a named receptor is what the official calculator exists for, and a "
         "plausible-looking imitation of it would be more dangerous than an obvious gap."),
        ("The constraint-shape figure is a schematic",
         "Its curves are characteristic forms, not calibrated site models, and nothing anywhere "
         "reads a value off them."),
        ("The border is a straight chord",
         "The real frontier is not straight, the population beyond it is not uniform, and "
         "permeability is not a scalar. All three simplifications understate the finding rather "
         "than manufacture it. The gravity model relaxes the uniform-population assumption but "
         "keeps the others: towns are points, distance is straight-line, and the decay exponent "
         "is a stated choice rather than an estimated one."),
        ("Conformal bands are calibrated, not prophetic",
         "The forecast intervals are calibrated on the backtest tail and assume the recent past is "
         "representative of the near future. They widen with distance ahead, but a regime shift the "
         "holdout never saw — a repeat of the textile collapse, or a sharp migration change — would "
         "fall outside any band, conformal or otherwise. The band's honesty is about the model's "
         "recent error, not about the world's stability."),
        ("Access sheds are summed, and the city is a disc",
         "The access section stylises the built-up area as a disc of equal area and models density "
         "as an exponential gradient. The metropolitan comparison sums station sheds rather than "
         "unioning them, so those figures are an upper bound."),
        ("Occupancy dominates the energy ladder",
         "Collective modes are only as efficient as they are filled, and the all-day averages used "
         "here are lower than the peak-hour figures usually quoted."),
        ("Nothing here is a permit assessment",
         "This is a way of seeing which constraints are reducible. It is not an environmental "
         "impact assessment, a nitrogen calculation, an acoustic report or a siting study."),
    ]:
        st.markdown(f"**{title}** — {body}")

    st.divider()
    st.subheader("This deployment")
    st.markdown(
        "This Streamlit application is a port of a Next.js platform in the same repository, not a "
        "wrapper around it: Streamlit Cloud runs Python, so the analytical constants are restated "
        "in Python and the figures rebuilt in Altair — which is Vega-Lite under a different "
        "surface, so the chart grammar carries over unchanged. The duplication is real and worth "
        "naming: there are two statements of the same numbers and they can drift. Everything that "
        "could drift lives in one clearly marked block at the top of `streamlit_app.py`, in the "
        "same order as the `data/*.ts` modules it mirrors."
    )
    st.markdown(
        "The app commits to a single light look rather than shipping a half-working dark mode, and "
        "every chart paints its own background so the figures stay internally consistent even if a "
        "viewer forces the dark theme from the settings menu."
    )


# =====================================================================
# Charts
# =====================================================================

def chart_constraint_shapes() -> alt.Chart:
    """Characteristic constraint forms, before and after a reduction at source.

    A schematic, and worth being blunt about it: the curves are the form of each
    constraint, not a calibrated model of any site. Nothing reads a value off it.
    What it is for is the one comparison the rest of the analysis rests on —
    that some of these curves can be pushed down and others cannot.
    """
    d = np.linspace(0, 3, 121)

    def curves(name: str, base, reduced, unit: str):
        # The unit belongs in the caption, not the panel title: a facet header
        # strip is about 150px wide and truncates anything longer.
        rows = []
        for dist in d:
            rows.append({"panel": name, "unit": unit, "d": dist, "v": base(dist),
                         "series": "As it stands"})
            rows.append({"panel": name, "unit": unit, "d": dist, "v": reduced(dist),
                         "series": "After a 30% reduction at source"})
        return rows

    rows = []
    rows += curves("Nitrogen deposition",
                   lambda x: 4.0 + 1.1 / (1 + x) ** 1.6,
                   lambda x: 4.0 * 0.79 + 0.7 * 1.1 / (1 + x) ** 1.6,
                   "× critical value")
    rows += curves("Road noise",
                   lambda x: (70 - 12 * math.log10(max(x, 0.01) / 0.01)) / 53,
                   lambda x: (60 - 12 * math.log10(max(x, 0.01) / 0.01)) / 53,
                   "× preference value")
    rows += curves("External safety",
                   lambda x: 6.5 / (1 + x * 9) ** 1.9,
                   lambda x: 0.745 * 6.5 / (1 + x * 9) ** 1.9,
                   "× the 10⁻⁶/yr contour")
    rows += curves("Groundwater capture",
                   lambda x: max(0.05, 2.4 - x * 0.85),
                   lambda x: max(0.05, (2.4 - x * 0.85) * 0.865),
                   "× the 25-year zone")
    rows += curves("Designated area boundary",
                   lambda x: 2.0 if x < 1.6 else 0.02,
                   lambda x: 2.0 if x < 1.6 else 0.02,
                   "inside or outside")

    df = pd.DataFrame(rows)

    # A faceted layer takes its data at the top level, so neither sub-chart
    # names it: passing data to the layer members instead makes the facet
    # unresolvable.
    lines = (
        alt.Chart()
        .mark_line(strokeWidth=2, strokeCap="round")
        .encode(
            x=alt.X("d:Q", title="km from source", axis=alt.Axis(values=[0, 1, 2, 3])),
            y=alt.Y("v:Q", title=None, scale=alt.Scale(zero=True)),
            color=alt.Color("series:N", scale=alt.Scale(
                domain=["As it stands", "After a 30% reduction at source"],
                range=[SERIES[0], SERIES[1]])),
            strokeDash=alt.StrokeDash("series:N", scale=alt.Scale(
                domain=["As it stands", "After a 30% reduction at source"],
                range=[[1, 0], [4, 3]]), legend=None),
        )
    )
    threshold = (
        alt.Chart()
        .mark_rule(strokeWidth=1, color=INK_3, opacity=0.5)
        .encode(y=alt.datum(1.0))
    )
    return style(
        alt.layer(threshold, lines, data=df)
        .properties(width=170, height=130)
        .facet(facet=alt.Facet("panel:N", title=None,
                               sort=["Nitrogen deposition", "Road noise", "External safety",
                                     "Groundwater capture", "Designated area boundary"],
                               header=alt.Header(labelLimit=200, labelFontSize=11)),
               columns=5)
        .resolve_scale(y="independent")
    )


def chart_critical_values() -> alt.Chart:
    df = HABITATS.assign(emphasis=np.where(HABITATS["kdw"] <= 500, "yes", "no"))
    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadiusEnd=4, height=18)
        .encode(
            y=alt.Y("label:N", sort=alt.SortField("kdw"), title=None,
                    axis=alt.Axis(labelLimit=400, labelColor=INK, labelFontSize=12)),
            x=alt.X("kdw:Q", title="mol nitrogen per hectare per year",
                    scale=alt.Scale(domain=[0, 2000], nice=False),
                    axis=alt.Axis(grid=True, gridColor=GRID, values=[0, 500, 1000, 1500, 2000])),
            color=alt.Color("emphasis:N", scale=alt.Scale(domain=["no", "yes"],
                                                          range=[SERIES[0], SERIES[1]]), legend=None),
            tooltip=["label", "code", "kdw"],
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"x": [BACKGROUND_DEPOSITION]}))
        .mark_rule(strokeWidth=2, color=INK, opacity=0.55)
        .encode(x="x:Q")
    )
    label = (
        alt.Chart(pd.DataFrame({"x": [BACKGROUND_DEPOSITION],
                                "t": [f"regional load {BACKGROUND_DEPOSITION:,}"]}))
        .mark_text(align="right", dx=-8, dy=-8, baseline="top", fontSize=11, color=INK_2)
        .encode(x="x:Q", text="t:N")
    )
    return style(alt.layer(bars, rule, label).properties(height=240))


def dwelling_nitrogen_table() -> pd.DataFrame:
    base = lifetime_nox_kg()
    rows = []
    for lever in LEVERS:
        construction = 0.0 if lever["electric_plant"] else CONSTRUCTION_NOX_KG
        use = annual_use_nox_kg() * lever["car_scale"] * DWELLING_LIFETIME_YEARS
        total = construction + use
        rows.append({
            "Scenario": lever["label"],
            "Construction, kg": round(construction),
            "Traffic, kg": round(use),
            "Total, kg": round(total),
            "Total, mol N": round(kg_nox_to_mol_n(total)),
            "vs baseline": "—" if total == base else f"−{(1 - total / base) * 100:.0f}%",
        })
    return pd.DataFrame(rows)


def chart_dwelling_nitrogen() -> alt.Chart:
    rows = []
    for lever in LEVERS:
        construction = 0.0 if lever["electric_plant"] else CONSTRUCTION_NOX_KG
        use = annual_use_nox_kg() * lever["car_scale"] * DWELLING_LIFETIME_YEARS
        rows.append({"scenario": lever["label"], "phase": "Construction plant", "kg": construction, "order": 0})
        rows.append({"scenario": lever["label"], "phase": "Traffic attracted, 50 years", "kg": use, "order": 1})
    df = pd.DataFrame(rows)
    order = [lever["label"] for lever in LEVERS]
    totals = df.groupby("scenario", as_index=False)["kg"].sum()

    # A 2px stroke in the surface colour is the gap, not a border: it is how
    # touching segments are separated without adding contrasting ink.
    bars = (
        alt.Chart(df)
        .mark_bar(height=20, cornerRadiusEnd=4, stroke=SURFACE, strokeWidth=2)
        .encode(
            y=alt.Y("scenario:N", sort=order, title=None,
                    axis=alt.Axis(labelLimit=420, labelColor=INK, labelFontSize=12)),
            x=alt.X("kg:Q", stack="zero", title="kg of nitrogen oxides over a fifty-year life",
                    scale=alt.Scale(domain=[0, 140], nice=False),
                    axis=alt.Axis(grid=True, gridColor=GRID)),
            color=alt.Color("phase:N", sort=["Construction plant", "Traffic attracted, 50 years"],
                            scale=alt.Scale(domain=["Construction plant", "Traffic attracted, 50 years"],
                                            range=[SERIES[1], SERIES[0]])),
            order=alt.Order("order:Q"),
            tooltip=["scenario", "phase", alt.Tooltip("kg:Q", format=".0f")],
        )
    )
    labels = (
        alt.Chart(totals)
        .mark_text(align="left", dx=10, fontSize=11, color=INK_2)
        .encode(y=alt.Y("scenario:N", sort=order, title=None), x="kg:Q",
                text=alt.Text("kg:Q", format=".0f"))
    )
    return style(alt.layer(bars, labels).properties(height=230))


def chart_energy_ladder() -> alt.Chart:
    """A dot plot rather than bars: the range spans a factor of fifty and a bar
    needs a zero baseline a logarithmic axis cannot give it."""
    # The lollipop stem starts at the axis minimum. It is carried as a real
    # column rather than as a bare datum: a datum encoding replaces the channel
    # outright, taking the log scale with it, and a layer whose x has neither
    # type nor scale is what Vega-Lite fails on at render time rather than at
    # build time.
    df = MODES.assign(emphasis=np.where(MODES["id"] == "ebike", "yes", "no"), origin=1.0)

    x_scale = alt.Scale(type="log", domain=[1, 200], nice=False)
    x_axis = alt.Axis(values=[1, 2, 5, 10, 20, 50, 100, 200], format="~s",
                      grid=True, gridColor=GRID)
    x_title = "passenger-kilometres per kilowatt-hour, logarithmic"

    base = alt.Chart(df).encode(
        y=alt.Y("label:N", sort=alt.SortField("pkm_per_kwh", order="descending"), title=None,
                axis=alt.Axis(labelColor=INK, labelFontSize=12, labelLimit=200)),
        x=alt.X("pkm_per_kwh:Q", scale=x_scale, title=x_title, axis=x_axis),
        color=alt.Color("emphasis:N", scale=alt.Scale(domain=["no", "yes"],
                                                      range=[SERIES[0], SERIES[1]]), legend=None),
    )
    rules = base.mark_rule(strokeWidth=2, opacity=0.35, strokeCap="round").encode(
        x=alt.X("origin:Q", scale=x_scale, title=x_title, axis=x_axis),
        x2="pkm_per_kwh:Q")
    dots = base.mark_point(filled=True, size=110, stroke=SURFACE, strokeWidth=2).encode(
        tooltip=["label", alt.Tooltip("pkm_per_kwh:Q", format=".1f"),
                 alt.Tooltip("kwh_per_pkm:Q", format=".3f"), "basis"])
    # Values wear a text token; the coloured dot beside them carries the emphasis.
    labels = base.mark_text(align="left", dx=12, fontSize=11).encode(
        text=alt.Text("pkm_per_kwh:Q", format=".0f"), color=alt.value(INK_2))
    return style(alt.layer(rules, dots, labels).properties(height=270))


def chart_energy_versus_space() -> alt.Chart:
    df = MODES.assign(emphasis=np.where(MODES["family"] == "private", "yes", "no"))
    base = alt.Chart(df).encode(
        x=alt.X("kwh_per_pkm:Q", scale=alt.Scale(type="log", domain=[0.008, 1], nice=False),
                title="kilowatt-hours per passenger-kilometre, logarithmic",
                axis=alt.Axis(values=[0.01, 0.03, 0.1, 0.3, 1], format=".2~f",
                              grid=True, gridColor=GRID)),
        y=alt.Y("m2:Q", scale=alt.Scale(type="log", domain=[1, 100], nice=False),
                title="m² of plan area per passenger, logarithmic",
                axis=alt.Axis(values=[1, 3, 10, 30, 100], format="~s", grid=True, gridColor=GRID)),
        color=alt.Color("emphasis:N", scale=alt.Scale(domain=["no", "yes"],
                                                      range=[SERIES[0], SERIES[1]]), legend=None),
    )
    dots = base.mark_point(filled=True, size=120, stroke=SURFACE, strokeWidth=2).encode(
        tooltip=["label", alt.Tooltip("kwh_per_pkm:Q", format=".3f"), "m2"])
    labels = base.mark_text(align="left", dx=11, dy=-1, fontSize=11).encode(
        text="label:N", color=alt.value(INK_2))
    return style(alt.layer(dots, labels).properties(height=300))


def chart_ridge() -> alt.Chart:
    crest = RIDGE_TRANSECT.loc[RIDGE_TRANSECT["m"].idxmax()]
    base = alt.Chart(RIDGE_TRANSECT).encode(
        x=alt.X("km:Q", title="km, west to east", axis=alt.Axis(values=list(range(0, 15, 2)))),
        y=alt.Y("m:Q", title="m above datum", scale=alt.Scale(domain=[20, 62], nice=False),
                axis=alt.Axis(values=[20, 30, 40, 50, 60], grid=True, gridColor=GRID)),
    )
    area = base.mark_area(color=SERIES[0], opacity=0.1, interpolate="monotone")
    line = base.mark_line(strokeWidth=2, color=SERIES[0], interpolate="monotone").encode(
        tooltip=["km", "m"])
    # One direct label, on the extreme. The axis carries the rest.
    peak = (
        alt.Chart(pd.DataFrame([{"km": crest["km"], "m": crest["m"], "t": f"{crest['m']} m"}]))
        .mark_text(dy=-14, fontSize=11, color=INK_2)
        .encode(x="km:Q", y="m:Q", text="t:N")
    )
    peak_dot = (
        alt.Chart(pd.DataFrame([{"km": crest["km"], "m": crest["m"]}]))
        .mark_point(filled=True, size=64, color=SERIES[0], stroke=SURFACE, strokeWidth=2)
        .encode(x="km:Q", y="m:Q")
    )
    return style(alt.layer(area, line, peak_dot, peak).properties(height=220))


def chart_access_sheds(reach_km: float) -> alt.Chart:
    """Sheds over the built-up area, drawn as a raster.

    A raster rather than a polygon union: the union of three overlapping discs
    clipped to a fourth has no convenient vector expression, and the cells are
    the same samples the coverage figures are computed from — so what is drawn
    is exactly what is counted.
    """
    g = access_grid(0.1)
    covered = np.zeros(len(g), dtype=bool)
    for _, s in STATIONS.iterrows():
        covered |= (g["x"] - s["x"]) ** 2 + (g["y"] - s["y"]) ** 2 <= reach_km**2
    df = g.assign(covered=np.where(covered, "Within reach", "Beyond reach"))
    df["density"] = df["w"] / df["w"].max()

    # The plot is square and the cells tile it exactly: 8 km across the domain
    # at 0.1 km spacing is 80 cells, so each is SHED_PX/80 wide. A fraction over
    # that closes the seams without visibly overlapping.
    cells = (
        alt.Chart(df)
        .mark_rect(width=SHED_PX / 80 + 0.2, height=SHED_PX / 80 + 0.2)
        .encode(
            x=alt.X("x:Q", title=None, scale=alt.Scale(domain=[-4, 4], nice=False), axis=None),
            y=alt.Y("y:Q", title=None, scale=alt.Scale(domain=[-4, 4], nice=False), axis=None),
            color=alt.Color("covered:N", scale=alt.Scale(
                domain=["Within reach", "Beyond reach"], range=[SERIES[0], INK_3])),
            # Opacity carries density, colour carries reach: a composite
            # encoding, so neither channel is asked to do both jobs.
            opacity=alt.Opacity("density:Q", scale=alt.Scale(range=[0.12, 0.85]), legend=None),
        )
    )
    dots = (
        alt.Chart(STATIONS)
        .mark_point(filled=True, size=90, color=SERIES[1], stroke=SURFACE, strokeWidth=2)
        .encode(x="x:Q", y="y:Q", tooltip=["label", "note"])
    )
    return style(alt.layer(cells, dots).properties(width=SHED_PX, height=SHED_PX))


def coverage_table() -> pd.DataFrame:
    rows = []
    for r in [0.8, 1.5, 2.0, 3.0, 4.0, 5.0]:
        c = coverage(r)
        rows.append({
            "Radius, km": r,
            "Shed per station, km²": round(shed_area_km2(r), 1),
            "Land covered": f"{c['land'] * 100:.0f}%",
            "Residents covered": f"{c['population'] * 100:.0f}%",
            "Gap, points": f"{(c['population'] - c['land']) * 100:.0f}",
        })
    return pd.DataFrame(rows)


def chart_coverage_curve() -> alt.Chart:
    radii = [0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
    rows = []
    for r in radii:
        c = coverage(r)
        rows.append({"radius": r, "basis": "Share of residents", "pct": c["population"] * 100})
        rows.append({"radius": r, "basis": "Share of built-up land", "pct": c["land"] * 100})
    df = pd.DataFrame(rows)

    # Direct labels go where the two series are furthest apart, not at the right
    # edge: both curves saturate at 100 well before the axis runs out, so an
    # end-label would put two identical numbers on top of each other.
    gaps = df.pivot(index="radius", columns="basis", values="pct")
    widest = (gaps["Share of residents"] - gaps["Share of built-up land"]).idxmax()
    marked = df[df["radius"] == widest]

    # `top` is a column for the same reason the ladder's origin is: a bare datum
    # replaces the channel and drops the scale with it.
    marks = pd.DataFrame([{"radius": m["radius_km"],
                           "label": m["id"].replace("ebike", "e-bike"),
                           "top": 108.0}
                          for m in ACCESS_MODES])

    domain = ["Share of residents", "Share of built-up land"]
    rules = alt.Chart(marks).mark_rule(strokeWidth=1, color=GRID).encode(x="radius:Q")
    mark_labels = alt.Chart(marks).mark_text(
        align="left", baseline="top", dx=5, fontSize=10, color=INK_3
    ).encode(x="radius:Q", y=alt.Y("top:Q", scale=alt.Scale(domain=[0, 110], nice=False),
                                   title=None), text="label:N")

    lines = (
        alt.Chart(df)
        .mark_line(strokeWidth=2, strokeCap="round")
        .encode(
            x=alt.X("radius:Q", title="access radius from the station, km",
                    scale=alt.Scale(domain=[0.4, 6], nice=False),
                    axis=alt.Axis(values=[1, 2, 3, 4, 5, 6])),
            # Headroom above 100 so the saturated curves sit clear of the top.
            y=alt.Y("pct:Q", title="% within reach of a station",
                    scale=alt.Scale(domain=[0, 110], nice=False),
                    axis=alt.Axis(values=[0, 25, 50, 75, 100], grid=True, gridColor=GRID)),
            color=alt.Color("basis:N", sort=domain, scale=alt.Scale(
                domain=domain, range=[SERIES[1], SERIES[0]]),
                legend=alt.Legend(orient="bottom")),
            tooltip=["basis", "radius", alt.Tooltip("pct:Q", format=".0f")],
        )
    )
    dots = alt.Chart(marked).mark_point(filled=True, size=80, stroke=SURFACE, strokeWidth=2).encode(
        x="radius:Q", y="pct:Q",
        color=alt.Color("basis:N", scale=alt.Scale(domain=domain, range=[SERIES[1], SERIES[0]]),
                        legend=None))
    labels = alt.Chart(marked).mark_text(align="left", dx=10, dy=-2, fontSize=11, color=INK_2).encode(
        x="radius:Q", y="pct:Q", text=alt.Text("pct:Q", format=".0f"))

    return style(alt.layer(rules, mark_labels, lines, dots, labels).properties(height=300))


def cape_town_table() -> pd.DataFrame:
    return pd.DataFrame([{
        "Access mode": f"{m['label']}, {m['minutes']} min",
        "Radius, km": m["radius_km"],
        "Shed per station, km²": round(shed_area_km2(m["radius_km"]), 1),
        "Summed, km²": round(CT_STATION_EQUIVALENTS * shed_area_km2(m["radius_km"])),
        "× the edge": f"{CT_STATION_EQUIVALENTS * shed_area_km2(m['radius_km']) / CT_EDGE_KM2:.2f}×",
    } for m in ACCESS_MODES])


def chart_cape_town() -> alt.Chart:
    df = pd.DataFrame([{
        "mode": f"{m['label']}, {m['minutes']} min",
        "summed": CT_STATION_EQUIVALENTS * shed_area_km2(m["radius_km"]),
        "ratio": CT_STATION_EQUIVALENTS * shed_area_km2(m["radius_km"]) / CT_EDGE_KM2,
        "shed": shed_area_km2(m["radius_km"]),
        "origin": 100.0,
    } for m in ACCESS_MODES])
    order = df["mode"].tolist()

    x_scale = alt.Scale(type="log", domain=[100, 4000], nice=False)
    x_axis = alt.Axis(values=[100, 300, 1000, 3000], format="~s", grid=True, gridColor=GRID)
    x_title = "summed station sheds, km², logarithmic"

    base = alt.Chart(df).encode(
        y=alt.Y("mode:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=260, labelColor=INK, labelFontSize=12)),
        x=alt.X("summed:Q", scale=x_scale, title=x_title, axis=x_axis),
    )
    rules = base.mark_rule(strokeWidth=2, opacity=0.35, strokeCap="round", color=SERIES[0]).encode(
        x=alt.X("origin:Q", scale=x_scale, title=x_title, axis=x_axis), x2="summed:Q")
    dots = base.mark_point(filled=True, size=130, color=SERIES[0], stroke=SURFACE, strokeWidth=2).encode(
        tooltip=["mode", alt.Tooltip("shed:Q", format=".1f"),
                 alt.Tooltip("summed:Q", format=".0f"), alt.Tooltip("ratio:Q", format=".2f")])
    labels = base.mark_text(align="left", dx=12, fontSize=11, color=INK_2).encode(
        text=alt.Text("ratio:Q", format=".2f"))
    edge = alt.Chart(pd.DataFrame({"x": [CT_EDGE_KM2]})).mark_rule(
        strokeWidth=2, color=SERIES[1]).encode(x="x:Q")
    edge_label = alt.Chart(
        pd.DataFrame({"x": [CT_EDGE_KM2], "t": [f"development edge, {CT_EDGE_KM2} km²"]})
    ).mark_text(align="left", dx=8, dy=-6, baseline="top", fontSize=11, color=INK_2).encode(
        x="x:Q", text="t:N")

    return style(alt.layer(rules, dots, labels, edge, edge_label).properties(height=150))


def chart_catchment_geometry(radius: int, permeability: float) -> alt.Chart:
    """The cut disc, rastered on the same principle as the access figure.

    Cells west of the border count in full; cells east of it count in proportion
    to how permeable the frontier is, which is exactly how the arithmetic treats
    them.
    """
    spacing = 1.0
    axis = np.arange(-32, 32 + spacing, spacing)
    xx, yy = np.meshgrid(axis, axis)
    r = np.hypot(xx, yy)
    inside = r <= radius
    x, y = xx[inside], yy[inside]
    beyond = x > BORDER_DISTANCE_KM

    df = pd.DataFrame({
        "x": x, "y": y,
        "side": np.where(beyond, "Beyond the border", "Within the border"),
        "weight": np.where(beyond, permeability, 1.0),
    })

    cells = (
        alt.Chart(df)
        .mark_rect(width=SHED_PX / 64 + 0.2, height=SHED_PX / 64 + 0.2)
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-32, 32], nice=False), axis=None, title=None),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-32, 32], nice=False), axis=None, title=None),
            color=alt.value(SERIES[0]),
            opacity=alt.Opacity("weight:Q", scale=alt.Scale(domain=[0, 1], range=[0.04, 0.5]),
                                legend=None),
        )
    )
    border = alt.Chart(pd.DataFrame({"x": [BORDER_DISTANCE_KM]})).mark_rule(
        strokeWidth=2, color=SERIES[1]).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-32, 32], nice=False), axis=None))
    centre = alt.Chart(pd.DataFrame({"x": [0], "y": [0]})).mark_point(
        filled=True, size=70, color=SERIES[0], stroke=SURFACE, strokeWidth=2).encode(
        x="x:Q", y="y:Q")

    return style(alt.layer(cells, border, centre).properties(width=SHED_PX, height=SHED_PX))


def chart_catchment_curve() -> alt.Chart:
    radii = [5, 10, 15, 20, 25, 30, 35, 40]
    shown = PERMEABILITY_SCENARIOS[:3]
    df = pd.DataFrame([
        {"scenario": label, "radius": r, "ratio": catchment_ratio(r, value) * 100}
        for label, value, _ in shown for r in radii
    ])
    order = [s[0] for s in shown]
    ends = df[df["radius"] == radii[-1]]

    lines = (
        alt.Chart(df)
        .mark_line(strokeWidth=2, strokeCap="round")
        .encode(
            x=alt.X("radius:Q", title="travel radius from the city centre, km",
                    scale=alt.Scale(domain=[5, 40], nice=False), axis=alt.Axis(values=radii)),
            y=alt.Y("ratio:Q", title="effective catchment as % of a full disc",
                    scale=alt.Scale(domain=[50, 100], nice=False),
                    axis=alt.Axis(values=[50, 60, 70, 80, 90, 100], grid=True, gridColor=GRID)),
            color=alt.Color("scenario:N", sort=order,
                            scale=alt.Scale(domain=order, range=SERIES),
                            legend=alt.Legend(orient="bottom")),
            tooltip=["scenario", "radius", alt.Tooltip("ratio:Q", format=".0f")],
        )
    )
    dots = alt.Chart(ends).mark_point(filled=True, size=80, stroke=SURFACE, strokeWidth=2).encode(
        x="radius:Q", y="ratio:Q",
        color=alt.Color("scenario:N", scale=alt.Scale(domain=order, range=SERIES), legend=None))
    labels = alt.Chart(ends).mark_text(align="right", dy=-14, fontSize=11, color=INK_2).encode(
        x="radius:Q", y="ratio:Q", text=alt.Text("ratio:Q", format=".0f"))
    return style(alt.layer(lines, dots, labels).properties(height=280))


def land_table() -> pd.DataFrame:
    rows = []
    for _, t in TECHNOLOGIES.iterrows():
        units = units_for_target(t)
        rows.append({
            "Technology": t["label"],
            "Units for the target": f"{units:,.0f} {t['unit']}s",
            "Associated km²": round(units * t["gross_km2"], 2),
            "Withdrawn km²": round(units * t["exclusive_km2"], 2),
            "Share of Enschede": f"{units * t['exclusive_km2'] / LAND_AREA_KM2 * 100:.1f}%",
        })
    return pd.DataFrame(rows)


def chart_land_per_twh() -> alt.Chart:
    plotted = TECHNOLOGIES[TECHNOLOGIES["gross_km2"] > 0].copy()
    plotted["units"] = plotted.apply(units_for_target, axis=1)
    plotted["gross"] = plotted["units"] * plotted["gross_km2"]
    plotted["exclusive"] = plotted["units"] * plotted["exclusive_km2"]
    order = plotted["label"].tolist()

    spans = plotted[["label", "gross", "exclusive"]].copy()
    spans["lo"] = spans[["gross", "exclusive"]].min(axis=1)
    spans["hi"] = spans[["gross", "exclusive"]].max(axis=1)

    long = plotted.melt(id_vars=["label"], value_vars=["gross", "exclusive"],
                        var_name="measure", value_name="km2")
    long["measure"] = long["measure"].map(
        {"gross": "Associated land", "exclusive": "Land withdrawn from other use"})

    y = alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelColor=INK, labelFontSize=12))
    x = alt.X("km2:Q", scale=alt.Scale(type="log", domain=[0.1, 100], nice=False),
              title=f"km² required for the {RES_TARGET_TWH} TWh per year regional target, logarithmic",
              axis=alt.Axis(values=[0.1, 1, 10, 100], format="~g", grid=True, gridColor=GRID))
    colour = alt.Color("measure:N", scale=alt.Scale(
        domain=["Associated land", "Land withdrawn from other use"], range=[SERIES[0], SERIES[1]]))

    connector = alt.Chart(spans).mark_rule(
        strokeWidth=2, color=INK_3, opacity=0.4, strokeCap="round").encode(
        y=alt.Y("label:N", sort=order, title=None),
        x=alt.X("lo:Q", scale=alt.Scale(type="log", domain=[0.1, 100], nice=False), title=None),
        x2="hi:Q")

    # Two point layers, sized so the coincident case still reads: solar withdraws
    # exactly the land it occupies, so its dots land on the same pixel. Drawing
    # the larger one underneath leaves a visible ring — "these are equal" rather
    # than "one of these is missing".
    big = alt.Chart(long[long["measure"] == "Associated land"]).mark_point(
        filled=True, size=220, stroke=SURFACE, strokeWidth=2).encode(
        y=y, x=x, color=colour, tooltip=["label", "measure", alt.Tooltip("km2:Q", format=".2f")])
    small = alt.Chart(long[long["measure"] != "Associated land"]).mark_point(
        filled=True, size=90, stroke=SURFACE, strokeWidth=2).encode(
        y=y, x=x, color=colour, tooltip=["label", "measure", alt.Tooltip("km2:Q", format=".2f")])

    return style(alt.layer(connector, big, small).properties(height=130))


# =====================================================================
# Entry point
# =====================================================================

# =====================================================================
# Navigation
# =====================================================================
#
# Two controls rather than one long list. The first picks the city, because
# that is the question a reader arrives with; the second picks the section
# within it. Fourteen items in a single flat list is a wall, and it hides the
# fact that the two cities are analysed to very different depths.

# The report has a reading order, so the menu shows one. Sections are numbered
# within each part, the parts run in the order you would read them, and the
# machine-learning part says so in its name rather than hiding behind
# "data and models".

PARTS: dict[str, dict[str, object]] = {
    "1 · The argument": {
        "1.1 Two cities that cannot build": lambda: page_opening(),
        "1.2 Side by side, in detail": lambda: page_compare(),
    },
    "2 · How much room is left": {
        "2.1 Cape Town: running out of land": lambda: page_cape_town(),
        "2.2 Enschede: land it may not use": lambda: page_constraints(),
    },
    "3 · Anatomy of a field constraint": {
        "3.1 Nitrogen: an allowance of zero": lambda: page_nitrogen(),
        "3.2 Energy and travel": lambda: page_mobility(),
        "3.3 Reaching a station": lambda: page_access(),
        "3.4 The German border": lambda: page_border(),
        "3.5 Land for energy": lambda: page_energy(),
    },
    "4 · People and growth": {
        "4.1 Population, 1950 to now": lambda: page_population(),
        "4.2 Forecasting 2050 — 7 models": lambda: page_projection(),
    },
    "5 · Where building goes": {
        "5.1 Predicting development — 3 models": lambda: page_development(),
        "5.2 Simulating growth to 2050": lambda: page_simulation(),
    },
    "6 · How people travel": {
        "6.1 How households choose": lambda: page_behaviour(),
        "6.2 Making it fast enough to use": lambda: page_scaling(),
    },
    "7 · Workbench": {
        "7.1 Run two futures against each other": lambda: page_simulator(),
    },
    "8 · Sources": {
        "8.1 Where the numbers come from": lambda: page_method(),
    },
}

PART_BLURB = {
    "1 · The argument": "The claim, the arithmetic behind it, and both cities in one frame.",
    "2 · How much room is left": "The land each city has, and what took the rest.",
    "3 · Anatomy of a field constraint": "What a limit with no edge does to a city. "
                                        "Enschede, in detail.",
    "4 · People and growth": "How many people are coming, and how much the models disagree.",
    "5 · Where building goes": "Which land develops, what it is worth, what the constraint "
                              "costs in hectares.",
    "6 · How people travel": "What households choose when prices change, and what that does "
                            "to the nitrogen account.",
    "7 · Workbench": "Set two futures against each other and read the difference.",
    "8 · Sources": "Every number, where it came from, and what this gets wrong.",
}

# Which parts analyse both cities. Shown in the menu so a reader can see at a
# glance that the coverage is not lopsided — the previous version buried this
# and the first thing anyone asked was where Cape Town's models were.
BOTH_CITIES = {
    "1 · The argument", "2 · How much room is left", "4 · People and growth",
    "5 · Where building goes", "6 · How people travel", "7 · Workbench", "8 · Sources",
}


def main() -> None:
    st.set_page_config(
        page_title="Cape Town and Enschede — what limits building",
        page_icon="◐",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Altair 6 ships chart data through narwhals/pyarrow internally, so the
    # heavy raster frames already cross as columnar buffers; there is no
    # separate "arrow" transformer to enable any more, and the vegafusion
    # transformer would add a dependency this app does not otherwise need. All
    # that is left to do is lift the row cap for the wide frames.
    alt.data_transformers.disable_max_rows()
    chrome.inject()

    with st.sidebar:
        st.markdown(
            "<div class='brand'><div class='brand-name'>Cape Town &amp; Enschede</div>"
            "<div class='brand-sub'>what limits building</div></div>",
            unsafe_allow_html=True)

        # Dropdowns rather than radio lists: eight parts and up to five sections
        # is a wall of always-visible options in a narrow column. A closed
        # select shows where you are in one line and opens to the rest.
        part = st.selectbox("Part of the report", list(PARTS), key="part")
        st.caption(PART_BLURB[part])

        # Coverage, stated in the menu. The report's own reader could not tell
        # which parts covered both cities, so it now says so where the choice
        # is made rather than three screens into the section.
        if part in BOTH_CITIES:
            st.markdown("<div class='cover-tag both'>Both cities</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<div class='cover-tag one'>Enschede in depth</div>",
                        unsafe_allow_html=True)

        sections = PARTS[part]
        if len(sections) > 1:
            section = st.selectbox("Section", list(sections), key=f"section_{part}")
        else:
            section = next(iter(sections))
            st.caption(f"→ {section}")

        st.divider()
        st.caption(
            "Every number says how solid it is — official, derived, engineering, estimate, "
            "reconstructed or synthetic — and where it came from."
        )

    # One place decides the section number; every header and figure derives
    # from it. See urban/ui.begin_section.
    ui_begin_section(section)
    sections[section]()


if __name__ == "__main__":
    main()
