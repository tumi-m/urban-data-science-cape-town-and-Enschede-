"""Charts that play, in the Our World in Data manner.

The thing that makes an OWID chart feel alive is not the animation itself, it
is that the animation is *scrubbable*: a play button that walks the years, and
a slider you can drag to any year and stop. The play button is a convenience
over the slider, not a replacement for it, and a chart that can only be watched
is worse than one that can only be read.

Everything here runs server-side through `st.fragment`, which reruns one block
of the page on a timer instead of the whole script. That matters: without it,
each frame re-runs every model on the page. There is no JavaScript and no
external library, so the animation works wherever the app does.

Two forms are provided, and they answer different questions:

  - `animated_lines` reveals series left to right. Use it when the question is
    "what happened, and in what order" — the reveal is doing real work, because
    a plateau you watch arrive reads differently from one already drawn.
  - `animated_scatter` moves points through a plane, the Gapminder form. Use it
    when the question is about the *relationship* between two quantities and
    whether it holds over time.

Both take the same controls, so a reader learns them once.
"""

from __future__ import annotations

from typing import Callable, Sequence

import altair as alt
import pandas as pd
import streamlit as st

from .theme import GRID, INK, INK_2, INK_3, SERIES, SURFACE, style

# Slow enough to read, fast enough that seventy years does not outlast patience.
DEFAULT_SPEED = 0.28


def player(key: str, frames: Sequence, render: Callable[[int], None], *,
           speed: float = DEFAULT_SPEED, label: str = "Year") -> None:
    """Play / pause / reset plus a scrub slider, driving `render(index)`.

    `render` is called once per frame with the index into `frames` and must
    draw the chart. It is called inside a fragment, so anything it draws is
    replaced on the next frame and everything else on the page is left alone.
    """
    ikey, pkey = f"{key}__i", f"{key}__play"
    st.session_state.setdefault(ikey, len(frames) - 1)
    st.session_state.setdefault(pkey, False)
    playing = st.session_state[pkey]

    c1, c2, c3 = st.columns([1.1, 1.0, 6.0], vertical_alignment="center")
    with c1:
        if st.button("⏸  Pause" if playing else "▶  Play",
                     key=f"{key}__b", width="stretch"):
            # Pressing play at the end restarts, rather than doing nothing —
            # which is what a reader who has just watched it means by it.
            if not playing and st.session_state[ikey] >= len(frames) - 1:
                st.session_state[ikey] = 0
            st.session_state[pkey] = not playing
            st.rerun()
    with c2:
        if st.button("↺  Reset", key=f"{key}__r", width="stretch"):
            st.session_state[ikey] = len(frames) - 1
            st.session_state[pkey] = False
            st.rerun()
    with c3:
        if playing:
            st.caption(f"{label}: {frames[min(st.session_state[ikey], len(frames) - 1)]}")
        else:
            st.session_state[ikey] = st.select_slider(
                label, options=list(range(len(frames))),
                value=min(st.session_state[ikey], len(frames) - 1),
                format_func=lambda i: str(frames[i]),
                key=f"{key}__s", label_visibility="collapsed")

    @st.fragment(run_every=speed if playing else None)
    def _frame():
        i = min(st.session_state[ikey], len(frames) - 1)
        render(i)
        if st.session_state[pkey]:
            if i >= len(frames) - 1:
                # Stop at the end and hand the slider back, rather than looping
                # forever and making the reader hunt for the pause button.
                st.session_state[pkey] = False
                st.rerun()
            st.session_state[ikey] = i + 1

    _frame()


# ---------------------------------------------------------------------
# The two chart forms
# ---------------------------------------------------------------------

def _range_for(entities: list, colours: dict[str, str] | None) -> list[str]:
    """Colours for a series list, without ever inventing a fourth identity.

    The palette has three slots that clear the colour-vision separation floor.
    Asking it for five categories would silently produce two nobody can tell
    apart. So anything past the third — and anything not named in `colours` —
    goes grey and becomes context rather than a category. That is the same
    emphasis rule the static charts use.
    """
    if colours:
        return [colours.get(e, INK_3) for e in entities]
    return [SERIES[i] if i < len(SERIES) else INK_3 for i in range(len(entities))]


