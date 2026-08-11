"""A workbench for running two futures against each other.

Every other simulation section in this report runs one scenario and describes
it. That is the weaker use of a model like this. A cellular automaton over a
synthetic grid cannot tell you what a city will look like in 2050, and any page
that shows one run invites the reader to believe it can.

What it can do is price a decision, by running two futures that differ in one
place and reporting the gap. That is what this page is for: pick the levers on
the left, pick different ones on the right, and read the difference. The
absolute numbers in either column are worth very little. The difference between
them is worth something, because the made-up parts are identical on both sides
and cancel.

Four kinds of lever are on the same page because in a real city they are the
same decision:

  - **How many people** — which population model, and to what year.
  - **Where they go** — densification versus conversion, station weighting, and
    the density new development is built at.
  - **Whether the constraints hold** — the protected mass and the hard edge, on
    or off. This is the one that prices the constraint in hectares.
  - **How they travel** — the parking, transit and e-bike levers from the
    behavioural section, which feed car-kilometres and therefore the nitrogen
    account that the Enschede sections show is what actually blocks building.
"""

from __future__ import annotations

from dataclasses import dataclass

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from . import animate
from . import behaviour as bh
from . import cities
from . import owid
from . import spatial as sp
from .forecast import MODELS, fit_and_forecast
from .theme import GRID, INK, INK_2, INK_3, SEQUENTIAL, SERIES, SURFACE, style
from .ui import figure, header, note, provenance, stats, values_table


@dataclass
class Levers:
    """One scenario, as the reader set it."""

    label: str
    model_key: str
    horizon: int
    densification: float
    respect_constraints: bool
    station_pull: float
    persons_per_ha: float
    parking: float
    transit: float
    ebike: float

    def policy(self) -> bh.Policy:
        return bh.Policy(
            self.label,
            parking_charge_per_trip=self.parking,
            transit_speed_multiplier=self.transit,
            ebike_subsidy=self.ebike,
        )


PRESETS: dict[str, dict] = {
    "Today, continued": dict(
        densification=0.60, respect_constraints=True, station_pull=1.0,
        persons_per_ha=65.0, parking=0.0, transit=1.0, ebike=0.0),
    "Build outward": dict(
        densification=0.20, respect_constraints=True, station_pull=0.3,
        persons_per_ha=35.0, parking=0.0, transit=1.0, ebike=0.0),
    "Build inward, price the car": dict(
        densification=0.90, respect_constraints=True, station_pull=2.2,
        persons_per_ha=110.0, parking=2.50, transit=1.35, ebike=400.0),
    "Ignore the constraints": dict(
        densification=0.40, respect_constraints=False, station_pull=0.8,
        persons_per_ha=55.0, parking=0.0, transit=1.0, ebike=0.0),
}


def _controls(side: str, default_preset: str, city) -> Levers:
    """One column of levers. Two of these make the comparison."""
    st.markdown(f"**Scenario {side}**")
    preset = st.selectbox("Start from", list(PRESETS), key=f"sim_{side}_preset",
                          index=list(PRESETS).index(default_preset))
    p = PRESETS[preset]

    with st.expander("Adjust", expanded=False):
        model_key = st.selectbox(
            "Population model", list(MODELS), key=f"sim_{side}_model",
            format_func=lambda k: MODELS[k].label,
            index=list(MODELS).index("logistic"))
        horizon = st.slider("Run to", 2030, 2070, 2050, 5, key=f"sim_{side}_hz")
        dens = st.slider("Growth absorbed by densification", 0.0, 1.0,
                         float(p["densification"]), 0.05, key=f"sim_{side}_dens",
                         help="The rest is converted from unbuilt land.")
        pph = st.slider("Density of new development, persons/ha", 20, 160,
                        int(p["persons_per_ha"]), 5, key=f"sim_{side}_pph")
        pull = st.slider("Station-oriented weighting", 0.0, 3.0,
                         float(p["station_pull"]), 0.1, key=f"sim_{side}_pull")
        keep = st.checkbox("Respect the constraints",
                           value=bool(p["respect_constraints"]),
                           key=f"sim_{side}_keep",
                           help="Off means the protected mass and the hard edge are "
                                "available for building. The difference is the price "
                                "of the constraint, in hectares.")
        st.caption("Travel policy")
        parking = st.slider("Parking charge, € per car trip", 0.0, 8.0,
                            float(p["parking"]), 0.25, key=f"sim_{side}_park")
        transit = st.slider("Transit speed multiplier", 0.8, 1.6,
                            float(p["transit"]), 0.05, key=f"sim_{side}_tr")
        ebike = st.slider("E-bike subsidy, € per year", 0.0, 600.0,
                          float(p["ebike"]), 50.0, key=f"sim_{side}_eb")

    return Levers(f"{side} · {preset}", model_key, horizon, dens, keep, pull,
                  pph, parking, transit, ebike)


