"""Chart forms in the Evans/Dediu idiom: one insight per chart.

Two analysts built careers showing that the *transform* is the analysis.
Horace Dediu draws charts where the shape of a curve, or the crossing of two,
is the whole point — trajectories indexed to a base, growth against share,
the year one line passes another — and picks exactly the quantity that hides
the conclusion. Benedict Evans does the same with less flourish: choose the
unit that makes the story, let the reader read it, add nothing else.

This module turns that habit into reusable Altair forms on top of the shared
house style, so a section can pick the lens that fits its question. Three
forms cover most of what the report compares:

  1. `trajectory` — indexed lines, labelled at the line, optional log y. For
     "how fast each thing is growing, compared to itself".
  2. `crossing_time` — two curves whose meeting point is the comment. For
     "when demand passes supply"; the whole point is the year it happens.
  3. `share_vs_growth` — Dediu's scatter/bubble: x is a share, y a growth
     rate, size a third quantity, one point wears a label. For "who is ahead
     and who is gaining".

Each returns a styled Altair chart the caller can drop straight into a figure
frame. `one_insight` writes the single-sentence claim the figure exists to
make, so the argument travels with the chart.
"""

from __future__ import annotations

import pandas as pd
import altair as alt

from .theme import GRID, HIGHLIGHT, INK, INK_2, INK_3, SERIES, SURFACE, style

MUTED = INK_3


def _ends(df: pd.DataFrame, x: str, entity: str) -> pd.DataFrame:
    """The last observation of each series, where its end label goes."""
    return df.sort_values(x).groupby(entity, as_index=False).tail(1)


def trajectory(df: pd.DataFrame, *, x: str, y: str, entity: str,
               highlight: str | None = None, log: bool = False,
               height: int = 330, x_title: str = "", y_title: str = "",
               y_format: str = ",.0f") -> alt.Chart:
    """Indexed lines, labelled at the line, one highlighted.

    The Evans form for "how they grow, compared to themselves": every entity is
    rebased to its own baseline before being passed in, so line height means
    its own rate, not its size. `highlight` picks the one the page is about;
    the rest recede to grey and stay readable as context.

    `log=True` turns the y-axis logarithmic, right when the quantities span
    several orders of magnitude — and it is usually the honest choice for a
    city that grew sixfold, because on a log axis a straight line is a
    constant rate, which is the most useful thing these charts can say.
    """
    scale = alt.Scale(type="log", zero=False) if log else alt.Scale(zero=False)
    if highlight and highlight not in set(df[entity]):
        highlight = None
    colour = (alt.Color(f"{entity}:N",
                        scale=alt.Scale(domain=[highlight], range=[HIGHLIGHT]),
                        legend=None)
              if highlight else
              alt.Color(f"{entity}:N", scale=alt.Scale(range=SERIES), legend=None))
    if highlight:
        stroke = alt.condition(alt.datum[entity] == highlight,
                               alt.value(HIGHLIGHT), alt.value(MUTED))
        opacity = alt.condition(alt.datum[entity] == highlight,
                                alt.value(1.0), alt.value(0.45))
    else:
        stroke = colour
        opacity = alt.value(1.0)

    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format="d", grid=False)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=scale,
                axis=alt.Axis(format=y_format, grid=True, gridColor=GRID)),
        color=colour,
        stroke=stroke,
        opacity=opacity,
    )
    line = base.mark_line(strokeWidth=2.4, strokeCap="round")
    ends = _ends(df, x, entity)
    dot = alt.Chart(ends).mark_point(filled=True, size=70, stroke=SURFACE,
                                     strokeWidth=2).encode(
        x=alt.X(f"{x}:Q", axis=None), y=alt.Y(f"{y}:Q", axis=None), color=colour, opacity=opacity)
    tag = alt.Chart(ends).mark_text(
        align="left", dx=8, fontSize=11, fontWeight="bold", color=INK).encode(
        x=alt.X(f"{x}:Q", axis=None), y=alt.Y(f"{y}:Q", axis=None),
        text=f"{entity}:N", color=colour)
    return style(alt.layer(line, dot, tag)
                 .properties(height=height, padding={"right": 90}))


