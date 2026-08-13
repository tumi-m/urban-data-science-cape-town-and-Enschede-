"""The two behavioural sections.

The growth simulation in the previous section allocates people to land by a
rule. Nobody in it decides anything. These two sections are the missing half:
households with incomes that choose where to live and how to travel, and then
the engineering question of how you run that for a population large enough to
matter.

Kept out of `pages.py` because that module is already long and these two pages
share a set of cached model runs that nothing else needs.
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from . import behaviour as bh
from . import owid
from . import society as so
from .theme import GRID, INK, INK_2, INK_3, SERIES, SURFACE, style
from .ui import caveat, figure, header, note, provenance, stats, values_table

# The population every scenario is run on. Big enough that the shares are
# stable to the third decimal, small enough that six scenarios finish inside a
# page load.
N_HOUSEHOLDS = 3000


# ---------------------------------------------------------------------
# Cached model runs
# ---------------------------------------------------------------------

@st.cache_data(show_spinner="Running the scenarios…")
def _scenarios(n: int = N_HOUSEHOLDS):
    table, outcomes = bh.run_all(n)
    rings = {k: v.rings.assign(scenario=k) for k, v in outcomes.items()}
    modes = pd.concat(
        [v.modes.assign(scenario=k) for k, v in outcomes.items()], ignore_index=True)
    return table, pd.concat(rings.values(), ignore_index=True), modes


@st.cache_data(show_spinner="Sweeping the parking charge…")
def _sweep(lever: str, values: tuple[float, ...], n: int = 1200):
    return bh.elasticity_curve(lever, np.array(values), n)


@st.cache_resource(show_spinner="Distilling the surrogates…")
def _surrogates():
    """Two surrogates, same algorithm, different training policies.

    The comparison between them is the section's finding, so both are built
    here rather than one being built on demand.
    """
    grid = so.policy_grid()
    narrow = so.distil(sample_size=900)
    wide = so.distil(sample_size=900, policies=grid)
    return narrow, wide, grid


@st.cache_data(show_spinner="Comparing surrogate against full model…")
def _coverage():
    narrow, wide, grid = _surrogates()
    return so.coverage_comparison(narrow, wide, None, grid, n=1000)


@st.cache_data(show_spinner="Timing both engines…")
def _scaling():
    _, wide, _ = _surrogates()
    return so.scaling_benchmark(wide)


@st.cache_data(show_spinner="Timing against the number of locations…")
def _locations():
    _, wide, _ = _surrogates()
    return so.location_benchmark(wide)


@st.cache_data(show_spinner="Checking both surrogates on the named scenarios…")
def _agreement():
    narrow, wide, _ = _surrogates()
    return so.scenario_agreement(narrow, wide)


# ---------------------------------------------------------------------
# 4.5 — How households choose
# ---------------------------------------------------------------------

def page_behaviour() -> None:
    header(
        "How households choose",
        "Every model so far moves people around by a rule. This one lets them decide. "
        "Each household has an income and a value of its own time. Each place has a rent. "
        "A household picks where to live by comparing what is left after rent and the cost "
        "of getting to work, and then picks how to travel by comparing time and money. "
        "Rents move until the demand for each place matches what is actually there. "
        "So when you change the price of parking, the answer moves — and it moves through "
        "car-kilometres into the nitrogen figure that the Enschede sections show is the "
        "thing actually blocking construction.",
    )

    caveat(
        "Made-up households",
        "The incomes, the rents and the behavioural numbers are typical values from the "
        "travel-choice literature, not measurements of Enschede. The <em>direction</em> and "
        "rough size of each response is worth something. The levels are not. Fitting this on "
        "the Dutch national travel survey (ODiN) and the property register would make the same "
        "code produce real numbers.",
        "critical")

    table, rings, modes = _scenarios()

    base = table.iloc[0]
    best = table.loc[table["Car km per household"].idxmin()]
    worst = table.loc[table["Car km per household"].idxmax()]
    stats([
        ("Car share today", f"{base['Car share']:.0%}",
         "Of commute trips, across all incomes, after the model has placed everyone."),
        ("Biggest cut", f"{best['vs today']:.0%}",
         f"Car-kilometres under “{best['Scenario']}”."),
        ("If driving gets cheaper", f"{worst['vs today']:+.0%}",
         "The counterfactual nobody asks for and everybody should."),
    ])

    st.divider()

    # ---- 1. the scenario table as ranked bars -----------------------
    figure(
        "Pricing parking does more than everything else combined",
        "Change in commuting car-kilometres per household against today, under each policy.",
        reads_as="Bars to the left are less driving. The three measures together barely beat "
                 "parking pricing on its own — because once the car has lost, the other two "
                 "have nothing left to win.",
    )
    bar_df = table[["Scenario", "vs today"]].copy()
    bar_df["pct"] = bar_df["vs today"] * 100
    bars = (
        alt.Chart(bar_df)
        .mark_bar(height=18, cornerRadiusEnd=2)
        .encode(
            x=alt.X("pct:Q", title="Change in car-km per household, %",
                    axis=alt.Axis(format="+d", grid=True, gridColor=GRID)),
            y=alt.Y("Scenario:N", sort=list(bar_df.sort_values("pct")["Scenario"]),
                    title=None),
            color=alt.condition(alt.datum.pct > 0, alt.value(SERIES[1]), alt.value(SERIES[0])),
            tooltip=["Scenario", alt.Tooltip("pct:Q", format="+.1f", title="% vs today")],
        )
    )
    labels = bars.mark_text(align="left", dx=6, fontSize=11, color=INK_2).encode(
        text=alt.Text("pct:Q", format="+.0f"), color=alt.value(INK_2))
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(
        strokeWidth=1, color=INK_3).encode(x="x:Q")
    st.altair_chart(
        style(alt.layer(bars, labels, zero).properties(height=200)),
        use_container_width=True, key="beh_bars")
    provenance("synthetic",
               "Multinomial logit mode choice with constants calibrated to a 45% car / 30% "
               "bicycle commuting split; bid-rent location choice cleared numerically.")

    st.divider()

    # ---- 2. mode split, stacked -------------------------------------
    figure(
        "Where the trips go instead",
        "Share of commute trips by mode, under each policy.",
        reads_as="Priced parking does not move people onto buses. It moves them onto bicycles, "
                 "which is what happens in a flat city with a 4 km median commute — the bus is "
                 "competing with a bike, not with the car.",
    )
    order = ["Car", "Bicycle", "Electric bike", "Bus or train", "Walk"]
    stack = modes.copy()
    stack["mode"] = pd.Categorical(stack["mode"], order, ordered=True)
    ramp = [SERIES[1], SERIES[0], "#7fb3ea", SERIES[2], "#9a9892"]
    chart = (
        alt.Chart(stack)
        .mark_bar(stroke=SURFACE, strokeWidth=1)
        .encode(
            x=alt.X("share:Q", title="Share of commute trips", stack="normalize",
                    axis=alt.Axis(format="%", grid=True, gridColor=GRID)),
            y=alt.Y("scenario:N", title=None,
                    sort=[s.name for s in bh.SCENARIOS]),
            color=alt.Color("mode:N", sort=order,
                            scale=alt.Scale(domain=order, range=ramp),
                            legend=alt.Legend(orient="top", columns=5)),
            tooltip=["scenario", "mode", alt.Tooltip("share:Q", format=".1%")],
        )
    )
    st.altair_chart(style(chart.properties(height=230)),
                    use_container_width=True, key="beh_modes")
    provenance("synthetic", "Logit mode shares, weighted by where the market clearing put "
                            "each income group.")

    st.divider()

    # ---- 3. the response curve --------------------------------------
    figure(
        "The response to a parking charge is a curve, not a slope",
        "Commuting car-kilometres per household as the charge per car trip rises.",
        reads_as="The first euro does most of the work and the fifth does almost none. "
                 "A charge is not a dial you turn linearly — there is a range where it bites "
                 "and a range beyond which you are only collecting money.",
    )
    sweep = _sweep("parking_charge_per_trip",
                   tuple(float(v) for v in np.arange(0, 6.01, 0.5)))
    st.altair_chart(
        owid.single_line(sweep, "value", "car_km",
                         x_title="Parking charge, € per car trip",
                         y_title="Car-km per household per year",
                         y_format=",.0f", x_format="$.2f", zero=True, height=300),
        use_container_width=True, key="beh_sweep")
    provenance("synthetic", "Full model re-run at each charge, 1,200 households.")

    with st.expander("Why the curve bends"):
        note(
            "A logit gives every mode a share, so the car never goes to zero — but its share "
            "falls fastest where it was close to being beaten. At €0 the car wins on time for "
            "most households; by €2.50 it has lost to the bicycle for the short trips and the "
            "only drivers left are the ones with far commutes and high values of time, who are "
            "exactly the ones a €1 increase does not reach. That is the shape, and it is the "
            "same shape you get from real elasticity estimates, which is mildly reassuring "
            "about the structure even though the levels here are invented."
        )

    st.divider()

    # ---- 4. rent gradient -------------------------------------------
    figure(
        "Making driving expensive makes the middle expensive",
        "Rent by distance from the centre, before and after parking is priced.",
        reads_as="The gradient steepens. Raising the cost of the commute raises what people "
                 "will pay to avoid it, so the benefit lands on whoever already owns near the "
                 "centre. This is the distributional catch, and it is a result of the model "
                 "rather than an opinion about it.",
    )
    two = rings[rings["scenario"].isin(["Today", "Parking priced"])]
    st.altair_chart(
        owid.line_with_end_labels(
            two, "km_to_centre", "rent", "scenario",
            x_title="Km from the centre", y_title="Rent, € per year",
            y_format=",.0f", x_format=".1f", height=300),
        use_container_width=True, key="beh_rent")
    provenance("synthetic", "Numerical bid-rent clearing, 12 concentric rings, "
                            "capacity from ring area at today's permitted density.")

    st.divider()

    # ---- 5. connect to nitrogen -------------------------------------
    # Deferred so the package does not import the app module at load time —
    # the app imports this module, and the constants belong to the nitrogen
    # section. Restating them here would be two definitions that drift.
    import streamlit_app as app

    figure(
        "None of it gets a dwelling to zero, and zero is the test",
        "Lifetime nitrogen from one dwelling under each policy. The bar spans two ways of "
        "attributing the model's effect to total driving; the true answer is inside it.",
        reads_as="The dashed line is a dwelling today, at 130 kg over fifty years. Even the "
                 "most generous reading of the strongest policy leaves about 23 kg, because "
                 "10 kg of it is the machinery that builds the house and the rest is the "
                 "driving that survives. The legal threshold is zero, so none of these bars "
                 "passes the test — they change how expensive the problem is, not whether "
                 "it exists.",
    )

    commute_share = float(table.iloc[0]["Car km per household"]) / app.CAR_KM_PER_DWELLING_YEAR
    rows = []
    for _, r in table.iterrows():
        cut = -r["vs today"]                       # positive = less driving
        # Lower bound: the policy only ever touches commuting, which this model
        # puts at ~6% of a dwelling's driving. Upper bound: the same
        # proportional response applies to every car trip.
        for label, scale in (
            ("If it only changes commuting", 1 - cut * commute_share),
            ("If it changes all car travel", 1 - cut),
        ):
            rows.append({
                "Scenario": r["Scenario"],
                "bound": label,
                "kg": app.lifetime_nox_kg(car_scale=max(scale, 0.0)),
            })
    nox = pd.DataFrame(rows)
    order = list(table.sort_values("vs today")["Scenario"])

    span = (
        alt.Chart(nox)
        .mark_line(strokeWidth=7, strokeCap="round", opacity=0.28, color=SERIES[0])
        .encode(
            y=alt.Y("Scenario:N", sort=order, title=None),
            x=alt.X("kg:Q", title="Lifetime nitrogen per dwelling, kg NOx",
                    scale=alt.Scale(zero=True),
                    axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
            detail="Scenario:N",
        )
    )
    dots = (
        alt.Chart(nox)
        .mark_point(filled=True, size=95, stroke=SURFACE, strokeWidth=1.5)
        .encode(
            y=alt.Y("Scenario:N", sort=order),
            x="kg:Q",
            color=alt.Color(
                "bound:N",
                scale=alt.Scale(domain=["If it only changes commuting",
                                        "If it changes all car travel"],
                                range=[SERIES[1], SERIES[2]]),
                legend=alt.Legend(orient="top", columns=2)),
            tooltip=["Scenario", "bound", alt.Tooltip("kg:Q", format=",.1f")],
        )
    )
    today = (
        alt.Chart(pd.DataFrame({"x": [app.lifetime_nox_kg()]}))
        .mark_rule(strokeDash=[4, 3], strokeWidth=1, color=INK_3).encode(x="x:Q")
    )
    st.altair_chart(style(alt.layer(span, dots, today).properties(height=230)),
                    use_container_width=True, key="beh_nitrogen")
    provenance("synthetic",
               "Policy response from the model above; nitrogen account and the 12,000 "
               "vehicle-km per dwelling from the nitrogen section.")
    values_table(nox.pivot(index="Scenario", columns="bound", values="kg").round(1).reset_index())

    note(
        f"**Why a range and not a number.** This model only sees commuting inside the city, "
        f"and it puts that at {commute_share:.0%} of a dwelling's driving. If a parking charge "
        f"changed nothing else, the nitrogen effect would be the small end of each bar. It "
        f"plainly changes more than that — a charge in the centre reaches shopping and leisure "
        f"trips too — but it reaches none of the driving to out-of-town retail, and it misses "
        f"the commutes that leave Enschede altogether, which are exactly the long ones this "
        f"ring model has no representation of. The honest position is that the answer is "
        f"inside the bar and this model cannot say where. A travel survey would settle it."
    )
    note(
        "**What survives the uncertainty.** The ordering. Pricing parking beats the other two "
        "levers under either assumption, and cheaper motoring makes things worse under either. "
        "That is enough to rank policies, which is what the ranking is for — and it is more "
        "than the growth simulation in the previous section can do, because that one has no "
        "prices in it at all."
    )

    st.divider()
    st.subheader("What this can and cannot tell you")
    note(
        "**Is:** a standard random-utility model — McFadden's discrete choice for the mode, "
        "Alonso-Muth-Mills bid rent for the location, cleared numerically. Nothing here is "
        "new, and the reason to use it is that it is old enough to be well understood."
    )
    note(
        "**Is not:** an estimate of what Enschede would do. The mode constants were calibrated "
        "to reproduce an assumed base split rather than estimated from observed choices, there "
        "is one trip purpose, no car ownership decision, no freight, no through traffic, and "
        "the twelve concentric rings are a caricature of a city that has a ridge running "
        "through it. Fitting on ODiN would fix the first; the rest need a real network."
    )


# ---------------------------------------------------------------------
# 4.6 — Scaling the simulation
# ---------------------------------------------------------------------

def page_scaling() -> None:
    header(
        "Making the model fast enough to be useful",
        "The model in the previous section costs households × locations, inside a loop that "
        "repeats until rents settle. A recent paper on very large agent simulations "
        "(Guan et al., “Modeling Earth-Scale Human-Like Societies with One Billion Agents”, "
        "arXiv:2506.12078) offers a way round that cost: run the expensive model on a sample, "
        "train a cheap model to imitate it, use the cheap one for everybody else. This section "
        "does that — and finds that most of the speed was available without it, that the cheap "
        "model is wrong in a way its own scores hide, and that there is still a case for it. "
        "In that order, because that is the order the work actually happened in.",
    )

    caveat(
        "No language model is involved",
        "The paper's expensive step is an LLM giving each agent opinions and conversations. "
        "The expensive step here is a discrete-choice model — far narrower and far cheaper. "
        "What has been borrowed is the structure: break the simulation into named operations, "
        "and distil-then-scale. Calling this an LLM agent society would be false.",
        "note")

    narrow, wide, grid = _surrogates()
    scal = _scaling()
    locs = _locations()

    at_1m = scal.iloc[-1]
    stats([
        ("Full model, 1m households", f"{at_1m['full_seconds']:.0f} s",
         "The exact model, no approximation, after the fix described below."),
        ("Surrogate, same run", f"{at_1m['surrogate_seconds']:.0f} s",
         f"{at_1m['speedup']:.1f}× faster — and only that."),
        ("Fit to its own training data", f"R² {wide.scores['car-km R²']:.3f}",
         "Which, as the second chart shows, tells you almost nothing."),
    ])

    st.divider()

    # ---- 1. the pipeline --------------------------------------------
    st.subheader("The simulation, as four named steps")
    note(
        "The paper's first idea is procedural rather than mathematical: stop writing the "
        "simulation as one loop that does everything, and write it as a list of operations "
        "that each move the state forward one way. It earned its place here for a dull "
        "reason — once each step was named and timed separately, it was obvious that the "
        "first step was being recomputed on every round of the clearing loop despite not "
        "depending on rents. That observation, plus doing the arithmetic over arrays instead "
        "of one household at a time, made the exact model between 100 and 250 times faster "
        "depending on the size of the run. No approximation, same answers to the decimal."
    )
    steps = pd.DataFrame([
        {"Step": op.name.replace("_", " "), "What it does": op.description}
        for op in so.PIPELINE
    ])
    st.dataframe(steps, hide_index=True, width="stretch")

    caveat(
        "A number this page used to report, and why it was wrong",
        "The first version claimed the surrogate was 275 times faster than the full model. It "
        "was — against a full model that spent 99 per cent of its time in a Python loop it did "
        "not need. Fixing that removed almost the whole margin. The number measured the code, "
        "not the method, and it is left on the page rather than quietly corrected because it "
        "is the most useful thing in this section: <strong>make the exact model fast before "
        "you approximate it.</strong>",
        "caution")

    st.divider()

    # ---- 2. speed ----------------------------------------------------
    figure(
        f"After the fix, the approximation buys {at_1m['speedup']:.0f}×, not 275×",
        "Seconds to run one scenario, against the number of households, at twelve locations.",
        reads_as="Both axes are logarithmic, so a straight line is a constant growth rate and "
                 "the vertical gap between the lines is the speed-up. The two lines are close "
                 "and roughly parallel: at this size the exact model is not the bottleneck "
                 "anyone thought it was.",
    )
    long = pd.concat([
        scal[["households", "surrogate_seconds"]].rename(
            columns={"surrogate_seconds": "seconds"}).assign(engine="Distilled surrogate"),
        scal[["households", "full_seconds"]].rename(
            columns={"full_seconds": "seconds"}).assign(engine="Full model"),
    ], ignore_index=True)

    line = (
        alt.Chart(long)
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(filled=True, size=55))
        .encode(
            x=alt.X("households:Q", title="Households",
                    scale=alt.Scale(type="log"),
                    axis=alt.Axis(format="~s", grid=False)),
            y=alt.Y("seconds:Q", title="Seconds to run one scenario",
                    scale=alt.Scale(type="log"),
                    axis=alt.Axis(format="~g", grid=True, gridColor=GRID)),
            color=alt.Color("engine:N",
                            scale=alt.Scale(domain=["Full model", "Distilled surrogate"],
                                            range=[SERIES[1], SERIES[0]]),
                            legend=alt.Legend(orient="top")),
            tooltip=["engine", alt.Tooltip("households:Q", format=","),
                     alt.Tooltip("seconds:Q", format=".3f")],
        )
    )
    st.altair_chart(style(line.properties(height=300)),
                    use_container_width=True, key="soc_scale")
    provenance("derived", "Wall-clock timing of both engines in this environment, "
                          "single-threaded.")
    values_table(scal.round(3))

    st.divider()

    # ---- 3. the failure, and the fix ---------------------------------
    figure(
        "A surrogate that scores perfectly can still be useless",
        "Car-kilometres against the parking charge: the full model, and two surrogates "
        "built by the same algorithm but trained on differently chosen policies.",
        reads_as="The orange staircase is a surrogate trained on the six named scenarios from "
                 "the previous section. Those six contain only two different parking charges, "
                 "so it has no idea what happens between them and answers €1.25 with the number "
                 "it learned for €0 — an error of over 13,000 per cent at the far end. The "
                 "green line is the identical algorithm trained on a designed set of policies: "
                 "much closer, and still a staircase, because a tree is a staircase. Both score "
                 "R² of about 1.0 on their own training data.",
    )
    cov = _coverage()
    engines = [so.ENGINE_FULL, so.ENGINE_NARROW, so.ENGINE_WIDE]
    cov_line = (
        alt.Chart(cov)
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(filled=True, size=45),
                   strokeCap="round")
        .encode(
            x=alt.X("parking_charge:Q", title="Parking charge, € per car trip",
                    axis=alt.Axis(format="$.2f", grid=False)),
            y=alt.Y("car_km:Q", title="Car-km per household per year",
                    scale=alt.Scale(zero=True),
                    axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
            color=alt.Color(
                "engine:N",
                scale=alt.Scale(domain=engines, range=[INK, SERIES[1], SERIES[2]]),
                legend=alt.Legend(orient="top", columns=3)),
            strokeDash=alt.StrokeDash(
                "engine:N",
                scale=alt.Scale(domain=engines, range=[[1, 0], [5, 3], [5, 3]]),
                legend=None),
            tooltip=["engine", alt.Tooltip("parking_charge:Q", format="$.2f"),
                     alt.Tooltip("car_km:Q", format=",.0f")],
        )
    )
    st.altair_chart(style(cov_line.properties(height=330)),
                    use_container_width=True, key="soc_coverage")
    provenance("synthetic", "Full model re-run at each charge on 1,000 households; both "
                            "surrogates asked the same question.")
    values_table(cov.pivot(index="parking_charge", columns="engine",
                           values="car_km").round(1).reset_index())

    note(
        "The reason is not exotic. A gradient-boosted tree is constant between the values it "
        "was shown — it splits the input space into boxes and returns a number per box. Give "
        "it two parking charges and it learns two boxes. Every method that replaces an "
        "expensive model with a learned one has this failure mode, and R² on training data "
        "will never reveal it, because the surrogate reproduces the points it saw perfectly. "
        "What reveals it is asking a question that was not in the training set."
    )

    with st.expander("The obvious fix does not work either, which is the more useful lesson"):
        note(
            "The first repair tried here was to draw all four policy levers uniformly at "
            "random — fourteen random policies instead of six named ones. It was worse. "
            "Drawing an e-bike subsidy from €0–600 fourteen times means almost every training "
            "policy has a large subsidy, so the surrogate never saw a city without one and put "
            "car use 90 per cent too low across the whole range. It had stopped stepping and "
            "started being wrong smoothly, which is harder to spot."
        )
        note(
            "What the green line actually uses is the dull classical design: move each lever "
            "across its range on its own with the others at today's value, keep today's policy "
            "in the set, and add a handful of random combinations on top for the interactions. "
            "One factor at a time for the main effects, random draws for the rest. It is a "
            "sixty-year-old idea from experimental design and it costs the same number of "
            "full-model runs as guessing."
        )
        note(
            "It does not make the problem go away, and the chart is drawn so you can see that. "
            "The green line still steps, because a gradient-boosted tree has no way not to. "
            "Denser sampling buys a finer staircase and nothing more; getting an actual curve "
            "needs a learner that interpolates. What the design does buy is the difference "
            "between being wrong by a factor of a hundred and being wrong by tens of per cent, "
            "which is the difference between a tool and a trap."
        )
        note(
            "Both failures are the same failure: the training policies did not cover the "
            "questions the surrogate would be asked. That is the thing to check when anyone "
            "offers you a fast approximation of a slow model, and the training score will not "
            "tell you."
        )

    st.divider()

    # ---- 3b. where distillation actually pays -------------------------
    top = locs.iloc[-1]
    figure(
        "Where the approximation would actually earn its keep",
        "Seconds to run one scenario, against the number of *locations*, at "
        f"{4_000:,} households.",
        reads_as="The full model's cost is households × locations, so it climbs with the "
                 "horizontal axis. The surrogate makes one pass over households and never "
                 "learns how many locations there were, so it is flat. The gap is not a "
                 f"property of the population — at {int(top['locations']):,} locations it is "
                 f"{top['speedup']:.0f}×, against {locs.iloc[0]['speedup']:.1f}× at twelve.",
    )
    long_loc = pd.concat([
        locs[["locations", "surrogate_seconds"]].rename(
            columns={"surrogate_seconds": "seconds"}).assign(engine="Distilled surrogate"),
        locs[["locations", "full_seconds"]].rename(
            columns={"full_seconds": "seconds"}).assign(engine="Full model"),
    ], ignore_index=True)
    loc_line = (
        alt.Chart(long_loc)
        .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(filled=True, size=55))
        .encode(
            x=alt.X("locations:Q", title="Locations the city is cut into",
                    scale=alt.Scale(type="log"), axis=alt.Axis(format="~s", grid=False)),
            y=alt.Y("seconds:Q", title="Seconds to run one scenario",
                    scale=alt.Scale(type="log"),
                    axis=alt.Axis(format="~g", grid=True, gridColor=GRID)),
            color=alt.Color("engine:N",
                            scale=alt.Scale(domain=["Full model", "Distilled surrogate"],
                                            range=[SERIES[1], SERIES[0]]),
                            legend=alt.Legend(orient="top")),
            tooltip=["engine", alt.Tooltip("locations:Q", format=","),
                     alt.Tooltip("seconds:Q", format=".3f")],
        )
    )
    st.altair_chart(style(loc_line.properties(height=300)),
                    use_container_width=True, key="soc_locations")
    provenance("derived", "Same timing method, holding households fixed and varying how "
                          "finely the city is divided.")
    values_table(locs.round(3))

    note(
        "Twelve concentric rings is a caricature of a city. A study anyone would act on uses "
        "census output areas — Enschede has on the order of a thousand — and at that point the "
        "exact model is genuinely expensive and the case for distilling it is real. So the "
        "paper's method is not wrong here; it was being tested against the wrong axis. That is "
        "worth separating: **the population was never the problem, the resolution is.**"
    )

    st.divider()

    # ---- 4. the trade-off, stated ------------------------------------
    st.subheader("Each surrogate is right exactly where the other is wrong")
    note(
        "The coverage chart above is only half the comparison. Here is the other half: both "
        "surrogates against the full model on the six named scenarios from the previous "
        "section. The narrow one was trained on precisely these and reproduces every one of "
        "them to within about a per cent. The designed grid never saw any of them and gets "
        "four of the six right — then misses badly on the two that fall in its blind spots: "
        "the €2.50 parking charge, which sits between its grid points, and “All three”, which "
        "moves three levers at once when the grid mostly moved them one at a time."
    )
    agree = _agreement()
    show = agree.copy()
    for c in show.columns:
        if c != "Scenario":
            show[c] = show[c].round(1)
    st.dataframe(show, hide_index=True, width="stretch")
    note(
        "With a piecewise-constant learner and a fixed budget of full-model runs you get one "
        "or the other: accurate on the policies you named, or roughly right across the space. "
        "Wanting both means either spending more full-model runs, or using a learner that can "
        "interpolate — and at that point you should ask what is wrong with running the exact "
        "model, which the first chart says takes half a minute."
    )

    st.divider()

    # ---- 5. household-level agreement --------------------------------
    st.subheader("Agreement household by household, not just on the average")
    note(
        "Matching the mean is easy and nearly meaningless — a model that returns the same "
        "number for everybody matches the mean. This is the check on individual households "
        "neither surrogate has seen, under today's policy, which the designed grid does "
        "contain."
    )
    hold = so.holdout_agreement(wide, bh.SCENARIOS[0], n=1200)
    st.dataframe(
        pd.DataFrame([{k: round(v, 3) for k, v in hold.items()}]),
        hide_index=True, width="stretch")

    st.divider()
    st.subheader("What this can and cannot tell you")
    note(
        "**Is:** an honest test of the distil-then-scale pattern on an ordinary discrete-choice "
        "model. Three results, none of them the one that was expected. Naming the steps found "
        "a 150× optimisation in the exact model and removed most of the reason to approximate "
        "it. The approximation is wrong between the policies it was trained on, and its own R² "
        "of 1.0 does not say so. And the margin that remains depends on the number of "
        "locations, not the number of people — which is the axis nobody was benchmarking."
    )
    note(
        "**Is not:** anything to do with the paper's actual subject. Light Society simulates a "
        "billion people with beliefs, running Trust Games and diffusing opinions, and its "
        "agents are grounded in real World Values Survey profiles. This is a mode-choice model "
        "on invented households. The architecture transfers; none of the findings do. And the "
        "speed here buys nothing yet: there is no register of real Dutch households wired into "
        "it, so a million-household run is a million made-up households — fast and worthless "
        "in equal measure."
    )
