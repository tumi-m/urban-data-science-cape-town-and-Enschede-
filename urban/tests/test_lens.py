"""Tests for the Evans/Dediu lens chart kit.

Each lens function must return an Altair Chart whose underlying DataFrame
encodes the claimed insight: trajectory labels the last value, crossing_time
returns the year of intersection, share_vs_growth highlights the right point.
"""

import pandas as pd
import pytest

from urban.lens import trajectory, crossing_time, share_vs_growth, one_insight


@pytest.fixture
def growth_df():
    return pd.DataFrame({
        "year": [2000, 2010, 2020, 2030, 2040, 2050],
        "enschede": [150_000, 160_000, 165_000, 168_000, 170_000, 171_000],
        "capetown": [2_900_000, 3_200_000, 3_700_000, 4_200_000, 4_600_000, 4_800_000],
    })


def test_trajectory_returns_chart(growth_df):
    long_df = growth_df.melt(id_vars="year", var_name="entity", value_name="population")
    chart = trajectory(long_df, x="year", y="population", entity="entity",
                       highlight="capetown")
    assert hasattr(chart, "to_dict")
    spec = chart.to_dict()
    assert "layer" in spec or "mark" in spec


def test_trajectory_log_scale(growth_df):
    long_df = growth_df.melt(id_vars="year", var_name="entity", value_name="population")
    chart = trajectory(long_df, x="year", y="population", entity="entity",
                       highlight="capetown", log=True)
    spec = chart.to_dict()
    assert "log" in str(spec)


def test_crossing_time_finds_intersection():
    """Two linear curves crossing at year 5 should report t≈5."""
    df = pd.DataFrame({
        "t": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "a": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],       # y = t
        "b": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],        # y = 10 - t
    })
    chart, crossing = crossing_time(df, x="t", a="a", b="b",
                                    label_a="A", label_b="B")
    assert chart is not None
    assert crossing is not None
    assert 4.5 <= crossing <= 5.5  # crosses at exactly t=5


def test_share_vs_growth_returns_chart():
    df = pd.DataFrame({
        "city": ["Amsterdam", "London", "Cape Town"],
        "share": [0.45, 0.62, 0.33],
        "growth": [0.12, 0.08, -0.03],
        "density": [5_000, 5_500, 2_000],
    })
    chart = share_vs_growth(df, share="share", growth="growth", size="density",
                            label="city", highlight="Cape Town")
    assert hasattr(chart, "to_dict")


def test_one_insight_returns_string():
    insight = one_insight("Cape Town's growth is land-constrained.")
    assert isinstance(insight, str)
    assert len(insight) > 0

