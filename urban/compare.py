"""The layer that makes this one report instead of two.

The complaint that produced this module was that the project read as an
Enschede study with Cape Town added as a footnote. It did, and the reason was
structural rather than cosmetic: the navigation was organised by city, so the
reader was asked to hold one city in their head, then start again with the
other. Nothing was ever put beside anything.

Everything here exists to put the two cities in the same frame:

  - `city_switch` is a visible control at the top of the page, not a dropdown
    buried in a sidebar. It has a **Both** setting, and the analytical sections
    default to it.
  - `ledger_chart` runs both cities through one arithmetic — every square
    kilometre, and what happens to it — and shows them ending in different
    places for different reasons. This is the report's whole argument as a
    single figure.
  - `scorecard` is the same twelve measures for both cities, always in the same
    order, so a reader learns the shape once.
  - `dual_lines` draws one chart with both cities on it rather than two charts
    the reader has to compare from memory.

The rule the module follows: if a number exists for both cities, it is shown
for both cities, in one place, at the same time.
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from . import cities
from .theme import GRID, INK, INK_2, INK_3, RULE, SERIES, SURFACE, style

BOTH = "Both"

# Constraint kinds, coloured by what they mean rather than by order of
# appearance: grey for land already spoken for, orange for a limit that removes
# land, blue for what survives.
LEDGER_COLOURS = {
    "total": INK,
    "used": "#b9b6ae",
    "hard": SERIES[1],
    "soft": "#f3b39a",
    "result": SERIES[0],
    "permitted": SERIES[2],
}


def city_switch(key: str, *, allow_both: bool = True, default: str = BOTH) -> list:
    """The control that decides which city the section is about.

    A segmented control at the top of the content, because the previous version
    of this was a sidebar dropdown and the first thing the reader said was that
    there were no models for Cape Town. There were. They could not be found.
    """
    options = [c.name for c in cities.CITIES.values()]
    if allow_both:
        options = options + [BOTH]
    if key not in st.session_state:
        st.session_state[key] = default if default in options else options[0]

    choice = st.segmented_control(
        "City", options, key=key, label_visibility="collapsed",
        help="Every model in this section runs on whichever city is selected.")
    if choice is None:                      # deselected — fall back, never blank
        choice = st.session_state[key] = default

    if choice == BOTH:
        return list(cities.CITIES.values())
    return [cities.pick(choice)]


def accent_scale(selected: list) -> alt.Scale:
    return alt.Scale(domain=[c.name for c in selected],
                     range=[c.accent for c in selected])


# ---------------------------------------------------------------------
# The land ledger
# ---------------------------------------------------------------------

def ledger_chart(city, height: int = 300) -> alt.Chart:
    """One city's land, from the municipal boundary down to what may be built on.

    A waterfall rather than a stacked bar, because the question is sequential:
    each row removes something, and the reader wants to see where the total
    stopped being large.
    """
    df = city.ledger().copy()
    order = df["step"].tolist()
    df["label"] = [f"{v:,.0f}" if k in ("total", "result", "permitted")
                   else f"{v:+,.0f}" for v, k in zip(df["value"], df["kind"])]

    bars = (
        alt.Chart(df)
        .mark_bar(height=26, cornerRadius=2)
        .encode(
            y=alt.Y("step:N", sort=order, title=None,
                    axis=alt.Axis(labelLimit=220, labelFontSize=11)),
            x=alt.X("start:Q", title="km²",
                    axis=alt.Axis(format="~s", grid=True, gridColor=GRID)),
            x2="end:Q",
            color=alt.Color("kind:N",
                            scale=alt.Scale(domain=list(LEDGER_COLOURS),
                                            range=list(LEDGER_COLOURS.values())),
                            legend=None),
            tooltip=["step", alt.Tooltip("value:Q", format=",.0f"),
                     alt.Tooltip("running:Q", format=",.0f", title="running total"),
                     "note"],
        )
    )
    # Value at the end of each bar, in text colour rather than the series colour.
    text = (
        alt.Chart(df)
        .mark_text(align="left", dx=7, fontSize=11, color=INK_2)
        .encode(y=alt.Y("step:N", sort=order),
                x=alt.X("running:Q"), text="label:N")
    )
    return style(alt.layer(bars, text)
                 .properties(height=height, padding={"right": 54}))


def ledger_pair() -> None:
    """Both ledgers, side by side, with the punchline stated under each.

    The two cities are deliberately *not* put on a shared axis here. Cape Town
    is seventeen times the area, so a shared axis would compress Enschede into a
    sliver and the reader would learn only that one city is bigger, which is not
    the finding. The finding is that the ledgers have the same structure and
    stop for different reasons, and that survives separate axes.
    """
    all_cities = list(cities.CITIES.values())
    cols = st.columns(len(all_cities), gap="large")
    for col, city in zip(cols, all_cities):
        with col:
            st.markdown(
                f"<div class='ledger-head' style='--accent:{city.accent}'>"
                f"<span class='ledger-city'>{city.name}</span>"
                f"<span class='ledger-sub'>{city.country}</span></div>",
                unsafe_allow_html=True)
            st.altair_chart(ledger_chart(city), width="stretch",
                            key=f"ledger_{city.key}")
            st.markdown(
                f"<div class='ledger-note'>{city.permitted_note}</div>",
                unsafe_allow_html=True)


# ---------------------------------------------------------------------
# The scorecard
# ---------------------------------------------------------------------

def scorecard_frame() -> pd.DataFrame:
    """The same measures for both cities, computed rather than transcribed."""
    rows = []
    for c in cities.CITIES.values():
        frame, _ = c.population()
        first, last = frame.iloc[0], frame.iloc[-1]
        ledger = c.ledger()
        physical = float(ledger[ledger["kind"] == "result"]["value"].iloc[0])
        built = float(-ledger[ledger["step"] == "Already built on"]["value"].iloc[0])
        rows.append({
            "City": c.name,
            "Country": c.country,
            "Population": last["population"],
            "Population 1950": first["population"],
            "Growth since 1950": last["population"] / first["population"] - 1,
            "Added since 1950": last["population"] - first["population"],
            "Municipal area, km²": c.land_area_km2,
            "Built-up, km²": built,
            "Land physically left, km²": physical,
            "Land permitted, km²": c.permitted_km2,
            "Density per built km²": last["population"] / built,
            "Years of growth left": np.nan,
            "What stops building": c.binding_constraint,
        })
    df = pd.DataFrame(rows)

    # How long the remaining permitted land lasts at the last decade's rate of
    # growth, at each city's own current built density. The single most useful
    # number in the report, and it is only meaningful because both cities are
    # run through the same ledger above.
    for i, c in enumerate(cities.CITIES.values()):
        frame, _ = c.population()
        recent = frame[frame["year"] >= frame["year"].max() - 10]
        per_year = (recent["population"].iloc[-1] - recent["population"].iloc[0]) / 10
        permitted = df.loc[i, "Land permitted, km²"]
        density = df.loc[i, "Density per built km²"]
        if per_year <= 0 or not permitted:
            df.loc[i, "Years of growth left"] = 0.0 if per_year > 0 else np.inf
        else:
            df.loc[i, "Years of growth left"] = permitted * density / per_year
    return df


def scorecard() -> None:
    """The comparison table, as a designed block rather than a dataframe dump."""
    df = scorecard_frame()
    accents = [cities.pick(name).accent for name in df["City"]]

    measures = [
        ("Population today", "{:,.0f}", "Population"),
        ("Population in 1950", "{:,.0f}", "Population 1950"),
        ("Growth since 1950", "{:+.0%}", "Growth since 1950"),
        ("People added since 1950", "{:+,.0f}", "Added since 1950"),
        ("Municipal area", "{:,.0f} km²", "Municipal area, km²"),
        ("Already built on", "{:,.0f} km²", "Built-up, km²"),
        ("Land physically left", "{:,.0f} km²", "Land physically left, km²"),
        ("Land it may build on", "{:,.0f} km²", "Land permitted, km²"),
        ("People per built km²", "{:,.0f}", "Density per built km²"),
    ]
    html = ["<table class='scorecard'><thead><tr><th></th>"]
    for row, accent in zip(df.itertuples(), accents):
        html.append(f"<th style='--accent:{accent}'>{row.City}</th>")
    html.append("</tr></thead><tbody>")
    for label, fmt, col in measures:
        cells = "".join(f"<td>{fmt.format(v)}</td>" for v in df[col])
        html.append(f"<tr><td class='m'>{label}</td>{cells}</tr>")

    def years(v):
        return "—" if not np.isfinite(v) else f"{v:,.0f} years"

    cells = "".join(f"<td>{years(v)}</td>" for v in df["Years of growth left"])
    html.append(f"<tr class='hi'><td class='m'>Growth the remaining land allows</td>"
                f"{cells}</tr>")
    cells = "".join(f"<td class='w'>{v}</td>" for v in df["What stops building"])
    html.append(f"<tr><td class='m'>What stops building</td>{cells}</tr>")
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)

    # Density has two defensible denominators and this report uses both, in
    # different places, for good reasons. Saying so here is cheaper than a
    # reader finding two different numbers for "Cape Town's density" three
    # sections apart and concluding one of them is wrong.
    st.caption(
        f"**On density.** The row above divides by land *already built on* — "
        f"{b['Built-up, km²']:,.0f} km² for Cape Town, {a['Built-up, km²']:,.0f} km² for "
        f"Enschede. The Cape Town section quotes {4_800_000 / 895:,.0f} per km² instead, "
        f"because it divides by the whole 895 km² inside the urban edge, including the 251 km² "
        f"not yet developed. Both are right; they answer different questions. The figure here "
        f"is the one that compares across cities, because 'land inside a development edge' is "
        f"a Cape Town legal category with no Enschede equivalent."
    )


# ---------------------------------------------------------------------
# Dual-city chart forms
# ---------------------------------------------------------------------

def dual_lines(df: pd.DataFrame, x: str, y: str, *, x_title: str, y_title: str,
               selected: list, y_format: str = ",.0f", height: int = 330,
               log: bool = False, entity: str = "city") -> alt.Chart:
    """Both cities on one set of axes, labelled at the line."""
    scale = alt.Scale(type="log") if log else alt.Scale(zero=False)
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format="d", grid=False)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=scale,
                axis=alt.Axis(format=y_format, grid=True, gridColor=GRID)),
        color=alt.Color(f"{entity}:N", scale=accent_scale(selected), legend=None),
    )
    line = base.mark_line(strokeWidth=2.4, strokeCap="round")
    ends = df.sort_values(x).groupby(entity, as_index=False).tail(1)
    dot = alt.Chart(ends).mark_point(
        filled=True, size=76, stroke=SURFACE, strokeWidth=2).encode(
        x=f"{x}:Q", y=f"{y}:Q",
        color=alt.Color(f"{entity}:N", scale=accent_scale(selected), legend=None))
    tag = alt.Chart(ends).mark_text(
        align="left", dx=9, fontSize=11, fontWeight="bold").encode(
        x=f"{x}:Q", y=f"{y}:Q", text=f"{entity}:N",
        color=alt.Color(f"{entity}:N", scale=accent_scale(selected), legend=None))
    return style(alt.layer(line, dot, tag)
                 .properties(height=height, padding={"right": 76}))


def facet_rasters(render, selected: list) -> None:
    """The same map for each selected city, side by side.

    Used wherever a figure is per-city and cannot share an axis — a grid of
    cells, for instance, where the two cities are at different scales. Side by
    side in one row is still one figure, and the reader compares without
    scrolling.
    """
    cols = st.columns(len(selected), gap="large")
    for col, city in zip(cols, selected):
        with col:
            st.markdown(
                f"<div class='mini-head' style='--accent:{city.accent}'>{city.name}</div>",
                unsafe_allow_html=True)
            render(city)


def city_header(city) -> None:
    """A coloured rule and the city's name, above a per-city block."""
    st.markdown(
        f"<div class='mini-head' style='--accent:{city.accent}'>{city.name}</div>",
        unsafe_allow_html=True)
