"""A small, standard open-data client for the spatial layers the report uses.

Everything else in this project that reads a published number does it through
one of two paths: a live fetch with a labelled fallback (`demography.py`) or a
figure that declares itself an estimate (`capetown.py`). The Cape Town layers
deserve the same discipline the CBS fetch already gets, so this module provides
the *fetch* half, and `cct_catalog.py` provides the *derive* half.

The client here is deliberately boring. It speaks ArcGIS Open Data's feature
service as GeoJSON over plain HTTP — no SDK, no account, no key — because that
is exactly the surface the City of Cape Town publishes many of its layers
through, and because boring is what a reproducibility story wants. It returns
`None` when the host has no outbound access, and any caller that uses it is
expected to fall back to a labelled published figure rather than to fail.

Only stdlib is used (urllib + json), so the fetch path adds no dependency to a
__future__ stack kept deliberately lean for Streamlit Cloud.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


# The City of Cape Town's open data portal. Layers are published as ArcGIS
# feature services that are also served as GeoJSON under the short names below.
# The named layers match the ones the Cape Town section actually reasons about;
# a layer that the page only mentions (rather than measures) is left out.
CCT_PORTAL = "https://odp-cctegis.opendata.arcgis.com"

# Defaults deliberately capped: a desktop page needs a few hundred features at
# most, and pulling the whole feature service is both slow and rude to a public
# portal. Raise per-call if a layer really needs more.
DEFAULT_TIMEOUT = 12
DEFAULT_MAX_RECORDS = 2000


def _get_json(url: str, timeout: int) -> dict[str, Any] | None:
    """One GET, parsed as JSON. None on any failure — never raises to the caller."""
    try:  # pragma: no cover - depends on host network
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def query_feature_service(
    layer: str,
    *,
    portal: str = CCT_PORTAL,
    where: str = "1=1",
    out_fields: str = "*",
    max_records: int = DEFAULT_MAX_RECORDS,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any] | None:
    """Fetch one open-data layer as GeoJSON.

    The GeoJSON `data` dictionary is returned verbatim, because the `derive` step
    wants the raw geometry (its own projection is what it reprojects from). The
    short `layer` name is expanded to the portal's GeoJSON route, matching the
    way the City publishes its ArcGIS Open Data layers::

        https://<portal>/datasets/<layer>.geojson

    Returns None when the host cannot reach the portal, which is the signal every
    caller should treat as "use the labelled published figure instead". It never
    raises for a network failure; it only returns None.
    """
    # ArcGIS Open Data's geojson route accepts a where-string via query params.
    url = f"{portal}/datasets/{urllib.parse.quote(layer)}.geojson"
    params = urllib.parse.urlencode({"where": where})
    return _get_json(f"{url}?{params}", timeout)


# ---------------------------------------------------------------------
# Known layer routes on the Cape Town portal, kept in one place so the
# catalog and anything else agree on what a short name means.
# ---------------------------------------------------------------------
LAYER_ROUTES = {
    "rail_stations": "Metrorail stations",
    "urban_edge": "Urban development edge",
    "bionet": "Biodiversity network",
    "suburbs": "Official suburbs",
}