def crossing_time(df: pd.DataFrame, *, x: str, a: str, b: str,
                  label_a: str, label_b: str, highlighted: tuple[int, int] | None = None,
                  height: int = 330, x_title: str = "", y_format: str = ",.0f",
                  y_title: str = "") -> tuple[alt.Chart, float | None]:
    """Two curves whose crossing is the comment.

    Dediu's "the year it happens" chart: demand growing, supply flat — the eye
    wants to know when the first passes the second, and the chart should say it
    directly. Two lines on a shared axis, the moving one in the highlight, the
    other muted; the crossing year is found by linear interpolation between
    adjacent points and returned so the caller can put it in prose too.

    Returns `(chart, crossing_year)`. `crossing_year` is the x at which `a`
    passes `b` (or None if the lines never cross within the data).
    """
    s = df.sort_values(x)[[x, a, b]].dropna().reset_index(drop=True)
    xv = s[x].to_numpy(dtype=float)
    av = s[a].to_numpy(dtype=float)
    bv = s[b].to_numpy(dtype=float)
    crossing: float | None = None
    for i in range(1, len(s)):
        d0 = av[i - 1] - bv[i - 1]
        d1 = av[i] - bv[i]
        if d0 * d1 < 0:
            frac = d0 / (d0 - d1)
            crossing = float(xv[i - 1] + frac * (xv[i] - xv[i - 1]))
            break

    a_line = alt.Chart(s).mark_line(strokeWidth=2.4, strokeCap="round",
                                    color=HIGHLIGHT).encode(
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format="d", grid=False)),
        y=alt.Y(f"{a}:Q", title=y_title,
                axis=alt.Axis(format=y_format, grid=True, gridColor=GRID)))
    b_line = alt.Chart(s).mark_line(strokeWidth=1.8, strokeDash=[3, 3],
                                    color=MUTED).encode(
        x=alt.X(f"{x}:Q", axis=None, title=x_title),
        y=alt.Y(f"{b}:Q", axis=None, title=y_title))
    end = s.tail(1)
    tags = alt.layer(
        alt.Chart(end).mark_text(align="left", dx=8, fontSize=11,
                                 fontWeight="bold", color=HIGHLIGHT).encode(
            x=alt.X(f"{x}:Q", axis=None), y=alt.Y(f"{a}:Q", axis=None),
            text=alt.value(label_a)),
        alt.Chart(end).mark_text(align="left", dx=8, fontSize=11,
                                 color=INK_2).encode(
            x=alt.X(f"{x}:Q", axis=None), y=alt.Y(f"{b}:Q", axis=None),
            text=alt.value(label_b)))
    chart = style(alt.layer(a_line, b_line, tags)
                  .properties(height=height, padding={"right": 90}))
    return chart, crossing

def share_vs_growth(df: pd.DataFrame, *, share: str, growth: str, size: str,
                    label: str, highlight: str | None = None,
                    share_title: str = "", growth_title: str = "",
                    height: int = 380) -> alt.Chart:
    """Dediu's scatter/bubble: share on x, growth on y, size on the bubbles.

    The question is always the same shape — "who is ahead and who is gaining"
    — and the bubble size carries a third quantity (population, land, spend)
    so one chart answers it without a second axis. `highlight` makes one point
    wear a label and a warmer colour; the rest recede to grey.
    """
    colour = (alt.condition(alt.datum[label] == highlight, alt.value(HIGHLIGHT),
                            alt.value(MUTED))
              if highlight else alt.value(HIGHLIGHT))
    base = alt.Chart(df).encode(
        x=alt.X(f"{share}:Q", title=share_title,
                axis=alt.Axis(grid=True, gridColor=GRID)),
        y=alt.Y(f"{growth}:Q", title=growth_title,
                axis=alt.Axis(grid=True, gridColor=GRID)),
        size=alt.Size(f"{size}:Q", legend=None),
        color=colour,
        tooltip=[label, f"{share}:Q", f"{growth}:Q", f"{size}:Q"],
    )
    points = base.mark_circle(opacity=0.55, stroke=SURFACE, strokeWidth=1)
    if highlight:
        hl = df[df[label] == highlight]
        tag = alt.Chart(hl).mark_text(
            align="left", dx=-9, dy=-24, fontSize=11, fontWeight="bold",
            color=HIGHLIGHT).encode(
            x=alt.X(f"{share}:Q", axis=None), y=alt.Y(f"{growth}:Q", axis=None),
            text=alt.value(highlight))
        chart = alt.layer(points, tag)
    else:
        chart = points
    return style(chart.properties(height=height))


def one_insight(claim: str) -> str:
    """The single-sentence claim a figure exists to make.

    The title's job is to say what is plotted and the deck's to say how to read
    it; this is the *why*. Kept as a plain string so the page can drop it into
    its own caption, making the argument travel with the figure rather than
    after it.
    """
    return claim


__all__ = ["trajectory", "crossing_time", "share_vs_growth", "one_insight"]