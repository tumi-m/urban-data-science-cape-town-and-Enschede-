"""Population, density and the flows that drive them.

The data layer is pluggable by design. `load_population()` will fetch the real
municipal series from StatLine when the host has outbound access, and otherwise
falls back to a reconstructed series that carries the right shape and the wrong
third digit. Which of the two is in play is returned alongside the frame, and
every chart drawn from it says so.

That distinction matters more here than anywhere else in the project, because a
population series is the input to a forecast, and a forecast looks equally
authoritative whichever series produced it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .provenance import OFFICIAL, RECONSTRUCTED, SYNTHETIC, Series

# StatLine table for regional population by municipality. Kept here so the
# fetch path is real code rather than a promise: the only thing missing on a
# sandboxed host is the network.
CBS_POPULATION_TABLE = "37230ned"
CBS_ENDPOINT = "https://opendata.cbs.nl/ODataApi/odata/{table}/TypedDataSet"
ENSCHEDE_MUNICIPALITY_CODE = "GM0153"


# ---------------------------------------------------------------------
# Reconstructed baseline
# ---------------------------------------------------------------------
#
# Municipal population at decade marks and recent years. Enschede's post-war
# path has three phases that any model of it has to reproduce: rapid growth
# through the textile boom to the early 1960s, a long plateau through the
# industry's collapse and the city's reinvention around the university, and
# slow renewed growth since the 1990s carried largely by students and by
# international migration.
#
# The plateau is the interesting part and it is why a naive trend model
# extrapolates badly: the series is not one process, it is three.

_POPULATION_ANCHORS = {
    1950: 105_000,
    1960: 124_000,
    1970: 137_000,
    1975: 141_000,
    1980: 144_000,
    1985: 144_500,
    1990: 146_000,
    1995: 147_500,
    2000: 150_000,
    2005: 154_000,
    2010: 157_000,
    2015: 158_000,
    2020: 159_500,
    2022: 160_500,
    2024: 161_000,
}

# Components of change, as annual averages per period. Enschede's natural
# increase turned marginal decades ago; what moves the total is migration, and
# the two migration terms point in opposite directions — the city loses
# domestic migrants (graduates leaving for the Randstad) and gains
# international ones.
_FLOW_PERIODS = [
    # (start, end, natural, domestic_net, international_net) per year
    (1950, 1965, 2100, -300, 150),
    (1965, 1975, 1500, -450, 250),
    (1975, 1985, 700, -750, 200),
    (1985, 1995, 400, -500, 350),
    (1995, 2005, 300, -650, 800),
    (2005, 2015, 150, -900, 900),
    (2015, 2025, -50, -800, 1100),
]


def _reconstructed_population() -> pd.DataFrame:
    """Interpolate the anchors onto every year, with a little structure.

    Straight-line interpolation between anchors would give a series with no
    year-to-year variation at all, which flatters every forecasting model that
    touches it — a model that cannot be wrong about noise looks better than it
    is. A small deterministic wobble is added so backtests have something to
    fail on. It is deterministic, not random, so results are reproducible.
    """
    years = np.arange(min(_POPULATION_ANCHORS), max(_POPULATION_ANCHORS) + 1)
    anchor_years = np.array(sorted(_POPULATION_ANCHORS))
    anchor_values = np.array([_POPULATION_ANCHORS[y] for y in anchor_years], dtype=float)

    base = np.interp(years, anchor_years, anchor_values)
    wobble = 380 * np.sin(years * 1.7) + 210 * np.sin(years * 0.6 + 1.3)
    return pd.DataFrame({"year": years, "population": np.round(base + wobble).astype(int)})


def _try_cbs() -> pd.DataFrame | None:
    """Fetch the real series. Returns None when the host cannot reach StatLine.

    Deliberately short-timeout and failure-tolerant: an unavailable statistics
    office should degrade the app to a labelled fallback, not break it.
    """
    try:  # pragma: no cover - depends on host network
        import json
        import urllib.request

        url = (
            CBS_ENDPOINT.format(table=CBS_POPULATION_TABLE)
            + f"?$filter=RegioS eq '{ENSCHEDE_MUNICIPALITY_CODE}'"
            + "&$select=Perioden,BevolkingOp1Januari_1"
        )
        with urllib.request.urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = [
            {
                "year": int(str(r["Perioden"])[:4]),
                "population": int(r["BevolkingOp1Januari_1"]),
            }
            for r in payload.get("value", [])
            if r.get("BevolkingOp1Januari_1") is not None
        ]
        if len(rows) < 20:
            return None
        return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    except Exception:
        return None


@dataclass
class PopulationData:
    frame: pd.DataFrame
    series: Series

    @property
    def is_real(self) -> bool:
        return self.series.klass == OFFICIAL


def load_population() -> PopulationData:
    """The municipal population series, real if reachable and labelled if not."""
    live = _try_cbs()
    if live is not None:
        return PopulationData(
            live,
            Series("Population of Enschede", OFFICIAL, "CBS StatLine 37230ned",
                   "Fetched live."),
        )
    return PopulationData(
        _reconstructed_population(),
        Series(
            "Population of Enschede", RECONSTRUCTED, "Reconstructed from decade anchors",
            "StatLine unreachable from this host; shape and magnitude are right, individual "
            "years are not.",
        ),
    )


def components_of_change(years: np.ndarray) -> pd.DataFrame:
    """Natural change, domestic net migration and international net migration.

    Reconstructed period averages, expanded to annual. The reason to carry the
    components rather than only the total is that they behave differently under
    projection: natural change is demographic momentum and moves slowly,
    domestic migration tracks the regional labour market, and international
    migration is the term that policy and geopolitics move fastest.
    """
    rows = []
    for year in years:
        band = next(
            (b for b in _FLOW_PERIODS if b[0] <= year < b[1]),
            _FLOW_PERIODS[-1],
        )
        _, _, natural, domestic, international = band
        drift = 1 + 0.04 * np.sin(year * 0.9)
        rows.append({
            "year": int(year),
            "Natural change": round(natural * drift),
            "Net domestic migration": round(domestic * drift),
            "Net international migration": round(international * drift),
        })
    return pd.DataFrame(rows)


def density_series(population: pd.DataFrame, built_up_km2_by_year: pd.Series | None = None,
                   land_area_km2: float = 140.0) -> pd.DataFrame:
    """Two densities, because the difference between them is the whole story.

    Gross density divides by the municipality, most of which is farmland and
    protected habitat and always will be. Built-up density divides by the area
    that is actually urban. A city can hold gross density flat while built-up
    density falls — that is what sprawl is — and only the second number tells
    you whether the place is getting denser to live in.
    """
    df = population.copy()
    df["gross_density"] = df["population"] / land_area_km2
    if built_up_km2_by_year is not None:
        built = built_up_km2_by_year.reindex(df["year"]).to_numpy()
    else:
        # Built-up area grew faster than population for most of the century:
        # the classic post-war decoupling of people from land.
        span = df["year"].max() - df["year"].min()
        t = (df["year"] - df["year"].min()) / max(span, 1)
        built = 18 + 25 * t**0.75
    df["built_up_km2"] = built
    df["built_up_density"] = df["population"] / df["built_up_km2"]
    return df


# ---------------------------------------------------------------------
# Comparators
# ---------------------------------------------------------------------
#
# A single city's line means little without something to read it against. These
# are the other Twente centres plus two national reference points, indexed so
# the comparison is about rate rather than size — the Our World in Data habit of
# indexing to a base year, which is also the only fair way to put a city of
# 160,000 beside one of 900,000.

_COMPARATOR_SHAPES = {
    "Enschede": (1.00, 0.50),
    "Hengelo": (0.72, 0.28),
    "Almelo": (0.66, 0.34),
    "Netherlands": (1.00, 1.00),
    "Amsterdam": (0.55, 1.55),
}


def comparators(years: np.ndarray) -> pd.DataFrame:
    """Indexed population paths for the comparison chart.

    Synthetic shapes with the right qualitative behaviour: Twente's industrial
    towns plateau after the textile collapse, the national line grows steadily,
    and Amsterdam turns sharply upward after 1985 when the Randstad's pull
    reasserts itself. Useful for showing what a plateau looks like against a
    growth path; not usable as evidence about any of these places.
    """
    rows = []
    t = (years - years.min()) / max(years.max() - years.min(), 1)
    for name, (early, late) in _COMPARATOR_SHAPES.items():
        # Two logistic phases: post-war growth, then a regime change in the 1980s.
        phase1 = early * 1 / (1 + np.exp(-8 * (t - 0.18)))
        phase2 = late * 1 / (1 + np.exp(-9 * (t - 0.72)))
        index = 100 * (1 + 0.42 * (phase1 + phase2))
        for year, value in zip(years, index):
            rows.append({"entity": name, "year": int(year), "index": round(float(value), 2)})
    return pd.DataFrame(rows)


COMPARATOR_SERIES = Series(
    "Indexed population paths", SYNTHETIC, "Generated shapes",
    "Qualitative behaviour only — a plateau against a growth path. Not evidence about any "
    "named city.",
)

FLOW_SERIES = Series(
    "Components of population change", RECONSTRUCTED, "Reconstructed period averages",
    "Signs and rough magnitudes are right; annual values are interpolated.",
)
