"""The registry: every city passes the same gates.

The `City` record is the project's promise that a city is not a special case:
whatever is registered in `CITIES` gets the ledger, the grid, the forecasting
suite and the comparison pages. That promise is only worth what its tests
enforce, so these tests iterate the registry rather than naming cities —
except where a named city's *shape* is the finding (Amsterdam's U, the
Johannesburg boundary artefact), because those shapes are exactly what the
forecasting pages ask the models to explain.
"""

import numpy as np
import pytest

from urban import cities, compare, spatial
from urban.forecast import fit_and_forecast, MODELS
from urban.provenance import OFFICIAL, RECONSTRUCTED


# ---------------------------------------------------------------------
# Registry integrity
# ---------------------------------------------------------------------

def test_four_cities_registered():
    assert set(cities.CITIES) == {"Enschede", "Cape Town",
                                  "Johannesburg", "Amsterdam"}


def test_keys_and_accents_unique():
    keys = [c.key for c in cities.CITIES.values()]
    accents = [c.accent for c in cities.CITIES.values()]
    assert len(set(keys)) == len(keys)
    assert len(set(accents)) == len(accents)


@pytest.mark.parametrize("name", list(cities.CITIES))
def test_population_frame_shape(name):
    frame, series = cities.pick(name).population()
    assert list(frame.columns) == ["year", "population"]
    assert frame["population"].gt(0).all()
    assert frame["year"].is_monotonic_increasing
    assert len(frame) >= 40          # a real history, not a handful of anchors
    assert series.source and series.note          # provenance is never empty


@pytest.mark.parametrize("name", list(cities.CITIES))
def test_ledger_arithmetic(name):
    city = cities.pick(name)
    ledger = city.ledger()
    total = float(ledger[ledger["kind"] == "total"]["value"].iloc[0])
    result = float(ledger[ledger["kind"] == "result"]["value"].iloc[0])
    subtractions = float(ledger[ledger["kind"].isin(["used", "hard"])]["value"].sum())
    assert result == pytest.approx(total + subtractions)
    assert 0 < result < total
    assert city.permitted_km2 <= result       # the law cannot permit more than exists
    # The scorecard reads these two rows by name — a city without them
    # silently breaks the comparison table.
    assert (ledger["step"] == "Already built on").any()
    assert (ledger["kind"] == "permitted").any()


@pytest.mark.parametrize("name", list(cities.CITIES))
def test_sites_inside_frame(name):
    city = cities.pick(name)
    sites = city.sites()
    e = city.geometry.extent_km
    assert sites["x"].abs().max() <= e
    assert sites["y"].abs().max() <= e


@pytest.mark.parametrize("name", list(cities.CITIES))
def test_grid_builds_and_leaves_room(name):
    """build_grid works for every geometry and the constraints actually bite."""
    geo = cities.pick(name).geometry
    assert geo.extent_km >= geo.radius_km + geo.edge_margin_km
    grid = spatial.build_grid(geometry=geo)
    assert len(grid) > 100
    assert grid["developable"].sum() < len(grid)     # something is withheld
    assert grid["developable"].sum() > 0             # and not everything is


# ---------------------------------------------------------------------
# The two new shapes
# ---------------------------------------------------------------------

def test_amsterdam_is_a_u_shape():
    """The only registered series with a genuine decline and recovery."""
    frame, series = cities.pick("Amsterdam").population()
    assert series.klass == OFFICIAL
    i_min = frame["population"].idxmin()
    trough_year = frame.loc[i_min, "year"]
    assert 1980 <= trough_year <= 1990            # the mid-1980s trough
    pop = frame["population"]
    assert pop.iloc[-1] > pop.iloc[0]             # net growth over the whole span
    assert pop.min() < pop.iloc[0]                # but it fell below its 1950 level
    # and it recovered: the last value is above the post-war peak
    assert pop.iloc[-1] > 870_000


def test_johannesburg_dip_is_only_the_boundary_artefact():
    """One non-monotone stretch — the 1996 amalgamation — in a long climb."""
    frame, series = cities.pick("Johannesburg").population()
    assert series.klass == RECONSTRUCTED
    pop = frame["population"]
    drops = (pop.diff() < 0)
    drop_years = frame.loc[drops, "year"]
    # every year that falls lies inside the 1991–1996 boundary window
    assert drop_years.between(1991, 1996).all()
    # after the boundary settles the series never falls again
    assert pop[frame["year"] >= 1996].is_monotonic_increasing


@pytest.mark.parametrize("name", ["Johannesburg", "Amsterdam"])
def test_linear_forecast_runs_on_new_cities(name):
    """The forecast machinery is registered-city-agnostic; prove it on both."""
    frame, _ = cities.pick(name).population()
    target = frame["year"].max() + 26
    fit = fit_and_forecast(frame, MODELS["linear"], {}, horizon_year=target)
    out = fit.forecast
    assert out["year"].min() == frame["year"].max() + 1
    assert out["year"].max() == target
    assert np.isfinite(out["population"]).all()


# ---------------------------------------------------------------------
# The comparison layer scales
# ---------------------------------------------------------------------

def test_scorecard_covers_all_registered_cities():
    df = compare.scorecard_frame()
    assert list(df["City"]) == list(cities.CITIES)
    # Johannesburg is the land-rich control case: it must be left with more
    # permitted land than land-poor Amsterdam or Cape Town.
    permitted = dict(zip(df["City"], df["Land permitted, km²"]))
    assert permitted["Johannesburg"] > permitted["Amsterdam"]
    assert permitted["Johannesburg"] > permitted["Cape Town"]
    assert df["Growth since 1950"].notna().all()
