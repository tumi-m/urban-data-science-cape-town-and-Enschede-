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
    or off. This one does not change how much land gets built on; it changes
    *where*. That turns out to be the whole finding.
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
from . import compare
from . import llm
from . import owid
from . import spatial as sp
from .forecast import MODELS, fit_and_forecast
from .theme import GRID, INK, INK_2, INK_3, SEQUENTIAL, SERIES, SURFACE, style
from .ui import caveat, figure, header, note, provenance, stats, values_table


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
            # Linear rather than logistic as the default. Not because it is the
            # better model — section 4.2 shows the seven of them disagreeing by
            # more than a million people on Cape Town — but because a logistic
            # fitted to Enschede's plateau predicts a small decline, and a
            # workbench whose default setting makes every lever do nothing
            # teaches the reader that the tool is broken rather than that the
            # model is pessimistic.
            index=list(MODELS).index("linear"))
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
                                "available for building. The land converted barely "
                                "moves; what moves is how far out it sits.")
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

    # How far out the new building sits. This is the measure the constraint
    # actually moves — the quantity of land converted is set by how many people
    # need housing, not by what is protected.
    final = result.frames[max(result.frames)]
    conv = final[final["converted"]]
    return result.yearly, result.frames, {
        "car_km": outcome.mean_car_km,
        "car_share": float(outcome.modes.set_index("mode").loc["Car", "share"]),
        "nox_kg": outcome.nox_kg_per_household,
        "mean_km_out": float(conv["d_centre"].mean()) if len(conv) else float("nan"),
        "protected_cells": int(conv["protected"].sum()) if len(conv) else 0,
        "converted_cells": int(len(conv)),
    }


@st.cache_data(show_spinner=False)
def _growth_cached(city_name: str, model_key: str, horizon: int) -> float:
    frame = _population(city_name)
    spec = MODELS[model_key]
    fit = fit_and_forecast(frame, spec, {p.key: p.default for p in spec.params}, horizon)
    return float(fit.forecast["population"].iloc[-1] - frame["population"].iloc[-1])


def _growth(city_name: str, lev: "Levers") -> float:
    return _growth_cached(city_name, lev.model_key, lev.horizon)


def page_simulator() -> None:
    header(
        "Run two futures against each other",
        f"Pick a set of decisions on the left and a different set on the right, and read the "
        f"gap. The absolute numbers in either column are close to meaningless — the grid is "
        f"made up and the labels were generated from it. The difference is not, because "
        "everything invented is identical on both sides and cancels.",
    )
    city = compare.city_switch("sim_city", allow_both=False, default="Enschede")[0]
    st.caption(f"{city.name.upper()}, {city.country.upper()}  ·  {city.binding_constraint}")
    _simulator_body(city)