@st.cache_data(show_spinner=False)
def _population(city_name: str):
    return cities.pick(city_name).population()[0]


@st.cache_data(show_spinner="Fitting the development model…")
def _developable(city_name: str):
    grid = sp.build_grid(geometry=cities.pick(city_name).geometry)
    return sp.fit_development(grid, "gbm", {}).grid


@st.cache_data(show_spinner="Running the scenario…")
def _run(city_name: str, lev_dict: dict):
    """One scenario end to end. Cached on the levers, so only what moved reruns."""
    lev = Levers(**lev_dict)
    city = cities.pick(city_name)
    frame = _population(city_name)
    grid = _developable(city_name)

    spec = MODELS[lev.model_key]
    fit = fit_and_forecast(frame, spec, {p.key: p.default for p in spec.params},
                           lev.horizon)
    path = pd.concat([frame.tail(1)[["year", "population"]],
                      fit.forecast[["year", "population"]]], ignore_index=True)

    result = sp.simulate(grid, path, lev.densification, lev.respect_constraints,
                         lev.station_pull, lev.persons_per_ha,
                         spacing_km=city.geometry.spacing_km)

    outcome = bh.simulate(lev.policy(), n_households=1500)
    return result.yearly, result.frames, {
        "car_km": outcome.mean_car_km,
        "car_share": float(outcome.modes.set_index("mode").loc["Car", "share"]),
        "nox_kg": outcome.nox_kg_per_household,
    }


