"""Tests for the Deep Cape Town data pipeline and provenance discipline.

These tests verify the live-fetch-with-fallback behavior documented in the plan:
when the City of Cape Town ArcGIS layers are reachable (online), figures are
derived from real geometry. In offline / CI environments without network,
the catalog falls back to published figures and the evidence table records
the "estimate" class so the page is never silent about provenance.
"""

import pytest

from urban.cct_catalog import Catalog, LAYERS
from urban.provenance import DERIVED, ESTIMATE


# ---------------------------------------------------------------------------
# Live catalog
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cat():
    return Catalog()


def test_catalog_has_required_layers(cat):
    """The catalog must expose all layers cited in its own LAYERS dict."""
    for key in LAYERS:
        assert key in cat.data or key in cat.state


def test_evidence_table_has_core_figures(cat):
    """Core headline figures must always appear in the evidence table."""
    df = cat.evidence()
    figures = set(df["figure"])
    expected = {
        "Inside the urban edge", "Protected nature",
        "Land within 800 m of a station", "Full municipality",
    }
    assert expected.issubset(figures), f"missing: {expected - figures}"


def test_evidence_classes_are_valid(cat):
    """Every figure must carry a valid provenance class."""
    df = cat.evidence()
    valid = {"official", "derived", "engineering", "estimate"}
    assert set(df["class"]).issubset(valid)


# ---------------------------------------------------------------------------
# Offline fallback behavior
# ---------------------------------------------------------------------------

def test_offline_returns_estimates(monkeypatch):
    """When all fetches return None, figures degrade to ESTIMATE with values."""
    import urban.cct_catalog as mod

    monkeypatch.setattr(mod.sources, "query_feature_service",
                        lambda *a, **kw: None)
    cat = Catalog()
    df = cat.evidence()

    # All figures should now be estimates with non-null values.
    assert (df["class"] == ESTIMATE).all()
    assert df["value"].notna().all()


def test_derived_when_data_present(monkeypatch):
    """When layers are returned, the primary figure becomes DERIVED."""
    import urban.cct_catalog as mod
    from shapely.geometry import Polygon, mapping

    # _fetch_layer looks up LAYER_ROUTES to get the human-readable route name.
    route_to_geom = {
        "Urban development edge": Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]),
        "Biodiversity network": Polygon([(0, 0), (0, 0.5), (0.5, 0.5), (0.5, 0)]),
        "Metrorail stations": None,  # return None for stations
    }

    def fake_fetch(route):
        geom = route_to_geom.get(route)
        if geom is None:
            return None
        return {"features": [{"geometry": mapping(geom), "properties": {}}]}

    monkeypatch.setattr(mod.sources, "query_feature_service", fake_fetch)
    cat = Catalog()
    val = cat.area_km2("urban_edge")
    assert val is not None
    assert val.klass == DERIVED


def _gdf(geom):
    import geopandas as gpd
    return gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")


# ---------------------------------------------------------------------------
# Spatial sanity checks (offline-safe)
# ---------------------------------------------------------------------------

def test_urban_edge_under_municipality(monkeypatch):
    """The urban edge cannot be larger than the municipal boundary."""
    import urban.cct_catalog as mod
    from shapely.geometry import Polygon, mapping

    edge = Polygon([(0, 0), (0, 0.1), (0.1, 0.1), (0.1, 0)])    # small, well under 2451 km²
    bionet = Polygon([(0, 0), (0, 0.5), (0.5, 0.5), (0.5, 0)])      # larger bionet

    route_to_geom = {
        "Urban development edge": edge,
        "Biodiversity network": bionet,
        "Metrorail stations": None,
    }

    def fake_fetch(route):
        geom = route_to_geom.get(route)
        if geom is None:
            return None
        return {"features": [{"geometry": mapping(geom), "properties": {}}]}

    monkeypatch.setattr(mod.sources, "query_feature_service", fake_fetch)
    cat = Catalog()
    e = cat.area_km2("urban_edge")
    m = cat.municipal_km2()
    # municipal_km2 always returns the published fallback, so check edge < fallback.
    assert e.value < m.value


def test_station_share_in_range(monkeypatch):
    """Station reach percentage must be within [0, 100]."""
    import urban.cct_catalog as mod
    from shapely.geometry import Polygon, Point, mapping

    edge = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
    station_point = Point(0.5, 0.5)

    route_to_geom = {
        "Urban development edge": edge,
        "Biodiversity network": None,
        "Metrorail stations": station_point,
    }

    def fake_fetch(route):
        geom = route_to_geom.get(route)
        if geom is None:
            return None
        return {"features": [{"geometry": mapping(geom), "properties": {}}]}

    monkeypatch.setattr(mod.sources, "query_feature_service", fake_fetch)
    cat = Catalog()
    share = cat.station_share()
    if share is not None:
        assert 0.0 <= share.value <= 100.0


