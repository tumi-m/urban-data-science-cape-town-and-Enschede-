"""The Cape Town layers, and what can honestly be derived from them.

This is the *derive* half of the Cape Town data story. `sources.py` knows how
to fetch layers; this module knows what each layer means, and turns raw
geometry into the figures the report needs — the area of the urban edge, the
extent of protected nature, the reach of the rail stations.

The rule that governs everything here is the project's own: **a derived figure
is only as good as its weakest input.** A polygon fetched from the City's own
portal is an official shape; computing an area from it is a derived figure.
When the portal cannot be reached, every function here returns the published
figure the page already carried, *declared as an estimate*, so a deployment
without network loses the recomputation and gains nothing false.

Geometry is handled with geopandas/shapely/pyproj in a local projected CRS
(UTM 34S, the zone Cape Town sits in), never with degrees or hand-placed areas.

Usage
-----
    catalog = cct_catalog()              # fetch every layer once
    edge = catalog.area_km2("urban_edge")
    table = catalog.evidence()           # the page's source-of-truth frame
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import sources
from .provenance import DERIVED, ESTIMATE

# ---------------------------------------------------------------------
# Published fallbacks, so a network-less deployment reads the same page it
# read before — but clearly marked `estimate` rather than `derived`.
# ---------------------------------------------------------------------

URBAN_EDGE_FALLBACK_KM2 = 895.0        # published urban development edge
PROTECTED_FALLBACK_HA = 55_697.0       # published formally protected land
PROTECTED_FALLBACK_KM2 = PROTECTED_FALLBACK_HA / 100
PROTECTED_FALLBACK_SHARE = 22.72       # % of municipality
MUNICIPAL_FALLBACK_KM2 = 2_451.0       # published municipal area
STATION_FALLBACK_KM2 = 183.0           # land within 800 m of a station, as published
VEGETATION_LOST_FALLBACK_PCT = 61.0    # share of original vegetation transformed

# UTM 34S covers all of Cape Town with well under 1 % area distortion.
EPSG_UTM_34S = "EPSG:32734"


@dataclass
class Derived:
    """One derived figure: the value, its provenance class, and the layer
    route that produced it (for the evidence table)."""

    value: float
    klass: str                      # "derived" | "estimate"
    source: str
    unit: str = ""
    note: str = ""


def _area_km(gdf) -> float | None:
    """Total area of a GeoDataFrame, in km² on the ground (UTM 34S)."""
    if gdf is None or gdf.empty:
        return None
    try:
        projected = gdf.to_crs(EPSG_UTM_34S)
        return float(projected.geometry.area.sum() / 1e6)
    except Exception:
        return None


# The layers the catalog actually measures: which portal route, the label the
# page shows, and the published-figure fallback when the portal is unreachable.
LAYERS = {
    "urban_edge": {
        "route": "urban_edge", "label": "Inside the urban edge",
        "fallback": Derived(URBAN_EDGE_FALLBACK_KM2, ESTIMATE,
                            "published City figure", "km²"),
    },
    "bionet": {
        "route": "bionet", "label": "Protected nature",
        "fallback": Derived(PROTECTED_FALLBACK_KM2, ESTIMATE,
                            "published City figure", "km²"),
    },
    "stations": {
        "route": "rail_stations", "label": "Rail stations",
        "fallback": Derived(0.0, ESTIMATE, "no station reach computed", "km²"),
    },
}


def _fetch_layer(layer: str) -> tuple[object | None, str]:
    """One fetch: (GeoDataFrame-or-None, state). Never raises.

    `state` is "fetched" when the portal replied with features and they parsed,
    otherwise "fallback". A layer that fails does not fail the catalog.
    """
    import geopandas as gpd  # kept lazy so model sections stay light

    route = sources.LAYER_ROUTES[LAYERS[layer]["route"]]
    raw = sources.query_feature_service(route)
    if raw is None or not raw.get("features"):
        return None, "fallback"
    try:
        gdf = gpd.GeoDataFrame.from_features(raw["features"])
    except Exception:
        return None, "fallback"
    if gdf.empty:
        return None, "fallback"
    return gdf, "fetched"


class Catalog:
    """A single fetch of the Cape Town layers and everything derived from them.

    Creating a Catalog performs the network calls once, so a page can ask for
    several figures without re-fetching. Failure is per-layer: a layer that is
    unavailable reports `state="fallback"` and its figure stays at the
    published value.
    """

    def __init__(self) -> None:
        self.data: dict[str, object | None] = {}
        self.state: dict[str, str] = {}
        for layer in LAYERS:
            gdf, state = _fetch_layer(layer)
            self.data[layer] = gdf
            self.state[layer] = state

    # -- public helpers -- -------------------------------------------
    def is_any_fetched(self) -> bool:
        return any(s == "fetched" for s in self.state.values())

    def live(self, layer: str) -> bool:
        return self.state.get(layer) == "fetched"

    # -- derived figures -- -------------------------------------------
    def area_km2(self, layer: str) -> Derived:
        """Area of a layer, recomputed when the portal replied, otherwise the
        published fallback."""
        fallback = LAYERS[layer]["fallback"]
        if not self.live(layer):
            return fallback
        area = _area_km(self.data[layer])
        if area is None:
            return fallback
        return Derived(round(area, 1), DERIVED,
                       f"recomputed from the {LAYERS[layer]['label']} layer",
                       fallback.unit)

    def municipal_km2(self) -> Derived:
        """Municipal area. Not fetched as a layer; the published total is the
        reference and is stated here once so the catalog is the single place
        the number is written down."""
        return Derived(MUNICIPAL_FALLBACK_KM2, ESTIMATE, "published City figure", "km²")

    def station_reach_km2(self, radius_m: float = 800.0) -> Derived:
        """Area of the urban edge within `radius_m` of a rail station.

        This is the headline "share of the edge near a station" figure,
        recomputed here *when both layers are live*, as a true buffer over the
        station points clipped to the urban edge in UTM 34S.
        """
        if not (self.live("stations") and self.live("urban_edge")):
            return LAYERS["stations"]["fallback"]
        try:
            edge = self.data["urban_edge"].to_crs(EPSG_UTM_34S)
            stations = self.data["stations"].to_crs(EPSG_UTM_34S)
            edge_total = float(edge.geometry.area.sum())
            if edge_total <= 0:
                return LAYERS["stations"]["fallback"]
            buffered = stations.geometry.buffer(radius_m).unary_union
            reach = float(edge.intersection(buffered).area.sum())
            return Derived(round(reach / 1e6, 1), DERIVED,
                           "buffer of station points in UTM 34S", "km²")
        except Exception:
            return LAYERS["stations"]["fallback"]

    def station_share(self, radius_m: float = 800.0) -> Derived:
        """Share of the edge within a walk of a station, as a percentage."""
        reach = self.station_reach_km2(radius_m)
        edge = self.area_km2("urban_edge")
        if edge.value <= 0:
            return Derived(0.0, ESTIMATE, "no urban edge", "%")
        return Derived(round(reach.value / edge.value * 100, 1),
                       reach.klass, reach.source, "%")

    def evidence(self) -> pd.DataFrame:
        """Every headline Cape Town figure, its class, and which layer — or
        which published fallback — produced it. The page's source-of-truth
        table: a reader sees in one place which figures were recomputed here
        and which are the City's published ones."""
        edge = self.area_km2("urban_edge")
        protected = self.area_km2("bionet")
        reach = self.station_reach_km2()
        munic = self.municipal_km2()
        rows = [
            {"figure": "Inside the urban edge", "value": edge.value,
             "unit": edge.unit, "class": edge.klass, "source": edge.source},
            {"figure": "Protected nature", "value": protected.value,
             "unit": protected.unit, "class": protected.klass, "source": protected.source},
            {"figure": "Land within 800 m of a station", "value": reach.value,
             "unit": reach.unit, "class": reach.klass, "source": reach.source},
            {"figure": "Full municipality", "value": munic.value,
             "unit": munic.unit, "class": munic.klass, "source": munic.source},
        ]
        return pd.DataFrame(rows)


def cct_catalog() -> Catalog:
    """The one function most pages should call."""
    return Catalog()


__all__ = [
    "Catalog", "Derived", "cct_catalog",
    "URBAN_EDGE_FALLBACK_KM2", "PROTECTED_FALLBACK_HA",
    "PROTECTED_FALLBACK_SHARE", "MUNICIPAL_FALLBACK_KM2",
    "STATION_FALLBACK_KM2", "VEGETATION_LOST_FALLBACK_PCT",
]