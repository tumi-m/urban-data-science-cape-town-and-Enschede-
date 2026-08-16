"""Unit tests for the Census 2022 spine ingest.

Hand-checked expected values: the national population count, households, and
the 2011 Cape Town baseline are the published figures from Stats SA's Census
2022 release (10 October 2023) and its "Statistics by place" page.
"""

from __future__ import annotations

import polars as pl

from kinetiek.ingest import za_census_2022_smallarea as mod


def _value(frame: pl.DataFrame, geography: str, year: int, indicator: str) -> int:
    row = frame.filter(
        (pl.col("geography") == geography)
        & (pl.col("census_year") == year)
        & (pl.col("indicator") == indicator)
    )
    assert row.height == 1, f"expected one row for {geography}/{year}/{indicator}"
    return int(row["value"][0])


def test_build_has_expected_shape():
    frame = mod.build()
    assert frame.columns == ["geography", "census_year", "indicator", "value", "unit"]
    assert frame.height == 9


def test_sa_population_2022():
    assert _value(mod.build(), "South Africa", 2022, "population") == 62_027_503


def test_sa_population_2011():
    assert _value(mod.build(), "South Africa", 2011, "population") == 51_770_560


def test_sa_households_2022():
    assert _value(mod.build(), "South Africa", 2022, "households") == 17_828_778


def test_sa_median_age_2022():
    assert _value(mod.build(), "South Africa", 2022, "median_age") == 28


def test_cct_population_2011():
    assert _value(mod.build(), "City of Cape Town", 2011, "population") == 3_740_026


def test_population_growth_is_positive():
    """The 2022 national count exceeds the 2011 count (a sanity check on the
    spine, not a re-derivation of the published growth rate)."""
    p2022 = _value(mod.build(), "South Africa", 2022, "population")
    p2011 = _value(mod.build(), "South Africa", 2011, "population")
    assert p2022 > p2011
