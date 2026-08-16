"""Ingest: Census 2022 population spine for South Africa (national + Cape Town).

This is the normalisation spine for the whole project: every per-capita and
per-worker rate in the Cape Town thread divides by a population denominator,
and that denominator has to come from one place, cited once.

The honest shape of this source matters more than its size. Stats SA does not
publish Census 2022 small-area (ward / sub-place) counts as a bulk download:
the municipal and small-area tables live behind the interactive SuperWEB2 and
ISIbalo portals, which have no machine-readable API. The City of Cape Town's
open-data portal serves some census-derived layers, but its GeoJSON and
feature-service routes return 403 to non-browser clients from this sandbox.

So this module curates the figures that *are* published and citable — the
national population count, households, and the 2011 municipal baseline for
Cape Town — and records, in the sidecar caveats, exactly which granularity is
not bulk-available. It does not invent ward-level numbers. A later task can
replace the curated spine with a real small-area fetch if Stats SA or the City
opens a bulk endpoint; until then the spine is honest about its resolution.

The figures are hand-checked against the sources named in the sidecar. The
module is idempotent: re-running it with the parquet already present is a
no-op, and it never touches the network.

Usage
-----
    python -m kinetiek.ingest.za_census_2022_smallarea
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

CURATED_DIR = Path(__file__).resolve().parents[3] / "data" / "curated"
NAME = "za_census_2022_smallarea"

# ---------------------------------------------------------------------
# Curated figures. Every value here is hand-checked against a published
# source named in the sidecar. Units are stated per column.
# ---------------------------------------------------------------------

# Census 2022 national results, released 10 October 2023 (Stats SA media
# release and Statistical Release P0301.4). Population counts are persons.
SA_POPULATION_2022 = 62_027_503
SA_POPULATION_2011 = 51_770_560
SA_HOUSEHOLDS_2022 = 17_828_778
SA_MEDIAN_AGE_2022 = 28  # years

# Census 2011 municipal baseline for the City of Cape Town, from the Stats SA
# "Statistics by place" page (still the published figure on that page as of
# retrieval). Census 2022 municipal counts are not bulk-published.
CCT_POPULATION_2011 = 3_740_026

# Population group counts, Census 2022 (national), persons.
GROUP_BLACK_AFRICAN = 50_486_856
GROUP_COLOURED = 5_052_349
GROUP_WHITE = 4_504_252
GROUP_ASIAN_INDIAN = 1_697_506

# ---------------------------------------------------------------------
# The curated frame: one row per (geography, census_year, indicator).
# Long form so a single metric column carries every number and the
# `indicator` column names what each number is.
# ---------------------------------------------------------------------

_ROWS: list[dict[str, object]] = [
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "population", "value": SA_POPULATION_2022, "unit": "persons"},
    {"geography": "South Africa", "census_year": 2011,
     "indicator": "population", "value": SA_POPULATION_2011, "unit": "persons"},
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "households", "value": SA_HOUSEHOLDS_2022, "unit": "households"},
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "median_age", "value": SA_MEDIAN_AGE_2022, "unit": "years"},
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "population_black_african", "value": GROUP_BLACK_AFRICAN,
     "unit": "persons"},
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "population_coloured", "value": GROUP_COLOURED,
     "unit": "persons"},
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "population_white", "value": GROUP_WHITE, "unit": "persons"},
    {"geography": "South Africa", "census_year": 2022,
     "indicator": "population_asian_indian", "value": GROUP_ASIAN_INDIAN,
     "unit": "persons"},
    {"geography": "City of Cape Town", "census_year": 2011,
     "indicator": "population", "value": CCT_POPULATION_2011, "unit": "persons"},
]

# Sidecar metadata. `licence` is Stats SA's open-data terms: the census
# results are published under the Statistics Act and Stats SA's data-access
# policy, which permits reuse with attribution. We do not claim a Creative
# Commons licence Stats SA has not granted.
_SIDECAR: dict[str, object] = {
    "name": NAME,
    "source_url": "https://www.statssa.gov.za/?p=16716",
    "publisher": "Statistics South Africa",
    "licence": "Stats SA open data (Statistics Act 6 of 1999); reuse with attribution",
    "retrieved_at": "2026-08-16T00:00:00Z",
    "sha256": "",  # filled after the parquet is written
    "rows": len(_ROWS),
    "columns": {
        "geography": "str",
        "census_year": "i64",
        "indicator": "str",
        "value": "i64",
        "unit": "str",
    },
    "spatial_unit": "national + municipality (no small-area granularity)",
    "temporal_range": ["2011", "2022"],
    "caveats": [
        ("Census 2022 small-area (ward / sub-place) counts are NOT bulk-"
         "downloadable: Stats SA serves them only through the interactive "
         "SuperWEB2 and ISIbalo portals, which have no machine-readable API."),
        ("The City of Cape Town 2022 municipal count is not bulk-published; "
         "only the 2011 municipal baseline (3,740,026) is curated here."),
        ("Census 2022 was assessed 'Fit for Purpose' by the Statistics "
         "Council, but independent demographers (Moultrie & Dorrington 2024) "
         "have raised accuracy concerns, especially for the Western Cape."),
        ("This spine is national + municipal resolution only. Per-capita "
         "rates for Cape Town must use a later small-area source or a "
         "documented estimate until a bulk endpoint opens."),
    ],
    "refresh": ("decennial (next census 2032); re-check for a bulk small-area "
                "endpoint before any per-capita Cape Town metric"),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> pl.DataFrame:
    """Return the curated Census 2022 spine as a polars frame."""
    return pl.DataFrame(_ROWS, schema={
        "geography": pl.Utf8,
        "census_year": pl.Int64,
        "indicator": pl.Utf8,
        "value": pl.Int64,
        "unit": pl.Utf8,
    })


def ingest() -> Path:
    """Write the curated parquet + sidecar. Idempotent: a no-op if present.

    Returns the path to the parquet. Never touches the network.
    """
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    parquet = CURATED_DIR / f"{NAME}.parquet"
    sidecar = CURATED_DIR / f"{NAME}.meta.json"

    if parquet.exists() and sidecar.exists():
        return parquet  # idempotent: already ingested

    frame = build()
    frame.write_parquet(parquet)

    meta = dict(_SIDECAR)
    meta["sha256"] = _sha256(parquet)
    meta["retrieved_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    sidecar.write_text(json.dumps(meta, indent=2) + "\n")
    return parquet


def main(argv: list[str] | None = None) -> int:
    path = ingest()
    print(f"ingested {path} ({len(_ROWS)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