@st.fragment
def _simulator_body(city) -> None:
    """The interactive workbench, scoped so a lever move reruns only this.

    The whole comparison — both control columns and every chart that depends
    on them — lives in one fragment. Streamlit reruns a fragment in isolation
    when a widget inside it changes, so dragging a lever no longer rebuilds
    the sidebar, the header and the city switch around it; only the futures
    re-run. The city switch stays outside, because switching city is a change
    of context, not of scenario.
    """
    city_name = city.name

    caveat(
        "A workbench, not a forecast",
        "Nothing here predicts what either city will look like. It prices decisions against "
        "each other under one stated set of rules, which is the only thing a model built on "
        "synthetic labels can honestly be used for.",
        "critical")

    left, right = st.columns(2)
    with left:
        a = _controls("A", "Today, continued", city)
    with right:
        b = _controls("B", "Build inward, price the car", city)

    if a == b:
        st.info("Both scenarios are currently identical, so every difference below is zero. "
                "Change a lever on one side.")

    growth_a = _growth(city_name, a)
    growth_b = _growth(city_name, b)
    if max(growth_a, growth_b) <= 0:
        caveat(
            "The population model you picked predicts no growth",
            f"{MODELS[a.model_key].label} projects "
            f"{growth_a:+,.0f} people for {city.name} by {a.horizon}, so there is nothing to "
            "allocate and every land figure below is zero. That is the model's answer, not a "
            "failure of the simulation — a logistic curve fitted to Enschede's thirty-year "
            "plateau saturates at roughly today's population. Pick a different population "
            "model under <em>Adjust</em>; section 4.2 shows how far apart the seven of them "
            "are, which is the more interesting finding.",
            "caution")

    ya, frames_a, mob_a = _run(city_name, a.__dict__)
    yb, frames_b, mob_b = _run(city_name, b.__dict__)

    dist_a = mob_a.get("mean_km_out", float("nan"))
    dist_b = mob_b.get("mean_km_out", float("nan"))
    fa, fb = ya.iloc[-1], yb.iloc[-1]
    start = ya.iloc[0]
    land_a = fa["built_up_km2"] - start["built_up_km2"]
    land_b = fb["built_up_km2"] - start["built_up_km2"]

    st.divider()
    stats([
        ("Land converted, A", f"{land_a:+,.1f} km²", a.label),
        ("Land converted, B", f"{land_b:+,.1f} km²", b.label),
        ("New building sits this far out",
         f"{dist_a:,.1f} → {dist_b:,.1f} km",
         "Mean distance from the centre of the land each run converts, A then B."),
        ("Car-km difference", f"{(mob_b['car_km'] / max(mob_a['car_km'], 1e-9) - 1) * 100:+.0f}%",
         "Commuting car-kilometres per household, B against A."),
    ])

    # ---- 1. land take over time -------------------------------------
    st.divider()
    figure(
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
        "Distance against driving: the trade nobody gets to avoid",
        "Each scenario as one point. Left is new building closer to the centre; down is less "
        "driving.",
        reads_as="The bottom-left corner is the one everybody wants. The horizontal axis is "
                 "where the new housing goes, not how much of it there is — the quantity is "
                 "set by the population and barely moves. Pushing development outward and "
                 "pricing the car pull in opposite directions on the vertical axis, which is "
                 "why a city that builds on its edge and then prices parking is fighting "
                 "itself.",
    )
    trade = pd.DataFrame([
        {"scenario": a.label, "km_out": dist_a, "car_km": mob_a["car_km"],
         "nox": mob_a["nox_kg"]},
        {"scenario": b.label, "km_out": dist_b, "car_km": mob_b["car_km"],
         "nox": mob_b["nox_kg"]},
    ])
    pts = (
        alt.Chart(trade)
        .mark_point(filled=True, size=340, stroke=SURFACE, strokeWidth=2)
        .encode(
            x=alt.X("km_out:Q", title="New building, mean km from the centre",
                    scale=alt.Scale(zero=False, nice=True),
                    axis=alt.Axis(format=",.1f", grid=True, gridColor=GRID)),
            y=alt.Y("car_km:Q", title="Commuting car-km per household per year",
                    scale=alt.Scale(zero=True),
                    axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
            color=alt.Color("scenario:N",
                            scale=alt.Scale(domain=[a.label, b.label],
                                            range=[SERIES[0], SERIES[1]]),
                            legend=None),
            tooltip=["scenario", alt.Tooltip("km_out:Q", format=",.2f"),
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
        ("New building, mean km from centre", dist_a, dist_b, ",.2f"),
        ("…of which on protected land, cells",
         mob_a["protected_cells"], mob_b["protected_cells"], ",.0f"),
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
        "Switch the constraints off on one side and the interesting thing is what does "
        "<em>not</em> move: the amount of land converted is the same either way, because the "
        "population needing housing is the same. What moves is the distance. In Cape Town the "
        "protected land is close in, so lifting the protection pulls new development from "
        "twenty kilometres out to five — and that, rather than any number of hectares, is what "
        "the constraint costs."
    )
    note(
        "**Is not:** a forecast, a plan, or evidence about either city. The grid is synthetic, "
        "the development labels were generated from the same features the model then learns "
        "from, the travel model runs on invented households, and the two halves are joined by "
        "assuming they describe the same place — which they only do because both were built to. "
        "The difference between two runs is defensible. Either column on its own is not."
    )

    # ---- grounded assistant ------------------------------------------
    context = (
        f"SECTION: Workbench — run two futures against each other ({city.name}).\n"
        f"This is NOT a forecast. It prices one decision against another under a stated rule. "
        f"The grid is synthetic, labels generated from the same features the model learns from, "
        f"travel model on invented households. The absolute numbers in either column are close to "
        f"meaningless; the DIFFERENCE is defensible because the invented parts are identical on "
        f"both sides and cancel. [synthetic]\n\n"
        f"SCENARIO A ({a.label}): population model {MODELS[a.model_key].label}, run to {a.horizon}; "
        f"densification {a.densification:.0%}, station weighting {a.station_pull:.1f}, density "
        f"{a.persons_per_ha:.0f} persons/ha, constraints "
        f"{'respected' if a.respect_constraints else 'ignored'}; parking €{a.parking:.2f}/trip, "
        f"transit {a.transit:.2f}x, e-bike €{a.ebike:.0f}/yr.\n"
        f"SCENARIO B ({b.label}): population model {MODELS[b.model_key].label}, run to {b.horizon}; "
        f"densification {b.densification:.0%}, station weighting {b.station_pull:.1f}, density "
        f"{b.persons_per_ha:.0f} persons/ha, constraints "
        f"{'respected' if b.respect_constraints else 'ignored'}; parking €{b.parking:.2f}/trip, "
        f"transit {b.transit:.2f}x, e-bike €{b.ebike:.0f}/yr.\n\n"
        f"RESULTS (A → B):\n"
        f"- Land converted: {land_a:+,.1f} → {land_b:+,.1f} km².\n"
        f"- New building mean distance from centre: {dist_a:,.1f} → {dist_b:,.1f} km "
        f"(the constraint moves WHERE, not HOW MUCH).\n"
        f"- Car-km per household: {mob_a['car_km']:,.0f} → {mob_b['car_km']:,.0f} "
        f"({(mob_b['car_km'] / max(mob_a['car_km'], 1e-9) - 1) * 100:+.0f}%).\n"
        f"- NOx kg/household/yr: {mob_a['nox_kg']:.3f} → {mob_b['nox_kg']:.3f}.\n"
        f"- Car share: {mob_a['car_share']:.1%} → {mob_b['car_share']:.1%}.\n\n"
        f"KEY FINDING: switching the constraints off does NOT change how much land is converted "
        f"(the population needing housing is the same) — it changes how far out the new building "
        f"sits. In Cape Town the protected land is close in, so lifting protection pulls "
        f"development from ~20 km out to ~5 km. That distance, not any hectare count, is what the "
        f"constraint costs. The border, nitrogen and parking levers all act through car-km into "
        f"the nitrogen account."
    )
    llm.assistant_box(context, key="simulator_llm",
                      label="Ask the workbench")
