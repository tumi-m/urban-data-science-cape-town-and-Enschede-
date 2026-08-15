"""A gravity model of the border catchment.

The border section's main figure treats population as a uniform density on
either side of the frontier — transparent, and the right way to show that the
loss grows with radius. But a city's market is not a smooth disc; it is a
small number of real towns at real distances, and the border falls on some of
them and not others. This module models that directly.

The method is the gravity model from transport geography: the pull of a place
is its population divided by a power of its distance, and a border multiplies
the effective distance of every centre on the far side. It is the same
question as the disc model — how much of the catchment does the frontier take
— answered with the actual settlement pattern instead of an assumed one.

The populations are published municipal figures and the coordinates are real;
both are written down below. What is *not* real is the abstraction of each
municipality to a single point, and the choice of decay exponent. Those are
stated, and the result is labelled accordingly: the *pattern* (which towns the
border touches, and how much opening it returns) is defensible; the third
decimal place is not.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------
# The real settlement pattern around Enschede
# ---------------------------------------------------------------------
#
# Populations are municipal figures rounded to the nearest thousand, from CBS
# (Dutch municipalities) and Destatis / the IT.NRW and LDS registers (German
# ones). Coordinates are town-centre latitude/longitude. `side` is which
# country the centre is in; the border impedance applies only across it.
#
# This is deliberately a short table — the dozen centres that actually make up
# Enschede's hinterland, not a synthetic surface. Adding a row changes the
# answer by that town's pull and nothing else.

CENTRES = pd.DataFrame([
    # name, side, population, lat, lon
    {"name": "Enschede", "side": "NL", "population": 161_000, "lat": 52.2215, "lon": 6.8937},
    {"name": "Hengelo", "side": "NL", "population": 82_000, "lat": 52.2658, "lon": 6.7931},
    {"name": "Almelo", "side": "NL", "population": 73_000, "lat": 52.3567, "lon": 6.6625},
    {"name": "Oldenzaal", "side": "NL", "population": 32_000, "lat": 52.3133, "lon": 6.9290},
    {"name": "Losser", "side": "NL", "population": 23_000, "lat": 52.2600, "lon": 7.0040},
    {"name": "Gronau", "side": "DE", "population": 50_000, "lat": 52.2110, "lon": 7.0220},
    {"name": "Ahaus", "side": "DE", "population": 40_000, "lat": 52.0794, "lon": 7.0134},
    {"name": "Nordhorn", "side": "DE", "population": 53_000, "lat": 52.4333, "lon": 7.0667},
    {"name": "Steinfurt", "side": "DE", "population": 35_000, "lat": 52.1505, "lon": 7.3366},
    {"name": "Münster", "side": "DE", "population": 320_000, "lat": 51.9607, "lon": 7.6261},
])

ORIGIN = "Enschede"

# Decay exponent. A value near 2 is the standard gravity form; the qualitative
# finding (which towns the border removes, and what opening it returns) is
# insensitive to it across the usual 1.5–2.5 range.
BETA = 2.0

# A floor on distance, in km, so the origin city does not dominate by sitting
# at zero. Set to the rough radius of the city itself.
D0_KM = 3.0

EARTH_R_KM = 6371.0


def _haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Great-circle distance in kilometres, vectorised over the second point."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(a))


def distances_from(origin: str = ORIGIN, centres: pd.DataFrame = CENTRES) -> pd.DataFrame:
    """Every centre's straight-line distance from the origin city."""
    o = centres.set_index("name").loc[origin]
    df = centres.copy()
    df["distance_km"] = _haversine_km(o["lat"], o["lon"], df["lat"].to_numpy(),
                                      df["lon"].to_numpy())
    return df


def accessibility(permeability: float, beta: float = BETA,
                  centres: pd.DataFrame = CENTRES, origin: str = ORIGIN,
                  include_self: bool = False) -> float:
    """The gravity accessibility of the origin city, in population-weighted units.

    Each centre contributes population / (distance + floor)^beta. A centre on
    the far side of the border has its effective distance divided by the
    permeability, so a closed frontier (permeability 0) removes it entirely and
    an open one (permeability 1) counts it at face value.

    By default the origin's own population is excluded: a city's *catchment* is
    the surrounding market it reaches out to, not the people already inside it.
    Including the city itself swamps the signal — Enschede's own 161,000 people
    would be ~94% of the total and the border would vanish, which is precisely
    the wrong answer to the question this model exists to ask. Pass
    `include_self=True` only for a self-sufficiency measure, which is a
    different question.
    """
    df = distances_from(origin, centres)
    o_side = df.set_index("name").loc[origin, "side"]
    if not include_self:
        df = df[df["name"] != origin]
    eff = df["distance_km"].to_numpy(dtype=float)
    cross = (df["side"] != o_side).to_numpy()
    # Border impedance lengthens the effective distance of a cross-border link.
    eff = np.where(cross, eff / max(permeability, 1e-6), eff)
    d = np.maximum(eff, 0.0) + D0_KM
    return float((df["population"].to_numpy(dtype=float) / d ** beta).sum())


def contribution_table(permeability: float, beta: float = BETA,
                       centres: pd.DataFrame = CENTRES,
                       origin: str = ORIGIN) -> pd.DataFrame:
    """Each centre's contribution to the origin's accessibility.

    This is the readable form of the model: not one number but a row per town,
    so the reader can see that the border falls hardest on Gronau — close and
    mid-sized — and barely reaches Münster, which is far enough that distance
    has already done most of the discounting before the border adds any.
    """
    df = distances_from(origin, centres)
    o_side = df.set_index("name").loc[origin, "side"]
    cross = (df["side"] != o_side).to_numpy()
    eff_open = df["distance_km"].to_numpy(dtype=float)
    eff_closed = np.where(cross, np.inf, eff_open)

    pop = df["population"].to_numpy(dtype=float)
    df["open"] = pop / (eff_open + D0_KM) ** beta
    df["at_permeability"] = pop / (
        np.where(cross, eff_open / max(permeability, 1e-6), eff_open) + D0_KM) ** beta
    df["closed"] = pop / (eff_closed + D0_KM) ** beta
    return df


def flow_frame(permeability: float, beta: float = BETA,
               centres: pd.DataFrame = CENTRES, origin: str = ORIGIN) -> pd.DataFrame:
    """Origin-to-centre flows for the map, in the model's own units.

    Used to draw the arcs: line weight is the interaction the model assigns to
    that link at the chosen permeability, so a harder border visibly thins the
    arcs that cross it.
    """
    df = contribution_table(permeability, beta, centres, origin)
    o = df.set_index("name").loc[origin]
    df = df[df["name"] != origin].copy()
    df["o_lat"] = o["lat"]
    df["o_lon"] = o["lon"]
    df["crosses_border"] = df["side"] != o["side"]
    df["flow"] = df["at_permeability"]
    return df