def lines_upto(df: pd.DataFrame, x: str, y: str, entity: str, upto, *,
               x_title: str, y_title: str, colours: dict[str, str] | None = None,
               log: bool = False, y_format: str = ",.0f",
               height: int = 360, x_domain=None, y_domain=None) -> alt.Chart:
    """One frame of a revealing line chart: everything up to `upto`.

    The axes are pinned to the full extent of the data rather than to the
    visible part. If they were not, the chart would rescale on every frame and
    a series that is merely being revealed would look like one that is moving.
    """
    shown = df[df[x] <= upto]
    entities = list(df[entity].unique())
    rng = _range_for(entities, colours)

    # nice=False, or Vega rounds 1950–2024 outward to 1950–2030 and the chart
    # implies six years of data that do not exist.
    x_scale = (alt.Scale(domain=list(x_domain), nice=False) if x_domain
               else alt.Scale(nice=False))
    y_scale = alt.Scale(type="log") if log else alt.Scale(zero=False)
    if y_domain:
        y_scale = (alt.Scale(type="log", domain=list(y_domain), nice=False) if log
                   else alt.Scale(domain=list(y_domain), nice=False))

    base = alt.Chart(shown).encode(
        x=alt.X(f"{x}:Q", title=x_title, scale=x_scale,
                axis=alt.Axis(format="d", grid=False)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=y_scale,
                axis=alt.Axis(format=y_format, grid=True, gridColor=GRID)),
        color=alt.Color(f"{entity}:N",
                        scale=alt.Scale(domain=entities, range=rng), legend=None),
    )
    line = base.mark_line(strokeWidth=2.4, strokeCap="round", strokeJoin="round")

    heads = shown.sort_values(x).groupby(entity, as_index=False).tail(1)
    dot = alt.Chart(heads).mark_point(
        filled=True, size=80, stroke=SURFACE, strokeWidth=2).encode(
        x=f"{x}:Q", y=f"{y}:Q",
        color=alt.Color(f"{entity}:N",
                        scale=alt.Scale(domain=entities, range=rng), legend=None))
    tag = alt.Chart(heads).mark_text(
        align="left", dx=10, fontSize=11, fontWeight="bold").encode(
        x=f"{x}:Q", y=f"{y}:Q", text=f"{entity}:N",
        color=alt.Color(f"{entity}:N",
                        scale=alt.Scale(domain=entities, range=rng), legend=None))

    return style(alt.layer(line, dot, tag)
                 .properties(height=height, padding={"right": 70}))


def scatter_at(df: pd.DataFrame, x: str, y: str, entity: str, frame_col: str,
               at, *, x_title: str, y_title: str, size: str | None = None,
               colours: dict[str, str] | None = None,
               log_x: bool = True, log_y: bool = False,
               height: int = 380, trail: pd.DataFrame | None = None) -> alt.Chart:
    """One frame of a Gapminder-style scatter, with an optional faded trail.

    The trail is what stops this being a chart you have to remember: without
    it, a bubble that has moved a long way looks exactly like one that has not.
    """
    now = df[df[frame_col] == at]
    entities = list(df[entity].unique())
    rng = _range_for(entities, colours)

    x_scale = alt.Scale(type="log" if log_x else "linear",
                        domain=[df[x].min() * 0.9, df[x].max() * 1.1])
    y_scale = alt.Scale(type="log" if log_y else "linear",
                        domain=[df[y].min() * 0.9, df[y].max() * 1.1])
    colour = alt.Color(f"{entity}:N",
                       scale=alt.Scale(domain=entities, range=rng), legend=None)

    layers = []
    if trail is not None and len(trail):
        layers.append(
            alt.Chart(trail[trail[frame_col] <= at])
            .mark_line(strokeWidth=1.4, opacity=0.30, strokeCap="round")
            .encode(x=alt.X(f"{x}:Q", scale=x_scale), y=alt.Y(f"{y}:Q", scale=y_scale),
                    color=colour, detail=f"{entity}:N")
        )

    enc = dict(
        x=alt.X(f"{x}:Q", title=x_title, scale=x_scale,
                axis=alt.Axis(format="~s", grid=True, gridColor=GRID)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=y_scale,
                axis=alt.Axis(format="~s", grid=True, gridColor=GRID)),
        color=colour,
        tooltip=[entity, alt.Tooltip(f"{frame_col}:Q", format="d"),
                 alt.Tooltip(f"{x}:Q", format=",.0f"),
                 alt.Tooltip(f"{y}:Q", format=",.0f")],
    )
    if size:
        enc["size"] = alt.Size(f"{size}:Q",
                               scale=alt.Scale(range=[120, 2200]), legend=None)

    layers.append(alt.Chart(now).mark_point(
        filled=True, opacity=0.82, stroke=SURFACE, strokeWidth=1.5).encode(**enc))
    layers.append(alt.Chart(now).mark_text(
        align="left", dx=16, fontSize=11, fontWeight="bold").encode(
        x=alt.X(f"{x}:Q", scale=x_scale), y=alt.Y(f"{y}:Q", scale=y_scale),
        text=f"{entity}:N", color=colour))

    # The year, set large and pale behind the points. Straight from the
    # Gapminder original, and it is there so the reader never has to look away
    # from the plot to know where they are. Positioned in pixels off the known
    # height and the left edge — the width is decided by the container at
    # render time, so anything anchored to the right could land off-canvas.
    stamp = alt.Chart(pd.DataFrame({"t": [str(at)]})).mark_text(
        align="left", baseline="bottom", fontSize=52,
        fontWeight="bold", opacity=0.11, color=INK).encode(
        x=alt.value(12), y=alt.value(height - 12), text="t:N")

    return style(alt.layer(*layers, stamp)
                 .properties(height=height, padding={"right": 80}))
