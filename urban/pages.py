"""The demographic, predictive and simulation sections.

Held apart from the constraint sections because they are a different kind of
claim. Everything in the constraint analysis can be checked with a calculator.
Nothing here can: these pages fit models, and a fitted model is an argument
about the future dressed as a measurement of the past.

The sections are therefore built to keep showing their own working — which
model, on which data, evaluated how, and what it cannot do.
"""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from . import animate
from . import cities
from . import compare
from . import demography as dem
from . import geo
from . import owid
from . import spatial as sp
from .forecast import MODELS, compare_all, fit_and_forecast
from .provenance import BADGE, SYNTHETIC, Series, worst_class
from .theme import GRID, INK_2, INK_3, SERIES, style
from .ui import (caveat, data_badge, figure, header, note, provenance, stats,
                 values_table)

LAND_AREA_KM2 = 140.0
SYNTHETIC_GRID = Series(
    "Cell grid, development labels and value surface", SYNTHETIC,
    "Generated from the stated process in urban/spatial.py",
    "Not observations of either city. The models below recover assumptions that were put in "
    "deliberately; swap in the municipal development register and the valuation roll — the WOZ "
    "file in the Netherlands, the general valuation roll in Cape Town — to make them real.",
)


@st.cache_data
def _population(city_name: str = "Enschede"):
    return cities.pick(city_name).population()


@st.cache_data
def _grid(city_name: str = "Enschede"):
    return sp.build_grid(geometry=cities.pick(city_name).geometry)


def _city(key: str = "ml_city", allow_both: bool = False, default: str = "Enschede"):
    """The city selector for a modelling section.

    This used to be a dropdown in the sidebar, and the result was a reader
    reporting that there were no models for Cape Town. There were; they could
    not be found. It is now a segmented control at the top of the content,
    which is the most prominent thing on the page because it changes the
    meaning of everything under it.

    Sections that can show both cities at once pass `allow_both`. Sections
    driven by a single set of sidebar model controls do not, because two
    parameterised models sharing one control panel would be a lie about what
    the controls apply to.
    """
    selected = compare.city_switch(key, allow_both=allow_both, default=default)
    if len(selected) == 1:
        st.caption(f"{selected[0].name.upper()}, {selected[0].country.upper()}"
                   f"  ·  {selected[0].binding_constraint}")
    return selected if allow_both else selected[0]


# =====================================================================
# 08 · Population
# =====================================================================

@st.cache_data
def _indexed_both() -> pd.DataFrame:
    """Both cities' populations rebased to their first common year."""
    out = []
    for c in cities.CITIES.values():
        f, _ = c.population()
        base = float(f["population"].iloc[0])
        out.append(pd.DataFrame({
            "year": f["year"], "entity": c.name,
            "index": f["population"] / base * 100,
        }))
    return pd.concat(out, ignore_index=True)


def _flattest_stretch(frame: pd.DataFrame, window: int = 20) -> dict:
    """The twenty years in which the city grew least.

    Enschede's plateau was hardcoded as 1975–1995, which is right for Enschede
    and meaningless for a city that never had one. Finding it instead means the
    same statistic says something true about both: for Enschede it recovers the
    textile collapse, and for Cape Town it reports the least-fast stretch of an
    unbroken climb, which is the honest answer to the same question.
    """
    best = None
    for start in range(len(frame) - window):
        a = frame["population"].iloc[start]
        b = frame["population"].iloc[start + window]
        growth = b / a - 1
        if best is None or growth < best["growth"]:
            best = {"growth": float(growth),
                    "start": int(frame["year"].iloc[start]),
                    "end": int(frame["year"].iloc[start + window])}
    return best