def page_simulator() -> None:
    with st.sidebar:
        st.markdown("#### City")
        city_name = st.selectbox("Analyse", list(cities.CITIES), key="sim_city",
                                 label_visibility="collapsed")
    city = cities.pick(city_name)

    header(
        "14 · Workbench",
        "Run two futures against each other",
        f"Pick a set of decisions on the left and a different set on the right, and read the "
        f"gap. The absolute numbers in either column are close to meaningless — the grid is "
        f"made up and the labels were generated from it. The *difference* is not, because "
        f"everything invented is identical on both sides and cancels. "
        f"Currently modelling {city.name}: {city.binding_constraint}",
    )

    st.warning(
        "**This is a workbench, not a forecast.** Nothing here predicts what either city will "
        "look like. It prices decisions against each other under one stated set of rules, which "
        "is the only thing a model on synthetic labels can honestly be used for."
    )

    left, right = st.columns(2)
    with left:
        a = _controls("A", "Today, continued", city)
    with right:
        b = _controls("B", "Build inward, price the car", city)

    if a == b:
        st.info("Both scenarios are currently identical, so every difference below is zero. "
                "Change a lever on one side.")

    ya, frames_a, mob_a = _run(city_name, a.__dict__)
    yb, frames_b, mob_b = _run(city_name, b.__dict__)

    fa, fb = ya.iloc[-1], yb.iloc[-1]
    start = ya.iloc[0]
    land_a = fa["built_up_km2"] - start["built_up_km2"]
    land_b = fb["built_up_km2"] - start["built_up_km2"]

    st.divider()
    stats([
        ("Land converted, A", f"{land_a:+,.1f} km²", a.label),
        ("Land converted, B", f"{land_b:+,.1f} km²", b.label),
        ("Difference", f"{land_b - land_a:+,.1f} km²",
         "What choosing B over A costs or saves in land."),
        ("Car-km difference", f"{(mob_b['car_km'] / max(mob_a['car_km'], 1e-9) - 1) * 100:+.0f}%",
         "Commuting car-kilometres per household, B against A."),
    ])

    # ---- 1. land take over time -------------------------------------
    st.divider()
    figure(
        "14.1",
        "How much land each future takes, year by year",
        "Built-up area under each scenario. Press play to watch them separate.",
        reads_as="The two lines start together because both begin from today. What matters is "
                 "where they part and how far apart they end — that gap is the decision, in "
                 "square kilometres.",
    )
    both = pd.concat([
        ya[["year", "built_up_km2"]].assign(entity=a.label),
        yb[["year", "built_up_km2"]].assign(entity=b.label),
    ], ignore_index=True)
    years = sorted(both["year"].unique())
    palette = {a.label: SERIES[0], b.label: SERIES[1]}
    animate.player(
        "wb_land", years,
        lambda i: st.altair_chart(
            animate.lines_upto(
                both, "year", "built_up_km2", "entity", years[i],
                x_title="", y_title="built-up area, km²", colours=palette,
                x_domain=(years[0], years[-1]),
                y_domain=(both["built_up_km2"].min() * 0.99,
                          both["built_up_km2"].max() * 1.01),
                y_format=",.1f", height=320),
            width="stretch", key="wb_land_chart"))
    provenance("synthetic", "Cellular automaton over the generated grid; population path from "
                            "the selected forecasting model.")

    # ---- 2. where it lands ------------------------------------------
    st.divider()
    figure(
        "14.2",
        "Where the new building lands",
        "Cells converted from unbuilt to built by the end of each run. Blue is scenario A, "
        "orange is B, and grey is land both leave alone.",
        reads_as="If one scenario reaches into the protected mass or past the hard edge, it is "
                 "because its constraints were switched off — the model has no other way to get "
                 "there.",
    )
    end_a = frames_a[max(frames_a)][["x", "y", "converted"]].rename(
        columns={"converted": "a"})
    end_b = frames_b[max(frames_b)][["x", "y", "converted"]].rename(
        columns={"converted": "b"})
    merged = end_a.merge(end_b, on=["x", "y"])
    merged["who"] = np.select(
        [merged["a"] & merged["b"], merged["a"], merged["b"]],
        ["Both", "A only", "B only"], default="Neither")
    shown = merged[merged["who"] != "Neither"]

    if len(shown):
        cell = city.geometry.spacing_km
        dots = (
            alt.Chart(shown)
            .mark_square(size=max(18, int(2600 / city.geometry.extent_km)))
            .encode(
                x=alt.X("x:Q", title="km east–west",
                        scale=alt.Scale(domain=[-city.geometry.extent_km,
                                                city.geometry.extent_km]),
                        axis=alt.Axis(grid=False)),
                y=alt.Y("y:Q", title="km north–south",
                        scale=alt.Scale(domain=[-city.geometry.extent_km,
                                                city.geometry.extent_km]),
                        axis=alt.Axis(grid=False)),
                color=alt.Color("who:N",
                                scale=alt.Scale(domain=["Both", "A only", "B only"],
                                                range=[INK_3, SERIES[0], SERIES[1]]),
                                legend=alt.Legend(orient="top")),
                tooltip=["who", alt.Tooltip("x:Q", format=".1f"),
                         alt.Tooltip("y:Q", format=".1f")],
            )
            .properties(width=460, height=460)
        )
        st.altair_chart(style(dots), width="content", key="wb_map")
        counts = shown["who"].value_counts().rename("cells").to_frame()
        counts["km²"] = (counts["cells"] * cell ** 2).round(2)
        st.dataframe(counts.reset_index(names="converted by"), hide_index=True,
                     width="stretch")
    else:
        st.info("Neither scenario converts any land over this horizon — the population path is "
                "flat enough to be absorbed by densification alone. Lower the densification "
                "share on one side to make them differ.")
    provenance("synthetic", "Grid and development labels generated in urban/spatial.py.")

    # ---- 3. the trade the workbench exists to show -------------------
    st.divider()
    figure(
        "14.3",
        "Land against driving: the trade nobody gets to avoid",
        "Each scenario as one point. Left is less land taken; down is less driving.",
        reads_as="The bottom-left corner is the one everybody wants. Building outward is cheap "
                 "per dwelling and lands top-right; building inward and pricing the car lands "
                 "bottom-left and costs political capital instead. There is no lever in this "
                 "model that reaches bottom-left for free.",
    )
    trade = pd.DataFrame([
        {"scenario": a.label, "land_km2": land_a, "car_km": mob_a["car_km"],
         "nox": mob_a["nox_kg"]},
        {"scenario": b.label, "land_km2": land_b, "car_km": mob_b["car_km"],
         "nox": mob_b["nox_kg"]},
    ])
    pts = (
        alt.Chart(trade)
        .mark_point(filled=True, size=340, stroke=SURFACE, strokeWidth=2)
        .encode(
            x=alt.X("land_km2:Q", title="Land converted by the horizon, km²",
                    scale=alt.Scale(zero=False, nice=True),
                    axis=alt.Axis(format=",.1f", grid=True, gridColor=GRID)),
            y=alt.Y("car_km:Q", title="Commuting car-km per household per year",
                    scale=alt.Scale(zero=True),
                    axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
            color=alt.Color("scenario:N",
                            scale=alt.Scale(domain=[a.label, b.label],
                                            range=[SERIES[0], SERIES[1]]),
                            legend=None),
            tooltip=["scenario", alt.Tooltip("land_km2:Q", format=",.2f"),
                     alt.Tooltip("car_km:Q", format=",.0f")],
        )
    )
    labels = pts.mark_text(align="left", dx=16, fontSize=11, fontWeight="bold").encode(
        text="scenario:N")
    st.altair_chart(style(alt.layer(pts, labels).properties(
        height=340, padding={"right": 110})), width="stretch", key="wb_trade")
    values_table(trade.round(2))

    st.divider()
    st.subheader("Every difference, in one table")
    rows = [
        ("Population at the horizon", fa["population"], fb["population"], ",.0f"),
        ("Built-up area, km²", fa["built_up_km2"], fb["built_up_km2"], ",.1f"),
        ("Land converted, km²", land_a, land_b, ",.2f"),
        ("Built-up density, per km²", fa["built_up_density"], fb["built_up_density"], ",.0f"),
        ("Car share of commutes", mob_a["car_share"], mob_b["car_share"], ".3f"),
        ("Commuting car-km per household", mob_a["car_km"], mob_b["car_km"], ",.0f"),
        ("NOx kg per household per year", mob_a["nox_kg"], mob_b["nox_kg"], ".3f"),
    ]
    table = pd.DataFrame([
        {"Measure": name,
         "A": format(va, fmt), "B": format(vb, fmt),
         "B − A": format(vb - va, fmt),
         "Change": ("—" if va == 0 else f"{(vb / va - 1) * 100:+.1f}%")}
        for name, va, vb, fmt in rows
    ])
    st.dataframe(table, hide_index=True, width="stretch")

    st.divider()
    st.subheader("What this can and cannot tell you")
    note(
        "**Is:** a way to price one decision against another under a stated rule, with every "
        "lever visible and the invented parts held identical on both sides so they cancel. "
        "Switching the constraints off on one side and leaving them on the other gives the cost "
        "of the constraint in square kilometres, which is a number worth having and is very "
        "hard to get any other way."
    )
    note(
        "**Is not:** a forecast, a plan, or evidence about either city. The grid is synthetic, "
        "the development labels were generated from the same features the model then learns "
        "from, the travel model runs on invented households, and the two halves are joined by "
        "assuming they describe the same place — which they only do because both were built to. "
        "The difference between two runs is defensible. Either column on its own is not."
    )
