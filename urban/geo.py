"""Real maps, on real coordinates, over OpenStreetMap.

Until now the spatial figures were drawn on a stylised disc: honest about being
a stylisation, and hard to relate to anywhere you have actually been. These are
the same analyses on real latitude and longitude with an OpenStreetMap
background, so a station is where the station is and a 800 m circle is 800 m.

Two things to know about the basemap.

  * The basemap is CARTO's "Positron without labels" vector style, fetched at
    view time. That needs outbound internet from wherever the app runs.
    Streamlit Cloud has it; the sandbox this was written in did not, so the
    tile rendering could not be verified locally — the layers, coordinates and
    radii could.
  * CARTO and OSM attribution policy requires attribution, and every map here
    carries it in the caption below the map.

Coordinates are given to four decimal places, which is about ten metres, and
they are hand-placed rather than geocoded. That is well inside the tolerance of
anything computed from them: the circles are kilometres wide.
"""

from __future__ import annotations

import pandas as pd
import pydeck as pdk

from .theme import SERIES

# The basemap is pydeck's built-in CARTO "Positron without labels" vector
# style, selected with `map_style="light_no_labels"` and
# `map_provider="carto"` on each Deck. A hosted vector style rather than a raw
# raster TileLayer, for two reasons:
#
#   * The raw raster approach left MapLibre's default attribution control
#     ("© Mapbox © OpenStreetMap") floating in the corner of every map — stray
#     text that fought the hand-placed labels. A proper map style carries its
#     own attribution, so the corner is clean and the credit lives in the
#     caption below the map instead.
#   * Positron-without-labels keeps the street and block geometry as pale
#     lines but drops every street-name and place-label, so the coloured data
#     layers and the hand-placed TextLayer labels are what the eye lands on.
#     No API key and no account, like the OSM tiles it replaces.
BASEMAP_ATTRIBUTION = (
    "Basemap © CARTO · © OpenStreetMap contributors, ODbL."
)
# Kept for the attribution strings already embedded in page captions below.
OSM_ATTRIBUTION = BASEMAP_ATTRIBUTION


def _rgb(hex_colour: str, alpha: int = 255) -> list[int]:
    h = hex_colour.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [alpha]


BLUE = _rgb(SERIES[0])
ORANGE = _rgb(SERIES[1])
GREEN = _rgb(SERIES[2])


# ---------------------------------------------------------------------
# Enschede
# ---------------------------------------------------------------------

ENSCHEDE_CENTRE = (52.2215, 6.8937)

STATIONS = pd.DataFrame([
    {"name": "Enschede Centraal", "lat": 52.2233, "lon": 6.8892,
     "note": "Terminus from the west, and the interchange to the German service."},
    {"name": "Enschede Kennispark", "lat": 52.2394, "lon": 6.8494,
     "note": "University campus and science park."},
    {"name": "Enschede De Eschmarke", "lat": 52.2264, "lon": 6.9351,
     "note": "Eastern suburban stop, on the line toward the border."},
])

PLACES = pd.DataFrame([
    {"name": "City centre", "kind": "Retail", "lat": 52.2205, "lon": 6.8937},
    {"name": "Medisch Spectrum Twente", "kind": "Hospital", "lat": 52.2185, "lon": 6.8850},
    {"name": "Roombeek", "kind": "Housing", "lat": 52.2333, "lon": 6.8900},
    {"name": "Kennispark", "kind": "Employment", "lat": 52.2394, "lon": 6.8494},
    {"name": "De Eschmarke", "kind": "Housing", "lat": 52.2264, "lon": 6.9351},
    {"name": "Aamsveen (protected bog)", "kind": "Protected", "lat": 52.1900, "lon": 6.9600},
    {"name": "Glanerbrug (German border)", "kind": "Border", "lat": 52.2200, "lon": 6.9750},
])


# ---------------------------------------------------------------------
# Cape Town
# ---------------------------------------------------------------------

