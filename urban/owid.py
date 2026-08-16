"""Chart forms in the Our World in Data idiom.

Four habits distinguish that idiom from a default plotting library, and all
four are about removing the reader's work rather than adding decoration:

  1. **Series are labelled at the line, not in a legend.** A legend makes the
     reader hold a colour in their head and carry it across the plot. A label
     at the end of the line is read where the eye already is.
  2. **Comparisons are indexed.** Putting a city of 160,000 beside one of
     900,000 on a shared absolute axis compares sizes when the question was
     about rates. Indexing to a base year answers the question that was asked.
  3. **Projections look like projections.** History is solid, forecast is
     dashed, and where the model produces one, uncertainty is a band rather
     than a footnote nobody reads.
  4. **The source rides with the chart.** Provenance under the figure, not in
     an appendix.

The functions here build the first three. The fourth is the caller's job and
the app does it on every figure.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

from .theme import DIVERGING, GRID, INK, INK_2, INK_3, SEQUENTIAL, SERIES, SHED_PX, SURFACE, style


def _end_points(df: pd.DataFrame, x: str, entity: str) -> pd.DataFrame:
    """The last observation of each series, where its label goes."""
    return df.sort_values(x).groupby(entity, as_index=False).tail(1)


def line_with_end_labels(
    df: pd.DataFrame,
    x: str,
    y: str,
    entity: str,
    *,
    x_title: str,
    y_title: str,
    highlight: str | None = None,
    y_format: str = ",.0f",
    height: int = 330,
    y_domain: tuple | None = None,
    zero: bool = False,
    log: bool = False,
    x_format: str = "d",
) -> alt.Chart:
    """Multi-series lines, labelled at the right-hand end.

    When one entity is the subject, it is picked out and the rest recede to a
    muted grey. Emphasis rather than identity: the greys are not eight
    categories the reader has to tell apart, they are context.

    `log` switches the measured axis to a log scale, for comparing growth
    rates rather than levels. Callers must say so in the subtitle.
    """
    entities = list(df[entity].unique())
    if highlight and highlight in entities:
        colour = alt.Color(
            f"{entity}:N",
            scale=alt.Scale(domain=[highlight], range=[SERIES[0]]),
            legend=None,
        )
        opacity = alt.condition(
            alt.datum[entity] == highlight, alt.value(1.0), alt.value(0.32))
        stroke = alt.condition(
            alt.datum[entity] == highlight, alt.value(SERIES[0]), alt.value(INK_3))
    else:
        colour = alt.Color(f"{entity}:N", scale=alt.Scale(range=SERIES), legend=None)
        opacity = alt.value(1.0)
        stroke = colour

    y_scale = alt.Scale(zero=zero, type="log" if log else "linear")
    if y_domain:
        y_scale = alt.Scale(domain=list(y_domain), nice=False)

    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format=x_format, grid=False)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=y_scale,
                axis=alt.Axis(format=y_format, grid=True, gridColor=GRID)),
    )
    lines = base.mark_line(strokeWidth=2, strokeCap="round", strokeJoin="round").encode(
        color=stroke, opacity=opacity,
        tooltip=[entity, alt.Tooltip(f"{x}:Q", format=x_format),
                 alt.Tooltip(f"{y}:Q", format=y_format)],
    )

    ends = _end_points(df, x, entity)
    dots = alt.Chart(ends).mark_point(
        filled=True, size=64, stroke=SURFACE, strokeWidth=2).encode(
        x=f"{x}:Q", y=f"{y}:Q", color=stroke, opacity=opacity)
    labels = alt.Chart(ends).mark_text(
        align="left", dx=9, fontSize=11, color=INK_2).encode(
        x=f"{x}:Q", y=f"{y}:Q", text=f"{entity}:N", opacity=opacity)

    return style(alt.layer(lines, dots, labels).properties(height=height))


def single_line(
    df: pd.DataFrame, x: str, y: str, *, x_title: str, y_title: str,
    label: str | None = None, height: int = 300, y_format: str = ",.0f",
    zero: bool = False, colour: str = SERIES[0], x_format: str = "d",
) -> alt.Chart:
    """One series needs no legend — the title already says what is plotted."""
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format=x_format, grid=False)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=alt.Scale(zero=zero),
                axis=alt.Axis(format=y_format, grid=True, gridColor=GRID)),
    )
    line = base.mark_line(strokeWidth=2, strokeCap="round", color=colour).encode(
        tooltip=[alt.Tooltip(f"{x}:Q", format=x_format),
                 alt.Tooltip(f"{y}:Q", format=y_format)])
    last = df.sort_values(x).tail(1)
    dot = alt.Chart(last).mark_point(
        filled=True, size=70, color=colour, stroke=SURFACE, strokeWidth=2).encode(
        x=f"{x}:Q", y=f"{y}:Q")
    text = alt.Chart(last).mark_text(
        align="left", dx=9, fontSize=11, color=INK_2).encode(
        x=f"{x}:Q", y=f"{y}:Q",
        text=alt.Text(f"{y}:Q", format=y_format) if label is None else alt.value(label))
    return style(alt.layer(line, dot, text).properties(height=height))


def stacked_components(
    df: pd.DataFrame, x: str, value: str, component: str, *,
    x_title: str, y_title: str, height: int = 300,
) -> alt.Chart:
    """Components of change, stacked around zero.

    Negative components stack below the axis and positive above, so the net is
    read as the distance between the top of the stack and the bottom — which is
    the only way to see that a city can grow while losing people to the rest of
    the country.
    """
    order = list(df[component].unique())
    bars = (
        alt.Chart(df)
        .mark_bar(stroke=SURFACE, strokeWidth=1)
        .encode(
            x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format="d", grid=False)),
            y=alt.Y(f"{value}:Q", title=y_title, stack="zero",
                    axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
            color=alt.Color(f"{component}:N", sort=order,
                            scale=alt.Scale(domain=order, range=SERIES),
                            legend=alt.Legend(orient="top")),
            tooltip=[component, alt.Tooltip(f"{x}:Q", format="d"),
                     alt.Tooltip(f"{value}:Q", format=",.0f")],
        )
    )
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        strokeWidth=1, color=INK_3).encode(y="y:Q")
    return style(alt.layer(bars, zero).properties(height=height))


def projection(
    history: pd.DataFrame, forecast: pd.DataFrame, *,
    x: str = "year", y: str = "population",
    x_title: str = "", y_title: str = "", height: int = 340,
    band: bool = True, band_cols: tuple[str, str] = ("lower", "upper"),
) -> alt.Chart:
    """History solid, forecast dashed, uncertainty as a band if there is one.

    The dash is not decoration. A projection drawn in the same stroke as the
    history invites the reader to treat the two as the same kind of statement,
    and they are not: one is a measurement and the other is an assumption with
    arithmetic attached.

    `band_cols` names the interval columns to draw. A model-native band uses
    the default ("lower", "upper"); a conformal band passes
    ("conf_lower", "conf_upper") so the two can be told apart.
    """
    layers = []

    lo_col, hi_col = band_cols
    if band and {lo_col, hi_col} <= set(forecast.columns):
        layers.append(
            alt.Chart(forecast).mark_area(opacity=0.14, color=SERIES[0]).encode(
                x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format="d", grid=False)),
                y=alt.Y(f"{lo_col}:Q", title=y_title,
                        axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
                y2=f"{hi_col}:Q",
            )
        )

    layers.append(
        alt.Chart(history).mark_line(strokeWidth=2, color=SERIES[0], strokeCap="round").encode(
            x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format="d", grid=False)),
            y=alt.Y(f"{y}:Q", title=y_title, scale=alt.Scale(zero=False),
                    axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
            tooltip=[alt.Tooltip(f"{x}:Q", format="d"), alt.Tooltip(f"{y}:Q", format=",.0f")],
        )
    )

    # Join the two so the dashed line starts where the solid one ends rather
    # than floating a year away from it.
    bridge = pd.concat([history.tail(1)[[x, y]], forecast[[x, y]]], ignore_index=True)
    layers.append(
        alt.Chart(bridge).mark_line(
            strokeWidth=2, color=SERIES[1], strokeDash=[5, 4], strokeCap="round").encode(
            x=f"{x}:Q", y=f"{y}:Q",
            tooltip=[alt.Tooltip(f"{x}:Q", format="d"), alt.Tooltip(f"{y}:Q", format=",.0f")])
    )

    end = forecast.tail(1)
    layers.append(alt.Chart(end).mark_point(
        filled=True, size=80, color=SERIES[1], stroke=SURFACE, strokeWidth=2).encode(
        x=f"{x}:Q", y=f"{y}:Q"))
    layers.append(alt.Chart(end).mark_text(
        align="right", dy=-14, fontSize=11, color=INK_2).encode(
        x=f"{x}:Q", y=f"{y}:Q", text=alt.Text(f"{y}:Q", format=",.0f")))

    return style(alt.layer(*layers).properties(height=height))


def ensemble_chart(history: pd.DataFrame, ensemble: dict, *,
                   x: str = "year", y: str = "population",
                   y_title: str = "inhabitants", height: int = 380) -> alt.Chart:
    """The one projection the registry will defend, with its calibrated band.

    History is solid ink. The ensemble mean is a dashed line, the conformal
    band a shaded region that widens with distance and with disagreement
    between the member families. Where a single-model chart shows one guess,
    this shows the weighted answer the whole registry converges on — and how
    much room is honestly left around it.
    """
    hist = history.rename(columns={y: "value"})
    fc = pd.DataFrame({
        x: ensemble["years"], "mean": ensemble["mean"],
        "lower": ensemble["lower"], "upper": ensemble["upper"],
    })

    band = alt.Chart(fc).mark_area(opacity=0.13, color=SERIES[0]).encode(
        x=alt.X(f"{x}:Q", title="", axis=alt.Axis(format="d", grid=False)),
        y=alt.Y("lower:Q", title=y_title,
                axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
        y2="upper:Q",
    )
    hist_line = alt.Chart(hist).mark_line(
        strokeWidth=2, color=SERIES[0], strokeCap="round").encode(
        x=alt.X(f"{x}:Q", axis=alt.Axis(format="d", grid=False)),
        y=alt.Y("value:Q", scale=alt.Scale(zero=False),
                axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
        tooltip=[alt.Tooltip(f"{x}:Q", format="d"), alt.Tooltip("value:Q", format=",.0f")],
    )
    bridge = pd.concat([
        hist.tail(1)[[x]].assign(mean=hist["value"].iloc[-1]),
        fc[[x, "mean"]],
    ], ignore_index=True)
    mean_line = alt.Chart(bridge).mark_line(
        strokeWidth=2.4, color=SERIES[1], strokeDash=[6, 4], strokeCap="round").encode(
        x=f"{x}:Q", y="mean:Q",
        tooltip=[alt.Tooltip(f"{x}:Q", format="d"), alt.Tooltip("mean:Q", format=",.0f")])
    end = fc.tail(1)
    end_pt = alt.Chart(end).mark_point(
        filled=True, size=90, color=SERIES[1], stroke=SURFACE, strokeWidth=2).encode(
        x=f"{x}:Q", y="mean:Q")
    end_tx = alt.Chart(end).mark_text(
        align="right", dy=-14, fontSize=11, color=INK_2).encode(
        x=f"{x}:Q", y="mean:Q", text=alt.Text("mean:Q", format=",.0f"))

    return style(alt.layer(band, hist_line, mean_line, end_pt, end_tx)
                 .properties(height=height))


def raster(
    df: pd.DataFrame, value: str, *,
    extent: float = 6.5, cells: int = 66,
    scheme: str = "sequential", title: str = "",
    domain: tuple | None = None, legend_title: str = "",
    points: pd.DataFrame | None = None, point_labels: bool = False,
) -> alt.Chart:
    """A square grid map, drawn as rect marks over the same cells the model uses.

    A raster rather than a polygon layer because what is being shown *is* the
    model's own discretisation. Drawing smoothed contours over it would imply a
    spatial resolution the model does not have.
    """
    size = SHED_PX / cells + 0.25
    if scheme == "diverging":
        limit = float(max(abs(df[value].min()), abs(df[value].max()), 1e-9))
        colour = alt.Color(
            f"{value}:Q", title=legend_title or None,
            scale=alt.Scale(range=DIVERGING, domain=[-limit, limit]),
            legend=alt.Legend(orient="bottom", direction="horizontal",
                              gradientLength=210, gradientThickness=10,
                              titleLimit=200, labelLimit=120))
    else:
        # `domain` is omitted rather than passed as None: an explicit None is a
        # value the schema rejects, where an absent key means "infer it".
        scale_kwargs = {"range": SEQUENTIAL}
        if domain:
            scale_kwargs["domain"] = list(domain)
        colour = alt.Color(
            f"{value}:Q", title=legend_title or None,
            scale=alt.Scale(**scale_kwargs),
            legend=alt.Legend(orient="bottom", direction="horizontal",
                              gradientLength=210, gradientThickness=10,
                              titleLimit=200, labelLimit=120))

    cells_layer = (
        alt.Chart(df)
        .mark_rect(width=size, height=size)
        .encode(
            x=alt.X("x:Q", axis=None, title=None,
                    scale=alt.Scale(domain=[-extent, extent], nice=False)),
            y=alt.Y("y:Q", axis=None, title=None,
                    scale=alt.Scale(domain=[-extent, extent], nice=False)),
            color=colour,
            tooltip=[alt.Tooltip("x:Q", format=".1f"), alt.Tooltip("y:Q", format=".1f"),
                     alt.Tooltip(f"{value}:Q", format=".3f")],
        )
    )

    layers = [cells_layer]
    if points is not None and len(points):
        layers.append(
            alt.Chart(points).mark_point(
                filled=True, size=90, color=SERIES[1], stroke=SURFACE, strokeWidth=2).encode(
                x="x:Q", y="y:Q",
                tooltip=[c for c in ("name", "kind", "note") if c in points.columns])
        )
        if point_labels and "name" in points.columns:
            # A label sitting on this ramp needs a halo, not a colour: the scale
            # runs from near-white to near-black under the same text, so no
            # single ink clears contrast everywhere. A surface-coloured stroke
            # behind the glyphs works at both ends.
            #
            # Placement comes from the data — label offsets and side are columns
            # — because there are eight labels, several of them collide, and
            # hand-placing eight is cheaper than an automatic placer.
            marks = points.copy()
            marks["lx"] = marks["x"] + marks.get("label_dx", 0.0)
            marks["ly"] = marks["y"] + marks.get("label_dy", 0.0)
            #
            # The halo is a separate layer underneath rather than a stroke on
            # the text mark. SVG paints fill before stroke, so a stroke wide
            # enough to be a halo covers the glyph it was meant to protect —
            # which renders the label as an outlined blob. Thick surface-
            # coloured text first, ink text on top.
            side = marks.get("label_align", pd.Series("left", index=marks.index))
            for align, dx in (("left", 9), ("right", -9)):
                subset = marks[side == align]
                if not len(subset):
                    continue
                spec = dict(align=align, dx=dx, fontSize=9.5)
                enc = dict(x="lx:Q", y="ly:Q", text="name:N")
                layers.append(
                    alt.Chart(subset).mark_text(
                        **spec, color=SURFACE, stroke=SURFACE, strokeWidth=3.5,
                        strokeOpacity=0.9).encode(**enc))
                layers.append(
                    alt.Chart(subset).mark_text(**spec, color=INK).encode(**enc))

    # Height carries the plot plus the legend band beneath it; without the
    # extra room the legend is cropped into a nested scrollbar.
    return style(alt.layer(*layers).properties(
        width=SHED_PX, height=SHED_PX, title=title or ""))


def scatter_actual_predicted(df: pd.DataFrame, actual: str = "actual",
                             predicted: str = "predicted", height: int = 280) -> alt.Chart:
    """Backtest predictions against outcomes, with the 45° line of perfection."""
    lo = float(min(df[actual].min(), df[predicted].min()))
    hi = float(max(df[actual].max(), df[predicted].max()))
    pad = (hi - lo) * 0.08 or 1.0
    scale = alt.Scale(domain=[lo - pad, hi + pad], nice=False)

    diagonal = alt.Chart(pd.DataFrame({"v": [lo - pad, hi + pad]})).mark_line(
        strokeWidth=1, color=INK_3, strokeDash=[4, 3]).encode(
        x=alt.X("v:Q", scale=scale, title="actual"),
        y=alt.Y("v:Q", scale=scale, title="predicted"))
    dots = alt.Chart(df).mark_point(
        filled=True, size=90, color=SERIES[0], stroke=SURFACE, strokeWidth=2).encode(
        x=alt.X(f"{actual}:Q", scale=scale, title="actual",
                axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
        y=alt.Y(f"{predicted}:Q", scale=scale, title="predicted",
                axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
        tooltip=["year", alt.Tooltip(f"{actual}:Q", format=",.0f"),
                 alt.Tooltip(f"{predicted}:Q", format=",.0f")])
    return style(alt.layer(diagonal, dots).properties(height=height))


def residual_plot(df: pd.DataFrame, height: int = 200) -> alt.Chart:
    """Residuals against time. Structure here means the model missed something."""
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        strokeWidth=1, color=INK_3).encode(y="y:Q")
    bars = alt.Chart(df).mark_bar(size=3, color=SERIES[0]).encode(
        x=alt.X("year:Q", title="", axis=alt.Axis(format="d", grid=False)),
        y=alt.Y("residual:Q", title="observed − fitted",
                axis=alt.Axis(format=",.0f", grid=True, gridColor=GRID)),
        tooltip=[alt.Tooltip("year:Q", format="d"),
                 alt.Tooltip("residual:Q", format=",.0f")])
    return style(alt.layer(bars, zero).properties(height=height))


def horizontal_bars(df: pd.DataFrame, label: str, value: str, *,
                    x_title: str, height: int = 200, value_format: str = ",.2f",
                    diverging: bool = False, label_limit: int = 320,
                    x_domain: tuple | None = None,
                    rule: float | None = None) -> alt.Chart:
    """Ranked bars with the value at the tip.

    `x_domain` pins the measured axis, for when the bars differ by a small
    amount on a large base and a zero baseline would flatten the difference
    into invisibility. Use it to show a spread, not to exaggerate one.

    `rule` draws a dashed reference line at that value — a threshold the bars
    are read against, such as a naive baseline. It is a line, not a bar, so it
    cannot be mistaken for one more series.
    """
    order = df.sort_values(value, ascending=False)[label].tolist()
    colour = (alt.condition(alt.datum[value] >= 0, alt.value(SERIES[0]), alt.value(SERIES[1]))
              if diverging else alt.value(SERIES[0]))
    x_scale = (alt.Scale(domain=list(x_domain), nice=False) if x_domain
               else alt.Scale(nice=True, padding=8))
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=4, height=16).encode(
        y=alt.Y(f"{label}:N", sort=order, title=None,
                axis=alt.Axis(labelColor=INK, labelFontSize=12, labelLimit=label_limit)),
        x=alt.X(f"{value}:Q", title=x_title,
                scale=x_scale,
                axis=alt.Axis(grid=True, gridColor=GRID)),
        color=colour,
        tooltip=[label, alt.Tooltip(f"{value}:Q", format=value_format)])
    labels = alt.Chart(df).mark_text(
        align="left", dx=8, fontSize=11, color=INK_2).encode(
        y=alt.Y(f"{label}:N", sort=order, title=None),
        x=f"{value}:Q", text=alt.Text(f"{value}:Q", format=value_format))
    layers = [bars, labels]
    if rule is not None:
        layers.append(
            alt.Chart(pd.DataFrame({"x": [rule]})).mark_rule(
                strokeWidth=1.5, color=INK_3, strokeDash=[4, 3]).encode(x="x:Q"))
    return style(alt.layer(*layers).properties(height=height))


def land_split_bar(df: pd.DataFrame, total_km2: float) -> alt.Chart:
    """One bar broken into parts, for a part-to-whole question.

    A stacked single bar rather than a pie: the question is "how much of the
    whole is left", the parts are ordered from most restricted to least, and a
    reader can compare lengths far more accurately than angles.
    """
    order = df.sort_values("order")["part"].tolist()

    # Labels on the segments, not in a legend. A legend above a single stacked
    # bar makes the reader carry three colours down to three blocks that are
    # already big enough to write on — and it was being clipped in half by the
    # chart's own height. Direct labelling removes the legend, the clipping and
    # the lookup in one move.
    plotted = df.sort_values("order").assign(row="")
    plotted["end"] = plotted["km2"].cumsum()
    plotted["mid"] = plotted["end"] - plotted["km2"] / 2
    plotted["share"] = plotted["km2"] / plotted["km2"].sum()
    plotted["value_label"] = [f"{v:,.0f} km²" for v in plotted["km2"]]
    plotted["share_label"] = [f"{s:.0%}" for s in plotted["share"]]

    bar = alt.Chart(plotted).mark_bar(
        stroke=SURFACE, strokeWidth=2, cornerRadiusEnd=4, height=54).encode(
        y=alt.Y("row:N", title=None, axis=None),
        x=alt.X("km2:Q", stack="zero",
                title=f"km² of Cape Town's {total_km2:,.0f} km²",
                # The axis is only there for scale. Its last tick used to sit
                # past the right edge of the container and get cut in half.
                axis=alt.Axis(format="~s", grid=True, gridColor=GRID,
                              values=[0, 500, 1000, 1500, 2000])),
        color=alt.Color("part:N", sort=order,
                        scale=alt.Scale(domain=order,
                                        range=[SERIES[2], SERIES[0], INK_3]),
                        legend=None),
        order=alt.Order("order:Q"),
        tooltip=["part", alt.Tooltip("km2:Q", format=","), "detail"],
    )

    def _text(field: str, dy: int, size: int, weight: str, opacity: float):
        return alt.Chart(plotted).mark_text(
            align="center", baseline="middle", dy=dy, fontSize=size,
            fontWeight=weight, color=SURFACE, opacity=opacity).encode(
            y=alt.Y("row:N", axis=None), x=alt.X("mid:Q"), text=f"{field}:N")

    # Three lines inside each block: what it is, how big, what share.
    name = _text("part", -15, 11, "bold", 1.0)
    value = _text("value_label", 1, 12, "normal", 0.95)
    share = _text("share_label", 17, 11, "normal", 0.75)

    return style(
        alt.layer(bar, name, value, share)
        .properties(height=120, padding={"right": 14, "top": 4})
    )