def page_population() -> None:
    header(
        "Where the people are, and where they came from",
        "Two cities whose population histories have almost nothing in common. One added five "
        "thousand people a decade and stopped for thirty years; the other added four million "
        "and has not stopped once. The models in the next section have to fit both, and that "
        "is where they start to disagree.",
    )
    selected = _city("pop_city", allow_both=True, default=compare.BOTH)
    both_mode = len(selected) > 1

    # ---- 01: the comparison, always shown, always first --------------
    figure("Both cities since 1950, indexed",
           "Both start at 100 in 1950, so the lines show growth rates rather than sizes. "
           "Press play to watch them separate.",
           "Indexing is the only fair way to put these two on one axis: Cape Town added more "
           "people since 1950 than Enschede has ever had, so on an absolute axis Enschede "
           "would be a flat line along the bottom. Cape Town ends near 780; Enschede near 155.")
    both = _indexed_both()
    shared = sorted(set(both[both["entity"] == "Enschede"]["year"])
                    & set(both[both["entity"] == "Cape Town"]["year"]))
    palette = {c.name: c.accent for c in cities.CITIES.values()}
    animate.player(
        "pop_indexed_both", shared,
        lambda i: st.altair_chart(
            animate.lines_upto(
                both, "year", "index", "entity", shared[i],
                x_title="", y_title="index, 1950 = 100", colours=palette,
                x_domain=(shared[0], shared[-1]),
                y_domain=(0, both["index"].max() * 1.08), height=340),
            width="stretch", key="pop_indexed_both_chart"))
    provenance("derived", "Both population series, rebased to 1950.")

    st.divider()

    # ---- 02: each city's own series, at its own scale ----------------
    figure("Each city at its own scale",
           "Absolute population. The two panels do not share an axis — Cape Town is thirty "
           "times larger, and a shared axis would show only that.",
           "Enschede's shape is three regimes with a thirty-year plateau in the middle. Cape "
           "Town's is one curve that never bends. Those two shapes are why the same seven "
           "forecasting models behave so differently on them.")

    def _one(c):
        f, sr = _population(c.name)
        yrs = f["year"].tolist()
        animate.player(
            f"pop_hist_{c.key}", yrs,
            lambda i: st.altair_chart(
                animate.lines_upto(
                    f.assign(entity=c.name), "year", "population", "entity",
                    yrs[i], x_title="", y_title="inhabitants",
                    colours={c.name: c.accent},
                    x_domain=(yrs[0], yrs[-1]),
                    y_domain=(0, f["population"].max() * 1.08), height=300),
                width="stretch", key=f"pop_history_{c.key}"))
        first, last = f.iloc[0], f.iloc[-1]
        slowest = _flattest_stretch(f)
        st.caption(
            f"{first['population']:,.0f} in {int(first['year'])} → "
            f"{last['population']:,.0f} in {int(last['year'])} "
            f"({last['population'] / first['population'] - 1:+.0%}). Slowest twenty years: "
            f"{slowest['start']}–{slowest['end']}, {slowest['growth']:+.0%}.")

    compare.facet_rasters(_one, selected)
    for c in selected:
        f, sr = _population(c.name)
        st.caption(f"{c.name} — {sr.caption()}")

    st.divider()

    # ---- the rest of the page runs per selected city -----------------
    for city in selected:
        frame, series = _population(city.name)
        if both_mode:
            compare.city_header(city)
        _population_detail(city, frame, series, both_mode)
        if both_mode and city is not selected[-1]:
            st.divider()