CAPE_TOWN_CENTRE = (-33.9800, 18.5600)

CT_PLACES = pd.DataFrame([
    {"name": "City centre (CBD)", "kind": "Employment", "lat": -33.9249, "lon": 18.4241},
    {"name": "Cape Town station", "kind": "Rail", "lat": -33.9222, "lon": 18.4256},
    {"name": "Table Mountain", "kind": "Protected", "lat": -33.9628, "lon": 18.4098},
    {"name": "Cape Flats (Khayelitsha)", "kind": "Housing", "lat": -34.0400, "lon": 18.6700},
    {"name": "Mitchells Plain", "kind": "Housing", "lat": -34.0350, "lon": 18.6180},
    {"name": "Philippi horticultural area", "kind": "Agriculture", "lat": -34.0100, "lon": 18.5700},
    {"name": "Cape Town International", "kind": "Transport", "lat": -33.9690, "lon": 18.6017},
])

KIND_COLOUR = {
    "Retail": ORANGE, "Hospital": ORANGE, "Housing": BLUE, "Employment": BLUE,
    "Protected": GREEN, "Border": ORANGE, "Rail": ORANGE, "Agriculture": GREEN,
    "Transport": BLUE,
}


# ---------------------------------------------------------------------
# Map builders
# ---------------------------------------------------------------------

def station_catchment_map(
    radius_m: float,
    *,
    stations: pd.DataFrame | None = None,
    centre: tuple[float, float] = ENSCHEDE_CENTRE,
    zoom: float = 11.2,
    height: int = 460,
) -> pdk.Deck:
    """Stations with a real catchment circle around each one.

    The circles are drawn in metres on the ground, so the thing the access
    section argues about — that the radius is a choice, and that area grows with
    its square — is visible against streets you can recognise rather than
    against a stylised disc.
    """
    df = (stations if stations is not None else STATIONS).copy()
    df["radius"] = radius_m

    return pdk.Deck(
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["lon", "lat"],
                get_radius="radius",
                get_fill_color=[*BLUE[:3], 55],
                get_line_color=[*BLUE[:3], 200],
                line_width_min_pixels=2,
                stroked=True,
                filled=True,
                pickable=False,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["lon", "lat"],
                get_radius=90,
                radius_min_pixels=5,
                get_fill_color=ORANGE,
                get_line_color=[255, 255, 255, 230],
                line_width_min_pixels=2,
                stroked=True,
                pickable=True,
            ),
        ],
        initial_view_state=pdk.ViewState(
            latitude=centre[0], longitude=centre[1], zoom=zoom, pitch=0),
        tooltip={"text": "{name}\n{note}"},
        height=height,
        map_provider="carto",
        map_style="light_no_labels",
    )


def places_map(
    places: pd.DataFrame,
    *,
    centre: tuple[float, float],
    zoom: float = 10.4,
    height: int = 460,
) -> pdk.Deck:
    """Named locations, coloured by what they are."""
    df = places.copy()
    df["colour"] = df["kind"].map(lambda k: KIND_COLOUR.get(k, BLUE))

    return pdk.Deck(
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["lon", "lat"],
                get_radius=420,
                radius_min_pixels=7,
                get_fill_color="colour",
                get_line_color=[255, 255, 255, 230],
                line_width_min_pixels=2,
                stroked=True,
                pickable=True,
            ),
            pdk.Layer(
                "TextLayer",
                data=df,
                get_position=["lon", "lat"],
                get_text="name",
                get_size=12,
                get_color=[20, 20, 20, 235],
                get_pixel_offset=[0, -18],
                background=True,
                get_background_color=[252, 252, 251, 205],
                background_padding=[4, 2, 4, 2],
                size_units="pixels",
            ),
        ],
        initial_view_state=pdk.ViewState(
            latitude=centre[0], longitude=centre[1], zoom=zoom, pitch=0),
        tooltip={"text": "{name} — {kind}"},
        height=height,
        map_provider="carto",
        map_style="light_no_labels",
    )


