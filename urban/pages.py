"""The demographic, predictive and simulation sections.

Held apart from the constraint sections because they are a different kind of
claim. Everything in the constraint analysis can be checked with a calculator.
Nothing here can: these pages fit models, and a fitted model is an argument
about the future dressed as a measurement of the past.

The sections are therefore built to keep showing their own working — which
model, on which data, evaluated how, and what it cannot do.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from . import demography as dem
from . import owid
from . import spatial as sp
from .forecast import MODELS, compare_all, fit_and_forecast
from .provenance import BADGE, SYNTHETIC, Series, worst_class
from .theme import SERIES
from .ui import data_badge, figure, header, note, provenance, stats, values_table

LAND_AREA_KM2 = 140.0
SYNTHETIC_GRID = Series(
    "Cell grid, development labels and value surface", SYNTHETIC,
    "Generated from the stated process in urban/spatial.py",
    "Not observations of Enschede. The models below recover assumptions that were put in "
    "deliberately; swap in the municipal register and the WOZ valuation file to make them real.",
)


@st.cache_data
def _population():
    data = dem.load_population()
    return data.frame, data.series


@st.cache_data
def _grid():
    return sp.build_grid()


# =====================================================================
# 08 · Population
# =====================================================================

def page_population() -> None:
    frame, series = _population()
    header(
        "08 · Population",
        "A city that stopped growing, then started again",
        "Enschede's population curve is not one process but three: rapid growth on textiles to "
        "the early 1960s, a plateau of roughly thirty years through the industry's collapse and "
        "the city's reinvention around its university, and slow renewed growth since the 1990s "
        "carried by students and by international migration. Any model of the series has to "
        "reproduce all three, and most models fitted to it reproduce whichever one dominates "
        "the training window.",
    )
    data_badge(series)

    first, last = frame.iloc[0], frame.iloc[-1]
    plateau = frame[(frame["year"] >= 1975) & (frame["year"] <= 1995)]
    stats([
        ("Population", f"{last['population']:,.0f}", f"In {int(last['year'])}."),
        ("Since 1950", f"+{(last['population'] / first['population'] - 1) * 100:.0f}%",
         f"From {first['population']:,.0f} in {int(first['year'])}."),
        ("The plateau", f"+{(plateau['population'].iloc[-1] / plateau['population'].iloc[0] - 1) * 100:.0f}%",
         "Across the two decades from 1975 — twenty years of essentially nothing."),
        ("Gross density", f"{last['population'] / LAND_AREA_KM2:,.0f}/km²",
         f"Over {LAND_AREA_KM2:.0f} km² of municipal land, most of which is not urban."),
    ])

    st.divider()
    figure("01", "Municipal population, 1950 onward",
           "The three regimes are visible without any statistics: a steep climb, a flat stretch, "
           "and a shallower climb that has not yet recovered the first one's slope.")
    st.altair_chart(
        owid.single_line(frame, "year", "population",
                         x_title="", y_title="inhabitants", height=320),
        width="stretch", key="pop_history")
    provenance(series.klass, series.source)

    st.divider()
    figure("02", "Indexed against other places",
           "Population indexed to 100 at the start of the series. Indexing is the only fair way "
           "to put a city of 160,000 beside one of 900,000: the question is about rates, and an "
           "absolute axis answers a question about sizes instead.")
    comp = dem.comparators(frame["year"].to_numpy())
    st.altair_chart(
        owid.line_with_end_labels(comp, "year", "index", "entity",
                                  x_title="", y_title="index, first year = 100",
                                  highlight="Enschede", y_format=",.0f", height=340),
        width="stretch", key="pop_indexed")
    data_badge(dem.COMPARATOR_SERIES)

    st.divider()
    figure("03", "Where the change actually comes from",
           "Components of annual change, stacked around zero. The net is the distance between "
           "the top and the bottom of the stack, not the height of either.")
    flows = dem.components_of_change(frame["year"].to_numpy())
    long = flows.melt(id_vars="year", var_name="component", value_name="people")
    st.altair_chart(
        owid.stacked_components(long, "year", "people", "component",
                                x_title="", y_title="people per year", height=300),
        width="stretch", key="pop_flows")
    values_table(flows.tail(20))
    data_badge(dem.FLOW_SERIES)
    note(
        "This is the chart that explains the plateau, and it is the one a total-population line "
        "cannot show. Natural increase fell away decades ago and is now marginal. Net domestic "
        "migration has been negative for most of the period — Enschede trains graduates and the "
        "Randstad hires them, which is the standard fate of a university city far from the "
        "economic core. What has held the total up since the 1990s is international migration. "
        "A city whose growth rests on one of three components, and the most policy-sensitive "
        "one, has a thinner base than its headline number suggests."
    )

    st.divider()
    figure("04", "Two densities, and why the difference matters",
           "Gross density divides by the whole municipality — mostly farmland and protected "
           "habitat, and always will be. Built-up density divides by the area that is actually "
           "urban.")
    density = dem.density_series(frame, land_area_km2=LAND_AREA_KM2)
    tidy = pd.concat([
        density[["year", "gross_density"]].rename(columns={"gross_density": "value"})
            .assign(measure="Gross, per km² of municipality"),
        density[["year", "built_up_density"]].rename(columns={"built_up_density": "value"})
            .assign(measure="Built-up, per km² of urban fabric"),
    ])
    st.altair_chart(
        owid.line_with_end_labels(tidy, "year", "value", "measure",
                                  x_title="", y_title="inhabitants per km²",
                                  y_format=",.0f", height=320),
        width="stretch", key="pop_density")
    note(
        "The two lines diverge, and the divergence is the definition of sprawl: population rose "
        "while the land it occupies rose faster, so the city got bigger and thinner at the same "
        "time. That is the process the settlement boundary was drawn to stop, and reading it off "
        "a gross-density series is impossible — gross density can hold perfectly flat while the "
        "urban fabric empties out underneath it."
    )
    provenance("derived", "Population series above, built-up area from the constraint sections")


# =====================================================================
# 09 · Projection
# =====================================================================

def page_projection() -> None:
    frame, series = _population()
    header(
        "09 · Projection",
        "The model decides the answer, not the data",
        "Seventy-five annual observations of a slow, smooth series cannot distinguish between a "
        "city heading for 175,000 and one heading for 158,000. The functional form does that, "
        "and the functional form is an assumption. So this section does not present a forecast. "
        "It presents a control panel, and invites you to watch 2050 move by twenty thousand "
        "people while the data underneath stays exactly the same.",
    )
    data_badge(series)

    with st.sidebar:
        st.markdown("#### Projection controls")
        key = st.selectbox("Model", list(MODELS), format_func=lambda k: MODELS[k].label,
                           key="fc_model")
        spec = MODELS[key]
        params = {}
        for p in spec.params:
            if p.kind == "int":
                params[p.key] = st.slider(p.label, int(p.low), int(p.high), int(p.default),
                                          int(p.step or 1), help=p.help or None,
                                          key=f"fc_{p.key}")
            elif p.kind == "float":
                params[p.key] = st.slider(p.label, float(p.low), float(p.high),
                                          float(p.default), float(p.step or 0.01),
                                          help=p.help or None, key=f"fc_{p.key}")
        horizon = st.slider("Horizon", 2030, 2080, 2050, 5, key="fc_horizon")
        holdout = st.slider("Backtest holdout, years", 5, 30, 15, 1, key="fc_holdout",
                            help="Years withheld from the end of the series and predicted.")

    fit = fit_and_forecast(frame, spec, params, horizon, holdout)

    st.markdown(f"**{spec.label}** · {spec.family}")
    st.caption(spec.blurb)
    if spec.caution:
        st.caption(f"⚠︎ {spec.caution}")

    final = float(fit.forecast["population"].iloc[-1])
    now = float(frame["population"].iloc[-1])
    stats([
        (f"Projected {horizon}", f"{final:,.0f}",
         f"{(final / now - 1) * 100:+.1f}% on {int(frame['year'].iloc[-1])}."),
        ("Backtest MAE", f"{fit.metrics['MAE']:,.0f}",
         f"Mean absolute error over {fit.metrics['Holdout years']} withheld years."),
        ("MAPE", f"{fit.metrics['MAPE %']:.2f}%", "Mean absolute percentage error on the holdout."),
        ("Extrapolates?", "yes" if spec.extrapolates else "no",
         "Whether the family can leave the range of its training targets at all."),
    ])

    for w in fit.warnings:
        st.warning(w)

    st.divider()
    figure("01", f"History and projection to {horizon}",
           "History solid, projection dashed. The dash is not decoration: one line is a "
           "measurement and the other is an assumption with arithmetic attached.")
    st.altair_chart(
        owid.projection(frame, fit.forecast, x_title="", y_title="inhabitants", height=340),
        width="stretch", key="fc_projection")
    if spec.uncertainty and "lower" in fit.forecast:
        note("The band is a 95% interval **given this kernel**. It is the model's uncertainty "
             "about the future conditional on its own assumptions being right — not uncertainty "
             "about whether those assumptions were the correct ones. No model in this registry "
             "can report the second kind, which is precisely why the comparison table below "
             "exists.")
    if fit.capacity:
        st.caption(f"Fitted saturation capacity: {fit.capacity:,.0f} inhabitants.")
    provenance(worst_class(series.klass, "derived"), "Model fitted here")

    st.divider()
    st.subheader("Evaluation")
    note(
        "The backtest withholds a contiguous block from the **end** of the series rather than a "
        "random sample. A random split on a time series lets the model see the future while "
        "predicting the past, and returns a score that means nothing. Holding out the tail asks "
        "the only question worth asking: standing in "
        f"{fit.metrics['Tested on'].split('–')[0]}, how wrong would this model have been about "
        "what followed?"
    )
    c1, c2 = st.columns(2)
    with c1:
        figure("02", "Predicted against actual, held-out years",
               "The dashed diagonal is perfection. Distance from it is the error; a run of "
               "points on one side of it is bias.")
        st.altair_chart(owid.scatter_actual_predicted(fit.backtest),
                        width="stretch", key="fc_scatter")
    with c2:
        figure("03", "Residuals over the whole series",
               "Observed minus fitted, in-sample. Structure here means the model has missed "
               "something systematic rather than merely being noisy.")
        st.altair_chart(owid.residual_plot(fit.residuals), width="stretch", key="fc_resid")

    st.dataframe(
        pd.DataFrame([{k: (f"{v:,.3f}" if isinstance(v, float) else v)
                       for k, v in fit.metrics.items()}]),
        hide_index=True, width="stretch")

    st.divider()
    st.subheader("Every model at once")
    note(
        "This is the section's actual argument. Each row is a different family at its defaults, "
        "on identical data. The spread across the projection column is far wider than any single "
        "model's confidence interval — which is the thing a single forecast with a tidy band "
        "will never tell you, and the reason a projection quoted without its alternatives is "
        "closer to rhetoric than to evidence."
    )
    table = compare_all(frame, horizon, holdout)
    st.dataframe(
        table.assign(**{
            str(horizon): table["2050"].map(lambda v: f"{v:,.0f}" if pd.notna(v) else "—"),
            "MAE": table["MAE"].map(lambda v: f"{v:,.0f}" if pd.notna(v) else "—"),
            "MAPE %": table["MAPE %"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "—"),
        }).drop(columns=["2050"]),
        hide_index=True, width="stretch")

    valid = table.dropna(subset=["2050"])
    if len(valid) > 1:
        spread = valid["2050"].max() - valid["2050"].min()
        extrap = valid[valid["Extrapolates"]]
        st.altair_chart(
            owid.horizontal_bars(
                valid.assign(**{"Projection": valid["2050"]}),
                "Model", "Projection",
                x_title=f"projected population in {horizon}",
                height=34 * len(valid) + 40, value_format=",.0f"),
            width="stretch", key="fc_compare")
        note(
            f"The families disagree by **{spread:,.0f} people** — about "
            f"{spread / now * 100:.0f} per cent of the current population. Restricting to the "
            f"models that can extrapolate at all narrows it to "
            f"{extrap['2050'].max() - extrap['2050'].min():,.0f}, which is the honest range. "
            "Note where the tree ensembles land: near today's figure, because that is the only "
            "thing they can say. Their excellent error scores are a measure of how well they "
            "memorised the recent past, not of how much they know about 2050."
        )

    st.divider()
    st.subheader("What would make this a real forecast")
    note(
        "A cohort-component model, which is what a statistics office actually runs: age the "
        "population forward one year at a time under fertility, mortality and migration "
        "schedules by age and sex, rather than fitting a curve to a total. It is less "
        "impressive-looking and far more reliable, because it carries the mechanism — a city "
        "whose 20-to-25 cohort is three times its 60-to-65 cohort has a future that no curve "
        "fitted to the total can see. The components chart in the previous section is the first "
        "input such a model would need."
    )


# =====================================================================
# 10 · Development
# =====================================================================

def page_development() -> None:
    header(
        "10 · Development",
        "Learning where a city grows, and what it does to values",
        "Two models here. A classifier that predicts which cells develop, from accessibility "
        "and existing density, filtered by the constraint mask the rest of this platform is "
        "about. And a hedonic surface that prices the result. Both are built on synthetic "
        "labels, and the section says so at every step, because a development probability map "
        "is the single most persuasive-looking output in this entire project and persuasiveness "
        "is exactly what it has not earned.",
    )
    data_badge(SYNTHETIC_GRID)

    grid = _grid()

    with st.sidebar:
        st.markdown("#### Development model")
        kind = st.selectbox("Classifier", list(sp.CLASSIFIERS),
                            format_func=lambda k: sp.CLASSIFIERS[k][0], index=2, key="dev_kind")
        label, _, param_spec, blurb = sp.CLASSIFIERS[kind]
        params = {}
        for key, plabel, low, high, default, step in param_spec:
            if isinstance(default, int) and isinstance(step, int):
                params[key] = st.slider(plabel, int(low), int(high), int(default), int(step),
                                        key=f"dev_{key}")
            else:
                params[key] = st.slider(plabel, float(low), float(high), float(default),
                                        float(step), key=f"dev_{key}")

    model = sp.fit_development(grid, kind, params)
    st.markdown(f"**{model.label}**")
    st.caption(blurb)

    m = model.metrics
    stats([
        ("Accuracy", f"{m['Accuracy']:.3f}", f"On {m['Test cells']:,} held-out cells."),
        ("ROC AUC", f"{m['ROC AUC']:.3f}", "Ranking quality, independent of the threshold."),
        ("Brier score", f"{m['Brier score']:.4f}",
         "Calibration of the probability. Lower is better; it matters more than accuracy here, "
         "because the probability is used to allocate, not to classify."),
        ("Base rate", f"{m['Base rate']:.2f}", "Share of cells developed — the score to beat."),
    ])

    st.error(
        "**Read these numbers correctly.** The labels were generated from these same features by "
        "a process written down in `urban/spatial.py`. A high score therefore measures whether "
        "the learner can recover assumptions that were deliberately put there — it is a test of "
        "the pipeline, not evidence about Enschede. The honest use of this page is to check that "
        "the machinery works and to see how the classifier families differ; the moment real "
        "labels arrive, the same code becomes a real model and nothing else changes."
    )

    st.divider()
    c1, c2 = st.columns([3, 2])
    with c1:
        figure("01", "Probability of development",
               "Model output per cell. Protected land and everything beyond the border are held "
               "at zero by the constraint mask, not by the model.")
        st.altair_chart(
            owid.raster(model.grid, "p_develop", legend_title="p(develop)",
                        points=sp.KNOWN_SITES, point_labels=True),
            width="content", key="dev_map")
        st.caption(
            "Marked points are real Enschede locations — the hospital, the science park, "
            "Roombeek, the eastern housing expansion. Coordinates are approximate and programme "
            "and status are not verified; they are here to give the surface something recognisable "
            "to be read against, not as a development register."
        )
    with c2:
        figure("02", "What the model leans on",
               "Feature weights. For the linear model these are log-odds coefficients and read "
               "directly; for the ensembles they are impurity-based importances, which say what "
               "is used and not in which direction.")
        st.altair_chart(
            owid.horizontal_bars(model.importance, "feature", "weight",
                                 x_title="weight", height=170, value_format=".3f",
                                 diverging=True),
            width="stretch", key="dev_importance")
        st.dataframe(
            pd.DataFrame(model.confusion,
                         index=["actual: no", "actual: yes"],
                         columns=["predicted: no", "predicted: yes"]),
            width="stretch")

    st.divider()
    st.subheader("Known development sites")
    st.dataframe(sp.KNOWN_SITES[["name", "kind", "note"]], hide_index=True, width="stretch")
    note(
        "One of these is worth pausing on. Most Dutch cities of this size moved acute hospital "
        "care to a ring-road site with a large car park; Enschede rebuilt its regional hospital "
        "on a central one. Read through the access section, that decision put the region's "
        "single largest generator of non-discretionary trips inside the walking shed of the "
        "central station instead of at the far end of a car journey — which is worth more, in "
        "the nitrogen accounting of the earlier sections, than any number of parking norms "
        "applied afterwards."
    )

    st.divider()
    figure("03", "Value surface",
           "Price per square metre implied by distance to the centre, distance to a station, "
           "local density and adjacency to open space.")
    grid_valued = model.grid.copy()
    grid_valued["value_eur_m2"] = sp.value_surface(grid_valued)
    c3, c4 = st.columns([3, 2])
    with c3:
        st.altair_chart(
            owid.raster(grid_valued, "value_eur_m2", legend_title="€/m²",
                        points=sp.KNOWN_SITES),
            width="content", key="dev_value")
    with c4:
        st.markdown("**Coefficients**")
        st.dataframe(
            pd.DataFrame([{"term": k, "value": v} for k, v in sp.VALUE_COEFFICIENTS.items()]),
            hide_index=True, width="stretch")
        note(
            "The signs on these are well established in the hedonic literature — value falls "
            "with distance from the centre and from a station, rises with local density, and "
            "carries a premium for open-space adjacency. The magnitudes here are illustrative "
            "and the surface is synthetic. Replace with the WOZ valuation file, which is public "
            "at property level, and this becomes a fitted hedonic model rather than a stated one."
        )
    provenance(SYNTHETIC, "Stated coefficients over the synthetic grid")

    st.divider()
    st.subheader("The uncomfortable part of a development-probability map")
    note(
        "A map like the one above is used in practice to justify where to invest, and it has a "
        "property worth naming: it is trained on where development *has* gone, so it predicts "
        "that development will continue to go there. As a forecast that is often right and as a "
        "basis for policy it is circular — the model will always tell you that the accessible, "
        "already-dense, already-valuable cells are the ones to build on, because that is what it "
        "was shown. It cannot tell you what would happen if you put a station somewhere new, "
        "because a feature it treats as fixed geography is in fact a decision. That is what the "
        "simulation in the next section is for: it lets the inputs move."
    )


# =====================================================================
# 11 · Simulation
# =====================================================================

def page_simulation() -> None:
    frame, series = _population()
    header(
        "11 · Simulation",
        "Running the city forward under a rule you can see",
        "A constrained cellular automaton in the tradition of SLEUTH and the land-use core of "
        "UrbanSim: each year's population increment is split between densifying built cells and "
        "converting unbuilt ones, allocation follows the development probability from the "
        "previous section, and the constraint mask decides what is off the table. It is not a "
        "novel AI method, and describing it as one would be the easiest way to make it sound "
        "more predictive than it is. Its value is comparative — the difference between two runs "
        "is meaningful even where neither run is a forecast.",
    )
    data_badge(SYNTHETIC_GRID)

    grid = _grid()

    with st.sidebar:
        st.markdown("#### Simulation")
        model_key = st.selectbox("Population path", list(MODELS),
                                 format_func=lambda k: MODELS[k].label,
                                 index=list(MODELS).index("logistic"), key="sim_model")
        horizon = st.slider("Run to", 2030, 2070, 2050, 5, key="sim_horizon")
        densification = st.slider(
            "Share of growth absorbed by densification", 0.0, 1.0, 0.6, 0.05, key="sim_dens",
            help="The rest is converted from unbuilt land.")
        persons_per_ha = st.slider("Density of new development, persons/ha", 20, 140, 65, 5,
                                   key="sim_pph")
        station_pull = st.slider("Station-oriented weighting", 0.0, 3.0, 1.0, 0.1,
                                 key="sim_station",
                                 help="How strongly allocation is pulled toward the stations.")

    dev = sp.fit_development(grid, "gbm", {})
    spec = MODELS[model_key]
    fit = fit_and_forecast(frame, spec, {p.key: p.default for p in spec.params}, horizon)
    path = pd.concat([
        frame.tail(1)[["year", "population"]],
        fit.forecast[["year", "population"]],
    ], ignore_index=True)

    with_constraints = sp.simulate(
        dev.grid, path, densification, True, station_pull, persons_per_ha)
    without = sp.simulate(
        dev.grid, path, densification, False, station_pull, persons_per_ha)

    final = with_constraints.yearly.iloc[-1]
    start = with_constraints.yearly.iloc[0]
    stats([
        (f"Built-up area {horizon}", f"{final['built_up_km2']:.1f} km²",
         f"From {start['built_up_km2']:.1f} km² today, under this rule."),
        ("Land converted", f"{final['built_up_km2'] - start['built_up_km2']:+.1f} km²",
         f"At {densification:.0%} of growth absorbed by densification."),
        (f"Built-up density {horizon}", f"{final['built_up_density']:,.0f}/km²",
         f"{(final['built_up_density'] / start['built_up_density'] - 1) * 100:+.1f}% on today."),
        ("Cost of the constraints",
         f"{without.yearly.iloc[-1]['built_up_km2'] - final['built_up_km2']:+.2f} km²",
         "Difference in converted land when the mask is switched off — the constraints' effect, "
         "read directly."),
    ])

    st.divider()
    figure("01", "Built-up area and density under the run",
           "Two outcomes of the same simulation. They move in opposite directions whenever "
           "growth is absorbed by conversion rather than by densification.")
    c1, c2 = st.columns(2)
    with c1:
        st.altair_chart(
            owid.single_line(with_constraints.yearly, "year", "built_up_km2",
                             x_title="", y_title="built-up km²", y_format=",.1f", height=260),
            width="stretch", key="sim_area")
    with c2:
        st.altair_chart(
            owid.single_line(with_constraints.yearly, "year", "built_up_density",
                             x_title="", y_title="inhabitants per built-up km²",
                             y_format=",.0f", height=260, colour=SERIES[1]),
            width="stretch", key="sim_density")
    values_table(with_constraints.yearly.round(2))

    st.divider()
    figure("02", "Where the growth lands",
           "Cells converted over the run, and the density added to cells that were already "
           "built. The constraint mask is doing visible work on the south-eastern edge.")
    c3, c4 = st.columns(2)
    with c3:
        st.altair_chart(
            owid.raster(with_constraints.final_grid.assign(
                converted_num=with_constraints.final_grid["converted"].astype(float)),
                "converted_num", legend_title="converted", points=sp.KNOWN_SITES),
            width="content", key="sim_converted")
    with c4:
        st.altair_chart(
            owid.raster(with_constraints.final_grid, "added_density",
                        legend_title="density added", points=sp.KNOWN_SITES),
            width="content", key="sim_added")

    st.divider()
    figure("03", "Value uplift implied by the added density",
           "Change in price per square metre from the density term alone. Accessibility is held "
           "fixed, because geography does not move unless somebody builds a station.")
    st.altair_chart(
        owid.raster(with_constraints.final_grid, "value_uplift", scheme="diverging",
                    legend_title="Δ €/m²", points=sp.KNOWN_SITES),
        width="content", key="sim_uplift")
    uplift = with_constraints.final_grid["value_uplift"]
    note(
        f"Total uplift across the grid comes to about "
        f"€{uplift.clip(lower=0).sum():,.0f} per square metre summed over cells — a figure worth "
        "distrusting on its own and worth reading as a distribution. The uplift concentrates "
        "where density was added to already-accessible land, which is the mechanism behind land "
        "value capture: the increment is created by the permission to build and by the transport "
        "that makes the site reachable, neither of which the landowner supplied. Whether it is "
        "captured or left with the owner is a policy choice, and it is a large one — on this "
        "surface the uplift is comparable to the cost of the infrastructure that generates it."
    )
    provenance(SYNTHETIC, "Simulation over the synthetic grid and value surface")

    st.divider()
    st.subheader("Two runs, one difference")
    delta = sp.scenario_delta(with_constraints, without)
    st.altair_chart(
        owid.single_line(delta, "year", "built_up_km2_delta",
                         x_title="", y_title="extra km² converted without the mask",
                         y_format=",.2f", height=240, colour=SERIES[1]),
        width="stretch", key="sim_delta")
    note(
        "This is the only output on the page I would defend. Both runs share every assumption "
        "except one, so the synthetic inputs cancel and what remains is the effect of the "
        "constraint mask under this rule. It is the general principle for simulation of this "
        "kind: the level is an artefact of the assumptions, and the difference between two runs "
        "that differ in one place is not."
    )

    st.divider()
    st.subheader("What this is and is not")
    note(
        "**Is:** a transparent transition rule, run forward, whose every parameter is on screen "
        "and adjustable. Useful for asking what happens to land take if densification runs at 40 "
        "per cent instead of 80, and for pricing a constraint in hectares."
    )
    note(
        "**Is not:** a prediction of Enschede in 2050. The grid is synthetic, the labels were "
        "generated from the features, the population path comes from a model that admits it "
        "cannot distinguish between plausible futures, and the rule contains no land market, no "
        "developer behaviour, no planning consent process and no feedback from prices to demand. "
        "Every one of those is a first-order omission. An agent-based model of the UrbanSim kind "
        "adds households and firms with budgets that bid against each other for locations, and "
        "that is the honest next step — but it needs the real register, the real valuation file "
        "and the real travel survey before it produces anything but a prettier version of this."
    )