def _population_detail(city, frame, series, both_mode: bool) -> None:
    """Per-city detail: what drives the change, and density."""
    if city.key == "enschede":
        figure("What drives the change: births, and people moving",
               "Three things that add or remove people each year. Bars above zero add, bars "
               "below take away.",
               "The overall change is the distance from the bottom of the stack to the top — not "
               "the height of any one bar. Watch the blue shrink: births minus deaths used to "
               "add 2,000 people a year and now adds almost none.")
        flows = dem.components_of_change(frame["year"].to_numpy())
        long = flows.melt(id_vars="year", var_name="component", value_name="people")
        st.altair_chart(
            owid.stacked_components(long, "year", "people", "component",
                                    x_title="", y_title="people per year", height=300),
            width="stretch", key="pop_flows")
        values_table(flows.tail(20))
        data_badge(dem.FLOW_SERIES)
        note(
            "This is the chart that explains the plateau, and it is the one a total-population "
            "line cannot show. Natural increase fell away decades ago and is now marginal. Net "
            "domestic migration has been negative for most of the period — Enschede trains "
            "graduates and the Randstad hires them, which is the standard fate of a university "
            "city far from the economic core. What has held the total up since the 1990s is "
            "international migration. A city whose growth rests on one of three components, and "
            "the most policy-sensitive one, has a thinner base than its headline number suggests."
        )
    else:
        st.subheader("What drives the change")
        st.info(
            "**This one chart is missing for Cape Town, and it is not being faked.** The "
            "decomposition into births, domestic migration and international migration needs an "
            "annual components-of-change series. There is a reconstructed one for Enschede in "
            "this project; there is no equivalent here, and inventing South African internal "
            "migration figures to fill the space would be worse than leaving it empty. "
            "Stats SA's mid-year population estimates carry the components — wire those in and "
            "this chart appears with no other change."
        )
        note(
            "Every other model in this part runs identically on both cities. This is the only "
            "place they differ, and it differs because of a missing input rather than a "
            "decision about which city deserved the attention."
        )

    st.divider()
    figure(f"Two ways of measuring density — {city.name}",
           "People per km². The orange line divides by the whole municipality; the blue divides "
           "only by the part that is actually built on.",
           "When the two lines pull apart, the city is spreading out faster than it is growing. "
           "That is sprawl, and the whole-municipality figure cannot show it — it can sit "
           "perfectly flat while the built-up part empties out.")
    density = dem.density_series(frame, land_area_km2=city.land_area_km2)
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
        width="stretch", key=f"pop_density_{city.key}")
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
    city = _city()
    frame, series = _population(city.name)
    header(
        f"Predicting {city.name}'s population in 2050",
        f"Seventy-five years of a smooth series cannot tell you where this city is heading. The "
        f"choice of model decides that, and the choice of model is a guess. So this is not a "
        f"forecast. It is a control panel: change the model and watch 2050 move while the data "
        f"stays exactly the same. {city.forecast_note}",
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
        caveat("What this model cannot do", w, "caution")

    st.divider()
    figure(f"History and projection to {horizon}",
           "Solid line is what happened. Dashed line is what the model you picked expects.",
           "The dash is not decoration. The solid part is measured; the dashed part is a guess "
           "with arithmetic attached. Change the model in the sidebar and watch only the dashed "
           "part move.")
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
        figure("Predicted versus what actually happened",
               "Each dot is one withheld year.",
               "The dashed diagonal is a perfect prediction. How far a dot sits from it is the "
               "error. Several dots on the same side means the model is not just noisy, it is "
               "consistently wrong in one direction.")
        st.altair_chart(owid.scatter_actual_predicted(fit.backtest),
                        width="stretch", key="fc_scatter")
    with c2:
        figure("How far off the model was, year by year",
               "What actually happened, minus what the model said.",
               "You want this to look like random noise around zero. A pattern — a run of bars "
               "on one side, or a wave — means the model has missed something real.")
        st.altair_chart(owid.residual_plot(fit.residuals), width="stretch", key="fc_resid")

    st.dataframe(
        pd.DataFrame([{k: (f"{v:,.3f}" if isinstance(v, float) else v)
                       for k, v in fit.metrics.items()}]),
        hide_index=True, width="stretch")

    st.divider()
    st.subheader("All the models side by side")
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
    st.subheader("What a real forecast would need")
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

def _mask_map(city) -> None:
    """One city's constraint mask, drawn at that city's own extent."""
    g = _grid(city.name)
    g = g.assign(state=np.where(~g["developable"], "Withheld", "Available"))
    e = city.geometry.extent_km
    chart = (
        alt.Chart(g)
        .mark_square(size=max(6, int(1900 / e)))
        .encode(
            x=alt.X("x:Q", title=None, scale=alt.Scale(domain=[-e, e]),
                    axis=alt.Axis(grid=False, labels=False, ticks=False)),
            y=alt.Y("y:Q", title=None, scale=alt.Scale(domain=[-e, e]),
                    axis=alt.Axis(grid=False, labels=False, ticks=False)),
            color=alt.Color("state:N",
                            scale=alt.Scale(domain=["Available", "Withheld"],
                                            range=["#d8d5cd", SERIES[1]]),
                            legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["state"],
        )
        .properties(width=300, height=300)
    )
    st.altair_chart(style(chart), width="content", key=f"mask_{city.key}")
    withheld = 1 - g["developable"].mean()
    st.caption(f"{withheld:.0%} of the modelled frame is withheld · "
               f"{e * 2:.0f} × {e * 2:.0f} km")


def page_development() -> None:
    header(
        "Predicting where building happens",
        "Two models. One predicts which areas get built on, using how reachable they are, how "
        "dense they already are, and which land is off-limits. The other estimates what land is "
        "worth. Both run on made-up data, and this page keeps saying so, because a map of where "
        "building will happen is the most convincing-looking thing in this whole project and it "
        "has not earned that.",
    )
    city = _city("dev_city")

    # The two constraint masks, side by side, before any model runs. This is
    # the report's thesis as geometry: a bog and a border against a mountain
    # and an ocean, and the fact that both cities' models are looking at the
    # same *kind* of picture is the reason they can be compared at all.
    figure("What each model is allowed to build on",
           "Grey is available. Orange is withheld by a constraint. Both cities, at their own "
           "scales — Cape Town's frame is four times wider.",
           "Cape Town loses a large connected mass to the mountain and the coast, and what "
           "survives is a ring. Enschede loses a small bite to the bog and a straight edge to "
           "the border, and what survives looks generous — which is the trap, because the "
           "constraint that actually stops Enschede building does not appear on this map at "
           "all. Nitrogen has no shape.")
    compare.facet_rasters(_mask_map, list(cities.CITIES.values()))
    provenance("synthetic", "Constraint masks from the geometry in urban/cities.py.")

    st.divider()
    data_badge(SYNTHETIC_GRID)

    grid = _grid(city.name)

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

    caveat(
        "Read these scores correctly",
        "The labels were generated from these same features by a process written down in "
        "<code>urban/spatial.py</code>. A high score therefore measures whether the learner can "
        "recover assumptions that were deliberately put there — it is a test of the pipeline, "
        f"not evidence about {city.name}. The honest use of this page is to check that the "
        "machinery works and to see how the classifier families differ; the moment real labels "
        "arrive, the same code becomes a real model and nothing else changes.",
        "critical")

    st.divider()
    c1, c2 = st.columns([3, 2])
    with c1:
        figure("How likely each area is to be built on",
               "Darker blue means the model thinks building is more likely there.",
               "The hole in the surface is protected land and the straight edge is the hard "
               "boundary — the German border for Enschede, the Atlantic for Cape Town. Both are "
               "set to zero by the rules, not by the model, which never sees them as an option.")
        st.altair_chart(
            owid.raster(model.grid, "p_develop", legend_title="p(develop)",
                        points=city.sites(), point_labels=True),
            width="content", key=f"dev_map_{city.key}")
        st.caption(
            f"Marked points are real {city.name} locations. Coordinates are approximate and "
            f"programme and status are not verified; they are here to give the surface something "
            f"recognisable to be read against, not as a development register."
        )
    with c2:
        figure("What the model uses to decide",
               "How much each input matters.",
               "For the logistic model these are directional — negative means it pushes "
               "building away. For the two tree models they only show how much an input gets "
               "used, not which way it pushes.")
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
    st.subheader(f"Places in {city.name} worth knowing")
    st.dataframe(city.sites()[["name", "kind", "note"]], hide_index=True, width="stretch")
    if city.key == "enschede":
        note(
            "One of these is worth pausing on. Most Dutch cities of this size moved acute "
            "hospital care to a ring-road site with a large car park; Enschede rebuilt its "
            "regional hospital on a central one. Read through the access section, that decision "
            "put the region's single largest generator of non-discretionary trips inside the "
            "walking shed of the central station instead of at the far end of a car journey — "
            "which is worth more, in the nitrogen accounting of the earlier sections, than any "
            "number of parking norms applied afterwards."
        )
    else:
        note(
            "Two of these are worth pausing on, and they are the same point twice. Khayelitsha "
            "and Mitchells Plain hold well over a million people between them, and both sit "
            "twenty kilometres from the CBD because they were placed there under apartheid-era "
            "removals. That is why the density comparison in the Cape Town section is "
            "misleading if read as a success: the city is dense, and dense in the places "
            "furthest from the work. A model that allocates new building by accessibility "
            "alone, as the one on this page does, will keep proposing the opposite pattern and "
            "will be right to — which is a statement about the last seventy years, not a plan "
            "for the next thirty."
        )

    st.divider()
    figure("What land is worth, by location",
           "Estimated price per square metre.",
           "Four things drive it: how far to the centre, how far to a station, how dense the "
           "area already is, and whether open space is next door. This is a made-up surface "
           f"showing the shape of the relationship, not {city.name} prices.")
    grid_valued = model.grid.copy()
    grid_valued["value_eur_m2"] = sp.value_surface(
        grid_valued, radius_km=city.geometry.radius_km)
    c3, c4 = st.columns([3, 2])
    with c3:
        st.altair_chart(
            owid.raster(grid_valued, "value_eur_m2", legend_title="€/m²",
                        points=city.sites()),
            width="content", key=f"dev_value_{city.key}")
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
    st.subheader("The problem with this kind of map")
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
    city = _city()
    frame, series = _population(city.name)
    header(
        f"Simulating {city.name}'s growth to 2050",
        "Each year, the extra people are split between filling in areas already built on and "
        "building on new land. Where the new building goes follows the map from the previous "
        "section, and protected land is off the table. This is an old and well-known method "
        "(it is called a cellular automaton; SLEUTH and UrbanSim are the standard examples), "
        "not new AI, and saying otherwise would just make it sound more predictive than it is. "
        "What it is good for is comparison: the difference between two runs means something "
        "even when neither run is a forecast.",
    )
    data_badge(SYNTHETIC_GRID)

    grid = _grid(city.name)

    with st.sidebar:
        st.markdown("#### Simulation")
        model_key = st.selectbox("Population path", list(MODELS),
                                 format_func=lambda k: MODELS[k].label,
                                 # See the note in pages_simulator: a logistic
                                 # fitted to Enschede's plateau predicts a small
                                 # decline, so it makes every lever on this page
                                 # look inert.
                                 index=list(MODELS).index("linear"), key="sim_model")
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

    # The cell size comes from the city, not from the default. Cape Town's grid
    # is 800 m cells against Enschede's 200 m, and a simulation that assumed
    # 200 m would under-report converted land by a factor of sixteen.
    spacing = city.geometry.spacing_km
    with_constraints = sp.simulate(
        dev.grid, path, densification, True, station_pull, persons_per_ha,
        spacing_km=spacing)
    without = sp.simulate(
        dev.grid, path, densification, False, station_pull, persons_per_ha,
        spacing_km=spacing)

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
    figure("Built-up area and density over the run",
           "Left: how much land is built on. Right: how many people per km² of it.",
           "These two move in opposite directions whenever growth spreads outward instead of "
           "filling in. Drag the densification slider in the sidebar and watch them trade off.")
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
    figure("Where the growth ends up",
           "Left: land newly built on. Right: extra people added where building already was.",
           "The gap on the south-eastern edge is protected land the simulation is not allowed "
           "to touch. That gap is the constraint doing its job, made visible.")
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
    figure("How much land values go up",
           "Change in price per square metre after the simulated building.",
           "Only density changes here — distance to the centre and to a station stay put, "
           "because geography does not move unless someone builds a new station. So this is the "
           "value created purely by permission to build more.")
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
    st.subheader("The only number here worth trusting")
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
    st.subheader("What this can and cannot tell you")
    note(
        "**Is:** a transparent transition rule, run forward, whose every parameter is on screen "
        "and adjustable. Useful for asking what happens to land take if densification runs at 40 "
        "per cent instead of 80, and for showing where a constraint pushes development to, which is what it actually changes."
    )
    note(
        f"**Is not:** a prediction of {city.name} in 2050. The grid is synthetic, the labels were "
        "generated from the features, the population path comes from a model that admits it "
        "cannot distinguish between plausible futures, and the rule contains no land market, no "
        "developer behaviour, no planning consent process and no feedback from prices to demand. "
        "Every one of those is a first-order omission. An agent-based model of the UrbanSim kind "
        "adds households and firms with budgets that bid against each other for locations, and "
        "that is the honest next step — but it needs the real register, the real valuation file "
        "and the real travel survey before it produces anything but a prettier version of this."
    )


# =====================================================================
# Cape Town
# =====================================================================

def page_cape_town() -> None:
    from . import capetown as ct

    header(
        "Cape Town: running out of room",
        "Cape Town has the opposite problem to Enschede. Enschede has land it cannot build "
        "on. Cape Town has almost no land left at all. Mountain on one side, ocean on two, "
        "and about a third of what remains is protected nature. What is left is a flat sandy "
        "plain that is both the worst ground to build on and the roof of the city's emergency "
        "water supply.",
    )

    stats([
        ("Land you can build on", f"{ct.URBAN_EDGE_KM2 / ct.MUNICIPAL_KM2 * 100:.0f}%",
         f"{ct.URBAN_EDGE_KM2} km² inside the urban edge, out of {ct.MUNICIPAL_KM2:,} km² of city."),
        ("People per km² of it", f"{ct.PEOPLE_PER_BUILDABLE_KM2:,.0f}",
         "Roughly five times Enschede's figure, on much harder ground."),
        ("Protected nature", f"{ct.PROTECTED_SHARE}%",
         f"{ct.PROTECTED_HA:,} hectares formally protected, before biodiversity areas count."),
        ("Original plant life gone", f"{ct.VEGETATION_LOST_PCT}%",
         "Mostly on the flat lowlands, which is where building is easiest."),
    ])

    st.divider()
    figure("Where Cape Town's land goes",
           "The whole municipality, split three ways. The blue block is everything the city "
           "is allowed to build on.")
    st.altair_chart(owid.land_split_bar(ct.land_split(), ct.MUNICIPAL_KM2),
                    width="stretch", key="ct_land")
    values_table(ct.land_split()[["part", "km2", "detail"]])
    note(
        f"The municipal total is worked out from the city's own numbers rather than looked up: "
        f"{ct.PROTECTED_HA:,} hectares is stated as {ct.PROTECTED_SHARE}% of the city, which "
        f"makes the whole {ct.MUNICIPAL_KM2:,} km². That matches the published area, which is a "
        f"useful sign the two figures agree."
    )
    provenance("derived", "City of Cape Town")

    st.divider()
    figure("Cape Town on the map",
           "The places this section talks about, on an OpenStreetMap background.",
           "Notice the geography doing the work: the CBD is pinned against the mountain and the "
           "sea in the north-west, while the housing is twenty-five kilometres away on the "
           "Cape Flats, out past the airport.")
    st.pydeck_chart(geo.places_map(geo.CT_PLACES, centre=geo.CAPE_TOWN_CENTRE, zoom=9.6),
                    height=470)
    st.markdown(geo.legend_html([
        ("Jobs and transport", SERIES[0]),
        ("Centre, rail and edges", SERIES[1]),
        ("Protected or farmed", SERIES[2]),
    ]), unsafe_allow_html=True)
    st.caption(f"{geo.OSM_ATTRIBUTION} Positions are approximate.")

    st.divider()
    figure("How much room is actually left",
           "Land per person, counted three ways.",
           "The headline is 895 km² for 4.8 million people. But most of that is already built "
           "on. What is left to build on works out at about 52 m² each — a quarter of a tennis "
           "court per person, including all the roads and parks that land still has to carry.")
    budget = ct.land_budget()
    st.altair_chart(
        owid.horizontal_bars(budget.assign(**{"m² per person": budget["m2_per_person"].round(0)}),
                             "measure", "m² per person",
                             x_title="m² of land per resident", height=190,
                             value_format=",.0f"),
        width="stretch", key="ct_budget")
    values_table(budget[["measure", "km2", "note"]])
    provenance("derived", "City of Cape Town figures, built share estimated")

    st.divider()
    figure("Protection comes in three layers",
           "Each tier restricts development a little less than the one above it.",
           "The headline protected figure is 22.7%. Add the two tiers below it and roughly a "
           "third of the city is restricted — which is why the buildable area is so much smaller "
           "than the municipality.")
    stack = ct.biodiversity_stack()
    st.altair_chart(
        owid.horizontal_bars(stack, "tier", "share",
                             x_title="% of land in this tier", height=180,
                             value_format=".1f"),
        width="stretch", key="ct_bionet")
    values_table(stack)
    provenance("official", "City of Cape Town biodiversity plan")

    st.divider()
    figure("Density, on the land people actually occupy",
           "People per km² of buildable land, not of whole municipality.",
           "Cape Town is already denser than Enschede or Johannesburg on the land it uses. The "
           "problem is not that Cape Town is sprawling by world standards — it is that the land "
           "it has left is the worst land it has.")
    dens = ct.density_comparison()
    st.altair_chart(
        owid.horizontal_bars(dens, "city", "people_per_km2",
                             x_title="people per km² of usable land", height=210,
                             value_format=",.0f"),
        width="stretch", key="ct_density")
    values_table(dens)
    provenance("estimate", "Mixed bases — see the table; the comparators are not recomputed here")

    st.divider()
    st.subheader("The four limits")
    note("Two of these are lines on a map and two are measurements. That split matters, "
         "because you can only argue about a line, whereas a measurement can be brought down.")
    for _, row in ct.LIMITS.iterrows():
        with st.expander(f"{row['limit']}  ·  {row['kind']}"):
            st.markdown(f"**What it is** — {row['what']}")
            st.markdown(f"**What it does** — {row['does']}")
            st.markdown(f"**Can it be brought down?** — {row['fixable']}")

    st.divider()
    st.subheader("The trap")
    st.markdown(
        f"Put the four together and you get a loop the city cannot easily escape. The urban "
        f"edge stops outward growth. Protected nature takes a third of the land. That leaves "
        f"the Cape Flats — flat, available, cheap."
    )
    st.markdown(
        f"But the Cape Flats is loose sand that can lose its strength in an earthquake between "
        f"about {ct.LIQUEFIABLE_FROM_M} and {ct.LIQUEFIABLE_TO_M:.0f} metres down. That is "
        f"exactly the depth foundations for tall buildings sit in, so building upward there "
        f"costs far more than it should. So the city builds outward and low instead, on the "
        f"cheapest land at the edge — furthest from the jobs."
    )
    st.markdown(
        f"And underneath that same sand is the aquifer: about {ct.AQUIFER_YIELD_MM3} million "
        f"cubic metres of water a year, which the city turned to when the dams nearly ran dry. "
        f"The sand that makes the water reachable is the same sand that lets anything spilled "
        f"on the surface reach it."
    )
    _, aquifer_days = ct.water_budget()
    st.info(
        "**So the limit pushes housing onto the one piece of land where building up is most "
        "expensive and where building at all threatens the water.** Every part of that is a "
        "reasonable decision on its own. Together they trap the city."
    )
    note(
        f"It is worth knowing how much water that actually is. The aquifer's "
        f"{ct.AQUIFER_YIELD_MM3} million cubic metres a year sounds enormous. Divided by what "
        f"the city drinks, it is about **{aquifer_days} days** of supply. That is not a "
        f"replacement for the dams — it is a buffer, and a buffer is exactly the kind of thing "
        f"you cannot afford to contaminate."
    )

    st.divider()
    st.subheader("Trains")
    st.markdown(
        f"About {ct.STATION_SHARE * 100:.0f}% of the land inside the urban edge is within an "
        f"800 metre walk of a station — {ct.STATION_BUFFERS_KM2} km² out of "
        f"{ct.URBAN_EDGE_KM2} km². That is usually read as proof the city needs decades of new "
        f"rail. Be careful with it. Cape Town already has a big rail network, and the access "
        f"section works through why that 20% is mostly a statement about how far people are "
        f"assumed to walk. And since the network was largely stripped by theft, coverage has "
        f"been beside the point: a station you can walk to is worth nothing if no train comes."
    )
    st.caption(
        "Figures on this page are the City of Cape Town's published numbers and research on "
        "the Cape Flats, plus one third-party station calculation, repeated as given. Nothing "
        "here is recomputed from source data — unlike the Enschede sections."
    )


def page_compare() -> None:
    from . import capetown as ct

    header(
        "Everything that is measured for one, measured for the other",
        "The two cities are in one project because they are hard to build in for opposite "
        "reasons, and the comparison shows something neither shows alone: what kind of limit "
        "you face decides what you can do about it. This page is the comparison in full — the "
        "scorecard, the ratios, and the questions answered twice.",
    )

    df = compare.scorecard_frame()
    en, ctn = df.iloc[0], df.iloc[1]

    stats([
        ("Cape Town is this many times larger",
         f"{ctn['Population'] / en['Population']:.0f}×", "By population."),
        ("…but only this much more built land",
         f"{ctn['Built-up, km²'] / en['Built-up, km²']:.0f}×",
         "Which is why it is the denser of the two."),
        ("Cape Town's limit", "A polygon",
         "You can argue about where the line goes; you cannot make it smaller."),
        ("Enschede's limit", "A field",
         "A number per hectare per year. No line to move, and no site that is safe."),
    ])

    st.divider()
    st.subheader("The scorecard")
    compare.scorecard()
    provenance("derived", "Computed from the population series and land ledgers.")

    st.divider()
    figure(
        "Where the two cities differ most",
        "Cape Town divided by Enschede, on each measure. A bar at 1 means they are equal.",
        reads_as="The axis is logarithmic, so equal distances are equal ratios. Population is "
                 "thirty times apart and built-up land only fifteen — that gap is the density "
                 "difference. The measure that matters is at the bottom: land each city may "
                 "still build on. Enschede's is zero, so the ratio is infinite and the bar "
                 "runs off the chart, which is the honest way to draw it.")
    ratio_rows = [
        ("Population", ctn["Population"], en["Population"]),
        ("Municipal area", ctn["Municipal area, km²"], en["Municipal area, km²"]),
        ("Built-up land", ctn["Built-up, km²"], en["Built-up, km²"]),
        ("People per built km²", ctn["Density per built km²"], en["Density per built km²"]),
        ("Growth since 1950", 1 + ctn["Growth since 1950"], 1 + en["Growth since 1950"]),
        ("Land physically left", ctn["Land physically left, km²"],
         en["Land physically left, km²"]),
    ]
    rat = pd.DataFrame([
        {"measure": m, "ratio": a / b if b else np.inf} for m, a, b in ratio_rows])
    rat["label"] = [f"{v:.1f}×" for v in rat["ratio"]]
    bars = (
        alt.Chart(rat)
        .mark_bar(height=20, cornerRadiusEnd=2, color=SERIES[1])
        .encode(
            y=alt.Y("measure:N", sort=list(rat.sort_values("ratio")["measure"]), title=None),
            x=alt.X("ratio:Q", title="Cape Town ÷ Enschede",
                    scale=alt.Scale(type="log"),
                    axis=alt.Axis(format="~g", grid=True, gridColor=GRID)),
            tooltip=["measure", alt.Tooltip("ratio:Q", format=".2f")],
        )
    )
    tick = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(
        strokeWidth=1.5, color=INK_3, strokeDash=[4, 3]).encode(x="x:Q")
    txt = bars.mark_text(align="left", dx=6, fontSize=11, color=INK_2).encode(
        text="label:N", color=alt.value(INK_2))
    st.altair_chart(style(alt.layer(bars, tick, txt).properties(
        height=230, padding={"right": 46})), width="stretch", key="cmp_ratio")
    note(
        "The dashed line is parity. Cape Town is larger on every physical measure and denser "
        "per built square kilometre, which is the finding people find surprising — a South "
        "African metro built around the car is more densely occupied, on the land it actually "
        "uses, than a compact Dutch city. Enschede's low figure is not sprawl in the American "
        "sense; it is a small city with a large agricultural municipality attached, and it is "
        "exactly why the gross-density measure had to be split in two in the population section."
    )

    st.divider()
    st.subheader("The same questions, both cities")
    for i, row in enumerate(ct.COMPARISON, 1):
        st.markdown(f"**{i:02d} · {row['question']}**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f":orange[**Cape Town**]")
            st.caption(row["ct"])
        with c2:
            st.markdown(f":blue[**Enschede**]")
            st.caption(row["en"])
        note(row["so"])
        st.write("")

    st.divider()
    st.subheader("The numbers next to each other")
    st.dataframe(ct.SIDE_BY_SIDE, hide_index=True, width="stretch")

    st.divider()
    st.subheader("What both cities have in common")
    for title, body in ct.SHARED_LESSONS:
        st.markdown(f"**{title}**")
        note(body)

    st.divider()
    st.subheader("What is still not equal here")
    note(
        "Both cities now run through the same land ledger, the same population models, the "
        "same development classifier, the same growth simulation and the same workbench. Two "
        "things remain uneven and neither is hidden. Cape Town has no annual "
        "components-of-change series here, so the births-and-migration decomposition exists "
        "for Enschede only. And section 3 spends five sections on Enschede's nitrogen because "
        "a field constraint takes that long to explain, while Cape Town's limit takes one "
        "because a reader already understands a fence."
    )
    note(
        "The deeper inequality is in the sourcing. The Enschede constraint figures are worked "
        "from Dutch statutory documents; the Cape Town figures come from published city "
        "documents and one third-party calculation, repeated as given. Redoing the Cape Town "
        "side from the open data portal at source is the obvious next step, and until it "
        "happens this is a fair comparison of two cities rather than of two analyses."
    )