def legend_html(entries: list[tuple[str, str]]) -> str:
    """A legend that is always visible, rather than one deck.gl does not draw.

    pydeck has no legend of its own, so a map without this has colours the
    reader has to guess at. Rendered as plain HTML under the map.
    """
    items = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'margin-right:18px;font-size:0.78rem;white-space:nowrap">'
        f'<span style="width:11px;height:11px;border-radius:3px;'
        f'background:{colour};display:inline-block"></span>{label}</span>'
        for label, colour in entries
    )
    return (
        f'<div style="display:flex;flex-wrap:wrap;gap:4px 0;margin:0.55rem 0 0.2rem 0">'
        f'{items}</div>'
    )


def gravity_flow_map(flows: pd.DataFrame, *,
                     centre: tuple[float, float] = ENSCHEDE_CENTRE,
                     zoom: float = 8.4, height: int = 520) -> pdk.Deck:
    """The border catchment as a flow map.

    One arc per surrounding town, drawn from the origin city out to it. The
    arc's weight and colour carry the interaction the gravity model assigns to
    that link: thick and warm where the pull is strong, thin and cool where
    distance or the border has thinned it. Arcs that cross the frontier are
    drawn in the warm ramp so the reader can see exactly which links the border
    is thinning — Gronau's arc, close and heavy when the border is open, is the
    one that collapses as permeability falls.
    """
    df = flows.copy()
    # Normalise flow to a 1–14 px width and split colour by whether the link
    # crosses the border. The scale is relative to the strongest link, so the
    # map reads the same at any permeability.
    fmax = max(float(df["flow"].max()), 1e-9)
    df["width"] = 1.0 + 13.0 * df["flow"] / fmax
    df["arc_colour"] = df.apply(
        lambda r: ([*ORANGE[:3], 200] if r["crosses_border"] else [*BLUE[:3], 170]),
        axis=1)
    df["town_colour"] = df.apply(
        lambda r: (ORANGE if r["crosses_border"] else BLUE), axis=1)

    arcs = pdk.Layer(
        "ArcLayer",
        data=df,
        get_source_position=["o_lon", "o_lat"],
        get_target_position=["lon", "lat"],
        get_width="width",
        get_source_color="arc_colour",
        get_target_color="arc_colour",
        pickable=True,
        auto_highlight=True,
    )
    towns = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_radius=900,
        radius_min_pixels=6,
        get_fill_color="town_colour",
        get_line_color=[255, 255, 255, 235],
        line_width_min_pixels=2,
        stroked=True,
        pickable=True,
    )
    labels = pdk.Layer(
        "TextLayer",
        data=df,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=12,
        get_color=[20, 20, 20, 235],
        get_pixel_offset=[0, -16],
        background=True,
        get_background_color=[252, 252, 251, 205],
        background_padding=[4, 2, 4, 2],
        size_units="pixels",
    )
    origin_df = df.head(1)[["o_lon", "o_lat"]].rename(
        columns={"o_lon": "lon", "o_lat": "lat"})
    origin_pt = pdk.Layer(
        "ScatterplotLayer",
        data=origin_df,
        get_position=["lon", "lat"],
        get_radius=1300,
        radius_min_pixels=9,
        get_fill_color=[11, 11, 11, 255],
        get_line_color=[255, 255, 255, 255],
        line_width_min_pixels=2,
        stroked=True,
        pickable=False,
    )
    return pdk.Deck(
        layers=[arcs, towns, labels, origin_pt],
        initial_view_state=pdk.ViewState(
            latitude=centre[0], longitude=centre[1], zoom=zoom, pitch=0),
        tooltip={"text": "{name}\npopulation {population}\nflow {flow}"},
        height=height,
        map_provider="carto",
        map_style="light_no_labels",
    )
